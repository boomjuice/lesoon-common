from .base import BaseCode


class PyMysqlCode(BaseCode):
    # DataError
    WARN_DATA_TRUNCATED = (1265, "truncate语法警告", "请避免使用truncate语法")
    WARN_NULL_TO_NOTNULL = (1263, "null到not null转换警告", "请检查数据是否合法")
    WARN_DATA_OUT_OF_RANGE = (1264, "数据越界警告", "请检查数据是否合法")
    NO_DEFAULT = (1230, "没有默认值", "请检查是否设置默认值或数据缺失")
    PRIMARY_CANT_HAVE_NULL = (1171, "主键不能为空", "请检查数据是否合法")
    DATA_TOO_LONG = (1406, "数据超长", "请检查数据是否合法")
    DATETIME_FUNCTION_OVERFLOW = (1441, "datetime函数溢出", "请检查日期时间数据是否合法")
    TRUNCATED_WRONG_VALUE_FOR_FIELD = (1366, "", "请检查执行SQL")
    ILLEGAL_VALUE_FOR_TYPE = (1367, "数据类型不匹配", "请检查数据类型是否合法")

    # IntegrityError
    DUP_ENTRY = (1062, "数据已存在", "请重新编辑")
    BAD_NULL_ERROR = (1048, "列值不能为空", "请检查数据是否合法")

    # NotSupportedError
    WARNING_NOT_COMPLETE_ROLLBACK = (1196, "不能回滚某些非事务性已变动表", "请检查执行SQL")
    NOT_SUPPORTED_YET = (1235, "当前版本暂不支持", "请联系DBA")
    FEATURE_DISABLED = (1289, "特性已禁止", "请联系DBA")
    DBACCESS_DENIED_ERROR = (1044, "数据库拒绝访问", "请联系DBA")
    ACCESS_DENIED_ERROR = (1045, "拒绝访问", "请联系DBA")
    CON_COUNT_ERROR = (1040, "连接过多", "请稍后再进行尝试")
    TABLEACCESS_DENIED_ERROR = (1142, "表拒绝访问", "请联系DBA")
    COLUMNACCESS_DENIED_ERROR = (1143, "列拒绝访问", "请联系DBA")
    LOCK_DEADLOC = (1213, "发生死锁", "请稍后再进行尝试")
