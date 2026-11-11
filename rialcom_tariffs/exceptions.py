"""Исключения парсера."""


class TariffParserError(Exception):
    """Базовая ошибка: не удалось загрузить, разобрать или сохранить тарифы."""


class PageLoadError(TariffParserError):
    """Не удалось получить HTML страницы."""


class PageStructureError(TariffParserError):
    """Разметка страницы не похожа на ожидаемую — вероятно, сайт изменился."""


class ExportError(TariffParserError):
    """Не удалось сохранить Excel-файл."""
