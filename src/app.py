import logging
import time
import os
import sqlite3
import uuid
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone

# Project specific imports
from src.verify import verify_email
from src.verify_storage import init_db as init_verify_db, save_result, get_result, get_all_results
from src.personalize_db import (
    init_db as init_personalize_db,
    save_signal,
    get_top_signals,
    get_all_signals,
    purge_old_signals,
    save_template as save_template_db,
    get_all_templates,
    pin_signal,
    unpin_signal,
    exclude_signal,
    get_exclusions,
    remove_exclusion,
    get_prospects,
    update_prospect_status,
    save_prospect
)
from src.personalize_engine import personalize_email, validate_output
from src.default_templates import load_default_templates
from src.autonomous_crawler import search_company_signals, discover_new_prospects
from src.press_signal_collector import search_press_releases_tavily
from src.job_board_crawler import search_job_boards_tavily
from src.product_launch_crawler import search_product_launches_tavily
from src.icp_scoring import calculate_icp_fit_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app, supports_credentials=True)

# Initialize databases
init_verify_db()
init_personalize_db()
load_default_templates()

PASS_THRESHOLD = int(os.getenv("VERIFIER_PASS_THRESHOLD", "75"))

@app.route('/')
def index():
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({
        "status": "running",
        "service": "Verify & Personalize API",
        "version": "1.0"
    })

@app.route('/<path:path>')
def serve_static(path):
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Not found"}), 404

# ============ EMAIL VERIFICATION ENDPOINTS ============

@app.route('/api/verify', methods=['POST'])
def verify_one():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "email is required"}), 400
    try:
        result = verify_email(email)
        save_result(result)
        result['passed'] = result['score'] >= PASS_THRESHOLD and result['smtp_status'] != 'invalid'
        return jsonify(result)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/batch', methods=['POST'])
def verify_batch():
    emails = []
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        import csv
        import io
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        for row in csv_reader:
            if row and row[0].strip():
                email = row[0].strip()
                name = row[1].strip() if len(row) > 1 else None
                if '@' in email:
                    emails.append({"email": email, "name": name})
    else:
        data = request.json
        raw_emails = data.get('emails', [])
        emails = [{"email": e, "name": None} if isinstance(e, str) else e for e in raw_emails]
    
    if not emails:
        return jsonify({"error": "No emails provided"}), 400
    
    try:
        results = []
        for item in emails:
            email = item["email"] if isinstance(item, dict) else item
            name = item.get("name") if isinstance(item, dict) else None
            result = verify_email(email)
            save_result(result)
            result['passed'] = result['score'] >= PASS_THRESHOLD and result['smtp_status'] != 'invalid'
            result['name'] = name
            results.append(result)
            time.sleep(0.35)
        return jsonify({"results": results})
    except Exception as e:
        logger.error(f"Batch verification failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/status/<email>', methods=['GET'])
def verify_status(email: str):
    try:
        result = get_result(email)
        if not result:
            return jsonify({"error": "Email not found"}), 404
        result['passed'] = result['score'] >= PASS_THRESHOLD and result['smtp_status'] != 'invalid'
        return jsonify(result)
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/history', methods=['GET'])
def verify_history():
    try:
        limit = request.args.get('limit', 100, type=int)
        results = get_all_results(limit)
        for r in results:
            score = int(r.get('score', 0)) if r.get('score') else 0
            smtp_status = r.get('smtp_status', 'unknown')
            r['score'] = score
            r['passed'] = score >= PASS_THRESHOLD and smtp_status != 'invalid'
        return jsonify({"results": results})
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/save', methods=['POST'])
def save_verified_email():
    try:
        data = request.get_json()
        email = data.get('email')
        score = data.get('score')
        name = data.get('name')
        if not email or score is None:
            return jsonify({"error": "Email and score required"}), 400
        from src.verify_storage import save_email
        save_email(email, score, name)
        return jsonify({"success": True, "email": email})
    except Exception as e:
        logger.error(f"Save email failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/saved', methods=['GET'])
def get_saved_emails_endpoint():
    try:
        limit = request.args.get('limit', 1000, type=int)
        from src.verify_storage import get_saved_emails
        emails = get_saved_emails(limit)
        return jsonify({"results": emails, "count": len(emails)})
    except Exception as e:
        logger.error(f"Get saved emails failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify/saved/<email>', methods=['DELETE'])
def delete_saved_email_endpoint(email: str):
    try:
        from src.verify_storage import delete_saved_email
        delete_saved_email(email)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Delete saved email failed: {e}")
        return jsonify({"error": str(e)}), 500

# ============ PERSONALIZATION ENDPOINTS ============

@app.route('/api/signals/ingest', methods=['POST'])
def ingest_signals():
    try:
        data = request.json
        signals = data.get('signals', [])
        if not signals:
            return jsonify({"error": "No signals provided"}), 400
        for signal in signals:
            save_signal(signal)
        return jsonify({"success": True, "count": len(signals)})
    except Exception as e:
        logger.error(f"Signal ingestion failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/<domain>', methods=['GET'])
def get_domain_signals(domain: str):
    try:
        limit = request.args.get('limit', 3, type=int)
        signals = get_top_signals(domain, limit)
        return jsonify({"signals": signals, "count": len(signals)})
    except Exception as e:
        logger.error(f"Get signals failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals', methods=['GET'])
def list_all_signals():
    try:
        limit = request.args.get('limit', 100, type=int)
        signals = get_all_signals(limit)
        return jsonify({"signals": signals, "count": len(signals)})
    except Exception as e:
        logger.error(f"List signals failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/personalize/render', methods=['POST'])
def render_personalization():
    try:
        data = request.json
        domain = data.get('domain')
        company = data.get('company')
        first_name = data.get('first_name')
        role = data.get('role')
        if not all([domain, company, first_name]):
            return jsonify({"error": "domain, company, and first_name required"}), 400
        result = personalize_email(domain, company, first_name, role)
        validation = validate_output(result['subject'], result['opening'])
        result['validation'] = validation
        return jsonify(result)
    except Exception as e:
        logger.error(f"Personalization failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    try:
        templates = get_all_templates()
        return jsonify({"templates": templates, "count": len(templates)})
    except Exception as e:
        logger.error(f"List templates failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    try:
        data = request.json
        template = {
            "id": str(uuid.uuid4()),
            "name": data.get('name'),
            "signal_type": data.get('signal_type', ''),
            "subject": data.get('subject'),
            "opening": data.get('opening'),
            "is_fallback": data.get('is_fallback', 0)
        }
        if not all([template['name'], template['subject'], template['opening']]):
            return jsonify({"error": "name, subject, and opening required"}), 400
        save_template_db(template)
        return jsonify({"success": True, "template": template})
    except Exception as e:
        logger.error(f"Create template failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/purge', methods=['POST'])
def purge_signals():
    try:
        days = request.json.get('days', 90)
        purge_old_signals(days)
        return jsonify({"success": True, "message": f"Purged signals older than {days} days"})
    except Exception as e:
        logger.error(f"Purge failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/<signal_id>/contact', methods=['POST'])
def mark_signal_contacted(signal_id):
    try:
        conn = sqlite3.connect('personalize.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE signals 
            SET contacted = 1, contacted_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), signal_id))
        conn.commit()
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Signal not found"}), 404
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Mark contacted failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/personalize/from-email', methods=['POST'])
def personalize_from_email():
    try:
        data = request.json
        email_or_domain = data.get('email')
        name = data.get('name', '')
        auto_crawl = data.get('auto_crawl', True)
        pinned_signal_id = data.get('pinned_signal_id')
        if not email_or_domain:
            return jsonify({"error": "email or domain required"}), 400
        if '@' in email_or_domain:
            domain = email_or_domain.split('@')[-1]
            first_name = name.split()[0] if name else email_or_domain.split('@')[0]
        else:
            domain = email_or_domain
            first_name = name.split()[0] if name else 'there'
        company = domain.replace('.com', '').replace('.io', '').replace('.ai', '').replace('.app', '').title()
        existing_signals = get_top_signals(domain, limit=1, max_age_days=45)
        crawled = False
        if auto_crawl and not existing_signals and not pinned_signal_id:
            new_signals = search_company_signals(domain, company)
            if new_signals:
                for signal in new_signals:
                    save_signal(signal)
                crawled = True
        result = personalize_email(domain, company, first_name, role=None, pinned_signal_id=pinned_signal_id)
        result['email'] = email_or_domain
        result['domain'] = domain
        result['auto_crawled'] = crawled
        return jsonify(result)
    except Exception as e:
        logger.error(f"Email personalization failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prospects', methods=['GET'])
def get_prospects_endpoint():
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        prospects = get_prospects(status, limit)
        return jsonify({"prospects": prospects, "count": len(prospects)})
    except Exception as e:
        logger.error(f"Get prospects failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prospects/<domain>', methods=['PATCH'])
def update_prospect_endpoint(domain: str):
    try:
        data = request.json
        status = data.get('status')
        notes = data.get('notes')
        if not status:
            return jsonify({"error": "status required"}), 400
        success = update_prospect_status(domain, status, notes)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Update prospect failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prospects/discover', methods=['POST'])
def discover_prospects_endpoint():
    try:
        prospects = discover_new_prospects()
        for prospect in prospects:
            save_prospect(prospect)
        return jsonify({"success": True, "discovered": len(prospects)})
    except Exception as e:
        logger.error(f"Prospect discovery failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/press-releases', methods=['POST'])
def collect_press_release_signals_endpoint():
    try:
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS funding', 'B2B product launch'])
        max_results = data.get('max_results', 10)
        signals = search_press_releases_tavily(keywords=keywords, max_results=max_results)
        for signal in signals:
            icp_result = calculate_icp_fit_score(signal.get('title', ''), signal.get('summary', ''))
            signal['icp_score'] = icp_result['total_score']
            save_signal(signal)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Press release collection failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/job-boards', methods=['POST'])
def collect_job_board_signals_endpoint():
    try:
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS remote hiring'])
        max_results = data.get('max_results', 10)
        signals = search_job_boards_tavily(keywords=keywords, max_results=max_results)
        for signal in signals:
            icp_result = calculate_icp_fit_score(signal.get('title', ''), signal.get('summary', ''))
            signal['icp_score'] = icp_result['total_score']
            signal_copy = {k: v for k, v in signal.items() if k != 'metadata'}
            save_signal(signal_copy)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Job board collection failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/product-launches', methods=['POST'])
def collect_product_launch_signals_endpoint():
    try:
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS product launch'])
        max_results = data.get('max_results', 10)
        signals = search_product_launches_tavily(keywords=keywords, max_results=max_results)
        for signal in signals:
            icp_result = calculate_icp_fit_score(signal.get('title', ''), signal.get('summary', ''))
            signal['icp_score'] = icp_result['total_score']
            signal_copy = {k: v for k, v in signal.items() if k != 'metadata'}
            save_signal(signal_copy)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Product launch collection failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
