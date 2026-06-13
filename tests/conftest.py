import pytest
import os

# Point to SQLite for tests – no Postgres required
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ["SCHEDULER_ENABLED"] = "false"