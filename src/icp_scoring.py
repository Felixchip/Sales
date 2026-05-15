"""
ICP (Ideal Customer Profile) Scoring System
Scores signals based on EchoTray's ideal customer criteria
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import re


# Default ICP Criteria (EchoTray)
DEFAULT_GROWTH_TRIGGERS = {
    'funding': ['funding', 'raised', 'series', 'investment', 'valuation', 'fundraise', 'capital'],
    'hiring': ['hiring', 'recruiting', 'new hires', 'job openings', 'talent', 'team growth', 'headcount'],
    'expansion': ['expansion', 'market entry', 'new market', 'international', 'global'],
    'product_launch': ['launch', 'released', 'introducing', 'new product', 'feature', 'beta'],
    'leadership': ['VP', 'Head of', 'Director', 'Chief', 'COO', 'CPO', 'CTO', 'appointed', 'joins']
}

DEFAULT_REMOTE_KEYWORDS = ['remote', 'distributed', 'async', 'hybrid', 'global team', 'work from anywhere', 'WFH']

DEFAULT_TOOLING_KEYWORDS = ['Slack', 'Microsoft Teams', 'Jira', 'Linear', 'Asana', 'Notion', 'ClickUp', 'Monday.com']

DEFAULT_INDUSTRY_KEYWORDS = {
    'saas': ['SaaS', 'software as a service', 'cloud platform'],
    'fintech': ['fintech', 'financial technology', 'payments', 'banking'],
    'devtools': ['developer tools', 'dev tools', 'DevOps', 'API', 'infrastructure'],
    'agency': ['agency', 'creative studio', 'design firm', 'consulting'],
    'ai_ml': ['AI', 'artificial intelligence', 'machine learning', 'ML', 'LLM']
}

DEFAULT_ICP_CONFIG = {
    'growth_triggers': DEFAULT_GROWTH_TRIGGERS,
    'remote_keywords': DEFAULT_REMOTE_KEYWORDS,
    'tooling_keywords': DEFAULT_TOOLING_KEYWORDS,
    'industry_keywords': DEFAULT_INDUSTRY_KEYWORDS,
    'team_size_min': 25,
    'team_size_max': 200,
    'threshold': 70
}


def calculate_recency_score(published_date: Optional[datetime], max_points: int = 20) -> tuple[int, str]:
    """
    Calculate recency score with decay
    - ≤ 7 days: full points (20)
    - After 7 days: -1 point per day (floor at 0)
    
    Returns: (score, explanation)
    """
    if not published_date:
        return 0, "No published date"
    
    days_old = (datetime.now() - published_date).days
    
    if days_old <= 7:
        return max_points, f"Fresh news ({days_old}d old)"
    
    # Decay: -1 per day after 7 days
    decay = min(days_old - 7, max_points)
    score = max(0, max_points - decay)
    
    return score, f"News {days_old}d old (decayed -{decay}pts)"


def detect_growth_triggers(text: str, triggers_config: Dict) -> tuple[int, list[str]]:
    """
    Detect growth triggers in text
    Returns: (score, list of detected triggers)
    """
    text_lower = text.lower()
    detected = []
    
    for trigger_type, keywords in triggers_config.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(trigger_type)
                break
    
    # Cap at +30 regardless of number of triggers
    score = min(30, len(detected) * 30) if detected else 0
    
    return score, list(set(detected))


def detect_remote_culture(text: str, keywords_config: list[str]) -> tuple[int, list[str]]:
    """
    Detect remote/hybrid/async culture indicators
    """
    text_lower = text.lower()
    detected = []
    
    for keyword in keywords_config:
        if keyword.lower() in text_lower:
            detected.append(keyword)
    
    score = 15 if detected else 0
    return score, detected


def detect_tooling_match(text: str, tooling_config: list[str]) -> tuple[int, list[str]]:
    """
    Detect collaboration tool mentions
    """
    detected = []
    
    for tool in tooling_config:
        if tool in text:  # Case-sensitive for brand names
            detected.append(tool)
    
    score = 10 if detected else 0
    return score, detected


def detect_industry_relevance(text: str, industry_config: Dict) -> tuple[int, list[str]]:
    """
    Detect industry relevance
    """
    text_lower = text.lower()
    detected = []
    
    for industry, keywords in industry_config.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(industry)
                break
    
    score = 10 if detected else 0
    return score, list(set(detected))


def estimate_team_size_score(text: str, min_size: int, max_size: int, employees_hint: Optional[int] = None) -> tuple[int, str]:
    """
    Score based on team size
    """
    # Try explicit employee count first
    if employees_hint and min_size <= employees_hint <= max_size:
        return 15, f"{employees_hint} employees (ideal range)"
    
    # Pattern matching for headcount mentions in text
    patterns = [
        r'(\d+)\s*(?:employee|people|person|member|team member)',
        r'team\s*of\s*(\d+)',
        r'(\d+)\+?\s*(?:hire|hiring|new hire)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            count = int(match.group(1))
            if min_size <= count <= max_size:
                return 15, f"~{count} team members (ideal range)"
            elif count < min_size:
                return 0, f"~{count} team members (too small)"
            else:
                return 0, f"~{count} team members (too large)"
    
    return 0, "Team size unknown"


def calculate_icp_fit_score(
    signal_title: str,
    signal_summary: str,
    published_date: Optional[datetime] = None,
    employees_hint: Optional[int] = None,
    icp_config: Optional[Dict] = None
) -> Dict:
    """
    Calculate comprehensive ICP fit score (0-100)
    """
    config = icp_config or DEFAULT_ICP_CONFIG
    combined_text = f"{signal_title} {signal_summary}"
    
    # Calculate each component
    recency_score, recency_reason = calculate_recency_score(published_date)
    growth_score, growth_triggers = detect_growth_triggers(combined_text, config.get('growth_triggers', DEFAULT_GROWTH_TRIGGERS))
    team_score, team_reason = estimate_team_size_score(
        combined_text, 
        config.get('team_size_min', 25), 
        config.get('team_size_max', 200), 
        employees_hint
    )
    remote_score, remote_keywords = detect_remote_culture(combined_text, config.get('remote_keywords', DEFAULT_REMOTE_KEYWORDS))
    tooling_score, tooling_found = detect_tooling_match(combined_text, config.get('tooling_keywords', DEFAULT_TOOLING_KEYWORDS))
    industry_score, industries = detect_industry_relevance(combined_text, config.get('industry_keywords', DEFAULT_INDUSTRY_KEYWORDS))
    
    # Total score
    total_score = (
        recency_score +
        growth_score +
        team_score +
        remote_score +
        tooling_score +
        industry_score
    )
    
    # Build explanation
    explanation_parts = []
    if recency_score > 0:
        explanation_parts.append(recency_reason)
    if growth_triggers:
        explanation_parts.append(f"Growth: {', '.join(growth_triggers)}")
    if team_score > 0:
        explanation_parts.append(team_reason)
    if remote_keywords:
        explanation_parts.append(f"Culture: {', '.join(remote_keywords[:2])}")
    if tooling_found:
        explanation_parts.append(f"Tools: {', '.join(tooling_found[:2])}")
    if industries:
        explanation_parts.append(f"Industry: {', '.join(industries)}")
    
    explanation = " | ".join(explanation_parts) if explanation_parts else "No ICP signals detected"
    
    return {
        'total_score': total_score,
        'breakdown': {
            'recency': recency_score,
            'growth_triggers': growth_score,
            'team_size': team_score,
            'remote_culture': remote_score,
            'tooling': tooling_score,
            'industry': industry_score
        },
        'detected': {
            'growth_triggers': growth_triggers,
            'remote_keywords': remote_keywords,
            'tooling': tooling_found,
            'industries': industries
        },
        'explanation': explanation,
        'qualifies': total_score >= config.get('threshold', 70)
    }


def score_prospect_company(company_data: Dict, icp_config: Optional[Dict] = None) -> Dict:
    """
    Score a prospect company for weekly shortlisting
    """
    signals = company_data.get('signals', [])
    if not signals:
        return {**company_data, 'fit_score': 0, 'top_signal': None}
    
    # Score each signal
    scored_signals = []
    for signal in signals:
        score_data = calculate_icp_fit_score(
            signal_title=signal.get('title', ''),
            signal_summary=signal.get('summary', ''),
            published_date=signal.get('published_date'),
            employees_hint=company_data.get('employees'),
            icp_config=icp_config
        )
        
        scored_signals.append({
            **signal,
            'icp_score': score_data['total_score'],
            'icp_breakdown': score_data['breakdown'],
            'icp_explanation': score_data['explanation']
        })
    
    # Get highest scoring signal
    top_signal = max(scored_signals, key=lambda s: s['icp_score'])
    
    return {
        **company_data,
        'fit_score': top_signal['icp_score'],
        'top_signal': top_signal,
        'all_signals': scored_signals
    }
