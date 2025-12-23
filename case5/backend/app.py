from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import csv
import os

app = Flask(__name__)
# Enable CORS for all routes (since frontend is on different port/origin in some setups, good for dev)
CORS(app)

# --- Configuration ---
CSV_PATH = os.path.join(os.path.dirname(__file__), 'kodewilayah.csv')
BMKG_API_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

# --- In-Memory Data ---
# Load locations into a list of dicts for simple search
locations = []
try:
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:e.
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                locations.append({
                    "code": row[0].strip(),
                    "name": row[1].strip()
                })
    
    # helper map for O(1) parent lookup
    code_map = {loc['code']: loc['name'] for loc in locations}
    
    print(f"Loaded {len(locations)} locations.")
except Exception as e:
    print(f"Error loading CSV: {e}")

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/locations', methods=['GET'])
def search_locations():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    matches = []
    seen_codes = set()
    
    # First pass: Collect all matches
    # Exclude ADM1 (Prov, 0 dots) and ADM2 (Kota/Kab, 1 dot).
    # Logic: count('.')
    for loc in locations:
        if loc['code'].count('.') >= 2 and query in loc['name'].lower():
            matches.append(loc.copy()) # Copy to avoid mutating global state when modifying name
            
    # Logic:
    # 1. Sort by code length (shorter = higher administrative level, e.g. City vs Village)
    # 2. Sort by "starts with" relevance
    matches.sort(key=lambda x: (len(x['code']), not x['name'].lower().startswith(query)))

    final_results = []
    
    for m in matches:
        if m['code'] in seen_codes:
            continue
            
        # Add Context (Parent ADM2 Name) if it's a sub-region (ADM3/ADM4, length > 5)
        # ADM2 is 5 chars (xx.xx).
        if len(m['code']) > 5:
            adm2_code = m['code'][:5]
            parent_name = code_map.get(adm2_code)
            if parent_name and parent_name.lower() != m['name'].lower():
                # Append parent name for clarity
                m['name'] = f"{m['name']} ({parent_name})"
        
        final_results.append(m)
        seen_codes.add(m['code'])
        
        if len(final_results) >= 20:
             break
    
    return jsonify(final_results)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    # Check if code is ADM2/3 (Aggregate) or ADM4 (Direct).
    # Heuristic: Count dots.
    # ADM2 (xx.xx) = 1 dot
    # ADM3 (xx.xx.xx) = 2 dots
    # ADM4 (xx.xx.xx.xxxx) = 3 dots
    
    if code.count('.') < 3:
        children = [loc for loc in locations if loc['code'].startswith(code + ".") and loc['code'].count('.') == 3]
        
        if not children:
             return jsonify({"error": "No sub-districts found for this code", "code": code}), 404
             
        # Take top 16 to avoid timeouts
        target_children = children[:16]
        
        results = []
        import concurrent.futures
        
        def fetch_one(child):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Docker-Case5-Student-Project)"}
                r = requests.get(f"{BMKG_API_URL}?adm4={child['code']}", headers=headers, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    # Inject name for UI
                    data['location_name'] = child['name'] 
                    return data
            except:
                return None
            return None

        # Increase workers for parallel fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_one, child) for child in target_children]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)
                    
        return jsonify({"multi": True, "results": results, "parent_code": code})

    # Normal ADM4 Fetch
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Docker-Case5-Student-Project)"
        }
        resp = requests.get(f"{BMKG_API_URL}?adm4={code}", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            return jsonify(resp.json())
        else:
            return jsonify({"error": "BMKG API Error", "status": resp.status_code}), resp.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
