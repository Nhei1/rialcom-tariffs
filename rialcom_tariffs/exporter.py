"""Выгрузка тарифов в Excel."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from rialcom_tariffs.exceptions import ExportError
from rialcom_tariffs.models import Tariff


class ExcelExporter:
    """Сохраняет тарифы в .xlsx в формате из ТЗ."""

    HEADERS = ("Название тарифа", "Количество каналов", "Скорость доступа", "Абонентская плата")
    MAX_COLUMN_WIDTH = 60

    def __init__(self, *, sheet_title: str = "Тарифы", null_value: str = "null") -> None:
        self._sheet_title = sheet_title
        self._null_value = null_value

    def export(self, tariffs: Sequence[Tariff], path: str | Path) -> Path:
        """Записывает тарифы в ``path`` (папки создаются при необходимости) и возвращает путь."""
        path = Path(path)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = self._sheet_title
        sheet.append(self.HEADERS)
        for tariff in tariffs:
            sheet.append(self._to_row(tariff))
        self._format(sheet)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            workbook.save(path)
        except PermissionError as exc:
            raise ExportError(
                f"Нет доступа к файлу {path}. Если он открыт в Excel, закройте его "
                "и запустите скрипт ещё раз."
            ) from exc
        except OSError as exc:
            raise ExportError(f"Не удалось сохранить файл {path}: {exc}") from exc
        return path

    def _to_row(self, tariff: Tariff) -> tuple[str | int | float, ...]:
        channels = self._null_value if tariff.channels is None else tariff.channels
        return tariff.name, channels, tariff.speed, tariff.monthly_fee

    def _format(self, sheet: Worksheet) -> None:
        """Шапка — жирная, закреплённая и с фильтром; ширина столбцов — по содержимому."""
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(fill_type="solid", fgColor="DDEBF7")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        for row in sheet.iter_rows(min_row=2, min_col=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")

        for index, column in enumerate(sheet.iter_cols(values_only=True), start=1):
            width = max(len(str(value)) for value in column if value is not None) + 2
            sheet.column_dimensions[get_column_letter(index)].width = min(
                width, self.MAX_COLUMN_WIDTH
            )
