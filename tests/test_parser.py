import pytest

from rialcom_tariffs.exceptions import PageStructureError
from rialcom_tariffs.models import Section, Tariff
from rialcom_tariffs.parser import RialcomTariffParser

EXPECTED = [
    # «Многоквартирные дома» / «Интернет»
    Tariff("РиалКомий-15+", None, 200, 1000),
    Tariff("Социальный", None, 2, 100),
    # «Многоквартирные дома» / «Интернет + Интерактивное ТВ» (столбец «50 + ТВ» закомментирован)
    Tariff("Комбо Лайт + РиалКом Интернет 100 + ТВ", 165, 100, 649),
    Tariff("Комбо Лайт + РиалКом Интернет 150 + ТВ", 165, 150, 949),
    Tariff("Эксклюзив + Кино + РиалКом Интернет 100 + ТВ", 302, 100, 1699),
    Tariff("Эксклюзив + Кино + РиалКом Интернет 150 + ТВ", 302, 150, 1999),
    # «Частные дома и коттеджи» / «Интернет»
    Tariff("Дом №5", None, 150, 3000),
    Tariff("Дом №1", None, 16, 900),
    # «Частные дома и коттеджи» / «Интернет + Интерактивное ТВ» (каналы — из многоквартирных домов)
    Tariff("Комбо Лайт + РиалКом Интернет 50 + ТВ_ч", 165, 50, 1599),
    Tariff("Комбо Лайт + РиалКом Интернет 100 + ТВ_ч", 165, 100, 2149),
    Tariff("Комбо Лайт + РиалКом Интернет 150 + ТВ_ч", 165, 150, 3149),
    Tariff("Эксклюзив + Кино + РиалКом Интернет 50 + ТВ_ч", 302, 50, 2649),
    Tariff("Эксклюзив + Кино + РиалКом Интернет 100 + ТВ_ч", 302, 100, 3199),
    Tariff("Эксклюзив + Кино + РиалКом Интернет 150 + ТВ_ч", 302, 150, 4199),
]


def test_parses_both_tabs_in_page_order(page_html: str) -> None:
    assert RialcomTariffParser().parse(page_html) == EXPECTED


def test_bootstrap5_accordion_is_supported() -> None:
    html = """
        <button data-bs-toggle="collapse" data-bs-target="#flat">Многоквартирные дома</button>
        <div id="flat">
            <h4>Интернет</h4>
            <div class="table-responsive">
                <table>
                    <tr>
                        <th>Название тарифа</th><th>Скорость доступа</th><th>Абонентская плата</th>
                    </tr>
                    <tr><td>Тест</td><td>до 50000 кбит/с</td><td>500 руб.</td></tr>
                </table>
            </div>
        </div>
    """
    parser = RialcomTariffParser([Section("Многоквартирные дома")])

    assert parser.parse(html) == [Tariff("Тест", None, 50, 500)]


def test_missing_tab_is_reported() -> None:
    parser = RialcomTariffParser([Section("Частные дома и коттеджи")])

    with pytest.raises(PageStructureError, match="Частные дома и коттеджи"):
        parser.parse("<html><body><p>Сайт на обслуживании</p></body></html>")
