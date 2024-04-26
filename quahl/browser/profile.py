from copy import copy
from typing import Union

from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtCore import QObject, QStandardPaths, Slot


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

    _settings: BrowserSettings
    _anonymous_profile: Union["BrowserProfile", None] = None

    def __init__(
            self,
            name: str = "DefaultProfile",
            parent: QObject | None = None,
            settings: BrowserSettings | None = None):
        super().__init__(name, parent)
        self._settings = settings if settings else BrowserSettings()
        self._apply_settings()

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
