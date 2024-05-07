import re
import json
from copy import copy
from typing import Union, Sequence, Iterable
from pathlib import Path

from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtCore import QObject, QStandardPaths, Slot, QStringListModel, QUrl

from .helpers import OS


class BrowserSettings:
    startup_clear_history: bool = True
    startup_clear_cache: bool = True
    startup_clear_cookies: bool = False
    startup_clear_session_cookies: bool = False
    shutdown_clear_history: bool = True
    shutdown_clear_cache: bool = True
    shutdown_clear_cookies: bool = False
    shutdown_clear_session_cookies: bool = False
    http_cache_type: QWebEngineProfile.HttpCacheType | None = None
    http_cache_maximum_size: int = 0
    http_user_agent: str | None = None
    http_accept_language: str | None = None
    download_path: str | None = None
    persistent_cookie_policy: QWebEngineProfile.PersistentCookiesPolicy = QWebEngineProfile.AllowPersistentCookies  # noqa: E501
    default_window_size: tuple[int, int] = (800, 600)
    inherit_window_size: bool = True
    window_stagger: tuple[int, int] = (20, 20)
    menu_bar_show: bool = (OS.detected() == OS.MACOS)
    navigation_bar_show: bool = True
    navigation_back_show: bool = True
    navigation_forward_show: bool = True
    navigation_stop_reload_show: bool = True
    navigation_url_show: bool = True
    navigation_url_editable: bool = True
    navigation_downloads_show: bool = True
    progress_bar_show: bool = True
    allow_context_menu: bool = True
    # @TODO: notification presenter??
    # @TODO: download requested slot connects here??
    # @TODO: urlscheme handlers (iterable?) to be installed?
    # @TODO: scripts support??
    # @TODO: spell checking support??


class BrowserProfile(QWebEngineProfile):

    _anonymous_profile: Union["BrowserProfile", None]
    _settings: BrowserSettings
    _suggestion_model: "BrowserUrlSuggestionModel"

    def __init__(
            self,
            name: str = "DefaultProfile",
            parent: QObject | None = None,
            settings: BrowserSettings | None = None):
        super().__init__(name, parent)
        self._anonymous_profile = None
        self._settings = settings if settings else BrowserSettings()
        self._suggestion_model = BrowserUrlSuggestionModel(None, self)
        self._apply_settings()
        self._load_suggestion_model()

    def _load_suggestion_model(self):
        storage_path = Path(self.persistentStoragePath())
        model_file = storage_path / "url_suggestion_model"
        if not model_file.is_file():
            return
        try:
            with model_file.open() as fh:
                model_data = json.load(fh)
            assert isinstance(model_data, dict)
            assert "urls" in model_data
            assert isinstance(model_data["urls"], list)
            assert "blacklist" in model_data
            assert isinstance(model_data["blacklist"], list)
        except Exception as e:
            print(
                "ERROR: Failed to load suggestion model from file at "
                f"{model_file}: {e}"
            )
            return
        self._suggestion_model.add_urls(model_data["urls"])
        self._suggestion_model.add_blacklist_patterns(model_data["blacklist"])

    def _store_suggestion_model(self):
        if self.isOffTheRecord():
            return
        storage_path = Path(self.persistentStoragePath())
        model_file = storage_path / "url_suggestion_model"
        model_data = json.dumps({
            "urls": list(self._suggestion_model.get_urls()),
            "blacklist": list(self._suggestion_model.get_blacklist_patterns()),
        })
        try:
            model_file.write_text(model_data)
        except Exception as e:
            print(
                "ERROR: Failed to write suggestion model to file at "
                f"{model_file}: {e}"
            )

    def _apply_settings(self):
        s = self._settings
        if s.http_cache_type is not None:
            self.setHttpCacheType(s.http_cache_type)
        self.setHttpCacheMaximumSize(s.http_cache_maximum_size)
        if s.http_user_agent is None:
            self.setHttpUserAgent(None)
            self.setHttpUserAgent(f"{self.httpUserAgent()} Quahl/0.0.1")
        else:
            self.setHttpUserAgent(s.http_user_agent)
        if s.download_path is not None:
            self.setDownloadPath(s.download_path)
        else:
            self.setDownloadPath(
                QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            )
        if s.http_accept_language is not None:
            self.setHttpAcceptLanguage(s.http_accept_language)
        self.setPersistentCookiesPolicy(s.persistent_cookie_policy)

    @property
    def settings(self) -> BrowserSettings:
        return self._settings

    @property
    def suggestion_model(self) -> "BrowserUrlSuggestionModel":
        return self._suggestion_model

    @Slot()
    def trigger_startup_actions(self):
        s = self._settings
        if s.startup_clear_cache:
            self.clearHttpCache()
        if s.startup_clear_history:
            self.clearAllVisitedLinks()
        if s.startup_clear_cookies:
            self.cookieStore().deleteAllCookies()
        if s.startup_clear_session_cookies:
            self.cookieStore().deleteSessionCookies()

    @Slot()
    def trigger_shutdown_actions(self):
        s = self._settings
        if s.shutdown_clear_cache:
            self.clearHttpCache()
        if s.shutdown_clear_history:
            self.clearAllVisitedLinks()
        if s.shutdown_clear_cookies:
            self.cookieStore().deleteAllCookies()
        if s.shutdown_clear_session_cookies:
            self.cookieStore().deleteSessionCookies()
        self._store_suggestion_model()

    def get_anonymous(self) -> "BrowserProfile":
        if not self._anonymous_profile:
            name = f"{self.storageName()}_Anonymous"
            settings = copy(self._settings)
            settings.startup_clear_cache = True
            settings.startup_clear_cookies = True
            settings.startup_clear_history = True
            settings.startup_clear_session_cookies = True
            settings.shutdown_clear_cache = True
            settings.shutdown_clear_cookies = True
            settings.shutdown_clear_history = True
            settings.shutdown_clear_session_cookies = True
            settings.http_cache_type = QWebEngineProfile.MemoryHttpCache
            settings.persistent_cookie_policy = QWebEngineProfile.NoPersistentCookies
            self._anonymous_profile = BrowserProfile(name, self.parent(), settings)
        return self._anonymous_profile


class BrowserUrlSuggestionModel(QStringListModel):

    _urls: set[str]
    _blacklist: set[str]

    def __init__(self, urls: Sequence[str] | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self.clear_blacklist()
        self.clear_urls()
        if urls:
            self.add_urls(urls)

    def add_url(self, url: str | QUrl):
        self._add_url_no_update(url)
        self._update_model()

    def add_urls(self, urls: Iterable[str | QUrl]):
        for url in urls:
            self._add_url_no_update(url)
        self._update_model()

    def add_blacklist_pattern(self, pattern: str):
        self._blacklist.add(pattern)

    def add_blacklist_patterns(self, patterns: Iterable[str]):
        self._blacklist = self._blacklist.union(patterns)

    def remove_url(self, url: str | QUrl):
        self._remove_url_no_update(url)
        self._update_model()

    def remove_urls(self, urls: Iterable[str | QUrl]):
        for url in urls:
            self._remove_url_no_update(url)
        self._update_model()

    def remove_blacklist_pattern(self, pattern: str):
        if pattern in self._blacklist:
            self._blacklist.remove(pattern)

    def remove_blacklist_patterns(self, patterns: Iterable[str]):
        for pattern in patterns:
            self.remove_blacklist_pattern(pattern)

    def set_urls(self, urls: Iterable[QUrl | str]):
        self.clear_urls()
        self.add_urls(urls)

    def set_blacklist_patterns(self, patterns: Iterable[str]):
        self.clear_blacklist()
        self.add_blacklist_patterns(patterns)

    def get_urls(self):
        return self._urls.copy()

    def get_blacklist_patterns(self):
        return self._blacklist.copy()

    def clear_urls(self):
        self._urls = set()
        self._update_model()

    def clear_blacklist(self):
        self._blacklist = {r"^quahl://"}

    def is_blacklisted(self, url: QUrl) -> bool:
        string = url.toDisplayString()
        for pattern in self._blacklist:
            if re.search(pattern, string):
                return True
        return False

    def contains_url(self, url: QUrl | str) -> bool:
        if isinstance(url, QUrl):
            url = url.toDisplayString()
        return url in self._urls

    def __contains__(self, item: QUrl | str) -> bool:
        return self.contains_url(item)

    def contains_blacklist_pattern(self, pattern: str):
        return pattern in self._blacklist

    def _add_url_no_update(self, url: str | QUrl):
        url = QUrl.fromUserInput(url) if isinstance(url, str) else QUrl(url)
        # Strip stuff we don't ever want to remember
        # Edge does remember user:pass in urls, and shows both cleartext - lolwut?
        url.setUserName(None)
        url.setPassword(None)
        if url.isEmpty() or url.isLocalFile() or not url.isValid() or self.is_blacklisted(url):
            return
        self._urls.add(url.toDisplayString())

    def _remove_url_no_update(self, url: str | QUrl):
        if isinstance(url, QUrl):
            url = url.toDisplayString()
        if url in self._urls:
            self._urls.remove(url)

    def _update_model(self):
        self.setStringList(self._urls)

    def __len__(self) -> int:
        return len(self._urls)
