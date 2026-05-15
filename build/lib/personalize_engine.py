import re
from typing import Dict, Optional
from src.personalize_db import get_top_signals, get_template_for_signal, get_fallback_template


def render_template(template_text: str, context: Dict) -> str:
    """
    Render template with context variables
    Supports {{variable}} and {{nested.variable}} syntax
    """
    def replace_var(match):
        var = match.group(1).strip()
        parts = var.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, '')
            else:
                return ''
        
        return str(value) if value is not None else ''
    
    return re.sub(r'\{\{([^}]+)\}\}', replace_var, template_text)


def personalize_email(
    domain: str,
    company: str,
    first_name: str,
    role: Optional[str] = None,
    pinned_signal_id: Optional[str] = None
) -> Dict:
    """
    Generate personalized subject and opening based on top signal
    
    AUTONOMOUS MODE (default):
    - Fetches top signals for domain
    - Applies freshness window (≤45 days) and score threshold (≥70)
    - Selects best signal automatically
    - Falls back to generic template if no valid signals
    
    MANUAL OVERRIDE:
    - Pass pinned_signal_id to force a specific signal
    
    Returns:
        {
            "subject": str,
            "opening": str,
            "signal": dict or None,
            "template_used": str,
            "selection_reason": str
        }
    """
    from src.personalize_db import get_signal_by_id, get_pinned_signal, get_exclusions
    
    if not pinned_signal_id:
        pinned_signal_id = get_pinned_signal(domain)
    
    if pinned_signal_id:
        pinned = get_signal_by_id(pinned_signal_id)
        if pinned:
            return _render_with_signal(pinned, company, first_name, role, reason="manual_pin")
    
    signals = get_top_signals(domain, limit=10, max_age_days=45)
    
    exclusions = get_exclusions(domain)
    excluded_ids = {e['signal_id'] for e in exclusions if e.get('signal_id')}
    excluded_types = {e['signal_type'] for e in exclusions if e.get('signal_type')}
    
    valid_signals = [
        s for s in signals 
        if s['score'] >= 70 
        and s.get('recency_days', 999) <= 45
        and s['id'] not in excluded_ids
        and s['type'] not in excluded_types
    ]
    
    if not valid_signals:
        reason = f"no_valid_signals (threshold: score≥70, age≤45d, {len(exclusions)} exclusions)"
        return _render_fallback(company, first_name, role, reason)
    
    top_signal = valid_signals[0]
    reason = f"auto_selected (score: {top_signal['score']}, age: {top_signal.get('recency_days', 0)}d, rank: 1/{len(valid_signals)})"
    return _render_with_signal(top_signal, company, first_name, role, reason)


def _render_with_signal(signal: Dict, company: str, first_name: str, role: Optional[str], reason: str) -> Dict:
    """Render personalization using a specific signal with dynamic generation - FULL EMAIL"""
    from src.personalize_generator import generate_dynamic_personalization
    
    # Generate complete 5-section email
    result = generate_dynamic_personalization(signal, company, first_name, full_email=True)
    
    return {
        "subject": result['subject'],
        "opening": result['opening'],
        "insight": result.get('insight', ''),
        "bridge": result.get('bridge', ''),
        "cta": result.get('cta', ''),
        "body": result.get('body', ''),
        "signal": signal,
        "template_used": result['template_used'],
        "selection_reason": reason,
        "validation": result.get('validation', {})
    }


def _render_fallback(company: str, first_name: str, role: Optional[str], reason: str) -> Dict:
    """Render fallback template when no valid signals"""
    template = get_fallback_template()
    
    if not template:
        return {
            "subject": "Clarity for fast-moving teams.",
            "opening": f"{first_name} — EchoTray helps teams stay aligned without the noise. We filter the updates that matter so you can focus on execution.",
            "signal": None,
            "template_used": "hardcoded-fallback",
            "selection_reason": reason
        }
    
    context = {
        "first_name": first_name,
        "company": company,
        "role": role or "your team"
    }
    
    return {
        "subject": render_template(template['subject'], context),
        "opening": render_template(template['opening'], context),
        "signal": None,
        "template_used": template['name'],
        "selection_reason": reason
    }


def extract_market(signal: Dict) -> str:
    """Extract market name from signal title/summary"""
    text = f"{signal['title']} {signal.get('summary', '')}".lower()
    
    markets = ['emea', 'apac', 'latam', 'europe', 'asia', 'americas']
    for market in markets:
        if market in text:
            return market.upper()
    
    return "new market"


def extract_product(signal: Dict) -> str:
    """Extract product name from signal title/summary"""
    text = signal['title']
    
    words = text.split()
    for i, word in enumerate(words):
        if word.lower() in ['launches', 'released', 'announces']:
            if i + 1 < len(words):
                return words[i + 1].strip('.,')
    
    return "product"


def validate_output(subject: str, opening: str) -> Dict:
    """
    Validate subject and opening meet quality standards
    
    Returns:
        {
            "valid": bool,
            "errors": list of str
        }
    """
    errors = []
    
    if len(subject) < 36 or len(subject) > 54:
        errors.append(f"Subject length {len(subject)} chars (must be 36-54)")
    
    if len(opening) > 220:
        errors.append(f"Opening length {len(opening)} chars (must be ≤220)")
    
    banned_phrases = [
        "tl;dr",
        "stay ahead of the curve",
        "leaders in tech innovation",
        "transforming",
        "we must embrace",
        "empowers",
        "driving success"
    ]
    
    text_lower = (subject + " " + opening).lower()
    for phrase in banned_phrases:
        if phrase in text_lower:
            errors.append(f"Contains banned phrase: '{phrase}'")
    
    required_keywords = ['clarity', 'focus', 'noise', 'signal', 'aligned', 'priorities']
    has_keyword = any(kw in text_lower for kw in required_keywords)
    if not has_keyword:
        errors.append(f"Missing clarity/focus keywords. Must include one of: {', '.join(required_keywords)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
