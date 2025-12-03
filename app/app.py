from flask import Flask, jsonify, send_from_directory
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymysql
import requests
import time
import logging
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, PUSHGATEWAY_URL, PROMETHEUS_URL

app = Flask(__name__, static_folder='static', static_url_path='/')
logging.basicConfig(level=logging.INFO)

def get_targets():
    conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT target FROM targets")
            rows = cur.fetchall()
            return [r[0] for r in rows]
    finally:
        conn.close()

def check_target(target, timeout=10):
    url = target
    if ':' in target and not target.startswith('http'):
        # If it's host:port, try http
        url = f"http://{target}"
    elif not target.startswith('http'):
        url = f"http://{target}"
    start = time.time()
    try:
        resp = requests.get(url, timeout=timeout)
        latency_ms = int((time.time() - start) * 1000)
        status = 1 if resp.status_code < 400 else 0
        logging.info(f"Checked {url}: status={resp.status_code} latency={latency_ms}ms")
        return {'target': target, 'url': url, 'status': status, 'status_code': resp.status_code, 'latency_ms': latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        logging.warning(f"Check failed for {url}: {e}")
        return {'target': target, 'url': url, 'status': 0, 'status_code': None, 'latency_ms': latency_ms, 'error': str(e)}

def push_metrics(results, job='url_checks'):
    registry = CollectorRegistry()
    g_up = Gauge('url_up', 'Is URL up (1/0)', ['target'], registry=registry)
    g_latency = Gauge('url_latency_ms', 'Latency in ms', ['target'], registry=registry)
    for r in results:
        g_up.labels(target=r['target']).set(r['status'])
        g_latency.labels(target=r['target']).set(r['latency_ms'] if r.get('latency_ms') is not None else 0)
    push_to_gateway(PUSHGATEWAY_URL, job=job, registry=registry)

@app.route('/run-once', methods=['POST'])
def run_once():
    targets = get_targets()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(check_target, t): t for t in targets}
        for fut in as_completed(futures):
            results.append(fut.result())
    push_metrics(results)
    return jsonify({'count': len(results), 'results': results})

@app.route('/metrics/latest', methods=['GET'])
def latest_metrics():
    # Query prometheus for up and latency for all targets
    # Returns simplified JSON
    q_up = 'url_up'
    q_latency = 'url_latency_ms'
    def query(q):
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': q}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('data', {}).get('result', [])
    up = query(q_up)
    latency = query(q_latency)
    # Build map
    res = {}
    for item in up:
        target = item['metric'].get('target')
        value = int(float(item['value'][1]))
        res.setdefault(target, {})['up'] = value
    for item in latency:
        target = item['metric'].get('target')
        value = int(float(item['value'][1]))
        res.setdefault(target, {})['latency_ms'] = value
    return jsonify(res)

@app.route('/', methods=['GET'])
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
