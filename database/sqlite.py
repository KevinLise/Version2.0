import aiosqlite
import os
from datetime import datetime
from config.settings import settings


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.database_path

    async def connect(self) -> aiosqlite.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        return conn

    async def init_tables(self) -> None:
        conn = await self.connect()
        try:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    response TEXT NOT NULL,
                    relevance_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                );

                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    request_id TEXT,
                    relevance_score REAL,
                    cache_hit INTEGER DEFAULT 0,
                    llm_called INTEGER DEFAULT 0,
                    escalated INTEGER DEFAULT 0,
                    response_time_ms REAL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    user_name TEXT,
                    original_message TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    context_retrieved TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key);
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
                CREATE INDEX IF NOT EXISTS idx_metrics_event ON metrics(event_type);
                CREATE INDEX IF NOT EXISTS idx_metrics_created ON metrics(created_at);

                CREATE TABLE IF NOT EXISTS inscripciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    edad INTEGER,
                    telefono TEXT,
                    email TEXT,
                    idioma TEXT NOT NULL,
                    nivel TEXT,
                    modalidad TEXT,
                    horario_preferido TEXT,
                    mensaje TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_inscripciones_estado ON inscripciones(estado);
                CREATE INDEX IF NOT EXISTS idx_inscripciones_created ON inscripciones(created_at);
            """)
            await conn.commit()
        finally:
            await conn.close()

    async def close(self, conn: aiosqlite.Connection) -> None:
        await conn.close()


db = Database()
