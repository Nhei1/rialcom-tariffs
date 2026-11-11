"""Парсер интернет-тарифов RialCom с выгрузкой в Excel.

Источник данных: https://www.rialcom.ru/internet_tariffs/
"""

from rialcom_tariffs.app import TariffScraper
from rialcom_tariffs.exporter import ExcelExporter
from rialcom_tariffs.models import Section, Tariff
from rialcom_tariffs.parser import RialcomTariffParser
from rialcom_tariffs.sources import FilePageSource, HttpPageSource, PageSource

__all__ = [
    "ExcelExporter",
    "FilePageSource",
    "HttpPageSource",
    "PageSource",
    "RialcomTariffParser",
    "Section",
    "Tariff",
    "TariffScraper",
]
