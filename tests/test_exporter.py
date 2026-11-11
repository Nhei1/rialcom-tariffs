from pathlib import Path

from openpyxl import load_workbook

from rialcom_tariffs.exporter import ExcelExporter
from rialcom_tariffs.models import Tariff


def test_export_writes_header_rows_and_null(tmp_path: Path) -> None:
    tariffs = [
        Tariff("РиалКомий-15+", None, 200, 1000),
        Tariff("Комбо Лайт + РиалКом Интернет 100 + ТВ", 165, 100, 649),
    ]

    path = ExcelExporter().export(tariffs, tmp_path / "nested" / "tariffs.xlsx")

    sheet = load_workbook(path).active
    assert list(sheet.values) == [
        ("Название тарифа", "Количество каналов", "Скорость доступа", "Абонентская плата"),
        ("РиалКомий-15+", "null", 200, 1000),
        ("Комбо Лайт + РиалКом Интернет 100 + ТВ", 165, 100, 649),
    ]
    assert sheet.freeze_panes == "A2"
