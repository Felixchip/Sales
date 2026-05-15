"""
On-demand signal collection
Triggered when user enters an email for personalization
"""
from typing import Dict, List
from src.signal_crawler import process_search_results_to_signals
from src.personalize_db import save_signal


def ingest_signals_from_search_results(search_results: List[Dict], domain: str, company: str) -> int:
    """
    Process and ingest signals from web search results
    
    Args:
        search_results: Raw search results from web_search
        domain: Company domain
        company: Company name
    
    Returns:
        Number of signals ingested
    """
    signals = process_search_results_to_signals(search_results, domain, company)
    
    count = 0
    for signal in signals:
        try:
            save_signal(signal)
            count += 1
        except Exception as e:
            print(f"Failed to save signal: {e}")
            continue
    
    return count


def build_signal_search_query(company: str) -> str:
    """Build optimized search query for company signals"""
    return f"{company} funding hiring expansion product launch news 2025"
