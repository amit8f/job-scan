"""Send NEW student or intern mentions found by the browser pass to Telegram.
Usage: python browser_notify.py <rendered.json> <scan/rendered_seen.json>
Needs TELEGRAM_TOKEN and TELEGRAM_CHAT_ID. DRY_RUN=1 prints instead of sending.
Only mentions not seen on an earlier run are sent, the seen file is saved only if Telegram accepted them."""
import json, os, sys, html, re, requests

rendered, seen_path = sys.argv[1], sys.argv[2]
R = json.load(open(rendered)) if os.path.exists(rendered) else []
first_run = not os.path.exists(seen_path)
seen = set(json.load(open(seen_path))) if not first_run else set()
NOISE = re.compile(r'student loan|internal|international|interface|internet|intern(al)?ship program for all', re.I)

new, keys = [], []
for r in R:
    hits = [h for h in r.get('hits', []) if not NOISE.search(h)]
    links = [l for l in r.get('links', []) if re.search(r'student|intern|סטודנט', l, re.I)]
    for h in (hits + links)[:3]:
        k = f"{r['company']}|{h[:120]}"
        keys.append(k)
        if k not in seen:
            new.append((r['company'], h, r['url']))
            break  # one line per company is enough
print(f'{len(R)} pages rendered, {len(new)} new mentions')
if first_run:  # old mentions are not news, so the first run only records a baseline
    json.dump(sorted(set(keys)), open(seen_path, 'w'), ensure_ascii=False)
    print('first run: saved', len(keys), 'mentions as the baseline, nothing sent')
    sys.exit(0)
if not new:
    json.dump(sorted(seen | set(keys)), open(seen_path, 'w'), ensure_ascii=False)
    sys.exit(0)

def esc(s, n):
    return html.escape(' '.join(html.unescape(str(s)).split())[:n])

msgs, cur = [], ''
for company, hit, url in new:
    entry = f'<b>{esc(company, 40)}</b>: {esc(hit, 110)}\n{html.escape(url)}\n\n'
    if len(cur) + len(entry) > 3500:
        msgs.append(cur); cur = ''
    cur += entry
if cur:
    msgs.append(cur)
msgs[0] = f'Browser pass: {len(new)} company pages mention students or interns. These are page mentions, not confirmed postings.\n\n' + msgs[0]

token, chat = os.environ.get('TELEGRAM_TOKEN', ''), os.environ.get('TELEGRAM_CHAT_ID', '')
for m in msgs:
    if os.environ.get('DRY_RUN') == '1':
        print(m); print('-' * 40); continue
    resp = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                         data={'chat_id': chat, 'text': m, 'parse_mode': 'HTML', 'disable_web_page_preview': 'true'}, timeout=30)
    if resp.status_code != 200:
        print('telegram error', resp.status_code, resp.text[:200], file=sys.stderr)
        sys.exit(1)
json.dump(sorted(seen | set(keys)), open(seen_path, 'w'), ensure_ascii=False)
print('sent', len(new))
