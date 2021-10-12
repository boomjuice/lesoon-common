import os
import errno
import signal
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError


def timeout(seconds=2, error_message=os.strerror(errno.ETIMEDOUT)):
    def decorator(fn):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = fn(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


def check_db():
    from lesoon_common.extensions import db
    try:
        db.engine.execute("SELECT 1")
        return True, "数据库连接正常"
    except SQLAlchemyError as e:
        return False, f"数据库连接异常:{e}"
