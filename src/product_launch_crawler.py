"""
Product Launch Signal Collector
Uses Tavily to search product launch sites for new product/rebrand signals
Detects product launches, feature releases, and company rebrands
"""
import os
from typing import List, Dict
from tavily import TavilyClient
import re
import hashlib
from datetime import datetime


PRODUCT_LAUNCH_SITES = [
    'producthunt.com',
    'techcrunch.com',
    'appsumo.com',
    'betalist.com',
    'medium.com',
    'substack.com',
    'venturebeat.com',
    'theverge.com'
]


def generate_signal_id(domain: str, title: str) -> str:
    """Generate unique signal ID"""
    unique_str = f"{domain}_{title}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:16]


def extract_company_from_launch(title: str, content: str, url: str) -> tuple[str, str]:
    """Extract company name and domain from product launch"""
    # Common patterns:
    # "CompanyName launches new product"
    # "CompanyName announces rebrand"
    # "CompanyName releases feature"
    # "Meet CompanyName: the new way to..."
    
    patterns = [
        r'^([A-Z][A-Za-z0-9\s&.®™]+?)\s+(?:launches?|announces?|releases?|unveils?|introduces?)',
        r'Meet\s+([A-Z][A-Za-z0-9\s&.®™]+?)[:;,]',
        r'([A-Z][A-Za-z0-9\s&.®™]+?)\s+(?:is|has)\s+(?:launching|announcing|releasing)',
        r'^([A-Z][A-Za-z0-9\s&.®™]+?)\s*[-–—]\s*',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            company = match.group(1).strip()
            # Clean up company name
            company = re.sub(r'\s+(Inc|Corp|LLC|Ltd|Limited)\.?$', '', company, flags=re.IGNORECASE)
            
            # Generate domain from company name
            domain = company.lower()
            domain = re.sub(r'[^\w\s]', '', domain)
            domain = domain.replace(' ', '').replace('and', '') + '.com'
            
            return company, domain
    
    # Fallback: try to extract from content
    content_patterns = [
        r'(?:^|\s)([A-Z][A-Za-z0-9]+?)\s+(?:launched|announced|released)',
    ]
    
    for pattern in content_patterns:
        match = re.search(pattern, content)
        if match:
            company = match.group(1).strip()
            domain = company.lower() + '.com'
            return company, domain
    
    # Try URL parsing
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        # ProductHunt pattern: /posts/company-name-product
        if 'producthunt.com' in parsed.netloc:
            path_match = re.search(r'/posts/([a-z0-9-]+)', parsed.path)
            if path_match:
                company_slug = path_match.group(1).split('-')[0]
                company = company_slug.title()
                return company, company_slug + '.com'
    except:
        pass
    
    return 'Unknown Company', 'unknown.com'


def detect_launch_type(title: str, content: str) -> str:
    """Detect type of product launch signal"""
    text = (title + ' ' + content).lower()
    
    # Priority order matters
    if re.search(r'\b(?:rebrand|rebranding|new\s+brand|brand\s+refresh)\b', text):
        return 'rebrand'
    elif re.search(r'\b(?:launched?|launches?|launching)\b', text):
        return 'product'
    elif re.search(r'\b(?:new\s+feature|feature\s+release|update|v\d+\.\d+)\b', text):
        return 'product'
    elif re.search(r'\b(?:announces?|announcing|unveils?|introduces?)\b', text):
        return 'product'
    else:
        return 'product'


def detect_launch_indicators(title: str, content: str) -> List[str]:
    """Detect indicators of significant product activity"""
    text = (title + ' ' + content).lower()
    indicators = []
    
    indicator_patterns = {
        'major_launch': [r'major\s+launch', r'biggest\s+release', r'flagship\s+product'],
        'beta_launch': [r'beta\s+launch', r'early\s+access', r'beta\s+release'],
        'public_launch': [r'public\s+launch', r'general\s+availability', r'now\s+available'],
        'feature_update': [r'new\s+feature', r'feature\s+release', r'update'],
        'rebrand': [r'rebrand', r'new\s+identity', r'brand\s+refresh'],
        'pivot': [r'pivot', r'new\s+direction', r'strategic\s+shift'],
        'integration': [r'integration', r'partners?\s+with', r'connects\s+with'],
    }
    
    for indicator, patterns in indicator_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                indicators.append(indicator)
                break
    
    return indicators


def calculate_launch_magnitude(title: str, content: str, indicators: List[str]) -> int:
    """Calculate magnitude of product launch (0-100)"""
    score = 30  # Base score for any launch
    
    # Major launch keywords
    text = (title + ' ' + content).lower()
    if re.search(r'\b(?:major|biggest|revolutionary|groundbreaking)\b', text):
        score += 30
    
    # Public availability
    if re.search(r'\b(?:now\s+available|public\s+launch|general\s+availability)\b', text):
        score += 20
    
    # Indicator bonuses
    if 'major_launch' in indicators:
        score += 20
    if 'public_launch' in indicators:
        score += 15
    if 'rebrand' in indicators:
        score += 25
    if 'pivot' in indicators:
        score += 20
    
    return min(100, score)


def search_product_launches_tavily(
    keywords: List[str] = None,
    launch_sites: List[str] = None,
    max_results: int = 10
) -> List[Dict]:
    """
    Use Tavily to search product launch sites for new product signals
    
    Args:
        keywords: Search keywords (default: SaaS launches, B2B products)
        launch_sites: Product launch sites to target
        max_results: Max results to return per keyword
    
    Returns:
        List of product launch signal dictionaries
    """
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if not tavily_api_key:
        print("❌ TAVILY_API_KEY not found")
        return []
    
    if keywords is None:
        keywords = [
            'SaaS product launch',
            'B2B software release',
            'collaboration tool launch',
            'productivity app announcement'
        ]
    
    if launch_sites is None:
        launch_sites = PRODUCT_LAUNCH_SITES
    
    signals = []
    client = TavilyClient(api_key=tavily_api_key)
    
    print(f"🚀 Searching product launch sites via Tavily...")
    
    for keyword in keywords:
        # Build query targeting launch sites
        site_filters = ' OR '.join([f'site:{site}' for site in launch_sites[:3]])  # Limit to avoid query length
        query = f'{keyword} ({site_filters})'
        
        try:
            print(f"  Searching: {keyword}")
            
            response = client.search(
                query=query,
                search_depth='basic',
                max_results=max_results,
                include_domains=launch_sites
            )
            
            for result in response.get('results', []):
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                if not title:
                    continue
                
                # Extract company and domain
                company, domain = extract_company_from_launch(title, content, url)
                
                # Detect launch type
                launch_type = detect_launch_type(title, content)
                
                # Detect launch indicators
                indicators = detect_launch_indicators(title, content)
                
                # Calculate magnitude
                magnitude = calculate_launch_magnitude(title, content, indicators)
                
                # Build summary
                summary = content[:400] if content else ''
                if indicators:
                    summary += f"\n\nLaunch indicators: {', '.join(indicators)}"
                
                # Generate product launch signal
                signal = {
                    'id': generate_signal_id(domain, title),
                    'domain': domain,
                    'company': company,
                    'type': launch_type,
                    'title': title,
                    'summary': summary[:500],
                    'url': url,
                    'published_at': datetime.now().isoformat(),
                    'magnitude': magnitude,
                    'relevance': 0.70,  # Product launches are relevant for ICP
                    'source': f'Tavily - {url.split("/")[2] if len(url.split("/")) > 2 else "product launch sites"}',
                    'metadata': {
                        'launch_indicators': indicators,
                        'launch_type': launch_type
                    }
                }
                
                signals.append(signal)
        
        except Exception as e:
            print(f"  ❌ Error searching '{keyword}': {e}")
            continue
    
    # Deduplicate by signal ID
    unique_signals = {}
    for signal in signals:
        unique_signals[signal['id']] = signal
    
    signals = list(unique_signals.values())
    
    print(f"✅ Found {len(signals)} unique product launch signals")
    
    # Show launch type distribution
    if signals:
        type_counts = {}
        for signal in signals:
            signal_type = signal.get('type', 'product')
            type_counts[signal_type] = type_counts.get(signal_type, 0) + 1
        
        print(f"\nLaunch type distribution:")
        for launch_type, count in type_counts.items():
            print(f"  {launch_type}: {count}")
    
    return signals


if __name__ == '__main__':
    # Test product launch crawler
    print("Testing Product Launch Signal Collector\n")
    
    signals = search_product_launches_tavily(
        keywords=['SaaS product launch', 'B2B software announcement'],
        max_results=5
    )
    
    if signals:
        print(f"\nSample product launch signals:")
        for signal in signals[:3]:
            metadata = signal.get('metadata', {})
            print(f"\n  Company: {signal['company']}")
            print(f"  Domain: {signal['domain']}")
            print(f"  Title: {signal['title'][:80]}...")
            print(f"  Type: {signal['type']}")
            print(f"  Indicators: {', '.join(metadata.get('launch_indicators', [])) or 'None'}")
            print(f"  Magnitude: {signal['magnitude']}")
            print(f"  Source: {signal['source']}")
