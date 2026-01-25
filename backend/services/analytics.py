import sqlite3
import time
import json
import os
from typing import Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stats.db")

class AnalyticsService:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_id TEXT,
                    tier TEXT,
                    endpoint TEXT,
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    bypass BOOLEAN,
                    intent TEXT,
                    city TEXT,
                    language TEXT,
                    error TEXT
                )
            """)
            conn.commit()

    def record_interaction(self, 
                           user_id: str, 
                           tier: str, 
                           endpoint: str, 
                           tokens_in: int = 0, 
                           tokens_out: int = 0, 
                           bypass: bool = False,
                           intent: str = "unknown",
                           city: str = "unknown",
                           error: str = None):
        """Log a single interaction to DB."""
        try:
            # Simple language detection from intent or just default
            # In a real app we'd save the detected language
            language = "es" # Default for now
            
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO requests 
                    (timestamp, user_id, tier, endpoint, tokens_in, tokens_out, bypass, intent, city, language, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (time.time(), user_id, tier, endpoint, tokens_in, tokens_out, bypass, intent, city, language, error))
        except Exception as e:
            print(f"Analytics Error: {e}")

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate all stats for the admin dashboard."""
        stats = {}
        now = time.time()
        day_ago = now - 86400
        week_ago = now - (86400 * 7)
        month_ago = now - (86400 * 30)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. USUARIOS
            stats["users"] = {
                "total_unique": cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests").fetchone()[0],
                "active_today": cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests WHERE timestamp > ?", (day_ago,)).fetchone()[0],
                "active_week": cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests WHERE timestamp > ?", (week_ago,)).fetchone()[0],
                "active_month": cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests WHERE timestamp > ?", (month_ago,)).fetchone()[0],
            }
            # New vs Returning (Simplified: users seen before today vs first seen today)
            # This is complex in SQL simple, let's approximate or skip for MVP
            # Approximation: Users valid > 24h ago are returning
            
            # 2. ENGAGEMENT
            total_reqs = cursor.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
            stats["engagement"] = {
                "total_queries": total_reqs,
                "avg_per_user": round(total_reqs / max(stats["users"]["total_unique"], 1), 1),
                # Duration requires session logic, skipping for simple MVP or doing max(ts) - min(ts) per user averaged
            }
            
            # 3. COSTOS
            # Pricing constants
            COST_IN = 0.003 / 1000
            COST_OUT = 0.015 / 1000
            COST_VOICE = 0.00003 * 5 # char approx per token

            sums = cursor.execute("SELECT SUM(tokens_in), SUM(tokens_out), SUM(case when bypass=1 then 1 else 0 end) FROM requests").fetchone()
            tin = sums[0] or 0
            tout = sums[1] or 0
            bypasses = sums[2] or 0
            
            llm_cost = (tin * COST_IN) + (tout * COST_OUT)
            voice_cost = tout * COST_VOICE
            total_cost = llm_cost + voice_cost
            
            stats["costs"] = {
                "tokens_in": tin,
                "tokens_out": tout,
                "total_usd": round(total_cost, 4),
                "cost_per_user": round(total_cost / max(stats["users"]["total_unique"], 1), 4),
                "bypass_rate": round((bypasses / max(total_reqs, 1)) * 100, 1)
            }

            # 4. PRODUCTO / TOP INTENTS
            top_intents = cursor.execute("SELECT intent, COUNT(*) as c FROM requests GROUP BY intent ORDER BY c DESC LIMIT 5").fetchall()
            stats["top_intents"] = [{"name": r[0], "count": r[1]} for r in top_intents]

            # 5. RETENTION (D1) 
            # Users active yesterday AND today
            # Skipping complex SQL for now to ensure speed
            
        return stats

analytics = AnalyticsService()
