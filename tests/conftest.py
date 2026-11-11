from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def page_path() -> Path:
    return FIXTURES / "internet_tariffs.html"


@pytest.fixture
def page_html(page_path: Path) -> str:
    return page_path.read_text(encoding="utf-8")
