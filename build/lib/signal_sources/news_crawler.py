import feedparser
import uuid
from datetime import datetime
import requests
from typing import List, Dict


def extract_magnitude_from_text(text: str) -> int:
    """Extract numeric magnitude from text (e.g., '20 hires' -> 20)"""
    import re
    
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        return int(numbers[0])
    return 0


def classify_signal_type(title: str, summary: str) -> str:
    """Classify signal type based on keywords"""
    text = (title + " " + summary).lower()
    
    if any(word in text for word in ['hire', 'hiring', 'employee', 'team member', 'staff']):
        return 'hiring'
    elif any(word in text for word in ['funding', 'investment', 'raised', 'series', 'round']):
        return 'funding'
    elif any(word in text for word in ['ceo', 'cto', 'vp', 'chief', 'president', 'executive']):
        return 'leadership'
    elif any(word in text for word in ['launch', 'release', 'announce', 'unveil', 'debut']):
        return 'product'
    elif any(word in text for word in ['expand', 'expansion', 'market', 'region', 'international']):
        return 'market'
    elif any(word in text for word in ['interview', 'podcast', 'feature', 'profile']):
        return 'interview'
    else:
        return 'press'


def calculate_relevance(title: str, summary: str) -> float:
    """Calculate relevance to EchoTray use case (0-1)"""
    text = (title + " " + summary).lower()
    
    relevance_keywords = [
        'team', 'collaboration', 'workflow', 'productivity', 
        'communication', 'remote', 'distributed', 'async',
        'update', 'meeting', 'status', 'alignment', 'handoff'
    ]
    
    score = sum(1 for kw in relevance_keywords if kw in text)
    return min(1.0, score / 5)


def crawl_rss_feed(feed_url: str, company: str, domain: str) -> List[Dict]:
    """Crawl RSS feed and extract signals"""
    try:
        feed = feedparser.parse(feed_url)
        signals = []
        
        for entry in feed.entries[:5]:
            title = entry.get('title', '')
            summary = entry.get('summary', entry.get('description', ''))
            link = entry.get('link', '')
            published = entry.get('published_parsed')
            
            if published:
                pub_date = datetime(*published[:6]).isoformat() + 'Z'
            else:
                pub_date = datetime.now().isoformat() + 'Z'
            
            signal_type = classify_signal_type(title, summary)
            magnitude = extract_magnitude_from_text(title + " " + summary)
            relevance = calculate_relevance(title, summary)
            
            if relevance < 0.3:
                continue
            
            signal = {
                "id": str(uuid.uuid4()),
                "domain": domain,
                "company": company,
                "type": signal_type,
                "title": title,
                "summary": summary[:300] if summary else title,
                "url": link,
                "published_at": pub_date,
                "magnitude": magnitude,
                "relevance": relevance
            }
            signals.append(signal)
        
        return signals
    except Exception as e:
        print(f"Error crawling {feed_url}: {e}")
        return []


def search_company_news(company: str, domain: str) -> List[Dict]:
    """Search for company news using multiple sources"""
    signals = []
    
    tech_feeds = [
        f'https://news.google.com/rss/search?q={company}+hiring',
        f'https://news.google.com/rss/search?q={company}+funding',
        f'https://news.google.com/rss/search?q={company}+launch',
    ]
    
    for feed_url in tech_feeds:
        signals.extend(crawl_rss_feed(feed_url, company, domain))
    
    return signals
