"""Разбор блоков (таблиц) внутри вкладки тарифов."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from rialcom_tariffs.exceptions import PageStructureError
from rialcom_tariffs.models import Number, Section, Tariff
from rialcom_tariffs.table import HtmlTable
from rialcom_tariffs.values import ValueParser

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TariffBlock:
    """Таблица тарифов вместе с вкладкой и заголовком блока, к которым она относится."""

    section: Section
    title: str
    table: HtmlTable

    @property
    def label(self) -> str:
        """Подпись для сообщений в логе: «Вкладка» / «Блок»."""
        return f"«{self.section.title}» / «{self.title}»"


class ChannelCatalog:
    """Справочник «ТВ-пакет → количество каналов».

    Количество каналов указано только в таблице многоквартирных домов
    («Комбо Лайт (165 каналов)»). В частном секторе его берут оттуда по названию пакета.
    """

    def __init__(self) -> None:
        self._channels: dict[str, int] = {}

    @classmethod
    def from_tables(cls, tables: Iterable[HtmlTable]) -> ChannelCatalog:
        """Собирает справочник по первым столбцам таблиц «Интернет + ТВ»."""
        catalog = cls()
        for table in tables:
            for row in table.rows:
                package, channels = ValueParser.split_channels(row[0])
                if channels is not None:
                    catalog.add(package, channels)
        return catalog

    def add(self, package: str, channels: int) -> None:
        self._channels[ValueParser.lookup_key(package)] = channels

    def get(self, package: str) -> int | None:
        return self._channels.get(ValueParser.lookup_key(package))

    def __len__(self) -> int:
        return len(self._channels)


@dataclass(frozen=True, slots=True)
class ComboColumn:
    """Столбец таблицы «Интернет + ТВ» — интернет-часть комбо-тарифа.

    Заголовки столбцов на вкладках записаны по-разному, а в названии тарифа используется единый
    вид «<услуга> <скорость> + ТВ», как в примере из ТЗ «Комбо Лайт + РиалКом Интернет 50 + ТВ_ч»:

    * «РиалКом Интернет 150* + ТВ»   → «РиалКом Интернет 150 + ТВ» (многоквартирные дома);
    * «РиалКом Интернет + ТВ Дом 50» → «РиалКом Интернет 50 + ТВ» (частный сектор).
    """

    title: str
    speed: Number

    _HEADER_PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(r"(?P<service>.+?) (?P<speed>\d+) ?\+ ?ТВ"),
        re.compile(r"(?P<service>.+?) ?\+ ?ТВ Дом (?P<speed>\d+)"),
    )

    @classmethod
    def from_header(cls, header: str) -> ComboColumn:
        text = ValueParser.strip_footnotes(header)
        for pattern in cls._HEADER_PATTERNS:
            match = pattern.fullmatch(text)
            if match is not None:
                speed = int(match["speed"])
                return cls(title=f"{match['service']} {speed} + ТВ", speed=speed)

        speed = ValueParser.parse_number(text)
        if speed is None:
            raise PageStructureError(
                f"Не удалось определить скорость по заголовку столбца «{header}»"
            )
        logger.warning(
            "Нестандартный заголовок столбца «%s» — в названии он будет как есть", header
        )
        return cls(title=text, speed=speed)


class BlockParser(ABC):
    """Парсер таблицы одного блока вкладки."""

    title: ClassVar[str]
    """Заголовок блока на сайте — по нему для таблицы выбирается парсер."""

    @abstractmethod
    def parse(self, block: TariffBlock) -> list[Tariff]:
        """Превращает таблицу блока в список тарифов."""


class InternetBlockParser(BlockParser):
    """Блок «Интернет»: каждая строка таблицы — отдельный тариф без ТВ."""

    title = "Интернет"

    _NAME_COLUMN = "Название тарифа"
    _FEE_COLUMN = "Абонентская плата"
    _SPEED_COLUMN = "Скорость доступа"

    def parse(self, block: TariffBlock) -> list[Tariff]:
        table = block.table
        name_column = self._find_column(table, self._NAME_COLUMN)
        fee_column = self._find_column(table, self._FEE_COLUMN)
        speed_column = self._find_column(table, self._SPEED_COLUMN)
        row_width = max(name_column, fee_column, speed_column) + 1

        tariffs: list[Tariff] = []
        for row in table.rows:
            if len(row) < row_width:
                logger.warning("%s: пропущена неполная строка %s", block.label, row)
                continue
            name = ValueParser.strip_footnotes(row[name_column])
            fee = ValueParser.parse_number(row[fee_column])
            speed = ValueParser.parse_speed_mbps(row[speed_column])
            if not name or fee is None or speed is None:
                logger.warning("%s: не удалось разобрать строку %s", block.label, row)
                continue
            tariffs.append(Tariff(name=name, channels=None, speed=speed, monthly_fee=fee))
        return tariffs

    @staticmethod
    def _find_column(table: HtmlTable, title: str) -> int:
        """Индекс столбца, заголовок которого начинается с ``title`` (без учёта регистра)."""
        prefix = title.casefold()
        for index, header in enumerate(table.header):
            if header.casefold().startswith(prefix):
                return index
        raise PageStructureError(f"В таблице нет столбца «{title}», есть: {list(table.header)}")


class ComboBlockParser(BlockParser):
    """Блок «Интернет + Интерактивное ТВ»: матрица «ТВ-пакет × интернет».

    Каждая ячейка с ценой — отдельный тариф. Название собирается из строки (ТВ-пакет без
    количества каналов) и столбца, к нему добавляется суффикс вкладки.
    """

    title = "Интернет + Интерактивное ТВ"

    def __init__(self, channel_catalog: ChannelCatalog) -> None:
        self._channel_catalog = channel_catalog

    def parse(self, block: TariffBlock) -> list[Tariff]:
        columns = [ComboColumn.from_header(header) for header in block.table.header[1:]]
        if not columns:
            raise PageStructureError(f"{block.label}: в таблице нет столбцов с тарифами")

        tariffs: list[Tariff] = []
        for label, *cells in block.table.rows:
            package, channels = self._package(label, block)
            if len(cells) != len(columns):
                logger.warning(
                    "%s: в строке «%s» цен %d, а столбцов %d",
                    block.label,
                    package,
                    len(cells),
                    len(columns),
                )
            for column, cell in zip(columns, cells, strict=False):
                fee = ValueParser.parse_number(cell)
                if fee is None:  # пустая ячейка — такой комбинации нет
                    continue
                tariffs.append(
                    Tariff(
                        name=f"{package} + {column.title}{block.section.combo_suffix}",
                        channels=channels,
                        speed=column.speed,
                        monthly_fee=fee,
                    )
                )
        return tariffs

    def _package(self, label: str, block: TariffBlock) -> tuple[str, int | None]:
        """Название ТВ-пакета и количество каналов: из самой строки или из справочника."""
        package, channels = ValueParser.split_channels(label)
        if channels is None:
            channels = self._channel_catalog.get(package)
            if channels is None:
                logger.warning(
                    "%s: не найдено количество каналов пакета «%s»", block.label, package
                )
        return package, channels
