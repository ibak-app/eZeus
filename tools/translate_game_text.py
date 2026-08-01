#!/usr/bin/env python3
"""Translate the game's own text (Zeus_Text.xml / Zeus_MM.xml) to Turkish.

The strings are translated in batches through Gemini, with the game's
vocabulary pinned by a glossary so building and god names stay consistent
across the 8000+ entries. Progress is checkpointed, so the script can be
re-run after an interruption and picks up where it stopped.

Usage: translate_game_text.py <in.xml> <out.xml> [cache.json]
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

MODEL = 'gemini-2.5-flash'
BATCH = 40
KEY_NAMES = ['GOOGLE_GEMINI_API_KEY', 'GOOGLE_GEMINI_KEY',
             'GOOGLE_AI_UTILITIES_KEY', 'GOOGLE_API_KEY']

GLOSSARY = """
sanctuary=tapınak, temple=tapınak, shrine=sunak, agora=agora,
housing=konut, elite housing=seçkin konut, common housing=sıradan konut,
granary=tahıl ambarı, warehouse=depo, storage yard=depo avlusu,
foundry=dökümhane, workshop=atölye, quarry=taş ocağı, mine=maden,
farm=çiftlik, orchard=meyve bahçesi, vineyard=bağ, olive=zeytin,
wine=şarap, marble=mermer, bronze=tunç, silver=gümüş, fleece=yapağı,
armor=zırh, chariot=savaş arabası, horse=at, sculpture=heykel,
walker=gezgin, hoplite=hoplit, colony=koloni, parent city=ana şehir,
drachma=drahmi, tribute=haraç, appeal=çekicilik, hygiene=hijyen,
unrest=huzursuzluk, philosopher=filozof, gymnasium=gymnasion,
podium=kürsü, palace=saray, maintenance=bakım, culture=kültür,
Zeus=Zeus, Poseidon=Poseidon, Athena=Athena, Hades=Hades, Ares=Ares,
Apollo=Apollon, Artemis=Artemis, Demeter=Demeter, Hera=Hera,
Hermes=Hermes, Aphrodite=Afrodit, Dionysus=Dionysos, Atlas=Atlas,
Hephaestus=Hephaistos
""".strip().replace('\n', ' ')

PROMPT = """You are localizing the 2000 city-building game "Zeus: Master of \
Olympus" into Turkish for Turkish players.

Rules:
- Translate naturally, as a professional game localizer would. Keep the \
mythological, slightly formal tone of the original.
- Keep these EXACTLY as they appear: placeholders (%1, %2, %s, %d), line \
breaks, leading/trailing spaces, punctuation style, and any markup.
- Keep proper names of gods/heroes/cities in their established Turkish \
spelling.
- UI labels must stay SHORT — never longer than the English label.
- If a string is a single word that is already a proper name or a number, \
return it unchanged.
- Use this glossary for consistency: {glossary}

Return ONLY a JSON array of translated strings, in the same order and with \
the same length as the input array. No commentary.

Input:
{payload}"""


def api_keys():
    path = os.path.expanduser('~/Keys/.env.master')
    found = {}
    with open(path) as f:
        for line in f:
            m = re.match(r'^([A-Z_]+)=(.+)$', line.strip())
            if m and m.group(1) in KEY_NAMES:
                found[m.group(1)] = m.group(2)
    keys = []
    for n in KEY_NAMES:
        v = found.get(n)
        if v and v not in keys:
            keys.append(v)
    return keys


KEYS = api_keys()
key_index = 0


def call_gemini(prompt):
    """Try each key in turn; rotate on quota errors."""
    global key_index
    for _ in range(len(KEYS)):
        key = KEYS[key_index]
        req = urllib.request.Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/'
            f'{MODEL}:generateContent?key={key}',
            data=json.dumps({
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.3,
                                     'responseMimeType': 'application/json'},
            }).encode(),
            headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            return data['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            if e.code in (429, 403, 401):
                key_index = (key_index + 1) % len(KEYS)
                time.sleep(2)
                continue
            raise
    raise RuntimeError('tüm anahtarlar kota dışı')


def translate_batch(texts):
    prompt = PROMPT.format(glossary=GLOSSARY,
                           payload=json.dumps(texts, ensure_ascii=False))
    for attempt in range(4):
        try:
            out = json.loads(call_gemini(prompt))
            if isinstance(out, list) and len(out) == len(texts):
                return [str(x) for x in out]
        except Exception as e:  # noqa: BLE001 — retried below
            if attempt == 3:
                print('  ! batch başarısız, İngilizce kalıyor:', e)
        time.sleep(2 + attempt*3)
    return texts


def main(src, dst, cache_path=None):
    cache_path = cache_path or dst + '.cache.json'
    raw = open(src, encoding='utf-8').read()

    # Collect the unique translatable strings.
    pattern = re.compile(r'(<string id="\d+">)(.*?)(</string>)', re.S)
    uniq = []
    seen = set()
    for _, body, _ in pattern.findall(raw):
        text = html.unescape(body)
        if not text.strip() or text.strip().isdigit():
            continue
        if text not in seen:
            seen.add(text)
            uniq.append(text)

    cache = {}
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path, encoding='utf-8'))
    todo = [t for t in uniq if t not in cache]
    print(f'{len(uniq)} benzersiz metin, {len(todo)} çevrilecek')

    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        cache.update(zip(chunk, translate_batch(chunk)))
        json.dump(cache, open(cache_path, 'w', encoding='utf-8'),
                  ensure_ascii=False)
        done = min(i + BATCH, len(todo))
        print(f'  {done}/{len(todo)}  ({100*done//max(len(todo), 1)}%)',
              flush=True)

    def replace(m):
        head, body, tail = m.groups()
        text = html.unescape(body)
        out = cache.get(text, text)
        return head + html.escape(out, quote=False) + tail

    open(dst, 'w', encoding='utf-8').write(pattern.sub(replace, raw))
    print('yazıldı:', dst)


if __name__ == '__main__':
    main(*sys.argv[1:])
