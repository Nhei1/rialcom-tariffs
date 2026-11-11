"""Модели данных."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

Number: TypeAlias = int | float


@dataclass(frozen=True, slots=True)
class Tariff:
    """Тариф — одна строка итогового Excel-файла.

    Attributes:
        name: название тарифа.
        channels: количество ТВ-каналов; ``None`` у тарифов без ТВ.
        speed: скорость доступа, Мбит/с.
        monthly_fee: абонентская плата в расчётный период (1 мес.), руб.
    """

    name: str
    channels: int | None
    speed: Number
    monthly_fee: Number


@dataclass(frozen=True, slots=True)
class Section:
    """Вкладка страницы тарифов («Многоквартирные дома», «Частные дома и коттеджи»).

    Attributes:
        title: заголовок вкладки на сайте.
        combo_suffix: суффикс к названиям тарифов «Интернет + ТВ» этой вкладки. У частного
            сектора это «_ч»: без него названия совпали бы с тарифами многоквартирных домов.
    """

    title: str
    combo_suffix: str = ""
