import sqlite3
import os
from datetime import datetime
from typing import Optional, Tuple

class StateManager:
    def __init__(self, db_path: str = "pulse_state.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initializes the SQLite database with the pulse_runs table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pulse_runs (
                    id INTEGER PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    iso_week TEXT NOT NULL,
                    status TEXT CHECK(status IN ('STARTED', 'SUCCESS', 'FAILED')),
                    doc_heading_id TEXT,
                    gmail_draft_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, iso_week)
                )
            """)
            conn.commit()

    def check_idempotency(self, product_id: str, iso_week: str) -> Optional[str]:
        """
        Checks if a successful run already exists for the given product and week.
        Returns the status if it exists, otherwise None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT status FROM pulse_runs WHERE product_id = ? AND iso_week = ?",
                (product_id, iso_week)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def start_run(self, product_id: str, iso_week: str):
        """Records the start of a run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pulse_runs (product_id, iso_week, status) VALUES (?, ?, 'STARTED')",
                (product_id, iso_week)
            )
            conn.commit()

    def complete_run(self, product_id: str, iso_week: str, doc_heading_id: str, gmail_draft_id: str):
        """Records a successful run completion with metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE pulse_runs 
                SET status = 'SUCCESS', doc_heading_id = ?, gmail_draft_id = ?, timestamp = CURRENT_TIMESTAMP
                WHERE product_id = ? AND iso_week = ?
                """,
                (doc_heading_id, gmail_draft_id, product_id, iso_week)
            )
            conn.commit()

    def fail_run(self, product_id: str, iso_week: str):
        """Records a failed run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE pulse_runs SET status = 'FAILED' WHERE product_id = ? AND iso_week = ?",
                (product_id, iso_week)
            )
            conn.commit()
