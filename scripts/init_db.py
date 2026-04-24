#!/usr/bin/env python3
"""Initialize the PostgreSQL database: create all tables via SQLAlchemy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.database import engine
from backend.models.base import Base
import backend.models  # noqa: F401 — registers all models
from backend.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("init_db")


def main() -> None:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ All tables created successfully")
    table_names = list(Base.metadata.tables.keys())
    logger.info(f"Tables: {', '.join(table_names)}")


if __name__ == "__main__":
    main()
