#в планах, test-AI
import os, sys, requests, hashlib, zipfile, tempfile, shutil

MANIFEST_URL = "https://example.com/ts/manifest.json"
RELEASES_DIR = os.path.join(os.path.dirname(__file__), "releases")
CURRENT_FILE = os.path.join(RELEASES_DIR, "current.txt")

def read_current():
    try:
        with open(CURRENT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

def write_current(name):
    os.makedirs(RELEASES_DIR, exist_ok=True)
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        f.write(name)

def check_for_update():
    r = requests.get(MANIFEST_URL, timeout=10)
    r.raise_for_status()
    m = r.json()
    latest_name = m.get("latest")
    if not latest_name:
        return None
    current = read_current()
    if current == latest_name:
        return None
    info = m["releases"].get(latest_name)
    return (latest_name, info) if info else None

def download_and_install(name, info, progress_callback=None):
    url = info["url"]
    expected = info.get("sha256")
    os.makedirs(RELEASES_DIR, exist_ok=True)
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False)
    h = hashlib.sha256()
    try:
        for chunk in r.iter_content(8192):
            if not chunk: continue
            tmp.write(chunk); h.update(chunk)
            if progress_callback:
                progress_callback(len(chunk))
        tmp.close()
        if expected and h.hexdigest() != expected:
            os.remove(tmp.name)
            raise ValueError("sha256 mismatch")
        # ..
        extract_dir = os.path.join(RELEASES_DIR, os.path.splitext(name)[0])
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(tmp.name, 'r') as z:
            z.extractall(extract_dir)
        write_current(name)
        return extract_dir
    finally:
        try: os.remove(tmp.name)
        except Exception: pass