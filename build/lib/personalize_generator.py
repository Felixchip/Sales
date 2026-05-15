"""
Dynamic personalization generator using actual signal data
Creates truly personalized subjects and openings (not template-based)
Now generates full 5-section emails: Subject + Opening + Insight + Bridge + CTA
"""
import re
from typing import Dict, Optional
from src.email_templates import build_full_email, validate_email_structure


def extract_amount_from_signal(signal: Dict) -> Optional[str]:
    """Extract funding amount from signal (e.g., '$17B', '$450M')"""
    if signal['type'] != 'funding':
        return None
    
    magnitude = signal.get('magnitude', 0)
    if magnitude >= 1000:
        return f"${magnitude/1000:.0f}B"
    elif magnitude > 0:
        return f"${magnitude}M"
    return None


def extract_company_short_name(company: str) -> str:
    """Get short company name (e.g., 'Deel' from 'Deel.Com')"""
    return company.split('.')[0].split('-')[0].title()


def generate_funding_personalization(signal: Dict, company: str, first_name: str) -> Dict:
    """Generate personalized subject/opening for funding signals"""
    amount = extract_amount_from_signal(signal)
    short_name = extract_company_short_name(company)
    
    if amount:
        if float(amount.replace('$', '').replace('B', '').replace('M', '')) >= 100:
            # Large funding
            subject = f"{short_name}'s next challenge after {amount}: staying clear while scaling."
        else:
            # Moderate funding
            subject = f"{short_name} raised {amount}. Now comes the hard part: keeping everyone aligned."
    else:
        subject = f"{short_name}'s scaling. Clarity shouldn't be the trade-off."
    
    opening = f"{first_name}, congratulations on the funding. Growth at that pace tends to make everything louder. Updates, meetings, and threads start multiplying overnight. We've been thinking a lot about how clarity scales with speed."
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-funding"
    }


def generate_hiring_personalization(signal: Dict, company: str, first_name: str) -> Dict:
    """Generate personalized subject/opening for hiring signals"""
    count = signal.get('magnitude', 0)
    short_name = extract_company_short_name(company)
    
    if count >= 50:
        subject = f"{short_name} added {count}+ people. Here's how to keep the signal high."
    elif count >= 20:
        subject = f"Growing fast at {short_name}? Clarity doesn't have to suffer."
    else:
        subject = f"{short_name}'s hiring. Keep your team aligned as you scale."
    
    opening = f"{first_name}, saw that {short_name} is expanding the team. That's the phase where update volume spikes and focus gets harder to maintain. We've helped teams at this stage filter the noise so execution stays sharp."
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-hiring"
    }


def generate_product_personalization(signal: Dict, company: str, first_name: str) -> Dict:
    """Generate personalized subject/opening for product launch signals"""
    short_name = extract_company_short_name(company)
    title = signal.get('title', '')
    
    # Try to extract product name from title
    product_match = re.search(r'launches?\s+([A-Z][a-zA-Z\s]+)', title, re.IGNORECASE)
    product_name = product_match.group(1).strip() if product_match else "new feature"
    
    subject = f"Post-launch at {short_name}: keeping teams aligned, not just informed."
    
    opening = f"{first_name}, nice work on the launch. The phase after shipping is where communication gets messy—Slack blows up, updates multiply, and clarity drops. We help teams cut through that so the right people see the right signals."
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-product"
    }


def generate_market_personalization(signal: Dict, company: str, first_name: str) -> Dict:
    """Generate personalized subject/opening for market expansion signals"""
    short_name = extract_company_short_name(company)
    
    subject = f"{short_name}'s expanding. Here's how to stay aligned across markets."
    
    opening = f"{first_name}, congrats on the expansion. Cross-market, cross-timezone work creates update overload fast. We've been working on how distributed teams maintain clarity without drowning in sync-ups."
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-market"
    }


def generate_leadership_personalization(signal: Dict, company: str, first_name: str) -> Dict:
    """Generate personalized subject/opening for leadership change signals"""
    short_name = extract_company_short_name(company)
    
    subject = f"New leadership at {short_name}. Time to realign priorities, not just communicate them."
    
    opening = f"{first_name}, saw the leadership update. Transitions like this create alignment challenges—everyone's waiting to see what matters now. We help teams cut through that uncertainty with clear, prioritized signals."
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-leadership"
    }


def generate_dynamic_personalization(signal: Dict, company: str, first_name: str, full_email: bool = True) -> Dict:
    """
    Generate truly personalized email using actual signal data
    
    Args:
        signal: Signal dict with type, magnitude, title, etc.
        company: Company name
        first_name: Recipient first name
        full_email: If True, generate complete 5-section email. If False, just subject/opening
    
    Returns:
        Full email dict with:
        - subject: str (36-54 chars)
        - opening: str
        - insight: str (from template)
        - bridge: str (static)
        - cta: str (static)
        - body: str (complete email body)
        - template_used: str
        - validation: dict with errors/warnings
    """
    signal_type = signal.get('type', 'press')
    
    generators = {
        'funding': generate_funding_personalization,
        'hiring': generate_hiring_personalization,
        'product': generate_product_personalization,
        'market': generate_market_personalization,
        'leadership': generate_leadership_personalization
    }
    
    generator = generators.get(signal_type)
    
    if generator:
        result = generator(signal, company, first_name)
        
        # Ensure subject is within 36-54 chars
        if len(result['subject']) > 54:
            result['subject'] = result['subject'][:51] + '...'
        elif len(result['subject']) < 36:
            result['subject'] = result['subject'] + " Time to adapt."
        
        # Build full email if requested
        if full_email:
            full_email_data = build_full_email(
                subject=result['subject'],
                opening=result['opening'],
                signal_type=signal_type,
                cta_option=0
            )
            
            # Add template info
            full_email_data['template_used'] = result['template_used']
            
            # Validate
            full_email_data['validation'] = validate_email_structure(full_email_data)
            
            return full_email_data
        
        return result
    
    # Fallback for unknown signal types
    short_name = extract_company_short_name(company)
    subject = f"{short_name}'s moving fast. Keep clarity high."
    opening = f"{first_name}, noticed the recent updates from {short_name}. Fast-moving teams tend to drown in notifications. We're building tools to filter that noise into clear, actionable priorities."
    
    if full_email:
        full_email_data = build_full_email(
            subject=subject,
            opening=opening,
            signal_type='press',
            cta_option=0
        )
        full_email_data['template_used'] = 'dynamic-fallback'
        full_email_data['validation'] = validate_email_structure(full_email_data)
        return full_email_data
    
    return {
        "subject": subject,
        "opening": opening,
        "template_used": "dynamic-fallback"
    }
