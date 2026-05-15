"""
Autonomous web search and signal crawling
Uses Tavily API to independently search for company signals
"""
import os
from typing import List, Dict, Optional
from tavily import TavilyClient
from datetime import datetime
import logging

from src.signal_crawler import (
    process_search_results_to_signals,
    process_search_results_to_prospects,
    get_prospect_search_queries
)

logger = logging.getLogger(__name__)


def get_tavily_client() -> Optional[TavilyClient]:
    """Get Tavily client if API key is available"""
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        logger.warning("TAVILY_API_KEY not found - autonomous crawling disabled")
        return None
    return TavilyClient(api_key=api_key)


def search_company_signals(domain: str, company: str) -> List[Dict]:
    """
    Autonomously search for company signals using ALL 4 collectors:
    1. General Tavily search
    2. Press release sites
    3. Job board sites  
    4. Product launch sites
    
    Args:
        domain: Company domain (e.g., 'linear.app')
        company: Company name (e.g., 'Linear')
    
    Returns:
        List of processed signals ready for ingestion
    """
    client = get_tavily_client()
    if not client:
        return []
    
    all_signals = []
    
    # 1. General Tavily search (existing)
    query = f"{company} funding hiring product launch news 2025"
    
    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=10
        )
        
        search_results = []
        for result in response.get('results', []):
            search_results.append({
                'title': result.get('title', ''),
                'description': result.get('content', ''),
                'url': result.get('url', '')
            })
        
        signals = process_search_results_to_signals(search_results, domain, company)
        all_signals.extend(signals)
        logger.info(f"General search: {len(signals)} signals for {company}")
        
    except Exception as e:
        logger.error(f"General Tavily search failed for {company}: {e}")
    
    # 2. Press release sites
    try:
        from src.press_signal_collector import search_press_releases_tavily
        press_signals = search_press_releases_tavily(
            keywords=[f"{company} funding", f"{company} announcement"],
            max_results=5
        )
        # Filter to only this company's domain
        press_signals = [s for s in press_signals if s.get('domain') == domain or company.lower() in s.get('title', '').lower()]
        all_signals.extend(press_signals)
        logger.info(f"Press releases: {len(press_signals)} signals for {company}")
    except Exception as e:
        logger.error(f"Press release search failed for {company}: {e}")
    
    # 3. Job board sites
    try:
        from src.job_board_crawler import search_job_boards_tavily
        job_signals = search_job_boards_tavily(
            keywords=[f"{company} hiring", f"{company} jobs"],
            max_results=5
        )
        # Filter to only this company's domain
        job_signals = [s for s in job_signals if s.get('domain') == domain or company.lower() in s.get('title', '').lower()]
        all_signals.extend(job_signals)
        logger.info(f"Job boards: {len(job_signals)} signals for {company}")
    except Exception as e:
        logger.error(f"Job board search failed for {company}: {e}")
    
    # 4. Product launch sites
    try:
        from src.product_launch_crawler import search_product_launches_tavily
        launch_signals = search_product_launches_tavily(
            keywords=[f"{company} launch", f"{company} product"],
            max_results=5
        )
        # Filter to only this company's domain
        launch_signals = [s for s in launch_signals if s.get('domain') == domain or company.lower() in s.get('title', '').lower()]
        all_signals.extend(launch_signals)
        logger.info(f"Product launches: {len(launch_signals)} signals for {company}")
    except Exception as e:
        logger.error(f"Product launch search failed for {company}: {e}")
    
    logger.info(f"TOTAL: {len(all_signals)} signals for {company} (from all 4 collectors)")
    return all_signals


def discover_new_prospects() -> List[Dict]:
    """
    Autonomous weekly prospecting - discover new B2B SaaS companies using ALL 4 collectors:
    1. General Tavily search
    2. Press release sites
    3. Job board sites
    4. Product launch sites
    
    Returns:
        List of qualified prospects
    """
    client = get_tavily_client()
    if not client:
        return []
    
    all_prospects = []
    seen_domains = set()
    
    # 1. General Tavily search (existing)
    logger.info("Running general web search for prospects...")
    for query in get_prospect_search_queries():
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=15
            )
            
            search_results = []
            for result in response.get('results', []):
                search_results.append({
                    'title': result.get('title', ''),
                    'description': result.get('content', ''),
                    'url': result.get('url', '')
                })
            
            prospects = process_search_results_to_prospects(search_results, seen_domains)
            all_prospects.extend(prospects)
            
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query}': {e}")
            continue
    
    logger.info(f"General search: {len(all_prospects)} prospects discovered")
    
    # 2. Press release sites for prospects
    logger.info("Running press release search for prospects...")
    try:
        from src.press_signal_collector import search_press_releases_tavily
        press_signals = search_press_releases_tavily(
            keywords=['SaaS funding', 'B2B Series A', 'startup raises'],
            max_results=15
        )
        # Convert signals to prospects
        press_prospects = signals_to_prospects(press_signals, seen_domains)
        all_prospects.extend(press_prospects)
        logger.info(f"Press releases: {len(press_prospects)} prospects discovered")
    except Exception as e:
        logger.error(f"Press release prospecting failed: {e}")
    
    # 3. Job board sites for prospects
    logger.info("Running job board search for prospects...")
    try:
        from src.job_board_crawler import search_job_boards_tavily
        job_signals = search_job_boards_tavily(
            keywords=['SaaS hiring engineers', 'B2B startup jobs', 'remote collaboration tool'],
            max_results=15
        )
        # Convert signals to prospects
        job_prospects = signals_to_prospects(job_signals, seen_domains)
        all_prospects.extend(job_prospects)
        logger.info(f"Job boards: {len(job_prospects)} prospects discovered")
    except Exception as e:
        logger.error(f"Job board prospecting failed: {e}")
    
    # 4. Product launch sites for prospects
    logger.info("Running product launch search for prospects...")
    try:
        from src.product_launch_crawler import search_product_launches_tavily
        launch_signals = search_product_launches_tavily(
            keywords=['SaaS product launch', 'B2B software release', 'collaboration tool'],
            max_results=15
        )
        # Convert signals to prospects
        launch_prospects = signals_to_prospects(launch_signals, seen_domains)
        all_prospects.extend(launch_prospects)
        logger.info(f"Product launches: {len(launch_prospects)} prospects discovered")
    except Exception as e:
        logger.error(f"Product launch prospecting failed: {e}")
    
    logger.info(f"TOTAL: {len(all_prospects)} new prospects discovered (from all 4 collectors)")
    return all_prospects


def signals_to_prospects(signals: List[Dict], seen_domains: set) -> List[Dict]:
    """
    Convert signals to prospect format, filtering for ICP fit
    
    Args:
        signals: List of signals from collectors
        seen_domains: Set of already-seen domains
    
    Returns:
        List of qualified prospects
    """
    from src.icp_scoring import calculate_icp_fit_score
    
    prospects = []
    
    for signal in signals:
        domain = signal.get('domain', '')
        company = signal.get('company', '')
        
        if not domain or not company or domain in seen_domains:
            continue
        
        # Get or calculate ICP score
        icp_score = signal.get('icp_score')
        icp_explanation = signal.get('icp_explanation', '')
        
        if icp_score is None:
            icp_data = calculate_icp_fit_score(
                signal_title=signal.get('title', ''),
                signal_summary=signal.get('summary', ''),
                published_date=datetime.now()
            )
            icp_score = icp_data['total_score']
            icp_explanation = icp_data['explanation']
        
        # Only include prospects that meet ICP threshold (>= 70)
        if icp_score < 70:
            continue
        
        seen_domains.add(domain)
        
        prospect = {
            'domain': domain,
            'company': company,
            'signal_type': signal.get('type', 'unknown'),
            'signal_title': signal.get('title', ''),
            'signal_summary': signal.get('summary', ''),
            'url': signal.get('url', ''),
            'relevance': signal.get('relevance', 0.5),
            'magnitude': signal.get('magnitude', 1),
            'fit_score': icp_score,
            'icp_explanation': icp_explanation,
            'discovered_at': datetime.now().isoformat()
        }
        
        prospects.append(prospect)
    
    return prospects


def test_tavily_connection() -> Dict:
    """Test if Tavily API is working"""
    client = get_tavily_client()
    if not client:
        return {'success': False, 'error': 'TAVILY_API_KEY not configured'}
    
    try:
        response = client.search(query="test", max_results=1)
        return {'success': True, 'message': 'Tavily API connected successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
