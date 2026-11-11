"""Консольный интерфейс."""

from __future__ import annotations

import argparse
import io
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from rialcom_tariffs.app import TariffScraper
from rialcom_tariffs.exceptions import TariffParserError
from rialcom_tariffs.sources import FilePageSource, HttpPageSource, PageSource

logger = logging.getLogger(__name__)


class CommandLineApp:
    """Разбирает аргументы командной строки, настраивает лог и запускает сбор тарифов."""

    DEFAULT_OUTPUT = Path("rialcom_tariffs.xlsx")

    def __init__(self, prog: str = "rialcom-tariffs") -> None:
        self._arg_parser = self._build_arg_parser(prog)

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Запускает сбор тарифов и возвращает код завершения (0 — успех)."""
        args = self._arg_parser.parse_args(argv)
        self._configure_logging(verbose=args.verbose)
        source: PageSource = FilePageSource(args.html) if args.html else HttpPageSource(args.url)
        try:
            TariffScraper(source).run(args.output)
        except TariffParserError as exc:
            logger.error("%s", exc)
            return 1
        return 0

    @classmethod
    def _build_arg_parser(cls, prog: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=prog,
            description=(
                "Собирает интернет-тарифы RialCom (вкладки «Многоквартирные дома» "
                "и «Частные дома и коттеджи») и сохраняет их в Excel."
            ),
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=cls.DEFAULT_OUTPUT,
            help="путь к итоговому .xlsx (по умолчанию: %(default)s)",
        )
        source = parser.add_mutually_exclusive_group()
        source.add_argument(
            "--url",
            default=HttpPageSource.DEFAULT_URL,
            help="адрес страницы тарифов (по умолчанию: %(default)s)",
        )
        source.add_argument(
            "--html",
            type=Path,
            metavar="FILE",
            help="разобрать сохранённую HTML-страницу вместо загрузки с сайта",
        )
        parser.add_argument("-v", "--verbose", action="store_true", help="подробный лог")
        return parser

    @staticmethod
    def _configure_logging(*, verbose: bool) -> None:
        for stream in (sys.stdout, sys.stderr):
            # Вывод в файл с однобайтовой кодировкой не должен падать на символах вне её.
            if isinstance(stream, io.TextIOWrapper):
                stream.reconfigure(errors="backslashreplace")
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s %(levelname)-7s %(message)s",
            datefmt="%H:%M:%S",
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа для ``rialcom-tariffs`` и ``python -m rialcom_tariffs``."""
    return CommandLineApp().run(argv)
