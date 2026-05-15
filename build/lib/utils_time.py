from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

# Primary posting windows: Mon-Thu at 9:15 AM and 12:40 PM ET, Fri at 9:15 AM only
PRIMARY = {
    0: [(9, 15), (12, 40)],  # Monday
    1: [(9, 15), (12, 40)],  # Tuesday
    2: [(9, 15), (12, 40)],  # Wednesday
    3: [(9, 15), (12, 40)],  # Thursday
    4: [(9, 15)]             # Friday
}

# Bump comment windows: Mon-Thu at 4:15 PM ET, Fri at 2:30 PM ET
BUMP = {
    0: (16, 15),  # Monday
    1: (16, 15),  # Tuesday
    2: (16, 15),  # Wednesday
    3: (16, 15),  # Thursday
    4: (14, 30)   # Friday
}


def next_publish_utc(now_utc, breaking=False):
    """Calculate next publish time in UTC based on ET business hours"""
    now_et = now_utc.astimezone(ET)
    wd = now_et.weekday()
    
    # Get today's windows
    windows = PRIMARY.get(wd, [])
    candidates = [datetime.combine(now_et.date(), time(h, m), tzinfo=ET) for h, m in windows]
    future = [c for c in candidates if c > now_et]
    
    # Breaking news can be published on next 30-min boundary before 4:30 PM ET
    if breaking and not future:
        cand = now_et.replace(minute=(now_et.minute // 30 + 1) * 30, second=0, microsecond=0)
        cutoff = now_et.replace(hour=16, minute=30, second=0, microsecond=0)
        if cand < cutoff:
            return cand.astimezone(UTC)
    
    if future:
        return future[0].astimezone(UTC)
    
    # Find next weekday 9:15 AM ET
    d = 1
    while True:
        nxt = now_et + timedelta(days=d)
        if nxt.weekday() <= 4:  # Monday=0 to Friday=4
            return datetime(nxt.year, nxt.month, nxt.day, 9, 15, tzinfo=ET).astimezone(UTC)
        d += 1


def bump_time_for_today_utc(now_utc):
    """Get bump comment time for today in UTC"""
    now_et = now_utc.astimezone(ET)
    wd = now_et.weekday()
    if wd > 4:  # Weekend
        return None
    h, m = BUMP[wd]
    bump = datetime.combine(now_et.date(), time(h, m), tzinfo=ET)
    return bump.astimezone(UTC)
