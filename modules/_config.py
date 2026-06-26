"""
Shared config helpers for AstralModules plugins.

Standardises the per-plugin config persistence pattern, replacing the
inconsistent ``userdata/<module>`` / ``userdata/<module>.json`` /
``temp/<module>`` mess seen in the source CustomModules repo.

All plugin config is stored as a single JSON document per plugin in the
AstralBot DB, under the env-var key ``PLUGIN_CONFIG_<plugin_name>``.
"""

from __future__ import annotations

import json
from typing import Any

_PREFIX = "PLUGIN_CONFIG_"


async def load_config(plugin_name: str, defaults: dict | None = None) -> dict:
    """Load a plugin's config from the DB, merged over defaults."""
    try:
        from astralbot import db
        if db is None:
            return dict(defaults or {})
        stored = await db.get_env(_PREFIX + plugin_name.upper(), default=None)
        if stored is None:
            return dict(defaults or {})
        if isinstance(stored, str):
            stored = json.loads(stored)
        merged = dict(defaults or {})
        merged.update(stored)
        return merged
    except Exception:
        return dict(defaults or {})


async def save_config(plugin_name: str, config: dict) -> None:
    """Persist a plugin's config to the DB."""
    try:
        from astralbot import db
        if db is None:
            return
        await db.set_env(_PREFIX + plugin_name.upper(), config)
    except Exception:
        pass


async def update_config(plugin_name: str, **changes: Any) -> dict:
    """Merge ``changes`` into the existing config and persist."""
    cfg = await load_config(plugin_name)
    cfg.update(changes)
    await save_config(plugin_name, cfg)
    return cfg
