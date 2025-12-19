# app/app.py
from flask import Flask, jsonify, send_from_directory, request
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymysql
import requests
import time
import logging
from logging.handlers import RotatingFileHandler
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from app.config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB,
    PUSHGATEWAY_URL, PROMETHEUS_URL, DEV_MODE
)

# --- App setup ---
app = Flask(__name__, static_folder='static', static_url_path='/')

# --- Logging setup (console + rotating file) ---
logger = logging.getLogger("url_monitor")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Console handler
ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)

# Rotating file handler (keeps disk usage small)
fh = RotatingFileHandler("app.log", maxBytes=2_000_000, backupCount=3)
fh.setFormatter(fmt)
logger.addHandler(fh)

logger.info("Starting URL monitoring app (DEV_MODE=%s)", DEV_MODE)

# --- Sample targets fallback (used when DB not available or in DEV_MODE) ---
SAMPLE_TARGETS = [
    "google.com","amazon.com","facebook.com","github.com","stackoverflow.com",
    "127.0.0.1:8080","localhost:80","example.com","python.org","wikipedia.org",
    "microsoft.com","apple.com","netflix.com","reddit.com","cnn.com",
    "yahoo.com","bing.com","zoom.us","slack.com","docker.com"
]

# --- Utility: safe DB connection + query ---
def get_targets():
    if DEV_MODE:
        logger.info("DEV_MODE enabled: using sample targets")
        return SAMPLE_TARGETS
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                               password=MYSQL_PASSWORD, db=MYSQL_DB, connect_timeout=5)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT target FROM targets")
                rows = cur.fetchall()
                targets = [r[0] for r in rows]
                logger.info("Fetched %d targets from MySQL", len(targets))
                return targets
        finally:
            conn.close()
    except Exception as e:
        logger.exception("Could not fetch targets from MySQL — falling back to sample targets")
        return SAMPLE_TARGETS

# --- HTTP check with retries and robust error handling ---
def check_target(target, timeout=10, retries=2, backoff=1.5):
    """
    Returns dict: {'target','url','status'(1/0),'status_code', 'latency_ms', 'error'(optional)}
    """
    # Build URL
    if ':' in target and not target.startswith('http'):
        url = f"http://{target}"
    elif not target.startswith('http'):
        url = f"http://{target}"
    else:
        url = target

    attempt = 0
    start_total = time.time()
    while True:
        attempt += 1
        start = time.time()
        try:
            resp = requests.get(url, timeout=timeout)
            latency_ms = int((time.time() - start_total) * 1000)
            status = 1 if resp.status_code < 400 else 0
            logger.info("Checked %s (attempt %d): status=%s latency=%dms",
                        url, attempt, resp.status_code, latency_ms)
            return {
                'target': target,
                'url': url,
                'status': status,
                'status_code': resp.status_code,
                'latency_ms': latency_ms
            }
        except requests.exceptions.RequestException as e:
            logger.warning("Attempt %d failed for %s: %s", attempt, url, str(e))
            if attempt > retries:
                latency_ms = int((time.time() - start_total) * 1000)
                logger.error("All attempts failed for %s", url)
                return {
                    'target': target,
                    'url': url,
                    'status': 0,
                    'status_code': None,
                    'latency_ms': latency_ms,
                    'error': str(e)
                }
            else:
                sleep_time = backoff ** attempt
                logger.info("Sleeping %.1fs before retrying %s", sleep_time, url)
                time.sleep(min(sleep_time, timeout))

# --- Push metrics to Pushgateway safely ---
def push_metrics(results, job='url_checks'):
    if DEV_MODE:
        logger.info("DEV_MODE: skipping push to Pushgateway")
        return
    try:
        registry = CollectorRegistry()
        g_up = Gauge('url_up', 'Is URL up (1/0)', ['target'], registry=registry)
        g_latency = Gauge('url_latency_ms', 'Latency in ms', ['target'], registry=registry)
        for r in results:
            g_up.labels(target=r['target']).set(r['status'])
            g_latency.labels(target=r['target']).set(r.get('latency_ms', 0) or 0)
        push_to_gateway(PUSHGATEWAY_URL, job=job, registry=registry)
        logger.info("Pushed %d metrics to Pushgateway", len(results))
    except Exception as e:
        logger.exception("Failed to push metrics to Pushgateway: %s", e)

# --- Flask endpoints ---

@app.route('/run-once', methods=['POST'])
def run_once():
    try:
        targets = get_targets()
        results = []
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = {ex.submit(check_target, t): t for t in targets}
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as e:
                    logger.exception("Exception during checking a target: %s", e)
        # Push metrics (best-effort)
        push_metrics(results)
        return jsonify({'count': len(results), 'results': results}), 200
    except Exception as e:
        logger.exception("Unhandled error in /run-once: %s", e)
        return jsonify({'error': 'internal error'}), 500

@app.route('/metrics/latest', methods=['GET'])
def latest_metrics():
    try:
        if DEV_MODE:
            logger.info("DEV_MODE: returning placeholder metrics")
            res = {t: {'up': 0, 'latency_ms': None} for t in SAMPLE_TARGETS}
            return jsonify(res), 200

        def query(q):
            try:
                resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': q}, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                return data.get('data', {}).get('result', [])
            except Exception as e:
                logger.exception("Prometheus query failed for %s: %s", q, e)
                return []

        up = query('url_up')
        latency = query('url_latency_ms')
        res = {}
        for item in up:
            target = item['metric'].get('target')
            try:
                value = int(float(item['value'][1]))
            except Exception:
                value = 0
            res.setdefault(target, {})['up'] = value
        for item in latency:
            target = item['metric'].get('target')
            try:
                value = int(float(item['value'][1]))
            except Exception:
                value = None
            res.setdefault(target, {})['latency_ms'] = value
        return jsonify(res), 200
    except Exception as e:
        logger.exception("Unhandled error in /metrics/latest: %s", e)
        # If Prometheus is down, return 503 to indicate dependency issue
        return jsonify({'error': 'prometheus unavailable'}), 503

@app.route('/health', methods=['GET'])
def health():
    status = {"app": "ok", "db": "unknown", "pushgateway": "unknown", "prometheus": "unknown"}
    # DB
    try:
        if DEV_MODE:
            status['db'] = 'dev-mode'
        else:
            conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                                   password=MYSQL_PASSWORD, db=MYSQL_DB, connect_timeout=3)
            conn.close()
            status['db'] = 'ok'
    except Exception as e:
        logger.warning("Health check DB failed: %s", e)
        status['db'] = 'error'
    # Pushgateway
    try:
        if DEV_MODE:
            status['pushgateway'] = 'dev-mode'
        else:
            resp = requests.get(PUSHGATEWAY_URL, timeout=3)
            status['pushgateway'] = 'ok' if resp.status_code < 400 else f'http:{resp.status_code}'
    except Exception as e:
        logger.warning("Health check Pushgateway failed: %s", e)
        status['pushgateway'] = 'error'
    # Prometheus
    try:
        if DEV_MODE:
            status['prometheus'] = 'dev-mode'
        else:
            resp = requests.get(f"{PROMETHEUS_URL}/api/v1/status/runtimeinfo", timeout=3)
            status['prometheus'] = 'ok' if resp.status_code < 400 else f'http:{resp.status_code}'
    except Exception as e:
        logger.warning("Health check Prometheus failed: %s", e)
        status['prometheus'] = 'error'
    return jsonify(status), 200

@app.route('/', methods=['GET'])
def index():
    return send_from_directory('static', 'index.html')

# --- Global error handler to return JSON instead of HTML ---
@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unhandled exception: %s", error)
    resp = jsonify({'error': 'internal_server_error'})
    resp.status_code = 500
    return resp

# --- Run server ---
if __name__ == '__main__':
    # When running locally in dev mode, Flask debug is okay
    app.run(host='0.0.0.0', port=5000, debug=DEV_MODE)
