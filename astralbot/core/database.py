"""
Database backend — pluggable.

Defaults to **SQLite** (zero-config, file-based) for single-instance deployments.
Optionally supports **MongoDB** via motor when DATABASE_URL is set.

Both backends expose the same async API so plugins can stay storage-agnostic.

Public surface (Database):
    await db.get(collection, query)        -> dict | None
    await db.find(collection, query)       -> list[dict]
    await db.insert(collection, doc)       -> inserted id
    await db.update(collection, query, set_doc) -> int  (count modified)
    await db.delete(collection, query)     -> int
    await db.count(collection, query=None) -> int

    # Runtime env-store (Zelretch-style ENV class pattern)
    await db.get_env(key, default=None)
    await db.set_env(key, value)
    await db.del_env(key)
    await db.list_env() -> dict

    # Sudo / master user helpers
    await db.add_master(user_id)
    await db.del_master(user_id)
    await db.is_master(user_id) -> bool
    await db.list_masters() -> list[int]
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

LOGS = logging.getLogger("astralbot.db")


class Database:
    """Abstract async DB interface. Subclasses implement the storage backend."""

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def get(self, collection: str, query: dict) -> dict | None: ...
    async def find(self, collection: str, query: dict | None = None) -> list[dict]: ...
    async def insert(self, collection: str, doc: dict) -> Any: ...
    async def update(self, collection: str, query: dict, set_doc: dict) -> int: ...
    async def delete(self, collection: str, query: dict) -> int: ...
    async def count(self, collection: str, query: dict | None = None) -> int: ...

    # ENV store — runtime config persistence
    async def get_env(self, key: str, default: Any = None) -> Any: ...
    async def set_env(self, key: str, value: Any) -> None: ...
    async def del_env(self, key: str) -> None: ...
    async def list_env(self) -> dict: ...

    # Master users — sudo tier management
    async def add_master(self, user_id: int) -> None: ...
    async def del_master(self, user_id: int) -> None: ...
    async def is_master(self, user_id: int) -> bool: ...
    async def list_masters(self) -> list[int]: ...


# ---------------------------------------------------------------------------
# SQLite backend (default)
# ---------------------------------------------------------------------------


class SQLiteDatabase(Database):
    """SQLite backend. Uses aiosqlite for async, falls back to thread-wrapped sync."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sync: sqlite3.Connection | None = None
        try:
            import aiosqlite
            self._aiosqlite_mod = aiosqlite
            self._aiosqlite = True
        except ImportError:
            self._aiosqlite_mod = None
            self._aiosqlite = False

    async def connect(self) -> None:
        if self._aiosqlite:
            self._conn = await self._aiosqlite_mod.connect(str(self.path))
            self._conn.row_factory = sqlite3.Row
            await self._init_schema()
            LOGS.info("SQLite (aiosqlite) connected at %s", self.path)
        else:
            self._sync = sqlite3.connect(str(self.path), check_same_thread=False)
            self._sync.row_factory = sqlite3.Row
            self._init_schema_sync()
            LOGS.info("SQLite (sync) connected at %s", self.path)

    async def close(self) -> None:
        if self._aiosqlite:
            await self._conn.close()
        elif self._sync:
            self._sync.close()

    # ----- schema -----
    async def _init_schema(self) -> None:
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS masters (
                user_id INTEGER PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS docs (
                collection TEXT NOT NULL,
                id TEXT NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (collection, id)
            );
            CREATE INDEX IF NOT EXISTS idx_docs_collection ON docs(collection);
            """
        )
        await self._conn.commit()

    def _init_schema_sync(self) -> None:
        self._sync.executescript(
            """
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS masters (
                user_id INTEGER PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS docs (
                collection TEXT NOT NULL,
                id TEXT NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (collection, id)
            );
            CREATE INDEX IF NOT EXISTS idx_docs_collection ON docs(collection);
            """
        )
        self._sync.commit()

    # ----- generic collection ops (mapped to JSON docs table) -----
    @staticmethod
    def _query_to_id(query: dict) -> str:
        # For SQLite we hash query keys to a deterministic id
        # Plugins are expected to query by a single primary key (e.g. {"_id": 123})
        if not query:
            return "_all"
        return json.dumps(query, sort_keys=True, default=str)

    async def get(self, collection: str, query: dict) -> dict | None:
        doc_id = self._query_to_id(query)
        if self._aiosqlite:
            cur = await self._conn.execute(
                "SELECT data FROM docs WHERE collection=? AND id=?", (collection, doc_id)
            )
            row = await cur.fetchone()
            await cur.close()
            return json.loads(row["data"]) if row else None
        cur = self._sync.execute(
            "SELECT data FROM docs WHERE collection=? AND id=?", (collection, doc_id)
        )
        row = cur.fetchone()
        return json.loads(row["data"]) if row else None

    async def find(self, collection: str, query: dict | None = None) -> list[dict]:
        # Simple: return all docs in collection, optionally filtered client-side
        if self._aiosqlite:
            cur = await self._conn.execute(
                "SELECT data FROM docs WHERE collection=?", (collection,)
            )
            rows = await cur.fetchall()
            await cur.close()
            docs = [json.loads(r["data"]) for r in rows]
        else:
            cur = self._sync.execute(
                "SELECT data FROM docs WHERE collection=?", (collection,)
            )
            rows = cur.fetchall()
            docs = [json.loads(r["data"]) for r in rows]
        if not query:
            return docs
        # Naive in-memory filter — sufficient for small per-chat plugin state
        return [
            d for d in docs
            if all(d.get(k) == v for k, v in query.items())
        ]

    async def insert(self, collection: str, doc: dict) -> str:
        if "_id" not in doc:
            doc["_id"] = str(int(time.time() * 1000))
        doc_id = self._query_to_id({"_id": doc["_id"]})
        data = json.dumps(doc, default=str)
        if self._aiosqlite:
            await self._conn.execute(
                "INSERT OR REPLACE INTO docs(collection, id, data) VALUES (?,?,?)",
                (collection, doc_id, data),
            )
            await self._conn.commit()
        else:
            self._sync.execute(
                "INSERT OR REPLACE INTO docs(collection, id, data) VALUES (?,?,?)",
                (collection, doc_id, data),
            )
            self._sync.commit()
        return doc["_id"]

    async def update(self, collection: str, query: dict, set_doc: dict) -> int:
        existing = await self.get(collection, query)
        if not existing:
            return 0
        existing.update(set_doc)
        await self.insert(collection, existing)
        return 1

    async def delete(self, collection: str, query: dict) -> int:
        doc_id = self._query_to_id(query)
        if self._aiosqlite:
            cur = await self._conn.execute(
                "DELETE FROM docs WHERE collection=? AND id=?", (collection, doc_id)
            )
            await self._conn.commit()
            return cur.rowcount
        cur = self._sync.execute(
            "DELETE FROM docs WHERE collection=? AND id=?", (collection, doc_id)
        )
        self._sync.commit()
        return cur.rowcount

    async def count(self, collection: str, query: dict | None = None) -> int:
        if not query:
            if self._aiosqlite:
                cur = await self._conn.execute(
                    "SELECT COUNT(*) FROM docs WHERE collection=?", (collection,)
                )
                row = await cur.fetchone()
                await cur.close()
                return row[0]
            cur = self._sync.execute(
                "SELECT COUNT(*) FROM docs WHERE collection=?", (collection,)
            )
            return cur.fetchone()[0]
        return len(await self.find(collection, query))

    # ----- env store -----
    async def get_env(self, key: str, default: Any = None) -> Any:
        if self._aiosqlite:
            cur = await self._conn.execute("SELECT value FROM kv WHERE key=?", (key,))
            row = await cur.fetchone()
            await cur.close()
            return json.loads(row["value"]) if row else default
        cur = self._sync.execute("SELECT value FROM kv WHERE key=?", (key,))
        row = cur.fetchone()
        return json.loads(row["value"]) if row else default

    async def set_env(self, key: str, value: Any) -> None:
        v = json.dumps(value, default=str)
        if self._aiosqlite:
            await self._conn.execute(
                "INSERT OR REPLACE INTO kv(key, value) VALUES (?,?)", (key, v)
            )
            await self._conn.commit()
        else:
            self._sync.execute(
                "INSERT OR REPLACE INTO kv(key, value) VALUES (?,?)", (key, v)
            )
            self._sync.commit()

    async def del_env(self, key: str) -> None:
        if self._aiosqlite:
            await self._conn.execute("DELETE FROM kv WHERE key=?", (key,))
            await self._conn.commit()
        else:
            self._sync.execute("DELETE FROM kv WHERE key=?", (key,))
            self._sync.commit()

    async def list_env(self) -> dict:
        if self._aiosqlite:
            cur = await self._conn.execute("SELECT key, value FROM kv")
            rows = await cur.fetchall()
            await cur.close()
        else:
            cur = self._sync.execute("SELECT key, value FROM kv")
            rows = cur.fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # ----- masters -----
    async def add_master(self, user_id: int) -> None:
        if self._aiosqlite:
            await self._conn.execute(
                "INSERT OR IGNORE INTO masters(user_id) VALUES (?)", (user_id,)
            )
            await self._conn.commit()
        else:
            self._sync.execute(
                "INSERT OR IGNORE INTO masters(user_id) VALUES (?)", (user_id,)
            )
            self._sync.commit()

    async def del_master(self, user_id: int) -> None:
        if self._aiosqlite:
            await self._conn.execute("DELETE FROM masters WHERE user_id=?", (user_id,))
            await self._conn.commit()
        else:
            self._sync.execute("DELETE FROM masters WHERE user_id=?", (user_id,))
            self._sync.commit()

    async def is_master(self, user_id: int) -> bool:
        if self._aiosqlite:
            cur = await self._conn.execute(
                "SELECT 1 FROM masters WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            await cur.close()
            return row is not None
        cur = self._sync.execute(
            "SELECT 1 FROM masters WHERE user_id=?", (user_id,)
        )
        return cur.fetchone() is not None

    async def list_masters(self) -> list[int]:
        if self._aiosqlite:
            cur = await self._conn.execute("SELECT user_id FROM masters")
            rows = await cur.fetchall()
            await cur.close()
        else:
            cur = self._sync.execute("SELECT user_id FROM masters")
            rows = cur.fetchall()
        return [r["user_id"] for r in rows]


# ---------------------------------------------------------------------------
# MongoDB backend (optional)
# ---------------------------------------------------------------------------


class MongoDBDatabase(Database):
    """MongoDB backend via motor. Used when DATABASE_URL is set."""

    def __init__(self, uri: str, db_name: str = "astralbot"):
        import motor.motor_asyncio  # type: ignore
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self._db = self._client[db_name]

    async def connect(self) -> None:
        await self._client.admin.command("ping")
        LOGS.info("MongoDB connected → db=%s", self._db.name)

    async def close(self) -> None:
        self._client.close()

    async def get(self, collection: str, query: dict) -> dict | None:
        return await self._db[collection].find_one(query)

    async def find(self, collection: str, query: dict | None = None) -> list[dict]:
        cur = self._db[collection].find(query or {})
        return await cur.to_list(length=None)

    async def insert(self, collection: str, doc: dict) -> Any:
        result = await self._db[collection].insert_one(doc)
        return result.inserted_id

    async def update(self, collection: str, query: dict, set_doc: dict) -> int:
        result = await self._db[collection].update_many(query, {"$set": set_doc})
        return result.modified_count

    async def delete(self, collection: str, query: dict) -> int:
        result = await self._db[collection].delete_many(query)
        return result.deleted_count

    async def count(self, collection: str, query: dict | None = None) -> int:
        return await self._db[collection].count_documents(query or {})

    async def get_env(self, key: str, default: Any = None) -> Any:
        doc = await self._db["env"].find_one({"_id": key})
        return doc["value"] if doc else default

    async def set_env(self, key: str, value: Any) -> None:
        await self._db["env"].update_one(
            {"_id": key}, {"$set": {"value": value}}, upsert=True
        )

    async def del_env(self, key: str) -> None:
        await self._db["env"].delete_one({"_id": key})

    async def list_env(self) -> dict:
        cur = self._db["env"].find({})
        docs = await cur.to_list(length=None)
        return {d["_id"]: d["value"] for d in docs}

    async def add_master(self, user_id: int) -> None:
        await self._db["masters"].update_one(
            {"_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
        )

    async def del_master(self, user_id: int) -> None:
        await self._db["masters"].delete_one({"_id": user_id})

    async def is_master(self, user_id: int) -> bool:
        return await self._db["masters"].count_documents({"_id": user_id}) > 0

    async def list_masters(self) -> list[int]:
        cur = self._db["masters"].find({})
        docs = await cur.to_list(length=None)
        return [d["user_id"] for d in docs]


async def open_database(cfg) -> Database:
    """Factory: pick the right backend based on Config."""
    if cfg.database_url:
        try:
            db = MongoDBDatabase(cfg.database_url, cfg.database_name)
            await db.connect()
            return db
        except Exception as exc:
            LOGS.warning("MongoDB connection failed (%s); falling back to SQLite.", exc)
    db = SQLiteDatabase(cfg.data_dir / "astralbot.db")
    await db.connect()
    return db
