# MIT License

# Copyright (c) 2026 Jaime Álvarez Díaz
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import logging
import platform
from os import getenv
from pathlib import Path
from typing import Optional


class Styles:
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DEBUG = '\033[0m'
    INFO = '\033[94m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CRITICAL = '\033[101m'
    SUCCEED = '\033[92m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'


class _MyFormatter(logging.Formatter):
    CUSTOM_STYLE_NAME = 'custom_style'

    def format(self, record: logging.LogRecord) -> str:
        org_msg: str = record.msg
        record.msg = record.msg.replace('%', '%%')
        if hasattr(record, self.CUSTOM_STYLE_NAME):
            custom_style: str = getattr(record, self.CUSTOM_STYLE_NAME)
        else:
            custom_style: str = Styles.ENDC
        arrow: str = '-' * (39 - len(record.levelname + f"[{record.name}]")) + '->'
        log_fmt: str = f'{custom_style}{record.levelname}[{record.name}] {arrow} %(asctime)s.%(msecs)03d:{Styles.ENDC} {record.msg}'
        formatter = logging.Formatter(log_fmt, datefmt='%d/%m/%Y %H:%M:%S')
        result: str = formatter.format(record)
        record.msg = org_msg
        return result


class _MyFileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        arrow: str = '-' * (39 - len(record.levelname + f"[{record.name}]")) + '->'
        log_fmt: str = f'{record.levelname}[{record.name}] {arrow} %(asctime)s.%(msecs)03d: {record.msg}'
        formatter = logging.Formatter(log_fmt, datefmt='%d/%m/%Y %H:%M:%S')
        return formatter.format(record)


class MyLogger:
    PATH_ENV_NAME: str = 'LOGS_PATH'

    def __init__(
        self,
        logger_name: str,
        logging_level: int = logging.DEBUG,
        file_path: Optional[Path | str] = None,
        save_logs: bool = False,
        enable: bool = True
    ) -> None:
        self.enable: bool = False
        self._file_handler: Optional[logging.FileHandler] = None
        self._save_logs: bool = False
        self._logger: logging.Logger = logging.getLogger(logger_name)
        self.level = logging_level
        self._create_stream_handler()
        self.logs_file_path = file_path
        self.save_logs = save_logs
        self.enable = enable

    @property
    def name(self) -> str:
        return self._logger.name

    @property
    def level(self) -> int:
        return self._logger.level

    @level.setter
    def level(self, lvl: int = logging.DEBUG) -> None:
        self._logger.setLevel(lvl)
        for handler in self._logger.handlers:
            handler.setLevel(lvl)

    @property
    def parent(self) -> Optional[logging.Logger]:
        return self._logger.parent

    @property
    def save_logs(self) -> bool:
        return self._save_logs

    @save_logs.setter
    def save_logs(self, value: bool) -> None:
        if value:
            self._add_file_handler()
        else:
            self._remove_file_handler()
        self._save_logs = value
        self.debug(f'Log saving state: {self.save_logs}')

    @property
    def logs_file_path(self) -> Optional[Path]:
        return self._file_path

    @logs_file_path.setter
    def logs_file_path(self, new_path: Optional[Path | str]) -> None:
        self._remove_file_handler()
        if new_path is not None:
            new_path = Path(new_path)
        self._create_file_handler(new_path)
        self.save_logs = self.save_logs
        self.debug(f'Log file path: {self.logs_file_path}')

    def _create_file_path(self, file_path: Optional[Path] = None) -> None:
        self._file_path: Optional[Path] = None
        if file_path is None:
            return
        if file_path.suffix != '.log':
            file_path = file_path.with_suffix('.log')
        if file_path.is_absolute():
            self._file_path = file_path
            return
        system: str = platform.system().lower()
        temp_path: str
        if system == 'windows':
            temp_path = getenv('TEMP', getenv('TMP', '.'))
        else:
            temp_path = '/tmp'
        self._file_path= Path(getenv(self.PATH_ENV_NAME, temp_path)) / file_path

    def _create_file_handler(self, file_path: Optional[Path] = None) -> None:
        self._create_file_path(file_path)
        if self._file_path is None:
            return
        if not self._file_path.parent.is_dir():
            self._file_path.parent.mkdir(parents= True)
            self._logger.debug(f'Created logs dir "{self._file_path}".')
        self._file_handler = logging.FileHandler(
            self._file_path,
            mode= 'a',
            encoding= 'UTF-8'
        )
        self._file_handler.setFormatter(_MyFileFormatter())
        self._file_handler.setLevel(self._logger.level)

    def _add_file_handler(self) -> None:
        if self._file_handler is None:
            return
        if self._file_handler not in self._logger.handlers:
            self._file_handler.setLevel(self._logger.level)
            self._logger.addHandler(self._file_handler)

    def _remove_file_handler(self) -> None:
        if self._file_handler in self._logger.handlers:
            self._logger.removeHandler(self._file_handler)

    def _create_stream_handler(self) -> None:
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self._logger.removeHandler(handler)
        self._stream_handler: logging.StreamHandler = logging.StreamHandler()
        self._stream_handler.setFormatter(_MyFormatter())
        self._stream_handler.setLevel(self._logger.level)
        self._logger.addHandler(self._stream_handler)

    def debug(self, msg: str, style: str = Styles.DEBUG) -> None:
        if not self.enable:
            return
        self._logger.debug(
            f'{msg}',
            extra= {_MyFormatter.CUSTOM_STYLE_NAME: style}
        )

    def info(self, msg: str, style: str = Styles.INFO) -> None:
        if not self.enable:
            return
        self._logger.info(
            f'{msg}',
            extra= {_MyFormatter.CUSTOM_STYLE_NAME: style}
        )

    def warning(self, msg: str, style: str = Styles.WARNING) -> None:
        if not self.enable:
            return
        self._logger.warning(
            f'{msg}',
            extra= {_MyFormatter.CUSTOM_STYLE_NAME: style}
        )

    def error(self, msg: str, style: str = Styles.ERROR) -> None:
        if not self.enable:
            return
        self._logger.error(
            f'{msg}',
            extra= {_MyFormatter.CUSTOM_STYLE_NAME: style}
        )

    def critical(self, msg: str, style: str = Styles.CRITICAL) -> None:
        if not self.enable:
            return
        self._logger.critical(
            f'{msg}',
            extra= {_MyFormatter.CUSTOM_STYLE_NAME: style}
        )


spincam_logger = MyLogger(
    logger_name= 'SpinCam'
)
