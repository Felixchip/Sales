"""
Dynamic Email Templates for Multi-Product Personalization
Based on the 5-section structure: Subject + Opening + Insight + Bridge + CTA
"""
from typing import Dict, Optional


def get_insight_for_signal_type(signal_type: str, product: Optional[Dict] = None) -> str:
    """Get insight paragraph based on signal type and product context"""
    # Default EchoTray Insights
    DEFAULT_INSIGHTS = {
        'funding': """When teams grow fast, priorities start to blur across Slack and email. People spend their mornings catching up instead of moving forward. That loss of focus compounds at scale.""",
        'hiring': """Adding new people is exciting, but alignment tends to slip. Each new hire multiplies communication paths, and clarity becomes harder to maintain without deliberate structure.""",
        'product': """After releases, communication volume spikes and clarity drops. Teams start firefighting updates instead of maintaining focus. The noise-to-signal ratio shifts fast.""",
        'market': """Operating across time zones makes staying in sync harder. Updates scatter, priorities blur, and teams end up spending more time aligning than executing.""",
        'leadership': """New leadership often resets direction, and clarity becomes fragile. Teams need to stay aligned through transitions without losing momentum or focus.""",
        'press': """When visibility increases, so does internal noise. Teams end up managing more updates, more threads, and more context switches. Focus gets harder to protect."""
    }
    
    # Use product-specific insights if available in product['icp_config']['insights']
    insights = DEFAULT_INSIGHTS
    if product and 'icp_config' in product:
        if isinstance(product['icp_config'], dict) and 'insights' in product['icp_config']:
            insights = product['icp_config']['insights']
    
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
    return insights.get(mapped_type, insights.get('press', ''))


def get_bridge(product: Optional[Dict] = None) -> str:
    """Get product bridge paragraph"""
    if product and product.get('value_prop'):
        return product.get('value_prop')
    
    return """EchoTray helps growing teams stay clear by surfacing only the 10% of updates that matter. It keeps everyone aligned across Slack, email, and project tools without adding another platform to manage."""


def get_cta(option: int = 0, product: Optional[Dict] = None) -> str:
    """Get product-specific CTA"""
    DEFAULT_CTAS = [
        "Would you be open to a short look at how scaling teams keep alignment steady while they grow?",
        "Worth a quick look next week?",
        "Open to seeing how we're helping teams stay focused after big transitions?"
    ]
    
    ctas = DEFAULT_CTAS
    if product and 'icp_config' in product:
        if isinstance(product['icp_config'], dict) and 'ctas' in product['icp_config']:
            ctas = product['icp_config']['ctas']
            
    return ctas[option % len(ctas)]


def build_full_email(
    subject: str,
    opening: str,
    signal_type: str,
    product: Optional[Dict] = None,
    cta_option: int = 0
) -> Dict[str, str]:
    """
    Build complete email with all 5 sections using product context
    """
    insight = get_insight_for_signal_type(signal_type, product)
    bridge = get_bridge(product)
    cta = get_cta(cta_option, product)
    
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
    if len(subject) < 30:
        errors.append("Subject too short (min 30 chars)")
    elif len(subject) > 60:
        errors.append("Subject too long (max 60 chars)")
    
    # Opening validation
    opening = email.get('opening', '')
    if len(opening) > 250:
        errors.append("Opening too long (max 250 chars)")
    
    # Body validation
    body = email.get('body', '')
    if len(body) < 150:
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
