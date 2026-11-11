"""Разбор страницы тарифов RialCom."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Iterable
from typing import ClassVar

from bs4 import BeautifulSoup, Tag

from rialcom_tariffs.blocks import (
    BlockParser,
    ChannelCatalog,
    ComboBlockParser,
    InternetBlockParser,
    TariffBlock,
)
from rialcom_tariffs.exceptions import PageStructureError
from rialcom_tariffs.models import Section, Tariff
from rialcom_tariffs.table import HtmlTable
from rialcom_tariffs.values import ValueParser

logger = logging.getLogger(__name__)


class RialcomTariffParser:
    """Извлекает тарифы со страницы https://www.rialcom.ru/internet_tariffs/.

    Страница устроена как аккордеон Bootstrap: у каждой вкладки есть кнопка-заголовок и
    раскрывающееся тело с таблицами. Содержимое всех вкладок уже есть в HTML (по клику
    меняется только видимость), поэтому браузер для парсинга не нужен.
    """

    DEFAULT_SECTIONS: ClassVar[tuple[Section, ...]] = (
        Section("Многоквартирные дома"),
        Section("Частные дома и коттеджи", combo_suffix="_ч"),
    )

    _TOGGLE_SELECTOR = '[data-toggle="collapse"], [data-bs-toggle="collapse"]'
    _TARGET_ATTRIBUTES = ("data-target", "data-bs-target", "href", "aria-controls")
    _TABLE_TAGS = frozenset({"table", "thead", "tbody", "tfoot", "tr", "th", "td"})
    _BLOCK_TITLES: ClassVar[dict[str, str]] = {
        ValueParser.lookup_key(title): title
        for title in (InternetBlockParser.title, ComboBlockParser.title)
    }

    def __init__(self, sections: Iterable[Section] = DEFAULT_SECTIONS) -> None:
        self._sections = tuple(sections)

    def parse(self, html: str) -> list[Tariff]:
        """Возвращает тарифы всех вкладок в том порядке, в каком они идут на странице."""
        soup = BeautifulSoup(html, "html.parser")
        blocks = [block for section in self._sections for block in self._find_blocks(soup, section)]

        catalog = ChannelCatalog.from_tables(
            block.table for block in blocks if block.title == ComboBlockParser.title
        )
        parsers: dict[str, BlockParser] = {
            parser.title: parser for parser in (InternetBlockParser(), ComboBlockParser(catalog))
        }

        tariffs: list[Tariff] = []
        for block in blocks:
            block_tariffs = parsers[block.title].parse(block)
            logger.info("%s, тарифов: %d", block.label, len(block_tariffs))
            tariffs.extend(block_tariffs)

        self._warn_about_duplicates(tariffs)
        return tariffs

    def _find_blocks(self, soup: BeautifulSoup, section: Section) -> list[TariffBlock]:
        """Находит во вкладке таблицы блоков «Интернет» и «Интернет + Интерактивное ТВ»."""
        body = self._find_section_body(soup, section)
        blocks: list[TariffBlock] = []
        for table in body.find_all("table"):
            title = self._block_title(table, body)
            if title is None:
                logger.debug(
                    "«%s»: пропущена таблица без известного заголовка блока", section.title
                )
                continue
            blocks.append(
                TariffBlock(section=section, title=title, table=HtmlTable.from_tag(table))
            )

        if not blocks:
            raise PageStructureError(f"Во вкладке «{section.title}» не найдено таблиц с тарифами")
        return blocks

    def _find_section_body(self, soup: BeautifulSoup, section: Section) -> Tag:
        """Находит раскрывающееся тело вкладки по тексту её кнопки-заголовка."""
        wanted = ValueParser.lookup_key(section.title)
        for toggle in soup.select(self._TOGGLE_SELECTOR):
            if ValueParser.lookup_key(toggle.get_text()) != wanted:
                continue
            for attribute in self._TARGET_ATTRIBUTES:
                target_id = str(toggle.get(attribute) or "").lstrip("#")
                body = soup.find(id=target_id) if target_id else None
                if isinstance(body, Tag):
                    return body
        raise PageStructureError(f"На странице не найдена вкладка «{section.title}»")

    def _block_title(self, table: Tag, body: Tag) -> str | None:
        """Ищет ближайший заголовок блока перед таблицей, не выходя за пределы вкладки."""
        for element in table.previous_elements:
            if element is body:
                return None
            if not isinstance(element, Tag) or element.name in self._TABLE_TAGS:
                continue
            title = self._BLOCK_TITLES.get(ValueParser.lookup_key(element.get_text()))
            if title is not None:
                return title
        return None

    @staticmethod
    def _warn_about_duplicates(tariffs: Iterable[Tariff]) -> None:
        for name, count in Counter(tariff.name for tariff in tariffs).items():
            if count > 1:
                logger.warning("Название тарифа «%s» встречается %d раза", name, count)
