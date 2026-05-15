"""
Job Board Signal Collector
Uses Tavily to search job board sites for hiring signals
Detects team growth, scale-up signals, and hiring momentum
"""
import os
from typing import List, Dict
from tavily import TavilyClient
import re
import hashlib
from datetime import datetime


JOB_BOARD_SITES = [
    'wellfound.com',  # AngelList
    'greenhouse.io',
    'lever.co',
    'workable.com',
    'weworkremotely.com',
    'remoteok.com',
    'ycombinator.com/jobs',
    'builtin.com',
    'otta.com'
]


def generate_signal_id(domain: str, title: str) -> str:
    """Generate unique signal ID"""
    unique_str = f"{domain}_{title}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:16]


def extract_company_from_job_title(title: str, url: str) -> tuple[str, str]:
    """Extract company name and domain from job posting"""
    # Common patterns:
    # "Senior Engineer at CompanyName"
    # "CompanyName is hiring Software Engineer"
    # "Join CompanyName as Product Manager"
    
    patterns = [
        r'at\s+([A-Z][A-Za-z0-9\s&.®™]+?)(?:\s*-\s*|\s*\||$)',
        r'([A-Z][A-Za-z0-9\s&.®™]+?)\s+is\s+hiring',
        r'Join\s+([A-Z][A-Za-z0-9\s&.®™]+?)\s+as',
        r'^([A-Z][A-Za-z0-9\s&.®™]+?)\s*-\s*',
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
    
    # Fallback: try to extract from URL
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        # Extract company from path or subdomain
        path_match = re.search(r'/companies/([a-z0-9-]+)', parsed.path, re.IGNORECASE)
        if path_match:
            company_slug = path_match.group(1)
            company = company_slug.replace('-', ' ').title()
            return company, company_slug + '.com'
    except:
        pass
    
    return 'Unknown Company', 'unknown.com'


def extract_job_count(title: str, content: str) -> int:
    """Extract number of job openings mentioned"""
    text = title + ' ' + content
    
    # Patterns for job count
    patterns = [
        r'(\d+)\s*(?:\+)?\s*(?:open\s+)?(?:positions?|jobs?|openings?|roles?)',
        r'hiring\s+(\d+)',
        r'(\d+)\s*new\s+(?:hires?|positions?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # Default: single job posting
    return 1


def detect_scale_indicators(title: str, content: str) -> List[str]:
    """Detect indicators of company scaling"""
    text = (title + ' ' + content).lower()
    indicators = []
    
    scale_patterns = {
        'rapid_growth': [r'rapid\s+growth', r'fast\s+growing', r'scaling\s+quickly'],
        'team_expansion': [r'expanding\s+team', r'growing\s+team', r'team\s+growth'],
        'new_department': [r'new\s+department', r'building\s+team', r'forming\s+team'],
        'high_volume': [r'\d+\s*\+?\s*openings?', r'multiple\s+positions?'],
        'remote_first': [r'remote[- ]first', r'fully\s+remote', r'distributed\s+team'],
    }
    
    for indicator, patterns in scale_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                indicators.append(indicator)
                break
    
    return indicators


def search_job_boards_tavily(
    keywords: List[str] = None,
    job_boards: List[str] = None,
    max_results: int = 10
) -> List[Dict]:
    """
    Use Tavily to search job board sites for hiring signals
    
    Args:
        keywords: Search keywords (default: SaaS, B2B, remote, hiring)
        job_boards: Job board sites to target
        max_results: Max results to return per keyword
    
    Returns:
        List of hiring signal dictionaries
    """
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if not tavily_api_key:
        print("❌ TAVILY_API_KEY not found")
        return []
    
    if keywords is None:
        keywords = [
            'SaaS hiring engineers',
            'B2B startup remote jobs',
            'collaboration tool hiring',
            'productivity software jobs'
        ]
    
    if job_boards is None:
        job_boards = JOB_BOARD_SITES
    
    signals = []
    client = TavilyClient(api_key=tavily_api_key)
    
    print(f"🔍 Searching job boards via Tavily...")
    
    for keyword in keywords:
        # Build query targeting job board sites
        site_filters = ' OR '.join([f'site:{site}' for site in job_boards[:3]])  # Limit to avoid query length
        query = f'{keyword} ({site_filters})'
        
        try:
            print(f"  Searching: {keyword}")
            
            response = client.search(
                query=query,
                search_depth='basic',
                max_results=max_results,
                include_domains=job_boards
            )
            
            for result in response.get('results', []):
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                if not title:
                    continue
                
                # Extract company and domain
                company, domain = extract_company_from_job_title(title, url)
                
                # Extract job count
                job_count = extract_job_count(title, content)
                
                # Detect scale indicators
                scale_indicators = detect_scale_indicators(title, content)
                
                # Calculate magnitude based on job count and indicators
                magnitude = min(100, job_count * 5 + len(scale_indicators) * 10)
                
                # Build summary
                summary = content[:400] if content else ''
                if scale_indicators:
                    summary += f"\n\nScale indicators: {', '.join(scale_indicators)}"
                if job_count > 1:
                    summary += f"\n\nJob openings: {job_count}"
                
                # Generate hiring signal
                signal = {
                    'id': generate_signal_id(domain, title),
                    'domain': domain,
                    'company': company,
                    'type': 'hiring',
                    'title': title,
                    'summary': summary[:500],
                    'url': url,
                    'published_at': datetime.now().isoformat(),
                    'magnitude': magnitude,
                    'relevance': 0.75,  # Hiring signals are highly relevant for ICP
                    'source': f'Tavily - {url.split("/")[2] if len(url.split("/")) > 2 else "job boards"}',
                    'metadata': {
                        'job_count': job_count,
                        'scale_indicators': scale_indicators
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
    
    print(f"✅ Found {len(signals)} unique hiring signals")
    
    # Show job count distribution
    if signals:
        total_jobs = sum(s.get('metadata', {}).get('job_count', 1) for s in signals)
        avg_jobs = total_jobs / len(signals) if signals else 0
        print(f"\nHiring metrics:")
        print(f"  Total job openings: {total_jobs}")
        print(f"  Average per company: {avg_jobs:.1f}")
        print(f"  Companies with scale indicators: {sum(1 for s in signals if s.get('metadata', {}).get('scale_indicators'))}")
    
    return signals


if __name__ == '__main__':
    # Test job board crawler
    print("Testing Job Board Signal Collector\n")
    
    signals = search_job_boards_tavily(
        keywords=['SaaS remote hiring', 'B2B startup jobs'],
        max_results=5
    )
    
    if signals:
        print(f"\nSample hiring signals:")
        for signal in signals[:3]:
            metadata = signal.get('metadata', {})
            print(f"\n  Company: {signal['company']}")
            print(f"  Domain: {signal['domain']}")
            print(f"  Title: {signal['title'][:80]}...")
            print(f"  Job openings: {metadata.get('job_count', 1)}")
            print(f"  Scale indicators: {', '.join(metadata.get('scale_indicators', [])) or 'None'}")
            print(f"  Magnitude: {signal['magnitude']}")
            print(f"  Source: {signal['source']}")
