""" 第三方类库自定义拓展模块. """
import typing as t
from importlib import util

from flask.globals import current_app
from flask.globals import request
from flask_mongoengine import BaseQuerySet
from flask_mongoengine import Pagination

from lesoon_common.globals import request


class LesoonQuerySet(BaseQuerySet):

    def paginate(self,
                 if_page: t.Optional[bool] = None,
                 page: t.Optional[int] = None,
                 per_page: t.Optional[int] = None):
        """
        执行分页查询.

        Args:
            if_page: 是否分页
            page: 页码
            per_page: 页大小
        """
        page = page or request.page  # type:ignore
        per_page = per_page or request.page_size  # type:ignore
        if_page = if_page or request.if_page  # type:ignore

        if if_page:
            return Pagination(self, page, per_page)
        else:
            return self.select_related()


if not util.find_spec('pymongo'):

    class CommandLogger:
        pass
else:
    from pymongo.monitoring import CommandListener

    class CommandLogger(CommandListener):  # type:ignore

        def started(self, event):
            current_app.logger.debug('Command {0.command_name} with request id '
                                     '{0.request_id} started on server '
                                     '{0.connection_id}'.format(event))

        def succeeded(self, event):
            current_app.logger.debug(
                'Command {0.command_name} with request id '
                '{0.request_id} on server {0.connection_id} '
                'succeeded in {0.duration_micros} '
                'microseconds'.format(event))

        def failed(self, event):
            current_app.logger.debug(
                'Command {0.command_name} with request id '
                '{0.request_id} on server {0.connection_id} '
                'failed in {0.duration_micros} '
                'microseconds'.format(event))
