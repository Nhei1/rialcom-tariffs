"""Текстовое представление HTML-таблицы."""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import Tag

from rialcom_tariffs.values import ValueParser


@dataclass(frozen=True, slots=True)
class HtmlTable:
    """Таблица в виде текста: строка заголовка и строки данных.

    Закомментированные в HTML ячейки (``<!-- <td>549</td> -->``) на сайте не видны, поэтому
    и сюда не попадают: BeautifulSoup не считает комментарии тегами.
    """

    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    @classmethod
    def from_tag(cls, table: Tag) -> HtmlTable:
        header: tuple[str, ...] = ()
        rows: list[tuple[str, ...]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            if not cells:
                continue
            values = tuple(ValueParser.clean(cell.get_text(" ")) for cell in cells)
            if cls._is_header_row(tr, cells):
                header = values
            else:
                rows.append(values)
        return cls(header=header, rows=tuple(rows))

    @staticmethod
    def _is_header_row(tr: Tag, cells: list[Tag]) -> bool:
        in_thead = tr.parent is not None and tr.parent.name == "thead"
        return in_thead or all(cell.name == "th" for cell in cells)
