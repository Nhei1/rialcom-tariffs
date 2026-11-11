import pytest

from rialcom_tariffs.blocks import ChannelCatalog, ComboColumn
from rialcom_tariffs.exceptions import PageStructureError


@pytest.mark.parametrize(
    ("header", "title", "speed"),
    [
        ("РиалКом Интернет 100 + ТВ", "РиалКом Интернет 100 + ТВ", 100),
        ("РиалКом Интернет 150* + ТВ", "РиалКом Интернет 150 + ТВ", 150),
        ("РиалКом Интернет + ТВ Дом 50", "РиалКом Интернет 50 + ТВ", 50),
        ("РиалКом Интернет + ТВ Дом 150*", "РиалКом Интернет 150 + ТВ", 150),
    ],
)
def test_combo_column_title_is_normalized(header: str, title: str, speed: int) -> None:
    assert ComboColumn.from_header(header) == ComboColumn(title=title, speed=speed)


def test_unknown_combo_header_is_kept_as_is() -> None:
    assert ComboColumn.from_header("Тариф 300") == ComboColumn(title="Тариф 300", speed=300)


def test_combo_header_without_speed_is_an_error() -> None:
    with pytest.raises(PageStructureError):
        ComboColumn.from_header("РиалКом Интернет + ТВ")


def test_channel_catalog_ignores_spacing_and_case() -> None:
    catalog = ChannelCatalog()
    catalog.add("Комбо Люкс +START", 237)

    assert catalog.get("комбо люкс + START") == 237
    assert catalog.get("Комбо Макс") is None
