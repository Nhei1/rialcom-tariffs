"""Сценарий целиком: загрузить страницу, разобрать тарифы, сохранить в Excel."""

from __future__ import annotations

import logging
from pathlib import Path

from rialcom_tariffs.exceptions import PageStructureError
from rialcom_tariffs.exporter import ExcelExporter
from rialcom_tariffs.models import Tariff
from rialcom_tariffs.parser import RialcomTariffParser
from rialcom_tariffs.sources import PageSource

logger = logging.getLogger(__name__)


class TariffScraper:
    """Связывает источник страницы, парсер и экспорт в Excel."""

    def __init__(
        self,
        source: PageSource,
        parser: RialcomTariffParser | None = None,
        exporter: ExcelExporter | None = None,
    ) -> None:
        self._source = source
        self._parser = parser or RialcomTariffParser()
        self._exporter = exporter or ExcelExporter()

    def collect(self) -> list[Tariff]:
        """Загружает страницу и возвращает найденные на ней тарифы."""
        logger.info("Загрузка страницы: %s", self._source.location)
        tariffs = self._parser.parse(self._source.read())
        if not tariffs:
            raise PageStructureError("На странице не найдено ни одного тарифа")
        return tariffs

    def run(self, output: str | Path) -> Path:
        """Собирает тарифы, сохраняет их в Excel и возвращает путь к файлу."""
        tariffs = self.collect()
        path = self._exporter.export(tariffs, output)
        logger.info("Сохранено тарифов: %d, файл: %s", len(tariffs), path.resolve())
        return path
