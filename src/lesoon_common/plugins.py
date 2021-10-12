""" 自定义的flask拓展插件模块."""
import typing as t
import time
import sys
from flask import Flask
from flask import current_app
from werkzeug.utils import import_string

from lesoon_common.response import success_response
from lesoon_common.response import error_response
from lesoon_common.utils.health_check import timeout


class HealthCheck(object):
    """
    为确保在应用运行中各组件正常,需要作健康检查.
    该类通过自定义的检查函数来检查各组件是否正常,且有缓存机制.

    Attributes:
        cache: 检查结果缓存字典
        err_timeout: 每个检查函数的超时时间
        checkers: 检查函数列表
        success_ttl: 检查通过的缓存时间
        failure_ttl: 检查失败的缓存时间

    """

    def __init__(self, app: Flask = None):
        self.cache = dict()
        self.headers = {"Content-Type": "application/json"}
        self.err_timeout = 0
        self.success_ttl = 0
        self.failure_ttl = 0
        self.checkers = list()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        for k, v in self._default_config().items():
            app.config.setdefault(k, v)

        if sys.platform != 'win32':
            # windows下面无signal.SIGALRM
            self.err_timeout = app.config['HEALTH_CHECK_TIMEOUT']
        self.success_ttl = app.config['HEALTH_CHECK_SUCCESS_TTL']
        self.failure_ttl = app.config['HEALTH_CHECK_FAILURE_TTL']
        for checker_path in app.config['HEALTH_CHECK_DEFAULT_CHECKERS']:
            try:
                checker = import_string(checker_path)
            except ImportError as e:
                app.logger.warning(f"'{checker_path}'导入异常:{e}")
                checker = None

            if checker:
                self.checkers.append(checker)

        if '/health' not in {r.rule for r in app.url_map.iter_rules()}:
            app.add_url_rule(rule='/health',
                             endpoint="health_check",
                             view_func=self.run)
        app.extensions['health_check'] = self

    def _default_config(self) -> dict:
        return {
            # 每个检查函数的超时时间
            'HEALTH_CHECK_TIMEOUT': 5,
            # 检查通过的缓存时间
            'HEALTH_CHECK_SUCCESS_TTL': 20,
            # 检查失败的缓存时间
            'HEALTH_CHECK_FAILURE_TTL': 5,
            # 默认的检查函数列表
            'HEALTH_CHECK_DEFAULT_CHECKERS': [
                'lesoon_common.utils.health_check.check_db'
            ],
        }

    def add_check(self, func: t.Callable):
        self.checkers.append(func)

    def run(self):
        results = []
        filtered = [c for c in self.checkers]
        for checker in filtered:
            if (checker in self.cache and
                self.cache[checker].get('expires') >= time.time()):
                result = self.cache[checker]
            else:
                result = self.run_check(checker)
                self.cache[checker] = result
            results.append(result)

        passed = all([result['passed'] for result in results])

        if passed:
            return success_response(output=results), 200, self.headers
        else:
            return error_response(output=results), 500, self.headers

    def run_check(self, checker: t.Callable) -> dict:
        start_time = time.time()

        try:
            if self.err_timeout > 0:
                passed, output = timeout(
                    self.err_timeout, "健康检查超时!")(checker)()
            else:
                passed, output = checker()
        except Exception as e:
            current_app.logger.exception(e)
            passed, output = False, e
        finally:
            elapsed_time = time.time() - start_time
            elapsed_time = float('{:.6f}'.format(elapsed_time))

        if passed:
            msg = f"健康检查:{checker.__name__} 通过"
            expires = time.time() + self.success_ttl
            current_app.logger.debug(msg)
        else:
            msg = f"健康检查: {checker.__name__} 异常:{output}"
            expires = time.time() + self.failure_ttl
            current_app.logger.error(msg)

        result = {'checker': checker.__name__,
                  'passed': passed,
                  'output': output,
                  'expires': expires,
                  'elapsed_time': elapsed_time}
        return result
