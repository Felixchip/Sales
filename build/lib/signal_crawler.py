"""
Signal processing and classification
Processes web search results into structured signals
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
from src.icp_scoring import calculate_icp_fit_score, score_prospect_company


SIGNAL_PATTERNS = {
    'funding': [
        r'raises?\s+\$?(\d+(?:\.\d+)?)\s*([MBmb])',
        r'funding\s+round',
        r'Series\s+[A-Z]',
        r'valuation'
    ],
    'hiring': [
        r'hiring\s+(\d+)',
        r'expands?\s+team',
        r'job\s+openings',
        r'recruiting'
    ],
    'product': [
        r'launches?',
        r'announces?\s+new',
        r'releases?',
        r'unveils?'
    ],
    'market': [
        r'expands?\s+to',
        r'enters?\s+market',
        r'new\s+markets?',
        r'geographic\s+expansion',
        r'opens?\s+(?:new\s+)?office',
        r'partnership\s+with',
        r'partners?\s+with',
        r'strategic\s+partnership',
        r'acquisition\s+of'
    ],
    'leadership': [
        r'appoints?\s+new',
        r'hires?\s+.*(?:CEO|CTO|CFO|COO)',
        r'promotes?\s+.*to',
        r'executive\s+team'
    ],
    'press': [
        r'featured\s+in',
        r'interview\s+with',
        r'spotlight'
    ]
}


def classify_signal_type(title: str, summary: str) -> str:
    """Classify signal type based on content patterns"""
    text = f"{title} {summary}".lower()
    
    scores = {}
    for signal_type, patterns in SIGNAL_PATTERNS.items():
        scores[signal_type] = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                scores[signal_type] += 1
    
    if max(scores.values()) == 0:
        return 'press'
    
    return max(scores, key=lambda x: scores[x])


def extract_magnitude(title: str, summary: str, signal_type: str) -> int:
    """Extract magnitude (numeric value) from signal"""
    text = f"{title} {summary}"
    
    if signal_type == 'funding':
        match = re.search(r'\$?(\d+(?:\.\d+)?)\s*([MBmb])', text)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()
            return int(value * 1000 if unit == 'B' else value)
    
    elif signal_type == 'hiring':
        match = re.search(r'(\d+)\s*(?:\+)?\s*(?:new\s+)?(?:hires?|positions?|employees?|jobs?)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    elif signal_type == 'market':
        match = re.search(r'(\d+)\s*(?:new\s+)?markets?', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 1


def calculate_relevance(title: str, summary: str) -> float:
    """Calculate relevance score (0.0-1.0) based on B2B SaaS indicators"""
    text = f"{title} {summary}".lower()
    
    relevance_keywords = {
        'high': ['saas', 'b2b', 'enterprise', 'teams', 'collaboration', 'productivity', 'workflow', 'automation'],
        'medium': ['software', 'platform', 'tool', 'business', 'startup', 'tech'],
        'low': ['api', 'cloud', 'data', 'integration']
    }
    
    score = 0.5
    
    for keyword in relevance_keywords['high']:
        if keyword in text:
            score += 0.1
    
    for keyword in relevance_keywords['medium']:
        if keyword in text:
            score += 0.05
    
    for keyword in relevance_keywords['low']:
        if keyword in text:
            score += 0.02
    
    return min(1.0, score)


def generate_signal_id(domain: str, title: str) -> str:
    """Generate unique signal ID from domain and title"""
    content = f"{domain}-{title}".encode('utf-8')
    return hashlib.md5(content).hexdigest()[:16]


def process_search_results_to_signals(search_results: List[Dict], domain: str, company: str) -> List[Dict]:
    """
    Process web search results into structured signals
    
    Args:
        search_results: List of search result dicts with title, description, url
        domain: Company domain (e.g., 'notion.so')
        company: Company name (e.g., 'Notion')
    
    Returns:
        List of processed signals ready for ingestion
    """
    signals = []
    
    for result in search_results:
        title = result.get('title', '')
        summary = result.get('description', result.get('snippet', ''))
        url = result.get('url', '')
        
        if not title or not summary:
            continue
        
        signal_type = classify_signal_type(title, summary)
        magnitude = extract_magnitude(title, summary, signal_type)
        relevance = calculate_relevance(title, summary)
        
        # Calculate ICP fit score
        icp_data = calculate_icp_fit_score(
            signal_title=title,
            signal_summary=summary,
            published_date=datetime.now()
        )
        
        signal = {
            'id': generate_signal_id(domain, title),
            'domain': domain,
            'company': company,
            'type': signal_type,
            'title': title,
            'summary': summary,
            'url': url,
            'published_at': datetime.now().isoformat() + 'Z',
            'magnitude': magnitude,
            'relevance': relevance,
            'icp_score': icp_data['total_score'],
            'icp_explanation': icp_data['explanation']
        }
        
        signals.append(signal)
    
    return signals


def process_search_results_to_prospects(search_results: List[Dict], seen_domains: Optional[set] = None) -> List[Dict]:
    """
    Process search results into prospect leads with ICP fit scoring
    
    Args:
        search_results: List of search result dicts
        seen_domains: Set of already-seen domains to avoid duplicates
    
    Returns:
        List of qualified prospects (ICP score >= 70)
    """
    if seen_domains is None:
        seen_domains = set()
    
    prospects = []
    
    for result in search_results:
        title = result.get('title', '')
        summary = result.get('description', result.get('snippet', ''))
        url = result.get('url', '')
        
        domain = extract_domain_from_url(url)
        if not domain or domain in seen_domains:
            continue
        
        company = extract_company_name(title)
        if not company:
            continue
        
        # Calculate ICP fit score
        icp_data = calculate_icp_fit_score(
            signal_title=title,
            signal_summary=summary,
            published_date=datetime.now()
        )
        
        # Only include prospects that meet ICP threshold (>= 70)
        if icp_data['total_score'] < 70:
            continue
        
        seen_domains.add(domain)
        
        signal_type = classify_signal_type(title, summary)
        magnitude = extract_magnitude(title, summary, signal_type)
        relevance = calculate_relevance(title, summary)
        
        prospect = {
            'domain': domain,
            'company': company,
            'signal_type': signal_type,
            'signal_title': title,
            'signal_summary': summary,
            'url': url,
            'relevance': relevance,
            'magnitude': magnitude,
            'fit_score': icp_data['total_score'],
            'icp_explanation': icp_data['explanation'],
            'discovered_at': datetime.now().isoformat()
        }
        
        prospects.append(prospect)
    
    return prospects


def get_prospect_search_queries() -> List[str]:
    """Get list of search queries for weekly prospecting"""
    return [
        "B2B SaaS startup funding 2025",
        "collaboration tool product launch 2025",
        "productivity software hiring 2025",
        "team workflow automation startup 2025",
        "enterprise software Series A 2025"
    ]


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL"""
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if match:
        domain = match.group(1)
        if domain.count('.') >= 1 and not domain.startswith('news.') and not domain.startswith('blog.'):
            return domain
    return None


def extract_company_name(title: str) -> Optional[str]:
    """Extract company name from title"""
    match = re.search(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', title)
    if match:
        name = match.group(1).strip()
        if len(name) >= 3 and name not in ['The', 'How', 'What', 'Why', 'When', 'Where']:
            return name
    return None
