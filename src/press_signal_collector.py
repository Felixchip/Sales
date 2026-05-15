"""
Hybrid Press Release Signal Collection
Uses Tavily to search press release sites specifically for targeted signal collection
Works alongside general Tavily search to maximize coverage
"""
import os
from typing import List, Dict
from tavily import TavilyClient
from src.signal_crawler import classify_signal_type, extract_magnitude, calculate_relevance
import hashlib
from datetime import datetime


def generate_signal_id(domain: str, title: str) -> str:
    """Generate unique signal ID"""
    unique_str = f"{domain}_{title}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:16]


def extract_company_and_domain(title: str, url: str) -> tuple[str, str]:
    """Extract company name and domain from press release"""
    import re
    from urllib.parse import urlparse
    
    # Try to extract company from title
    # Pattern: "CompanyName Announces/Launches/Raises..."
    patterns = [
        r'^([A-Z][A-Za-z0-9\s&.®™]+?)\s+(Announces|Launches|Raises|Expands|Appoints|Hires|Partners)',
        r'^([A-Z][A-Za-z0-9\s&.®™]+?):\s+',
        r'^([A-Z][A-Za-z0-9\s&.®™]+?)\s+-\s+'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            company = match.group(1).strip()
            # Clean up company name
            company = re.sub(r'\s+(Inc|Corp|LLC|Ltd|Limited)\.?$', '', company, flags=re.IGNORECASE)
            
            # Generate domain from company name
            domain = company.lower()
            domain = re.sub(r'[^\w\s]', '', domain)  # Remove special chars
            domain = domain.replace(' ', '').replace('and', '') + '.com'
            
            return company, domain
    
    # Fallback: try to extract from URL
    try:
        parsed = urlparse(url)
        # Look for domain mentions in URL path
        path_match = re.search(r'/([a-z0-9-]+)(?:/|$)', parsed.path)
        if path_match:
            company = path_match.group(1).replace('-', ' ').title()
            return company, path_match.group(1) + '.com'
    except:
        pass
    
    return 'Unknown Company', 'unknown.com'


def search_press_releases_tavily(
    keywords: List[str] = None,
    press_sites: List[str] = None,
    max_results: int = 10
) -> List[Dict]:
    """
    Use Tavily to search press release sites for company signals
    
    Args:
        keywords: Search keywords (default: funding, product launch, expansion, etc.)
        press_sites: Press release sites to target (default: PR Newswire, GlobeNewswire, etc.)
        max_results: Max results to return
    
    Returns:
        List of signal dictionaries
    """
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if not tavily_api_key:
        print("❌ TAVILY_API_KEY not found")
        return []
    
    if keywords is None:
        keywords = [
            'funding', 'Series A', 'Series B', 'raises capital',
            'expands to', 'opens new office', 'enters market', 'geographic expansion',
            'partnership', 'product launch', 'acquisition'
        ]
    
    if press_sites is None:
        press_sites = [
            'prnewswire.com',
            'globenewswire.com',
            'businesswire.com',
            'crunchbase.com',
            'news.crunchbase.com',
            'sifted.eu',
            'techcabal.com',
            'theinformation.com',
            'venturebeat.com',
            'techcrunch.com'
        ]
    
    signals = []
    client = TavilyClient(api_key=tavily_api_key)
    
    print(f"🔍 Searching press release sites via Tavily...")
    
    for keyword in keywords:
        # Build query targeting press release sites
        site_filters = ' OR '.join([f'site:{site}' for site in press_sites])
        query = f'{keyword} technology startups SaaS ({site_filters})'
        
        try:
            print(f"  Searching: {keyword}")
            
            response = client.search(
                query=query,
                search_depth='basic',
                max_results=max_results,
                include_domains=press_sites
            )
            
            for result in response.get('results', []):
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                if not title:
                    continue
                
                # Extract company and domain
                company, domain = extract_company_and_domain(title, url)
                
                # Classify signal type
                signal_type = classify_signal_type(title, content)
                
                # Calculate magnitude
                magnitude = extract_magnitude(title, content, signal_type)
                
                # Calculate relevance
                relevance = calculate_relevance(title, content)
                
                # Generate signal
                signal = {
                    'id': generate_signal_id(domain, title),
                    'domain': domain,
                    'company': company,
                    'type': signal_type,
                    'title': title,
                    'summary': content[:500] if content else '',
                    'url': url,
                    'published_at': datetime.now().isoformat(),  # Tavily doesn't always provide dates
                    'magnitude': magnitude,
                    'relevance': relevance,
                    'source': f'Tavily - {url.split("/")[2]}'  # e.g., "Tavily - prnewswire.com"
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
    
    print(f"✅ Found {len(signals)} unique press release signals")
    
    # Show distribution by type
    type_counts = {}
    for signal in signals:
        t = signal['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    if type_counts:
        print(f"\nSignal type distribution:")
        for signal_type, count in sorted(type_counts.items()):
            print(f"  {signal_type}: {count}")
    
    return signals


def collect_hybrid_signals(
    company_query: str = None,
    include_press_sites: bool = True,
    include_general_web: bool = True,
    max_results_per_source: int = 10
) -> List[Dict]:
    """
    Hybrid signal collection combining press release sites and general web search
    
    Args:
        company_query: Specific company to search for (optional)
        include_press_sites: Search press release sites via Tavily
        include_general_web: General Tavily web search
        max_results_per_source: Max results per search type
    
    Returns:
        Combined list of signals from both sources
    """
    all_signals = []
    
    # 1. Search press release sites (if enabled)
    if include_press_sites:
        keywords = []
        if company_query:
            keywords = [f'{company_query} funding', f'{company_query} product launch', f'{company_query} expansion']
        else:
            keywords = ['SaaS funding round', 'B2B product launch', 'startup Series A', 'team collaboration tool']
        
        press_signals = search_press_releases_tavily(
            keywords=keywords,
            max_results=max_results_per_source
        )
        all_signals.extend(press_signals)
        print(f"  📰 Press sites: {len(press_signals)} signals")
    
    # 2. General web search via Tavily (if enabled)
    if include_general_web and company_query:
        from src.signal_crawler import search_company_signals
        general_signals = search_company_signals(company_query, max_results=max_results_per_source)
        all_signals.extend(general_signals)
        print(f"  🌐 General web: {len(general_signals)} signals")
    
    # Deduplicate
    unique_signals = {}
    for signal in all_signals:
        unique_signals[signal['id']] = signal
    
    final_signals = list(unique_signals.values())
    
    print(f"\n✅ Total unique signals: {len(final_signals)}")
    return final_signals


if __name__ == '__main__':
    # Test hybrid signal collection
    print("Testing Hybrid Press Release Signal Collection\n")
    
    signals = search_press_releases_tavily(
        keywords=['SaaS funding', 'B2B product launch'],
        max_results=5
    )
    
    if signals:
        print(f"\nSample signals:")
        for signal in signals[:3]:
            print(f"\n  Company: {signal['company']}")
            print(f"  Domain: {signal['domain']}")
            print(f"  Type: {signal['type']}")
            print(f"  Title: {signal['title'][:80]}...")
            print(f"  Source: {signal['source']}")
