import re
from typing import Dict, Optional
from src.personalize_db import (
    get_top_signals, 
    get_template_for_signal, 
    get_fallback_template, 
    get_product, 
    get_signal_by_id, 
    get_pinned_signal, 
    get_exclusions
)


def render_template(template_text: str, context: Dict) -> str:
    """
    Render template with context variables
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
    product_id: str = 'echotray',
    role: Optional[str] = None,
    pinned_signal_id: Optional[str] = None
) -> Dict:
    """
    Generate personalized subject and opening based on top signal for a specific product
    """
    product = get_product(product_id)
    if not product:
        # Fallback to default EchoTray if product_id is invalid
        product = get_product('echotray')
    
    if not pinned_signal_id:
        pinned_signal_id = get_pinned_signal(domain, product_id)
    
    if pinned_signal_id:
        pinned = get_signal_by_id(pinned_signal_id)
        if pinned:
            return _render_with_signal(pinned, company, first_name, product, role, reason="manual_pin")
    
    signals = get_top_signals(domain, product_id, limit=10, max_age_days=45)
    
    exclusions = get_exclusions(domain, product_id)
    excluded_ids = {e['signal_id'] for e in exclusions if e.get('signal_id')}
    excluded_types = {e['signal_type'] for e in exclusions if e.get('signal_type')}
    
    # Use product-specific ICP threshold if defined, else fallback to 70
    threshold = product.get('icp_config', {}).get('threshold', 70) if product else 70
    
    valid_signals = [
        s for s in signals 
        if s['score'] >= threshold 
        and s.get('recency_days', 999) <= 45
        and s['id'] not in excluded_ids
        and s['type'] not in excluded_types
    ]
    
    if not valid_signals:
        reason = f"no_valid_signals (threshold: score≥{threshold}, age≤45d, {len(exclusions)} exclusions)"
        return _render_fallback(company, first_name, product, role, reason)
    
    top_signal = valid_signals[0]
    reason = f"auto_selected (score: {top_signal['score']}, age: {top_signal.get('recency_days', 0)}d, rank: 1/{len(valid_signals)})"
    return _render_with_signal(top_signal, company, first_name, product, role, reason)


def _render_with_signal(signal: Dict, company: str, first_name: str, product: Dict, role: Optional[str], reason: str) -> Dict:
    """Render personalization using a specific signal and product context"""
    from src.personalize_generator import generate_dynamic_personalization
    
    # Generate complete 5-section email
    result = generate_dynamic_personalization(signal, company, first_name, product=product, full_email=True)
    
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


def _render_fallback(company: str, first_name: str, product: Dict, role: Optional[str], reason: str) -> Dict:
    """Render fallback template when no valid signals"""
    product_id = product.get('id', 'echotray')
    template = get_fallback_template(product_id)
    
    if not template:
        return {
            "subject": f"Thought on {company}",
            "opening": f"{first_name} — I was reading about {company}'s recent growth. {product.get('value_prop', 'We help teams scale efficiently.')}",
            "signal": None,
            "template_used": "dynamic-fallback",
            "selection_reason": reason
        }
    
    context = {
        "first_name": first_name,
        "company": company,
        "role": role or "your team",
        "product_name": product.get('name'),
        "value_prop": product.get('value_prop')
    }
    
    return {
        "subject": render_template(template['subject'], context),
        "opening": render_template(template['opening'], context),
        "signal": None,
        "template_used": template['name'],
        "selection_reason": reason
    }


def validate_output(subject: str, opening: str, product: Optional[Dict] = None) -> Dict:
    """
    Validate subject and opening meet quality standards
    """
    errors = []
    
    if len(subject) < 30 or len(subject) > 60:
        errors.append(f"Subject length {len(subject)} chars (must be 30-60)")
    
    if len(opening) > 250:
        errors.append(f"Opening length {len(opening)} chars (must be ≤250)")
    
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
    
    # Product specific keywords
    if product:
        # If product has custom validation keywords, use them
        required_keywords = product.get('icp_config', {}).get('validation_keywords', [])
        if required_keywords:
            has_keyword = any(kw.lower() in text_lower for kw in required_keywords)
            if not has_keyword:
                errors.append(f"Missing required keywords. Must include one of: {', '.join(required_keywords)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
