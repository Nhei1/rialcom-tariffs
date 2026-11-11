"""Источники HTML страницы с тарифами."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from rialcom_tariffs.exceptions import PageLoadError


class PageSource(ABC):
    """Источник HTML страницы тарифов."""

    @property
    @abstractmethod
    def location(self) -> str:
        """Адрес или путь к странице — для сообщений в логе."""

    @abstractmethod
    def read(self) -> str:
        """Возвращает HTML страницы."""


class HttpPageSource(PageSource):
    """Загружает страницу с сайта: с таймаутом, повторами при сбоях и «браузерными» заголовками."""

    DEFAULT_URL = "https://www.rialcom.ru/internet_tariffs/"
    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }

    def __init__(
        self,
        url: str = DEFAULT_URL,
        *,
        timeout: float = 20.0,
        retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._retries = retries
        self._session = session

    @property
    def location(self) -> str:
        return self._url

    def read(self) -> str:
        if self._session is not None:
            return self._fetch(self._session)
        with self._create_session() as session:
            return self._fetch(session)

    def _fetch(self, session: requests.Session) -> str:
        try:
            response = session.get(self._url, headers=self.HEADERS, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PageLoadError(f"Не удалось загрузить страницу {self._url}: {exc}") from exc

        if "charset" not in response.headers.get("Content-Type", "").lower():
            # Без charset requests взял бы ISO-8859-1 — определяем кодировку по содержимому.
            response.encoding = response.apparent_encoding
        return response.text

    def _create_session(self) -> requests.Session:
        retry = Retry(
            total=self._retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session


class FilePageSource(PageSource):
    """Читает сохранённую HTML-страницу с диска — для отладки и запуска без сети."""

    def __init__(self, path: str | Path, encoding: str = "utf-8") -> None:
        self._path = Path(path)
        self._encoding = encoding

    @property
    def location(self) -> str:
        return str(self._path)

    def read(self) -> str:
        try:
            return self._path.read_text(encoding=self._encoding)
        except (OSError, UnicodeDecodeError) as exc:
            raise PageLoadError(f"Не удалось прочитать файл {self._path}: {exc}") from exc
