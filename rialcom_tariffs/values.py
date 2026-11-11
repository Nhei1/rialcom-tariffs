"""Разбор и нормализация текстовых значений из ячеек таблиц."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import ClassVar

from rialcom_tariffs.models import Number


class ValueParser:
    """Правила, по которым текст с сайта превращается в значения нужного типа.

    Состояния у парсера нет, поэтому все методы классовые: класс объединяет связанные
    регулярные выражения и операции над ними.
    """

    _WHITESPACE = re.compile(r"\s+")
    _FOOTNOTE = re.compile(r"\s*\*+")
    # Число с необязательными разделителями тысяч и дробной частью: «72000», «1 000», «99,50».
    _NUMBER = re.compile(r"\d+(?: \d{3})*(?:[.,]\d+)?")
    _SPEED = re.compile(
        r"(?P<value>\d+(?: \d{3})*(?:[.,]\d+)?)\s*(?P<unit>[кмгkmg])(?:бит|bit)",
        re.IGNORECASE,
    )
    _CHANNELS = re.compile(r"\(\s*(?P<count>\d+)\s*канал[а-яё]*\s*\)", re.IGNORECASE)
    _MBPS_PER_UNIT: ClassVar[dict[str, Decimal]] = {
        "к": Decimal("0.001"),
        "k": Decimal("0.001"),
        "м": Decimal(1),
        "m": Decimal(1),
        "г": Decimal(1000),
        "g": Decimal(1000),
    }

    @classmethod
    def clean(cls, text: str) -> str:
        """Схлопывает пробельные символы (включая неразрывные пробелы) и обрезает края."""
        return cls._WHITESPACE.sub(" ", text).strip()

    @classmethod
    def strip_footnotes(cls, text: str) -> str:
        """Убирает сноски-звёздочки: «Социальный **» → «Социальный», «150* + ТВ» → «150 + ТВ»."""
        return cls.clean(cls._FOOTNOTE.sub("", text))

    @classmethod
    def parse_number(cls, text: str) -> Number | None:
        """Возвращает первое число из текста («1 000 руб.» → 1000) или ``None``, если чисел нет."""
        match = cls._NUMBER.search(cls.clean(text))
        if match is None:
            return None
        return cls._to_number(cls._to_decimal(match.group()))

    @classmethod
    def parse_speed_mbps(cls, text: str) -> Number | None:
        """Переводит скорость в Мбит/с: «до 200000 кбит/с» → 200, «до 1 Гбит/с» → 1000."""
        match = cls._SPEED.search(cls.clean(text))
        if match is None:
            return None
        mbps = cls._to_decimal(match["value"]) * cls._MBPS_PER_UNIT[match["unit"].lower()]
        return cls._to_number(mbps)

    @classmethod
    def split_channels(cls, label: str) -> tuple[str, int | None]:
        """Отделяет количество каналов от названия ТВ-пакета.

        «Комбо Лайт (165 каналов)» → («Комбо Лайт», 165); «Комбо Лайт» → («Комбо Лайт», None).
        """
        text = cls.clean(label)
        match = cls._CHANNELS.search(text)
        if match is None:
            return cls.strip_footnotes(text), None
        name = text[: match.start()] + text[match.end() :]
        return cls.strip_footnotes(name), int(match["count"])

    @classmethod
    def lookup_key(cls, text: str) -> str:
        """Ключ для сравнения названий без учёта регистра и пробелов."""
        return cls._WHITESPACE.sub("", text).casefold()

    @staticmethod
    def _to_decimal(raw: str) -> Decimal:
        return Decimal(raw.replace(" ", "").replace(",", "."))

    @staticmethod
    def _to_number(value: Decimal) -> Number:
        """Целое значение возвращает как ``int``, дробное — как ``float``."""
        if value == value.to_integral_value():
            return int(value)
        return float(value)
