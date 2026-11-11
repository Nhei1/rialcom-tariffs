import pytest

from rialcom_tariffs.values import ValueParser


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1000 руб.", 1000),
        ("1 000 руб.", 1000),
        ("1 000 руб.", 1000),
        ("99,50 руб.", 99.5),
        ("1149", 1149),
        ("—", None),
        ("", None),
    ],
)
def test_parse_number(text: str, expected: float | None) -> None:
    assert ValueParser.parse_number(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("до 200000 кбит/с", 200),
        ("до 2000 кбит/с", 2),
        ("до 200 000 кбит/с", 200),
        ("до 512 кбит/с", 0.512),
        ("до 100 Мбит/с", 100),
        ("до 1 Гбит/с", 1000),
        ("без ограничений", None),
    ],
)
def test_parse_speed_mbps(text: str, expected: float | None) -> None:
    assert ValueParser.parse_speed_mbps(text) == expected


def test_whole_speed_is_int() -> None:
    assert isinstance(ValueParser.parse_speed_mbps("до 72000 кбит/с"), int)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Комбо Лайт (165 каналов)", ("Комбо Лайт", 165)),
        ("Оптима (271 канал)", ("Оптима", 271)),
        ("Комбо Микс + AMEDIATEKA (233 канала)", ("Комбо Микс + AMEDIATEKA", 233)),
        ("Эксклюзив + Кино  (302 канала)", ("Эксклюзив + Кино", 302)),
        ("Комбо Лайт", ("Комбо Лайт", None)),
    ],
)
def test_split_channels(label: str, expected: tuple[str, int | None]) -> None:
    assert ValueParser.split_channels(label) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Социальный **", "Социальный"),
        ("РиалКом Интернет 150* + ТВ", "РиалКом Интернет 150 + ТВ"),
        ("РиалКомий-15+", "РиалКомий-15+"),
    ],
)
def test_strip_footnotes(text: str, expected: str) -> None:
    assert ValueParser.strip_footnotes(text) == expected


def test_lookup_key_ignores_case_and_spaces() -> None:
    assert ValueParser.lookup_key("Комбо Люкс +START") == ValueParser.lookup_key(
        " комбо люкс + start"
    )
