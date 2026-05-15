import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DB_PATH = "personalize.db"


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            company TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            published_at TEXT NOT NULL,
            magnitude INTEGER DEFAULT 0,
            relevance REAL DEFAULT 0.5,
            recency_days INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            UNIQUE(domain, title)
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            signal_type TEXT,
            subject TEXT NOT NULL,
            opening TEXT NOT NULL,
            is_fallback INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        )
        """)
        
        c.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_domain ON signals(domain)
        """)
        
        c.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(score DESC)
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS signal_pins (
            domain TEXT PRIMARY KEY,
            signal_id TEXT NOT NULL,
            pinned_at INTEGER NOT NULL,
            pinned_by TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS signal_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            signal_id TEXT,
            signal_type TEXT,
            excluded_at INTEGER NOT NULL,
            excluded_by TEXT,
            reason TEXT,
            UNIQUE(domain, signal_id),
            UNIQUE(domain, signal_type)
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            company TEXT NOT NULL,
            signal_type TEXT,
            signal_title TEXT,
            signal_summary TEXT,
            url TEXT,
            relevance REAL DEFAULT 0.5,
            magnitude INTEGER DEFAULT 0,
            discovered_at TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            notes TEXT
        )
        """)
        
        c.execute("""
        CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status)
        """)
        
        c.commit()


def calculate_score(published_at: str, relevance: float, magnitude: int) -> int:
    """
    Calculate signal score (0-100)
    Recency: 0-40, Relevance: 0-40, Magnitude: 0-20
    """
    try:
        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
        
        if days_old <= 7:
            recency_score = 40
        elif days_old <= 30:
            recency_score = 30
        elif days_old <= 60:
            recency_score = 20
        elif days_old <= 90:
            recency_score = 10
        else:
            recency_score = 0
        
        relevance_score = min(40, int(relevance * 40))
        
        magnitude_score = min(20, int((magnitude / 50) * 20))
        
        return recency_score + relevance_score + magnitude_score
    except Exception:
        return 0


def save_signal(signal: Dict):
    """Save or update a signal"""
    with sqlite3.connect(DB_PATH) as c:
        pub_date = datetime.fromisoformat(signal['published_at'].replace('Z', '+00:00'))
        days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
        
        score = calculate_score(
            signal['published_at'],
            signal.get('relevance', 0.5),
            signal.get('magnitude', 0)
        )
        
        c.execute("""
            INSERT INTO signals (
                id, domain, company, type, title, summary, url, 
                published_at, magnitude, relevance, recency_days, score, 
                icp_score, icp_explanation, employees, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain, title) DO UPDATE SET
                summary=excluded.summary,
                url=excluded.url,
                magnitude=excluded.magnitude,
                relevance=excluded.relevance,
                recency_days=excluded.recency_days,
                score=excluded.score,
                icp_score=excluded.icp_score,
                icp_explanation=excluded.icp_explanation,
                employees=excluded.employees
        """, (
            signal['id'],
            signal['domain'],
            signal['company'],
            signal['type'],
            signal['title'],
            signal.get('summary', ''),
            signal.get('url', ''),
            signal['published_at'],
            signal.get('magnitude', 0),
            signal.get('relevance', 0.5),
            days_old,
            score,
            signal.get('icp_score', 0),
            signal.get('icp_explanation', ''),
            signal.get('employees'),
            int(time.time())
        ))
        c.commit()


def get_top_signals(domain: str, limit: int = 3, max_age_days: int = 45) -> List[Dict]:
    """Get top N signals for a domain, ordered by score, within freshness window"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("""
            SELECT * FROM signals 
            WHERE domain = ? AND recency_days <= ?
            ORDER BY score DESC 
            LIMIT ?
        """, (domain, max_age_days, limit)).fetchall()
        
        return [dict(row) for row in rows]


def get_signal_by_id(signal_id: str) -> Optional[Dict]:
    """Get a specific signal by ID"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
        return dict(row) if row else None


def get_all_signals(limit: int = 100) -> List[Dict]:
    """Get all signals ordered by score"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("""
            SELECT * FROM signals 
            ORDER BY score DESC, created_at DESC 
            LIMIT ?
        """, (limit,)).fetchall()
        
        return [dict(row) for row in rows]


def update_signal_icp_score(signal_id: str, icp_score: int, icp_explanation: str) -> bool:
    """Update ICP score and explanation for a signal"""
    with sqlite3.connect(DB_PATH) as c:
        try:
            c.execute("""
                UPDATE signals 
                SET icp_score = ?, icp_explanation = ?
                WHERE id = ?
            """, (icp_score, icp_explanation, signal_id))
            c.commit()
            return True
        except Exception as e:
            print(f"Update ICP score failed: {e}")
            return False


def purge_old_signals(days: int = 90):
    """Delete signals older than N days"""
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            DELETE FROM signals 
            WHERE recency_days > ?
        """, (days,))
        c.commit()


def save_template(template: Dict):
    """Save or update a template"""
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            INSERT INTO templates (
                id, name, signal_type, subject, opening, is_fallback, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                signal_type=excluded.signal_type,
                subject=excluded.subject,
                opening=excluded.opening,
                is_fallback=excluded.is_fallback
        """, (
            template['id'],
            template['name'],
            template.get('signal_type', ''),
            template['subject'],
            template['opening'],
            template.get('is_fallback', 0),
            int(time.time())
        ))
        c.commit()


def get_template(name: str) -> Optional[Dict]:
    """Get template by name"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM templates WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None


def get_template_for_signal(signal_type: str) -> Optional[Dict]:
    """Get best template for signal type"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("""
            SELECT * FROM templates 
            WHERE signal_type = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (signal_type,)).fetchone()
        return dict(row) if row else None


def get_fallback_template() -> Optional[Dict]:
    """Get fallback template"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        row = c.execute("""
            SELECT * FROM templates 
            WHERE is_fallback = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        """, ()).fetchone()
        return dict(row) if row else None


def get_all_templates() -> List[Dict]:
    """Get all templates"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM templates ORDER BY name").fetchall()
        return [dict(row) for row in rows]


def pin_signal(domain: str, signal_id: str, pinned_by: str = "user") -> bool:
    """Pin a signal for a domain (overrides autonomous selection)"""
    with sqlite3.connect(DB_PATH) as c:
        try:
            c.execute("""
                INSERT INTO signal_pins (domain, signal_id, pinned_at, pinned_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    signal_id=excluded.signal_id,
                    pinned_at=excluded.pinned_at,
                    pinned_by=excluded.pinned_by
            """, (domain, signal_id, int(time.time()), pinned_by))
            c.commit()
            return True
        except Exception as e:
            print(f"Pin signal failed: {e}")
            return False


def unpin_signal(domain: str) -> bool:
    """Remove pinned signal for domain (restore autonomous mode)"""
    with sqlite3.connect(DB_PATH) as c:
        c.execute("DELETE FROM signal_pins WHERE domain = ?", (domain,))
        c.commit()
        return True


def get_pinned_signal(domain: str) -> Optional[str]:
    """Get pinned signal ID for domain"""
    with sqlite3.connect(DB_PATH) as c:
        row = c.execute("""
            SELECT signal_id FROM signal_pins WHERE domain = ?
        """, (domain,)).fetchone()
        return row[0] if row else None


def exclude_signal(domain: str, signal_id: Optional[str] = None, signal_type: Optional[str] = None, 
                   reason: str = "", excluded_by: str = "user") -> bool:
    """Exclude a specific signal or signal type for a domain"""
    if not signal_id and not signal_type:
        return False
    
    with sqlite3.connect(DB_PATH) as c:
        try:
            c.execute("""
                INSERT INTO signal_exclusions 
                (domain, signal_id, signal_type, excluded_at, excluded_by, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (domain, signal_id, signal_type, int(time.time()), excluded_by, reason))
            c.commit()
            return True
        except Exception as e:
            print(f"Exclude signal failed: {e}")
            return False


def remove_exclusion(domain: str, signal_id: Optional[str] = None, signal_type: Optional[str] = None) -> bool:
    """Remove signal or type exclusion"""
    with sqlite3.connect(DB_PATH) as c:
        if signal_id:
            c.execute("DELETE FROM signal_exclusions WHERE domain = ? AND signal_id = ?", 
                     (domain, signal_id))
        elif signal_type:
            c.execute("DELETE FROM signal_exclusions WHERE domain = ? AND signal_type = ?", 
                     (domain, signal_type))
        c.commit()
        return True


def get_exclusions(domain: str) -> List[Dict]:
    """Get all exclusions for a domain"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("""
            SELECT * FROM signal_exclusions WHERE domain = ?
        """, (domain,)).fetchall()
        return [dict(row) for row in rows]


def save_prospect(prospect: Dict) -> bool:
    """Save discovered prospect to database"""
    with sqlite3.connect(DB_PATH) as c:
        try:
            c.execute("""
                INSERT INTO prospects (
                    domain, company, signal_type, signal_title, signal_summary,
                    url, relevance, magnitude, fit_score, icp_explanation, 
                    discovered_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    signal_type=excluded.signal_type,
                    signal_title=excluded.signal_title,
                    signal_summary=excluded.signal_summary,
                    url=excluded.url,
                    relevance=excluded.relevance,
                    magnitude=excluded.magnitude,
                    fit_score=excluded.fit_score,
                    icp_explanation=excluded.icp_explanation
            """, (
                prospect['domain'],
                prospect['company'],
                prospect.get('signal_type', ''),
                prospect.get('signal_title', ''),
                prospect.get('signal_summary', ''),
                prospect.get('url', ''),
                prospect.get('relevance', 0.5),
                prospect.get('magnitude', 0),
                prospect.get('fit_score', 0),
                prospect.get('icp_explanation', ''),
                prospect.get('discovered_at', datetime.now().isoformat()),
                'new'
            ))
            c.commit()
            return True
        except Exception as e:
            print(f"Save prospect failed: {e}")
            return False


def get_prospects(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Get prospects, optionally filtered by status"""
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        if status:
            rows = c.execute("""
                SELECT * FROM prospects WHERE status = ? 
                ORDER BY discovered_at DESC LIMIT ?
            """, (status, limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT * FROM prospects 
                ORDER BY discovered_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def update_prospect_status(domain: str, status: str, notes: Optional[str] = None) -> bool:
    """Update prospect status (new, contacted, qualified, disqualified)"""
    with sqlite3.connect(DB_PATH) as c:
        if notes:
            c.execute("""
                UPDATE prospects SET status = ?, notes = ? WHERE domain = ?
            """, (status, notes, domain))
        else:
            c.execute("""
                UPDATE prospects SET status = ? WHERE domain = ?
            """, (status, domain))
        c.commit()
        return True
