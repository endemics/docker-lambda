from __future__ import print_function
import sys
import os
import random
import uuid
import time
import resource
import datetime

orig_stdout = sys.stdout
orig_stderr = sys.stderr

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def _random_account_id():
  return random.randint(100000000000, 999999999999)

def _random_invoke_id():
    return str(uuid.uuid4())

def _get_from_env(key, default):
    if key in os.environ:
        return os.environ[key]
    else:
        return default

def _arn(region, account_id, fct_name):
  return 'arn:aws:lambda:%s:%s:function:%s' % (region, account_id, fct_name)

_GLOBAL_HANDLER = sys.argv[1] if len(sys.argv) > 1 else _get_from_env('AWS_LAMBDA_FUNCTION_HANDLER', 'lambda_function.lambda_handler')
_GLOBAL_EVENT_BODY = sys.argv[2] if len(sys.argv) > 2 else _get_from_env('AWS_LAMBDA_EVENT_BODY', '{}')
_GLOBAL_FCT_NAME = _get_from_env('AWS_LAMBDA_FUNCTION_NAME', 'test')
_GLOBAL_VERSION = _get_from_env('AWS_LAMBDA_FUNCTION_VERSION', '$LATEST')
_GLOBAL_MEM_SIZE = _get_from_env('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 1536)
_GLOBAL_TIMEOUT = _get_from_env('AWS_LAMBDA_FUNCTION_TIMEOUT', 300)
_GLOBAL_REGION = _get_from_env('AWS_REGION', 'us-east-1')
_GLOBAL_ACCOUNT_ID = _get_from_env('AWS_ACCOUNT_ID', _random_account_id())
_GLOBAL_ACCESS_KEY_ID = _get_from_env('AWS_ACCESS_KEY_ID', 'SOME_ACCESS_KEY_ID')
_GLOBAL_SECRET_ACCESS_KEY = _get_from_env('AWS_SECRET_ACCESS_KEY', 'SOME_SECRET_ACCESS_KEY')
_GLOBAL_SESSION_TOKEN = _get_from_env('AWS_SESSION_TOKEN', None)

_GLOBAL_INVOKEID = _random_invoke_id()
_GLOBAL_MODE = 'event' # Either 'http' or 'event'
_GLOBAL_SUPRESS_INIT = True # Forces calling _get_handlers_delayed()
_GLOBAL_DATA_SOCK = -1
_GLOBAL_CONTEXT_OBJS = {
    'clientcontext': None,
    'cognitoidentityid': None,
    'cognitopoolid': None,
}
_GLOBAL_CREDENTIALS = {
    'key': _GLOBAL_ACCESS_KEY_ID,
    'secret': _GLOBAL_SECRET_ACCESS_KEY,
    'session': _GLOBAL_SESSION_TOKEN
}
_GLOBAL_INVOKED_FUNCTION_ARN = _arn(_GLOBAL_REGION, _GLOBAL_ACCOUNT_ID, _GLOBAL_FCT_NAME)
_GLOBAL_INVOKED = False
_GLOBAL_ERRORED = False
_GLOBAL_START_TIME = None
_GLOBAL_TODAY = datetime.date.today()
# export needed stuff
os.environ['AWS_LAMBDA_LOG_GROUP_NAME'] = '/aws/lambda/%s' % _GLOBAL_FCT_NAME
os.environ['AWS_LAMBDA_LOG_STREAM_NAME'] = "%s/%s/%s/[%s]%s" % (
        _GLOBAL_TODAY.year,
        _GLOBAL_TODAY.month,
        _GLOBAL_TODAY.day,
        _GLOBAL_VERSION,
        '%016x' % random.randrange(16**16)
    )
os.environ["AWS_LAMBDA_FUNCTION_NAME"] = _GLOBAL_FCT_NAME
os.environ['AWS_LAMBDA_FUNCTION_MEMORY_SIZE'] = str(_GLOBAL_MEM_SIZE)
os.environ['AWS_LAMBDA_FUNCTION_VERSION'] = _GLOBAL_VERSION
os.environ['AWS_REGION'] = _GLOBAL_REGION
os.environ['AWS_DEFAULT_REGION'] = _GLOBAL_REGION

def recv_start(ctrl_sock):
    sys.stdout = orig_stdout
    sys.stderr = orig_stderr
    return (
        _GLOBAL_INVOKEID,
        _GLOBAL_MODE,
        _GLOBAL_HANDLER,
        _GLOBAL_SUPRESS_INIT,
        _GLOBAL_CREDENTIALS
    )

def report_running(invokeid):
    return

def receive_invoke(ctrl_sock):
    global _GLOBAL_INVOKED
    global _GLOBAL_START_TIME

    if not _GLOBAL_INVOKED:
        eprint(
            "START RequestId: %s Version: %s" %
            (_GLOBAL_INVOKEID, _GLOBAL_VERSION)
        )
        _GLOBAL_INVOKED = True
        _GLOBAL_START_TIME = time.time()

    return (
        _GLOBAL_INVOKEID,
        _GLOBAL_DATA_SOCK,
        _GLOBAL_CREDENTIALS,
        _GLOBAL_EVENT_BODY,
        _GLOBAL_CONTEXT_OBJS,
        _GLOBAL_INVOKED_FUNCTION_ARN
    )

def report_fault(invokeid, msg, except_value, trace):
    global _GLOBAL_ERRORED

    _GLOBAL_ERRORED = True

    if msg and except_value:
        eprint('%s: %s' % (msg, except_value))
    if trace:
        eprint('%s' % trace)
    return

def report_done(invokeid, errortype, result):
    global _GLOBAL_INVOKED
    global _GLOBAL_ERRORED

    if _GLOBAL_INVOKED:
        eprint("END RequestId: %s" % invokeid)

        duration = int((time.time() - _GLOBAL_START_TIME) * 1000)
        billed_duration = min(100 * ((duration / 100) + 1), _GLOBAL_TIMEOUT * 1000)
        max_mem = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)

        eprint(
            "REPORT RequestId: %s Duration: %s ms Billed Duration: %s ms Memory Size: %s MB Max Memory Used: %s MB" % (
                invokeid, duration, billed_duration, _GLOBAL_MEM_SIZE, max_mem
            )
        )
        if result:
            print(result)
        sys.exit(1 if _GLOBAL_ERRORED else 0)
    else:
        return

def log_bytes(msg, fileno):
    eprint(msg)
    return

def get_remaining_time():
    return ((_GLOBAL_TIMEOUT * 1000) - int((time.time() - _GLOBAL_START_TIME) * 1000))

def send_console_message(msg):
    eprint(msg)
    return
