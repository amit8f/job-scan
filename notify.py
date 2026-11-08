"""Send new job candidates to Telegram. Usage: python notify.py <new_candidates.json>

Needs the environment variables TELEGRAM_TOKEN and TELEGRAM_CHAT_ID (set as GitHub secrets).
With DRY_RUN=1 it prints the messages instead of sending them.
"""
import json, os, re, sys, html, requests

# Last filter before it reaches your phone: keep titles that look technical. merge.py already dropped
# obvious non-tech roles, this catches the Hebrew and odd titles that slip through.
TECH = re.compile(
    r'software|develop|engineer|data|algorithm|cyber|security|research|backend|back-end|full ?stack|embedded|'
    r'\bAI\b|machine|\bML\b|vision|python|C\+\+|devops|cloud|R&D|firmware|analyst|quant|'
    r'תוכנה|פיתוח|אלגורית|סייבר|דאטה|מפתח|ראייה|ממוחשבת|למידת|בינה|מחקר|אבטחת',
    re.I)
# Which of the five CVs to send, picked from the title. First match wins, backend is the default.
CV_RULES = [
    ('security', re.compile(r'cyber|security|infosec|סייבר|אבטחת', re.I)),
    ('cloud', re.compile(r'devops|cloud|infrastructure|\bSRE\b|platform', re.I)),
    ('systems', re.compile(r'embedded|firmware|C\+\+|low.?level|kernel|GPU|FPGA|driver|simulation|systems|real.?time|סימולצי|משובצ', re.I)),
    ('ai_data', re.compile(r'\bAI\b|machine|\bML\b|learning|data|vision|algorithm|research|quant|analyst|NLP|אלגורית|דאטה|למידת|בינה|ראייה|מחקר', re.I)),
]


def pick_cv(title):
    for name, rx in CV_RULES:
        if rx.search(title or ''):
            return name
    return 'backend'


NOISE = re.compile(r'^\((hidden on HireMe|see posting|telegram[^)]*)\)$', re.I)


# Amit skips roles that ask for a GPA of 85 or more. Text comes from the posting itself when the scan carried it
# (HireMe, Goozali, Workday) and from the public LinkedIn page otherwise. No text means no filtering.
GPA_A = re.compile(r'(?:gpa|grade average|average grade|average score|weighted average|ממוצע|ציון)[^.\n]{0,40}?(\d{2,3})', re.I)
GPA_B = re.compile(r'(\d{2,3})\+?\s*(?:and above|or above|or higher|ומעלה|ויותר)?[^.\n]{0,25}?(?:gpa|average|ממוצע)', re.I)


def gpa_floor(text):
    vals = [int(v) for rx in (GPA_A, GPA_B) for v in rx.findall(text or '') if 60 <= int(v) <= 100]
    return max(vals) if vals else None


def posting_text(j):
    if j.get('desc'):
        return str(j['desc'])
    url = j.get('url') or ''
    if 'linkedin.com/jobs/view' in url:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scan'))
            import lidesc, time
            time.sleep(1.2)
            return lidesc.desc(url).get('desc', '') or ''
        except Exception as e:
            print('description fetch failed', e, file=sys.stderr)
    return ''


def clean(s, n):
    s = ' '.join(html.unescape(str(s or '')).split())
    return html.escape(s[:n])


def line(j):
    company = clean(j.get('company'), 40)
    if NOISE.match(company):
        company = ''
    title = clean(j.get('title'), 100)
    loc = clean(j.get('location'), 40)
    url = html.unescape((j.get('url') or '').strip())
    head = f'<b>{company}</b>: {title}' if company else title
    if loc:
        head += f' ({loc})'
    cv = pick_cv(str(j.get('title') or ''))
    note = f' (GPA {j["gpa_note"]} mentioned)' if j.get('gpa_note') else ''
    return f'{head}\nCV: {cv}{note}\n{html.escape(url)}'


path = sys.argv[1]
cands = json.load(open(path)) if os.path.exists(path) else []
total = len(cands)
cands = [j for j in cands if TECH.search(str(j.get('title') or ''))]
kept = []
for j in cands:
    g = gpa_floor(posting_text(j))
    if g is not None and g >= 85:
        print('dropped, GPA', g, j.get('company'), j.get('title'))
        continue
    if g is not None and g >= 80:
        j['gpa_note'] = g
    kept.append(j)
cands = kept
print(f'{total} new, {len(cands)} look technical and pass the GPA check')
if not cands:
    print('nothing to send')
    sys.exit(0)

token = os.environ.get('TELEGRAM_TOKEN', '')
chat = os.environ.get('TELEGRAM_CHAT_ID', '')
dry = os.environ.get('DRY_RUN') == '1'

# Telegram messages are capped at 4096 characters, so pack several postings per message.
msgs, cur = [], ''
for j in cands:
    entry = line(j) + '\n\n'
    if len(cur) + len(entry) > 3500:
        msgs.append(cur)
        cur = ''
    cur += entry
if cur:
    msgs.append(cur)

head = f'{len(cands)} new student posting' + ('s' if len(cands) != 1 else '') + '\n\n'
msgs[0] = head + msgs[0]

for m in msgs:
    if dry:
        print(m)
        print('-' * 40)
        continue
    r = requests.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data={'chat_id': chat, 'text': m, 'parse_mode': 'HTML', 'disable_web_page_preview': 'true'},
        timeout=30,
    )
    if r.status_code != 200:
        print('telegram error', r.status_code, r.text[:200], file=sys.stderr)
        sys.exit(1)
print('sent', len(cands), 'candidates in', len(msgs), 'messages')
