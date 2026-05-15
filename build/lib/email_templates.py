"""
Full Email Templates for EchoTray Personalization
Based on the 5-section structure: Subject + Opening + Insight + Bridge + CTA
"""
from typing import Dict, Optional


# Insight templates by signal type
INSIGHT_TEMPLATES = {
    'funding': """When teams grow fast, priorities start to blur across Slack and email. People spend their mornings catching up instead of moving forward. That loss of focus compounds at scale.""",
    
    'hiring': """Adding new people is exciting, but alignment tends to slip. Each new hire multiplies communication paths, and clarity becomes harder to maintain without deliberate structure.""",
    
    'product': """After releases, communication volume spikes and clarity drops. Teams start firefighting updates instead of maintaining focus. The noise-to-signal ratio shifts fast.""",
    
    'market': """Operating across time zones makes staying in sync harder. Updates scatter, priorities blur, and teams end up spending more time aligning than executing.""",
    
    'leadership': """New leadership often resets direction, and clarity becomes fragile. Teams need to stay aligned through transitions without losing momentum or focus.""",
    
    'press': """When visibility increases, so does internal noise. Teams end up managing more updates, more threads, and more context switches. Focus gets harder to protect."""
}


# EchoTray Bridge - Static core
BRIDGE_TEMPLATE = """EchoTray helps growing teams stay clear by surfacing only the 10% of updates that matter. It keeps everyone aligned across Slack, email, and project tools without adding another platform to manage."""


# CTA options
CTA_OPTIONS = [
    "Would you be open to a short look at how scaling teams keep alignment steady while they grow?",
    "Worth a quick look next week?",
    "Open to seeing how we're helping teams stay focused after big transitions?"
]


def get_insight_for_signal_type(signal_type: str) -> str:
    """Get insight paragraph based on signal type"""
    # Map variations to core types
    type_mapping = {
        'funding': 'funding',
        'hiring': 'hiring',
        'product': 'product',
        'market': 'market',
        'leadership': 'leadership',
        'press': 'press',
        'expansion': 'market',
        'launch': 'product'
    }
    
    mapped_type = type_mapping.get(signal_type.lower(), 'press')
    return INSIGHT_TEMPLATES[mapped_type]


def get_bridge() -> str:
    """Get EchoTray bridge paragraph (static)"""
    return BRIDGE_TEMPLATE


def get_cta(option: int = 0) -> str:
    """Get CTA (Call to Action)"""
    return CTA_OPTIONS[option % len(CTA_OPTIONS)]


def build_full_email(
    subject: str,
    opening: str,
    signal_type: str,
    cta_option: int = 0
) -> Dict[str, str]:
    """
    Build complete email with all 5 sections
    
    Args:
        subject: Dynamic subject line (from signal)
        opening: Dynamic opening paragraph (from signal)
        signal_type: Signal type to determine insight template
        cta_option: Which CTA variation to use (0-2)
    
    Returns:
        Dict with all email components
    """
    insight = get_insight_for_signal_type(signal_type)
    bridge = get_bridge()
    cta = get_cta(cta_option)
    
    # Combine into full body
    body = f"{opening}\n\n{insight}\n\n{bridge}\n\n{cta}"
    
    return {
        'subject': subject,
        'opening': opening,
        'insight': insight,
        'bridge': bridge,
        'cta': cta,
        'body': body,
        'signal_type': signal_type
    }


def validate_email_structure(email: Dict) -> Dict[str, any]:
    """Validate email components meet quality standards"""
    errors = []
    warnings = []
    
    # Subject validation
    subject = email.get('subject', '')
    if len(subject) < 36:
        errors.append("Subject too short (min 36 chars)")
    elif len(subject) > 54:
        errors.append("Subject too long (max 54 chars)")
    
    # Opening validation
    opening = email.get('opening', '')
    if len(opening) > 220:
        errors.append("Opening too long (max 220 chars)")
    if '?' in opening:
        warnings.append("Opening contains question mark (avoid)")
    if ' if ' in opening.lower() or ' did ' in opening.lower() or ' maybe ' in opening.lower():
        warnings.append("Opening uses speculative phrasing")
    
    # Body validation
    body = email.get('body', '')
    if len(body) < 200:
        errors.append("Email body too short")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'char_counts': {
            'subject': len(subject),
            'opening': len(opening),
            'body': len(body)
        }
    }
