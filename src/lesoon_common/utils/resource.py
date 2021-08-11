import datetime as dt
import decimal
import logging

from flask_sqlalchemy import Model
from marshmallow.utils import from_iso_datetime

from ..dataclass.resource import ImportData
from ..dataclass.resource import ImportParseResult
from ..exceptions import ServiceError
from ..parse.sqla import parse_attribute_name
from ..response import ResponseCode
from ..utils.str import udlcase

log = logging.getLogger(__name__)


def parse_import_data(
    import_data: ImportData, model: Model, check_exist: bool = False
) -> ImportParseResult:
    # 初始化数据
    union_key_set = {udlcase(mk) for mk in import_data.union_key}
    union_key_value_set = set()
    obj_list = list()
    err_output_list = list()
    err_extract_list = list()
    col_attrs = list()

    try:
        flag = True
        for col_name in import_data.col_names:
            attr = parse_attribute_name(col_name, model)
            if attr is None:
                raise AttributeError(f"{model}不存在列:{col_name}")
            col_attrs.append(attr)

        for rid, row in enumerate(import_data.data_list):
            union_key_value = ""
            union_filter = list()
            obj = model()
            for cid, attr in enumerate(col_attrs):
                if cid >= len(row):
                    raise AttributeError(f"列[{attr.name}]在数据集中不存在")
                col_value = row[cid]

                # 位置, chr将cid转换为大写字母
                excel_position = (
                    f"Excel [{rid + import_data.import_start_index}行,{chr(65 + cid)}列]"
                    f"{attr.name}:{col_value}"
                )

                # 值为空
                if not bool(col_value):
                    # 不允许为空
                    if import_data.must_array[cid]:
                        err_output_list.append(excel_position + "不能为空")
                        flag = False
                        break
                    # 允许为空
                    else:
                        continue

                # 类型检测
                if attr.type.python_type is int:
                    if not col_value.lstrip("-").isdigit():
                        err_output_list.append(excel_position + "必须为整数")
                        flag = False
                        break

                if attr.type.python_type in (decimal.Decimal, float):
                    if not col_value.lstrip("-").replace(",", "", 1).isdigit():
                        err_output_list.append(excel_position + "必须为数值")
                        flag = False
                        break

                if attr.type.python_type is dt.datetime:
                    try:
                        col_value = from_iso_datetime(col_value)
                    except ValueError:
                        err_output_list.append(excel_position + "日期格式无法解析,需遵循ISO8601标准")
                        flag = False
                        break

                # 约束赋值
                if attr.name in union_key_set:
                    union_key_value += col_value
                    union_filter.append(attr.__eq__(col_value))

                # 设置对象值
                setattr(obj, attr.name, col_value)

            if union_key_value:
                if union_key_value in union_key_value_set:
                    # excel中是否已存在当前数据
                    err_output_list.append(
                        f"Excel [{rid + import_data.import_start_index}行,] "
                        f"违反唯一约束[{import_data.union_key_name}]"
                    )
                    flag = False
                    continue
                else:
                    union_key_value_set.add(union_key_value)

                if check_exist and model.query.filter(*union_filter).count():
                    msg_detail = (
                        f"Excel [{rid + import_data.import_start_index}行,] "
                        f"根据约束[{import_data.union_key_name}]数据已存在"
                    )
                    flag = False
                    if import_data.validate_all:
                        err_extract_list.append(msg_detail)
                    else:
                        raise ValueError(msg_detail)

            if flag:
                obj_list.append(obj)

    except Exception as e:
        raise ServiceError(ResponseCode.Error, f"导入数据异常:{e}")

    log.info(f"解析成功的行数为:{len(obj_list)}")
    import_parse_result = ImportParseResult(obj_list, err_output_list, err_extract_list)
    return import_parse_result
