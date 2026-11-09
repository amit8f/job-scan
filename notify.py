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
# Which of the five CVs to send. Each CV has keywords, a title hit scores 3 and a hit in the posting text scores 1.
# The highest score wins and backend is the default when nothing scores.
CV_WORDS = {
    'backend': r'backend|back-end|\bAPI\b|microservice|\bREST\b|\bJava\b|node\.?js|golang|database|django|flask|full ?stack|server|web',
    'security': r'cyber|security|infosec|penetration|vulnerab|malware|threat|סייבר|אבטחת',
    'cloud': r'devops|cloud|terraform|\bsre\b|infrastructure|observability',
    'systems': r'embedded|firmware|c\+\+|\brtos\b|kernel|linux|driver|\bgpu\b|cuda|fpga|real.?time|simulation|low.?level|networking|packet|סימולצי|משובצ',
    'ai_data': r'machine learning|deep learning|\bAI\b|\bML\b|\bLLM\b|\bNLP\b|computer vision|algorithm|neural|pytorch|tensorflow|data scien|data analy|analytics|\bSQL\b|pandas|quant|ראייה|למידת|בינה|דאטה',
}
CV_RX = {k: re.compile(v, re.I) for k, v in CV_WORDS.items()}


def pick_cv(title, text=''):
    best, score = 'backend', 0
    for name, rx in CV_RX.items():
        sc = (2 if name == 'backend' and re.search(r'software (?:engineer|developer)|developer|full ?stack|backend', title or '', re.I) else 0) + 3 * len(set(m.lower() for m in rx.findall(title or ''))) + len(set(m.lower() for m in rx.findall(text or '')))
        if sc > score:
            best, score = name, sc
    return best


# Amit studies computer science. Roles that need an engineering degree he does not have are dropped when the text says so.
CS_SIGNAL = re.compile(r'computer science|software engineering|computer engineering|information systems|\bCS\b|מדעי המחשב|הנדסת תוכנה|הנדסת מחשבים|מדמ"ח', re.I)
NON_CS_DEGREE = re.compile(r'(?:enrolled|studying|student|degree|pursuing|B\.?Sc\.?|M\.?Sc\.?)[^.\n]{0,40}?(?:electrical|electronic|mechanical|chemical|biomedical|aerospace|aeronautical|materials)\s+engineering|הנדסת (?:חשמל|אלקטרוניקה|מכונות|כימיה|חומרים)', re.I)


def wrong_degree(title, text):
    if re.search(r'electrical|electronic|mechanical|chemical|biomedical|\bRF\b|analog|VLSI', title or '', re.I):
        return True
    if not text:
        return False
    return bool(NON_CS_DEGREE.search(text)) and not CS_SIGNAL.search(text)


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
    cv = pick_cv(str(j.get('title') or ''), j.get('_text', ''))
    note = f' (GPA {j["gpa_note"]} mentioned)' if j.get('gpa_note') else ''
    return f'{head}\nCV: {cv}{note}\n{html.escape(url)}'


path = sys.argv[1]
cands = json.load(open(path)) if os.path.exists(path) else []
total = len(cands)
cands = [j for j in cands if TECH.search(str(j.get('title') or ''))]
kept = []
for j in cands:
    text = posting_text(j)
    j['_text'] = text
    if wrong_degree(str(j.get('title') or ''), text):
        print('dropped, degree is not CS', j.get('company'), j.get('title'))
        continue
    g = gpa_floor(text)
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
