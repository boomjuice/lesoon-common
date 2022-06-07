""" 自定义的flask拓展插件模块."""
import configparser
import os
import sys
import time
import typing as t
import warnings

import filelock
import jaeger_client
import yaml
from flask_opentracing import FlaskTracing
from jaeger_client import config as jaeger_config
from opentracing.ext import tags
from opentracing_instrumentation.client_hooks import install_all_patches
from werkzeug.utils import import_string

from lesoon_common.globals import current_app
from lesoon_common.response import error_response
from lesoon_common.response import success_response
from lesoon_common.utils.health_check import timeout

if t.TYPE_CHECKING:
    from lesoon_common.base import LesoonFlask


class HealthCheck:
    """
    为确保在应用运行中各组件正常,需要做健康检查.
    该类通过自定义的检查函数来检查各组件是否正常,且有缓存机制.

    Attributes:
        cache: 检查结果缓存字典
        err_timeout: 每个检查函数的超时时间
        checkers: 检查函数列表
        success_ttl: 检查通过的缓存时间
        failure_ttl: 检查失败的缓存时间

    """

    def __init__(self, app: t.Optional['LesoonFlask'] = None):
        self.cache: t.Dict[t.Callable, dict] = dict()
        self.headers = {'Content-Type': 'application/json'}
        self.err_timeout = 0
        self.success_ttl = 0
        self.failure_ttl = 0
        self.checkers: t.List[t.Callable] = list()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: 'LesoonFlask'):
        healthcheck_config = app.config.get('HEALTH_CHECK', {})
        for k, v in self._default_config().items():
            healthcheck_config.setdefault(k, v)

        if sys.platform != 'win32':
            # windows下面无signal.SIGALRM
            self.err_timeout = healthcheck_config['TIMEOUT']
        self.success_ttl = healthcheck_config['SUCCESS_TTL']
        self.failure_ttl = healthcheck_config['FAILURE_TTL']
        for checker_path in healthcheck_config['DEFAULT_CHECKERS']:
            try:
                checker = import_string(checker_path)
            except ImportError as e:
                app.logger.warning(f"'{checker_path}'导入异常:{e}")
                checker = None

            if checker:
                self.checkers.append(checker)

        if '/health' not in {r.rule for r in app.url_map.iter_rules()}:
            app.add_url_rule(rule='/health',
                             endpoint='health_check',
                             view_func=self.run)
        app.extensions['health_check'] = self

    @staticmethod
    def _default_config() -> dict:
        return {
            # 每个检查函数的超时时间
            'TIMEOUT': 5,
            # 检查通过的缓存时间
            'SUCCESS_TTL': 20,
            # 检查失败的缓存时间
            'FAILURE_TTL': 5,
            # 默认的检查函数列表
            'DEFAULT_CHECKERS': ['lesoon_common.utils.health_check.check_db'],
        }

    def add_check(self, func: t.Callable):
        self.checkers.append(func)

    def run(self):
        """
        健康检查入口.
        运行正常则缓存结果,异常也会缓存结果以防止频繁访问.
        Returns:
            response: `lesoon-common.Response`
            status_code:
                success = 200
                failure = 500
        """
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
        """
        运行健康检查函数.
        Args:
            checker: 健康检查函数

        """
        start_time = time.time()

        try:
            if self.err_timeout > 0:
                passed, output = timeout(self.err_timeout, '健康检查超时!')(checker)()
            else:
                passed, output = checker()
        except Exception as e:
            current_app.logger.exception(e)
            passed, output = False, e
        finally:
            elapsed_time = time.time() - start_time
            elapsed_time = float(f'{elapsed_time:.6f}')

        if passed:
            msg = f'健康检查:{checker.__name__} 通过'
            expires = time.time() + self.success_ttl
            current_app.logger.debug(msg)
        else:
            msg = f'健康检查: {checker.__name__} 异常:{output}'
            expires = time.time() + self.failure_ttl
            current_app.logger.error(msg)

        result = {
            'checker': checker.__name__,
            'passed': passed,
            'output': output,
            'expires': expires,
            'elapsed_time': elapsed_time
        }
        return result


class EnvInterpolation(configparser.ExtendedInterpolation):
    """环境变量插值拓展."""

    def before_get(self, parser, section, option, value, defaults):
        if (env_var := os.path.expandvars(value)) != value:
            # 存在环境变量
            return str(env_var)
        else:
            # 不存在于环境变量,不存在值会返回[DEFAULT]中的默认值
            return super().before_get(parser, section, option, value, defaults)


class Bootstrap:
    """ 配置引导拓展.
    主要用于配置的自动读取以及热更新
    目前支持kubernetes.configmap,apollo方式.

    Attributes:
        bootstrap_filename: 引导文件名, 默认为 bootstrap.cfg
        config_filename: 配置文件名, 默认为app.config_path
    """
    BOOTSTRAP_FILENAME = 'bootstrap.cfg'

    FIXED_SECTIONS = {'app', 'config'}

    # K8S项名称
    KUBERNETES_SECTION = 'kubernetes.config'

    # Apollo项名称
    APOLLO_SECTION = 'apollo.config'

    def __init__(self,
                 bootstrap_filename: t.Optional[str] = None,
                 app: t.Optional['LesoonFlask'] = None):
        self.BOOTSTRAP_FILENAME = bootstrap_filename or self.BOOTSTRAP_FILENAME
        self.config_filename = app.config_path  # type:ignore
        if app:
            self.init_app(app)

    def init_app(self, app: 'LesoonFlask'):
        parser = configparser.ConfigParser(interpolation=EnvInterpolation())

        # 读取bootstrap配置
        if not parser.read(self.BOOTSTRAP_FILENAME):
            warnings.warn(f'启动配置:{self.BOOTSTRAP_FILENAME}不存在', RuntimeWarning)
            return
        if not all([parser.has_section(sec) for sec in self.FIXED_SECTIONS]):
            raise RuntimeError(f'必须配置以下sections:{self.FIXED_SECTIONS}')

        if parser.getboolean('config', 'kubernetes_enabled', fallback=False):
            # 通过k8s读取配置
            self.reload_config_from_configmap(parser=parser, app=app)

        if parser.getboolean('config', 'apollo_enabled', fallback=False):
            # 通过apollo读取配置
            self.reload_config_from_apollo(parser=parser, app=app)

        if parser.getboolean('config', 'prometheus_enabled', fallback=False):
            self.init_prometheus_client(app=app)

    @staticmethod
    def rewrite_config(app: 'LesoonFlask', rewrite_type: str,
                       config_filename: str, content: str):
        success_filename = 'config_rewrite.success'
        if not os.path.exists(success_filename):
            try:
                with filelock.FileLock('config.lock', timeout=0):
                    app.logger.info(f'已获取文件锁,正在从{rewrite_type}中重载配置文件...')
                    with open(config_filename, mode='w',
                              encoding='utf-8') as fp:
                        app.logger.info(
                            f'正在将{rewrite_type}中配置写入{config_filename}')
                        fp.write(content)
                    open(success_filename, 'w').close()
            except filelock.Timeout:
                app.logger.info('文件锁已被占领, 等待其他进程重载配置文件...')
        while not os.path.lexists(success_filename):
            continue
        if os.path.exists(success_filename):
            os.remove(success_filename)
        app.__class__.config_path = config_filename

    def reload_config_from_configmap(self, parser: configparser.ConfigParser,
                                     app: 'LesoonFlask'):
        """
        从k8s.configmap获取配置文件,写入本地的配置文件中.
        Args:
            parser: `configparser.ConfigParser`
            app: `LesoonFlask`

        """
        if not parser.has_section(self.KUBERNETES_SECTION):
            raise RuntimeError(f'{self.BOOTSTRAP_FILENAME}配置异常:'
                               f'不存在名为{self.KUBERNETES_SECTION}的section')
        from kubernetes import client, config
        name = parser.get(self.KUBERNETES_SECTION, 'name')
        namespace = parser.get(self.KUBERNETES_SECTION,
                               'namespace',
                               fallback='default')
        env_flag = parser.get(self.KUBERNETES_SECTION, 'env')
        app.logger.info(f'正在获取k8s configmap, name:{name} namespace:{namespace}')

        # 获取configmap
        config.load_incluster_config()
        k8s_api = client.CoreV1Api()

        config_filename = f'{env_flag}-{self.config_filename}'
        # cm = {"xx.py":"python code"}
        cm = k8s_api.read_namespaced_config_map(name=name, namespace=namespace)

        # configmap中存储的为python文件的字符串格式
        content = cm.data.get(f'{name}.yml')
        self.rewrite_config(app=app,
                            rewrite_type='K8S',
                            content=content,
                            config_filename=config_filename)

    @staticmethod
    def _convert_properties_to_dict(config: dict) -> dict:
        """
        将properties格式的键转换为嵌套字典
        Args:
            config: 存在properties格式的键
            e.q: {'a.b.c':1,'a.b.d':2} => {'a':{'b':{'c':1,'d':2}}}

        Returns:

        """
        new_config: dict = {}
        for k, v in config.items():
            if '.' in k:
                keys = k.split('.')
                ck = new_config
                for i in keys[:-1]:
                    if i not in ck:
                        ck[i] = {}
                    ck = ck[i]
                ck[keys[-1]] = v
            else:
                new_config[k] = v
        return new_config

    def reload_config_from_apollo(self, parser: configparser.ConfigParser,
                                  app: 'LesoonFlask'):
        """
        从apollo获取配置,写入本地的配置文件中.
        Args:
            parser: `configparser.ConfigParser`
            app: `LesoonFlask`

        """
        if not parser.has_section(self.APOLLO_SECTION):
            raise RuntimeError(f'{self.BOOTSTRAP_FILENAME}配置异常:'
                               f'不存在名为{self.APOLLO_SECTION}的section')

        name = parser.get(self.APOLLO_SECTION, 'name')
        name = name if name.startswith('api') else f'{name}-api'
        server_url = parser.get(self.APOLLO_SECTION, 'server_url')
        env_flag = parser.get(self.APOLLO_SECTION, 'env')
        namespaces = parser.get(self.APOLLO_SECTION, 'namespaces')
        from apollo_client_python import ApolloClient

        client = ApolloClient(app_id=name,
                              config_url=server_url,
                              namespaces=namespaces,
                              start_hot_update=False)

        app.logger.info(f'正在获取apollo配置, name:{name} namespaces:{namespaces}')

        config_filename = f'{env_flag}-{self.config_filename}'

        config = self._convert_properties_to_dict(client.get_config())
        self.rewrite_config(
            app=app,
            rewrite_type='Apollo',
            content=yaml.safe_dump(config).replace("'", ''),  # type: ignore
            config_filename=config_filename,
        )

    def init_prometheus_client(self, app: 'LesoonFlask'):
        if os.environ.get('gunicorn_flag', False):
            from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
            metrics = GunicornPrometheusMetrics(app)
            setattr(app, 'metrics', metrics)


class LinkTracer:
    """ 链路跟踪器. """

    @staticmethod
    def _default_config() -> dict:
        return {
            # 链路跟踪类型
            'TYPE': 'jaeger',
            # 是否开启链路跟踪
            'ENABLED': False,
            # jaeger跟踪配置
            'JAEGER': {
                # 应用名称
                'SERVICE_NAME': 'tracer-default',
                # 日志输出
                'LOGGING': True,
                # 生成128位trace_id
                'GENERATE_128BIT_TRACE_ID': True,
                # 每个RPC请求生成一个SPAN
                'ONE_SPAN_PER_RPC': True,
                # 采样类型
                'SAMPLER_TYPE': 'const',
                # 采样参数
                'SAMPLER_PARAM': True
            }
        }

    def init_app(self, app: 'LesoonFlask'):
        """
        初始化链路跟踪器jaeger.
        Args:
            app: `LesoonFlask`

        """
        tracing_config = app.config.get('TRACING', {})
        for k, v in self._default_config().items():
            tracing_config.setdefault(k, v)

        if tracing_config.get('ENABLED', False):
            tracing_type = tracing_config.get('TYPE')
            if tracing_type == 'jaeger':
                self.init_jaeger_tracing(app=app, tracing_config=tracing_config)
            else:
                raise RuntimeError(f'不支持的链路跟踪类型:{tracing_type}')

    def init_jaeger_tracing(self, app: 'LesoonFlask', tracing_config: dict):
        config: dict = tracing_config.get('JAEGER')  # type:ignore
        for k, v in self._default_config().get('JAEGER', {}).items():
            config.setdefault(k, v)

        service_name = config.get('SERVICE_NAME')
        if not service_name:
            warnings.warn(
                'TRACING.JAEGER_CONFIG.SERVICE_NAME为空, jaeger链路跟踪初始化异常',
                RuntimeWarning)
            return

        # tracer参数
        sampler_type = config.get('SAMPLER_TYPE')
        sampler_param = config.get('SAMPLER_PARAM')
        logging = config.get('LOGGING')
        generate_128bit_trace_id = config.get('GENERATE_128BIT_TRACE_ID')
        one_span_per_rpc = config.get('ONE_SPAN_PER_RPC')

        jc = jaeger_config.Config(
            service_name=service_name,
            config={
                'sampler': {
                    'type': sampler_type,
                    'param': sampler_param,
                },
                'logging': logging,
                'propagation': 'b3',
                'generate_128bit_trace_id': generate_128bit_trace_id,
                # FlaskTracing集成jaeger-client时此处存在bug,
                # 初始化span的时候未设置span.kind为rpc,
                # 会导致此时的span永远是新的对象,无法继承父类的span,
                # 导致链路信息断层无法收集,jaeger上无法显示链路信息
                # 具体判断逻辑见`jaeger_client.tracer.py:182`
                'tags': {
                    tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER
                }
            },
            validate=True)
        tracer: jaeger_client.Tracer = jc.initialize_tracer(
        )  # type:ignore[assignment]
        tracer.one_span_per_rpc = one_span_per_rpc  # type:ignore[assignment]
        # 加载通用跟踪钩子
        install_all_patches()
        app.extensions['link_tracer'] = FlaskTracing(tracer=tracer,
                                                     trace_all_requests=True,
                                                     app=app)
