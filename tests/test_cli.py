from pathlib import Path

import pytest
import requests
from openpyxl import load_workbook

from rialcom_tariffs.cli import main
from rialcom_tariffs.exceptions import PageLoadError
from rialcom_tariffs.sources import HttpPageSource


def test_builds_excel_from_saved_page(page_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "tariffs.xlsx"

    assert main(["--html", str(page_path), "--output", str(output)]) == 0

    rows = list(load_workbook(output).active.values)
    assert len(rows) == 1 + 14
    assert rows[1] == ("РиалКомий-15+", "null", 200, 1000)
    assert rows[-1] == ("Эксклюзив + Кино + РиалКом Интернет 150 + ТВ_ч", 302, 150, 4199)


def test_unreadable_page_gives_exit_code_1(tmp_path: Path) -> None:
    output = tmp_path / "tariffs.xlsx"

    assert main(["--html", str(tmp_path / "missing.html"), "--output", str(output)]) == 1
    assert not output.exists()


class _FakeResponse:
    headers = {"Content-Type": "text/html; charset=utf-8"}  # noqa: RUF012
    text = "<html>Тарифы</html>"

    def raise_for_status(self) -> None:
        pass


class _FakeSession:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        if self._error is not None:
            raise self._error
        return _FakeResponse()


def test_http_source_returns_page_text() -> None:
    source = HttpPageSource("https://example.test/", session=_FakeSession())

    assert source.read() == "<html>Тарифы</html>"


def test_http_source_wraps_network_errors() -> None:
    session = _FakeSession(error=requests.ConnectionError("нет сети"))
    source = HttpPageSource("https://example.test/", session=session)

    with pytest.raises(PageLoadError, match="нет сети"):
        source.read()
