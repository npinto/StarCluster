"""
StarCluster logging module
"""
import os
import sys
import types
import logging
import logging.handlers
import textwrap
import StringIO

from starcluster import static

INFO = logging.INFO
DEBUG = logging.DEBUG
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
RAW = "raw"

RAW_FORMAT = "%(message)s"
INFO_FORMAT = " ".join([">>>", RAW_FORMAT])
DEFAULT_CONSOLE_FORMAT = " - ".join(["%(levelname)s", RAW_FORMAT])
ERROR_CONSOLE_FORMAT = " ".join(["!!!", DEFAULT_CONSOLE_FORMAT])
WARN_CONSOLE_FORMAT = " ".join(["***", DEFAULT_CONSOLE_FORMAT])
FILE_INFO_FORMAT = " - ".join(["%(filename)s:%(lineno)d",
                               DEFAULT_CONSOLE_FORMAT])
DEBUG_FORMAT = " ".join(["%(asctime)s", FILE_INFO_FORMAT])
DEBUG_FORMAT_PID = " ".join(["%(asctime)s", "PID: %s" % str(static.PID),
                             FILE_INFO_FORMAT])


class ConsoleLogger(logging.StreamHandler):

    formatters = {
        INFO: logging.Formatter(INFO_FORMAT),
        DEBUG: logging.Formatter(DEBUG_FORMAT),
        WARN: logging.Formatter(WARN_CONSOLE_FORMAT),
        ERROR: logging.Formatter(ERROR_CONSOLE_FORMAT),
        CRITICAL: logging.Formatter(ERROR_CONSOLE_FORMAT),
        FATAL: logging.Formatter(ERROR_CONSOLE_FORMAT),
        RAW: logging.Formatter(RAW_FORMAT),
    }

    def __init__(self, stream=sys.stdout, error_stream=sys.stderr):
        self.error_stream = error_stream or sys.stderr
        logging.StreamHandler.__init__(self, stream or sys.stdout)

    def format(self, record):
        if hasattr(record, '__raw__'):
            result = self.formatters[RAW].format(record)
        else:
            result = self.formatters[record.levelno].format(record)
        return result

    def _wrap(self, msg):
        tw = textwrap.TextWrapper(width=60, replace_whitespace=False)
        if hasattr(tw, 'break_on_hyphens'):
            tw.break_on_hyphens = False
        if hasattr(tw, 'drop_whitespace'):
            tw.drop_whitespace = True
        return tw.wrap(msg) or ['']

    def _emit_textwrap(self, record):
        lines = []
        for line in record.msg.splitlines():
            lines.extend(self._wrap(line))
        if hasattr(record, '__nosplitlines__'):
            lines = ['\n'.join(lines)]
        for line in lines:
            record.msg = line
            self._emit(record)

    def _emit(self, record):
        msg = self.format(record)
        fs = "%s\n"
        if hasattr(record, '__nonewline__'):
            msg = msg.rstrip()
            fs = "%s"
        stream = self.stream
        if record.levelno in [ERROR, CRITICAL, FATAL]:
            stream = self.error_stream
        if not hasattr(types, "UnicodeType"):
             # if no unicode support...
            stream.write(fs % msg)
        else:
            try:
                stream.write(fs % msg)
            except UnicodeError:
                stream.write(fs % msg.encode("UTF-8"))
        self.flush()

    def emit(self, record):
        try:
            if hasattr(record, '__textwrap__'):
                self._emit_textwrap(record)
            else:
                self._emit(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def get_starcluster_logger():
    log = logging.getLogger('starcluster')
    log.addHandler(NullHandler())
    return log


log = get_starcluster_logger()
console = ConsoleLogger()
session = logging.StreamHandler(StringIO.StringIO())


def configure_sc_logging(use_syslog=False):
    """
    Configure logging for StarCluster *application* code

    By default StarCluster's logger has no formatters and a NullHandler so that
    other developers using StarCluster as a library can configure logging as
    they see fit. This method is used in StarCluster's application code (i.e.
    the 'starcluster' command) to toggle StarCluster's application specific
    formatters/handlers

    use_syslog - enable logging all messages to syslog. currently only works if
    /dev/log exists on the system (standard for most Linux distros)
    """
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(DEBUG_FORMAT_PID)
    static.create_sc_config_dirs()
    rfh = logging.handlers.RotatingFileHandler(static.DEBUG_FILE,
                                               maxBytes=1048576,
                                               backupCount=2)
    rfh.setLevel(logging.DEBUG)
    rfh.setFormatter(formatter)
    log.addHandler(rfh)
    console.setLevel(logging.INFO)
    log.addHandler(console)
    session.setLevel(logging.DEBUG)
    session.setFormatter(formatter)
    log.addHandler(session)
    syslog_device = '/dev/log'
    if use_syslog and os.path.exists(syslog_device):
        log.debug("Logging to %s" % syslog_device)
        syslog_handler = logging.handlers.SysLogHandler(address=syslog_device)
        syslog_handler.setFormatter(formatter)
        syslog_handler.setLevel(logging.DEBUG)
        log.addHandler(syslog_handler)


def configure_ssh_logging():
    """
    Configure ssh to log to a file for debug
    """
    l = logging.getLogger("ssh")
    l.setLevel(logging.DEBUG)
    static.create_sc_config_dirs()
    lh = logging.handlers.RotatingFileHandler(static.SSH_DEBUG_FILE,
                                              maxBytes=1048576,
                                              backupCount=2)
    lh.setLevel(logging.DEBUG)
    format = (('PID: %s ' % str(static.PID)) +
              '%(levelname)-.3s [%(asctime)s.%(msecs)03d] '
              'thr=%(_threadid)-3d %(name)s: %(message)s')
    date_format = '%Y%m%d-%H:%M:%S'
    lh.setFormatter(logging.Formatter(format, date_format))
    l.addHandler(lh)


def configure_boto_logging():
    """
    Configure boto to log to a file for debug
    """
    l = logging.getLogger("boto")
    l.setLevel(logging.DEBUG)
    static.create_sc_config_dirs()
    lh = logging.handlers.RotatingFileHandler(static.AWS_DEBUG_FILE,
                                              maxBytes=1048576,
                                              backupCount=2)
    lh.setLevel(logging.DEBUG)
    format = (('PID: %s ' % str(static.PID)) +
              '%(levelname)-.3s [%(asctime)s.%(msecs)03d] '
              '%(name)s: %(message)s')
    date_format = '%Y%m%d-%H:%M:%S'
    lh.setFormatter(logging.Formatter(format, date_format))
    l.addHandler(lh)
