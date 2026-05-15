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
    save_prospect,
    save_product,
    get_product,
    get_all_products,
    delete_product
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

# Debug: List directories to find where index.html is
logger.info(f"CWD: {os.getcwd()}")
logger.info(f"App Dir: {os.path.dirname(os.path.abspath(__file__))}")

def find_index_html_paths(start_path):
    matches = []
    for root, dirs, files in os.walk(start_path):
        if 'index.html' in files:
            matches.append(root)
    return matches

found_paths = find_index_html_paths('/app') + find_index_html_paths(os.getcwd())
logger.info(f"All found index.html paths: {found_paths}")

# Prioritize paths containing 'dist'
static_folder = None
for path in found_paths:
    if 'dist' in path:
        static_folder = path
        break

if not static_folder and found_paths:
    # Fallback to any path that isn't the root or a known source folder if possible
    static_folder = found_paths[0]

if not static_folder:
    logger.error("COULD NOT FIND INDEX.HTML ANYWHERE IN /APP")
    static_folder = os.path.join(os.getcwd(), 'frontend', 'dist')

logger.info(f"Discovered static folder: {static_folder}")

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, supports_credentials=True)

# Initialize databases
init_verify_db()
init_personalize_db()
load_default_templates()

PASS_THRESHOLD = int(os.getenv("VERIFIER_PASS_THRESHOLD", "75"))

def get_product_id():
    """Helper to extract product_id from headers or args"""
    return request.headers.get('X-Product-Id', request.args.get('product_id', 'echotray'))

@app.route('/')
def index():
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({
        "status": "running",
        "service": "Verify & Personalize API",
        "version": "1.0"
    })

# ============ PRODUCT MANAGEMENT ENDPOINTS ============

@app.route('/api/products', methods=['GET'])
def list_products():
    try:
        products = get_all_products()
        return jsonify({"products": products, "count": len(products)})
    except Exception as e:
        logger.error(f"List products failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def create_product_endpoint():
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({"error": "name is required"}), 400
        
        product = {
            "id": data.get('id', str(uuid.uuid4())[:8]),
            "name": data['name'],
            "description": data.get('description', ''),
            "value_prop": data.get('value_prop', ''),
            "from_email": data.get('from_email', ''),
            "icp_config": data.get('icp_config', {}),
            "prompts_config": data.get('prompts_config', {})
        }
        save_product(product)
        return jsonify({"success": True, "product": product})
    except Exception as e:
        logger.error(f"Create product failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<id>', methods=['GET'])
def get_product_endpoint(id):
    try:
        product = get_product(id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(product)
    except Exception as e:
        logger.error(f"Get product failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<id>', methods=['DELETE'])
def delete_product_endpoint(id):
    try:
        success = delete_product(id)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Delete product failed: {e}")
        return jsonify({"error": str(e)}), 500


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

# ============ PERSONALIZATION ENDPOINTS ============

@app.route('/api/signals/ingest', methods=['POST'])
def ingest_signals():
    try:
        data = request.json
        product_id = get_product_id()
        signals = data.get('signals', [])
        if not signals:
            return jsonify({"error": "No signals provided"}), 400
        for signal in signals:
            save_signal(signal, product_id)
        return jsonify({"success": True, "count": len(signals)})
    except Exception as e:
        logger.error(f"Signal ingestion failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/<domain>', methods=['GET'])
def get_domain_signals(domain: str):
    try:
        product_id = get_product_id()
        limit = request.args.get('limit', 3, type=int)
        signals = get_top_signals(domain, product_id, limit)
        return jsonify({"signals": signals, "count": len(signals)})
    except Exception as e:
        logger.error(f"Get signals failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals', methods=['GET'])
def list_all_signals():
    try:
        product_id = get_product_id()
        limit = request.args.get('limit', 100, type=int)
        signals = get_all_signals(product_id, limit)
        return jsonify({"signals": signals, "count": len(signals)})
    except Exception as e:
        logger.error(f"List signals failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/personalize/render', methods=['POST'])
def render_personalization():
    try:
        data = request.json
        product_id = get_product_id()
        domain = data.get('domain')
        company = data.get('company')
        first_name = data.get('first_name')
        role = data.get('role')
        if not all([domain, company, first_name]):
            return jsonify({"error": "domain, company, and first_name required"}), 400
        
        product = get_product(product_id)
        result = personalize_email(domain, company, first_name, product_id, role)
        validation = validate_output(result['subject'], result['opening'], product)
        result['validation'] = validation
        return jsonify(result)
    except Exception as e:
        logger.error(f"Personalization failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    try:
        product_id = get_product_id()
        templates = get_all_templates(product_id)
        return jsonify({"templates": templates, "count": len(templates)})
    except Exception as e:
        logger.error(f"List templates failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    try:
        data = request.json
        product_id = get_product_id()
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
        save_template_db(template, product_id)
        return jsonify({"success": True, "template": template})
    except Exception as e:
        logger.error(f"Create template failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/personalize/from-email', methods=['POST'])
def personalize_from_email():
    try:
        data = request.json
        product_id = get_product_id()
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
        
        existing_signals = get_top_signals(domain, product_id, limit=1, max_age_days=45)
        crawled = False
        
        if auto_crawl and not existing_signals and not pinned_signal_id:
            new_signals = search_company_signals(domain, company)
            if new_signals:
                for signal in new_signals:
                    save_signal(signal, product_id)
                crawled = True
                
        result = personalize_email(domain, company, first_name, product_id, role=None, pinned_signal_id=pinned_signal_id)
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
        product_id = get_product_id()
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        prospects = get_prospects(product_id, status, limit)
        return jsonify({"prospects": prospects, "count": len(prospects)})
    except Exception as e:
        logger.error(f"Get prospects failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prospects/<domain>', methods=['PATCH'])
def update_prospect_endpoint(domain: str):
    try:
        product_id = get_product_id()
        data = request.json
        status = data.get('status')
        notes = data.get('notes')
        if not status:
            return jsonify({"error": "status required"}), 400
        success = update_prospect_status(domain, status, product_id, notes)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Update prospect failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prospects/discover', methods=['POST'])
def discover_prospects_endpoint():
    try:
        product_id = get_product_id()
        product = get_product(product_id)
        icp_config = product.get('icp_config') if product else None
        
        prospects = discover_new_prospects(icp_config=icp_config)
        for prospect in prospects:
            save_prospect(prospect, product_id)
        return jsonify({"success": True, "discovered": len(prospects)})
    except Exception as e:
        logger.error(f"Prospect discovery failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/press-releases', methods=['POST'])
def collect_press_release_signals_endpoint():
    try:
        product_id = get_product_id()
        product = get_product(product_id)
        icp_config = product.get('icp_config') if product else None
        
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS funding', 'B2B product launch'])
        max_results = data.get('max_results', 10)
        signals = search_press_releases_tavily(keywords=keywords, max_results=max_results)
        
        for signal in signals:
            icp_result = calculate_icp_fit_score(
                signal.get('title', ''), 
                signal.get('summary', ''),
                icp_config=icp_config
            )
            signal['icp_score'] = icp_result['total_score']
            save_signal(signal, product_id)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Press release collection failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/job-boards', methods=['POST'])
def collect_job_board_signals_endpoint():
    try:
        product_id = get_product_id()
        product = get_product(product_id)
        icp_config = product.get('icp_config') if product else None
        
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS remote hiring'])
        max_results = data.get('max_results', 10)
        signals = search_job_boards_tavily(keywords=keywords, max_results=max_results)
        
        for signal in signals:
            icp_result = calculate_icp_fit_score(
                signal.get('title', ''), 
                signal.get('summary', ''),
                icp_config=icp_config
            )
            signal['icp_score'] = icp_result['total_score']
            signal_copy = {k: v for k, v in signal.items() if k != 'metadata'}
            save_signal(signal_copy, product_id)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Job board collection failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals/product-launches', methods=['POST'])
def collect_product_launch_signals_endpoint():
    try:
        product_id = get_product_id()
        product = get_product(product_id)
        icp_config = product.get('icp_config') if product else None
        
        data = request.json or {}
        keywords = data.get('keywords', ['SaaS product launch'])
        max_results = data.get('max_results', 10)
        signals = search_product_launches_tavily(keywords=keywords, max_results=max_results)
        
        for signal in signals:
            icp_result = calculate_icp_fit_score(
                signal.get('title', ''), 
                signal.get('summary', ''),
                icp_config=icp_config
            )
            signal['icp_score'] = icp_result['total_score']
            signal_copy = {k: v for k, v in signal.items() if k != 'metadata'}
            save_signal(signal_copy, product_id)
        return jsonify({"success": True, "collected": len(signals)})
    except Exception as e:
        logger.error(f"Product launch collection failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
