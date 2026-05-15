import re
import asyncio
import time
import os
import socket
import dns.resolver
import smtplib
from email.utils import parseaddr

ROLE_PREFIXES = {"info", "contact", "sales", "support", "help", "hello", "hi", "admin", "team"}
DISPOSABLES_FILE = "disposables.txt"
CATCH_ALL_PROBES = ["doesnotexist123", "randomxyz987", "nopeaddress555"]

HELO_DOMAIN = os.getenv("VERIFIER_HELO_DOMAIN", "echotray.ai")
FROM_EMAIL = os.getenv("VERIFIER_FROM_EMAIL", "verify@echotray.ai")
SLOW_MS = int(os.getenv("VERIFIER_SLOW_MODE_MS", "300"))

_disposables = set()


def load_disposables():
    global _disposables
    if not _disposables and os.path.exists(DISPOSABLES_FILE):
        with open(DISPOSABLES_FILE, "r") as f:
            _disposables = {line.strip().lower() for line in f if line.strip()}


def is_role_address(local: str) -> bool:
    return local.split("+")[0].lower() in ROLE_PREFIXES


def is_disposable(domain: str) -> bool:
    load_disposables()
    return domain.lower() in _disposables


def syntax_valid(email: str) -> bool:
    try:
        name, addr = parseaddr(email)
        if '@' not in addr:
            return False
        local, domain = addr.rsplit('@', 1)
        if not local or not domain:
            return False
        # Basic regex check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, addr))
    except Exception:
        return False


def get_mx_records(domain: str):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return sorted([(str(a.exchange).rstrip('.'), a.preference) for a in answers], key=lambda x: x[1])
    except Exception:
        return []


def smtp_rcpt_check(mx_host: str, target_email: str, timeout=5):
    try:
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.set_debuglevel(0)
        smtp.connect(mx_host, 25)
        smtp.ehlo(HELO_DOMAIN)
        smtp.mail(FROM_EMAIL)
        code, msg = smtp.rcpt(target_email)
        smtp.quit()

        if 200 <= code < 300:
            return "valid", code, str(msg)
        elif code in (450, 451, 452):
            return "unknown", code, str(msg)
        else:
            return "invalid", code, str(msg)
    except socket.timeout:
        return "unknown", 408, "Connection timeout"
    except smtplib.SMTPConnectError as e:
        return "unknown", 421, f"Connection refused: {str(e)}"
    except smtplib.SMTPServerDisconnected:
        return "unknown", 421, "Server disconnected"
    except Exception as e:
        return "unknown", 500, f"Error: {str(e)}"


def detect_catch_all(mx_host: str, domain: str, timeout=5):
    positives = 0
    for prefix in CATCH_ALL_PROBES[:2]:  # Only test 2 instead of 3 for speed
        try_email = f"{prefix}{int(time.time())}@{domain}"
        status, code, _ = smtp_rcpt_check(mx_host, try_email, timeout=timeout)
        if status == "valid":
            positives += 1
        time.sleep(SLOW_MS / 1000)
    return positives >= 2


def verify_email(email: str):
    result = {
        "email": email,
        "syntax": False,
        "has_mx": False,
        "smtp_status": "unknown",
        "smtp_code": None,
        "catch_all": False,
        "disposable": False,
        "role": False,
        "score": 0
    }

    if not syntax_valid(email):
        return result

    result["syntax"] = True
    local, domain = email.split("@", 1)
    result["role"] = is_role_address(local)
    result["disposable"] = is_disposable(domain)

    mx_records = get_mx_records(domain)
    result["has_mx"] = len(mx_records) > 0
    if not result["has_mx"]:
        return score_result(result)

    # Try first MX server only for speed
    for (mx_host, _prio) in mx_records[:1]:
        try:
            status, code, msg = smtp_rcpt_check(mx_host, email, timeout=5)
            result["smtp_status"] = status
            result["smtp_code"] = code

            # Skip catch-all detection if SMTP check failed or timed out
            if status == "unknown" and code in (408, 421, 500):
                # Connection issues - skip catch-all
                result["catch_all"] = False
            elif status != "valid":
                try:
                    result["catch_all"] = detect_catch_all(mx_host, domain, timeout=3)
                except Exception:
                    result["catch_all"] = False

            break
        except Exception as e:
            result["smtp_status"] = "unknown"
            result["smtp_code"] = 500
            break

    return score_result(result)


def score_result(r: dict):
    score = 0
    if r["syntax"]: 
        score += 20
    if r["has_mx"]: 
        score += 40

    if r["smtp_status"] == "valid":
        score += 30
    elif r["smtp_status"] == "unknown":
        score += 10

    if r["disposable"]: 
        score -= 15
    if r["role"]: 
        score -= 10
    if r["catch_all"]: 
        score -= 10

    r["score"] = max(0, min(100, score))
    return r
