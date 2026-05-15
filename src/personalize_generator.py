import openai
import json
import os
from typing import Dict, Optional
from src.email_templates import build_full_email, validate_email_structure

# LLM Config
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def extract_amount_from_signal(signal: Dict) -> Optional[str]:
    """Extract funding amount from signal (e.g., '$17B', '$450M')"""
    if signal.get('type') != 'funding':
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


def llm_generate_personalization(signal: Dict, product: Dict, first_name: str) -> Dict:
    """Use LLM to generate personalization based on product context"""
    
    company = signal.get('company', 'their company')
    short_name = extract_company_short_name(company)
    
    prompt = f"""
    You are an expert sales copywriter. Generate a personalized email subject line and opening line for a prospect.
    
    PRODUCT CONTEXT:
    - Product Name: {product.get('name')}
    - Description: {product.get('description')}
    - Value Proposition: {product.get('value_prop')}
    
    PROSPECT CONTEXT:
    - First Name: {first_name}
    - Company: {company}
    
    SIGNAL DETECTED:
    - Type: {signal.get('type')}
    - Title: {signal.get('title')}
    - Summary: {signal.get('summary')}
    
    REQUIREMENTS:
    1. Subject Line: Must be 36-54 characters, conversational, and tie the signal to the product's value.
    2. Opening Line: Must be 2-3 sentences, congratulate/acknowledge the signal naturally, and bridge to the product's value prop.
    3. Tone: Professional but conversational, 8th-grade reading level.
    4. NO BANNED WORDS: "TL;DR", "stay ahead of the curve", "transforming", "empowers".
    
    Return strict JSON:
    {{
        "subject": "...",
        "opening": "..."
    }}
    """
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        res = json.loads(response.choices[0].message.content)
        return {
            "subject": res.get('subject', f"Quick thought on {short_name}"),
            "opening": res.get('opening', f"Hi {first_name}, I saw the news about {short_name}..."),
            "template_used": "llm-dynamic"
        }
    except Exception as e:
        print(f"LLM generation failed: {e}")
        # Fallback to a very generic one
        return {
            "subject": f"Question regarding {short_name}'s {signal.get('type')}",
            "opening": f"{first_name}, I saw the recent {signal.get('type')} update regarding {short_name}. It's an interesting phase for the team.",
            "template_used": "llm-fallback"
        }


def generate_dynamic_personalization(signal: Dict, company: str, first_name: str, product: Optional[Dict] = None, full_email: bool = True) -> Dict:
    """
    Generate truly personalized email using actual signal data and product context
    """
    # Use EchoTray default if no product provided
    if not product:
        product = {
            "name": "EchoTray",
            "description": "A tool for clear handoffs, fast catch-ups, and tight recaps.",
            "value_prop": "Helping teams maintain clarity and alignment as they scale."
        }

    # Generate personalization
    result = llm_generate_personalization(signal, product, first_name)
    
    # Ensure subject length constraints
    if len(result['subject']) > 54:
        result['subject'] = result['subject'][:51] + '...'
    elif len(result['subject']) < 30:
        result['subject'] = result['subject'] + f" - {product.get('name')}"

    # Build full email if requested
    if full_email:
        full_email_data = build_full_email(
            subject=result['subject'],
            opening=result['opening'],
            signal_type=signal.get('type', 'press'),
            cta_option=0
        )
        
        # Add template info
        full_email_data['template_used'] = result['template_used']
        
        # Validate
        full_email_data['validation'] = validate_email_structure(full_email_data)
        
        return full_email_data
    
    return result
