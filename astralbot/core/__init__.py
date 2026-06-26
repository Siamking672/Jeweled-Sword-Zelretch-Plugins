"""astralbot.core package — re-exports for convenience."""

from astralbot.core.config import Config, ConfigError
from astralbot.core.database import Database, open_database, SQLiteDatabase, MongoDBDatabase
from astralbot.core.client import AstralClient, build_clients, stop_clients
from astralbot.core.loader import PluginLoader, PluginManifest
from astralbot.core.logger import setup_logging, TelegramLogHandler
from astralbot.core.permissions import can_run, PermissionDenied
from astralbot.core.updater import clone_or_pull_plugin_repo, restart_process

__all__ = [
    "Config",
    "ConfigError",
    "Database",
    "open_database",
    "SQLiteDatabase",
    "MongoDBDatabase",
    "AstralClient",
    "build_clients",
    "stop_clients",
    "PluginLoader",
    "PluginManifest",
    "setup_logging",
    "TelegramLogHandler",
    "can_run",
    "PermissionDenied",
    "clone_or_pull_plugin_repo",
    "restart_process",
]
