#!/usr/bin/env python3
"""eZeus Asset Studio — oyun mekanikleri referansı + Nano Banana Pro asset üretimi.

Tek sayfa yerel web uygulaması:
  * /api/mechanics  — eZeus kaynak kodundan çıkarılan mekanik envanteri
  * /api/assets     — oyun dizinindeki asset türleri envanteri
  * /api/generate   — Nano Banana Pro (Gemini image) ile asset üretimi
  * /api/gallery    — üretilen asset galerisi

Çalıştır: python3 server.py   (http://localhost:8765)
API anahtarı ~/Keys/.env.master içinden okunur (GOOGLE_GEMINI_API_KEY).
"""
import base64
import json
import os
import re
import time
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GAME_DIR = os.path.expanduser('~/Games/Zeus and Poseidon')
GENERATED = os.path.join(HERE, 'generated')
os.makedirs(GENERATED, exist_ok=True)

# Nano Banana Pro tercih sırası; ilk bulunan kullanılır.
IMAGE_MODEL_PREFERENCE = [
    'gemini-3-pro-image',
    'nano-banana-pro',
    'gemini-3-pro-image-preview',
    'gemini-2.5-flash-image',
]


KEY_NAMES = ['GOOGLE_GEMINI_API_KEY', 'GOOGLE_GEMINI_KEY',
             'GOOGLE_AI_UTILITIES_KEY', 'GOOGLE_API_KEY',
             'REPLICATE_API_TOKEN']

# Nano Banana Pro on Replicate — a paid account, unlike the Gemini free
# tier whose image quota is zero.
REPLICATE_MODEL = 'google/nano-banana-pro'


def env_values():
    path = os.path.expanduser('~/Keys/.env.master')
    found = {}
    with open(path) as f:
        for line in f:
            m = re.match(r'^([A-Z_]+)=(.+)$', line.strip())
            if m and m.group(1) in KEY_NAMES:
                found[m.group(1)] = m.group(2)
    return found


def api_keys():
    """Kota aşımına karşı sırayla denenecek Gemini anahtarları."""
    found = env_values()
    keys = []
    for name in KEY_NAMES:
        if name == 'REPLICATE_API_TOKEN':
            continue
        v = found.get(name)
        if v and v not in keys:
            keys.append(v)
    return keys


# --- Mekanik çıkarımı -------------------------------------------------------

ENUMS = {
    'Binalar': ('buildings/ebuilding.h', 'eBuildingType'),
    'Kaynaklar': ('engine/eresourcetype.h', 'eResourceType'),
    'Tanrılar': ('characters/gods/egodtype.h', 'eGodType'),
    'Araziler': ('engine/eterrain.h', 'eTerrain'),
    'Karakterler': ('characters/echaracterbase.h', 'eCharacterType'),
    'Canavarlar': ('characters/monsters/emonstertype.h', 'eMonsterType'),
    'Kahramanlar': ('characters/heroes/ehero.h', 'eHeroType'),
}


def parse_enum(path, name):
    with open(os.path.join(REPO, path)) as f:
        src = f.read()
    m = re.search(r'enum class %s\b[^{]*\{(.*?)\};' % re.escape(name),
                  src, re.S)
    if not m:
        return []
    # Yorumları bölmeden ÖNCE soy — yorum içindeki virgüller üyeleri bozar.
    body = re.sub(r'//.*', '', m.group(1))
    members = []
    for raw in body.split(','):
        raw = re.sub(r'=.*', '', raw).strip()
        if raw and re.match(r'^\w+$', raw):
            members.append(raw)
    return members


def mechanics():
    cats = {}
    for title, (path, name) in ENUMS.items():
        try:
            members = parse_enum(path, name)
        except OSError:
            members = []
        cats[title] = {'count': len(members), 'items': members}
    cats['Hız Seviyeleri'] = {
        'count': 8,
        'items': ['2', '10', '25', '50', '100',
                  '100 ×5 (turbo)', '100 ×10 (turbo)', '100 ×20 (turbo)'],
    }
    return cats


# --- Asset envanteri --------------------------------------------------------

def scan(root, exts=None):
    out = []
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            if exts is None or os.path.splitext(name)[1].lower() in exts:
                out.append({'name': name,
                            'sizeMB': round(os.path.getsize(p)/1048576, 1)})
    return out


def assets():
    ez = os.path.join(GAME_DIR, 'eZeus')
    return {
        'Sprite paketleri (orijinal .sg3/.555)':
            scan(os.path.join(GAME_DIR, 'DATA'), {'.sg3', '.555'}),
        'eZeus arayüz dokuları (.e)': scan(ez, {'.e'}),
        'Sesler (Audio)': [{'name': d, 'sizeMB': ''}
                           for d in sorted(os.listdir(os.path.join(GAME_DIR, 'Audio')))
                           ][:20] if os.path.isdir(os.path.join(GAME_DIR, 'Audio')) else [],
        'Maceralar (Adventures)':
            [{'name': d, 'sizeMB': ''}
             for d in sorted(os.listdir(os.path.join(ez, 'Adventures')))
             ] if os.path.isdir(os.path.join(ez, 'Adventures')) else [],
        'Fontlar': scan(os.path.join(ez, 'Fonts'), {'.ttf'}),
        'Metinler': scan(ez, {'.xml'}),
    }


# --- Nano Banana Pro --------------------------------------------------------

def pick_model(key):
    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=1000'
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    names = [m['name'].split('/')[-1] for m in data.get('models', [])]
    for want in IMAGE_MODEL_PREFERENCE:
        for name in names:
            if name == want or name.startswith(want):
                return name
    for name in names:  # son çare: adında image geçen ilk model
        if 'image' in name:
            return name
    raise RuntimeError('Görüntü üretebilen Gemini modeli bulunamadı')


def save_png(raw):
    fname = f'asset-{int(time.time())}.png'
    with open(os.path.join(GENERATED, fname), 'wb') as f:
        f.write(raw)
    return fname


def generate_replicate(prompt):
    """Nano Banana Pro via Replicate (paid, so it actually has quota)."""
    token = env_values().get('REPLICATE_API_TOKEN')
    if not token:
        raise RuntimeError('REPLICATE_API_TOKEN yok')
    req = urllib.request.Request(
        f'https://api.replicate.com/v1/models/{REPLICATE_MODEL}/predictions',
        data=json.dumps({'input': {'prompt': prompt}}).encode(),
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json',
                 # Block until the prediction finishes instead of polling.
                 'Prefer': 'wait=60'})
    with urllib.request.urlopen(req, timeout=180) as r:
        pred = json.load(r)

    # 'Prefer: wait' may still return early for slow generations.
    for _ in range(60):
        if pred.get('status') in ('succeeded', 'failed', 'canceled'):
            break
        time.sleep(3)
        poll = urllib.request.Request(
            pred['urls']['get'], headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(poll, timeout=60) as r:
            pred = json.load(r)

    if pred.get('status') != 'succeeded':
        raise RuntimeError(f"Replicate {pred.get('status')}: "
                           f"{pred.get('error')}")
    out = pred.get('output')
    url = out[0] if isinstance(out, list) else out
    with urllib.request.urlopen(url, timeout=120) as r:
        return {'file': save_png(r.read()), 'model': REPLICATE_MODEL}


def generate_image(prompt):
    data = None
    last_err = None
    for key in api_keys():
        try:
            model = pick_model(key)
            url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
                   f'{model}:generateContent?key={key}')
            body = json.dumps({
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
            }).encode()
            req = urllib.request.Request(
                url, data=body, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (401, 403, 429):
                continue  # sıradaki anahtarı dene
            raise
    if data is None:
        # Every Gemini key is out of quota — fall back to Replicate.
        try:
            return generate_replicate(prompt)
        except Exception as e:  # noqa: BLE001 — reported to the UI
            raise RuntimeError(f'Gemini: {last_err} | Replicate: {e}')
    for cand in data.get('candidates', []):
        for part in cand.get('content', {}).get('parts', []):
            inline = part.get('inlineData') or part.get('inline_data')
            if inline and inline.get('data'):
                return {'file': save_png(base64.b64decode(inline['data'])),
                        'model': model}
    raise RuntimeError('Modelden görüntü dönmedi: %s' %
                       json.dumps(data)[:400])


# --- HTTP -------------------------------------------------------------------

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, *args):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/mechanics':
            self.send_json(mechanics())
        elif self.path == '/api/assets':
            self.send_json(assets())
        elif self.path == '/api/gallery':
            files = sorted(os.listdir(GENERATED), reverse=True)
            self.send_json([f for f in files if f.endswith('.png')])
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/generate':
            self.send_json({'error': 'bilinmeyen uç'}, 404)
            return
        length = int(self.headers.get('Content-Length', 0))
        try:
            payload = json.loads(self.rfile.read(length))
            result = generate_image(payload['prompt'])
            self.send_json(result)
        except Exception as e:  # noqa: BLE001 — hata mesajı UI'da gösterilir
            self.send_json({'error': str(e)}, 500)


if __name__ == '__main__':
    print(f'eZeus Asset Studio: http://localhost:{PORT}')
    HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
