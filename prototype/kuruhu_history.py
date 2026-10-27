import re, sqlite3, sys
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlsplit

DB = sys.argv[1]
con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)

STRONG = re.compile(
    r"billing|subscri|payment.?method|payment.?settings|membership|renew|invoice|"
    r"saved.?cards?|manage.?(plan|card)|paid_memberships|primecentral|youraccount|"
    r"/wallet|/plan\b|/plans\b|cancel.?plan|change.?plan|upgrade",
    re.I,
)
GATEWAY = re.compile(
    r"(billing|checkout|invoice)\.stripe\.com|chargebee|paddle\.com|lemonsqueezy|"
    r"razorpay|payu|cashfree|billdesk|ccavenue|payments\.google\.com|pay\.google\.com|"
    r"juspay|paytm|phonepe",
    re.I,
)
SKIP_HOST = re.compile(r"akamai|localhost|127\.0\.0\.1|google\.com/search", re.I)


def t(us):
    return datetime.fromtimestamp(us / 1e6 - 11644473600, timezone.utc).astimezone()


def clean(url):
    s = urlsplit(url)
    frag = "" if re.search(r"token|code|key|secret|session", s.fragment, re.I) else s.fragment
    return s.netloc, s.path[:90] + (("#" + frag[:40]) if frag else "")


rows = con.execute(
    """SELECT u.id, u.url, u.title, u.visit_count, u.last_visit_time,
              (SELECT r.url FROM visits v JOIN visits pv ON pv.id = v.from_visit
                 JOIN urls r ON r.id = pv.url
                WHERE v.url = u.id ORDER BY v.visit_time DESC LIMIT 1) AS ref
         FROM urls u ORDER BY u.last_visit_time DESC"""
).fetchall()

hits = defaultdict(list)
for _id, url, title, n, last, ref in rows:
    host, path = clean(url)
    if SKIP_HOST.search(host):
        continue
    text = path
    kind = "gateway" if GATEWAY.search(host) else ("billing" if STRONG.search(text) else None)
    if not kind:
        continue
    hits[host].append((last, n, path, (title or "")[:70], kind, clean(ref)[0] if ref else ""))

for host, items in sorted(hits.items(), key=lambda kv: -max(i[0] for i in kv[1])):
    items.sort(reverse=True)
    print(f"\n## {host}  (last {t(items[0][0]):%Y-%m-%d %H:%M}, {len(items)} urls)")
    for last, n, path, title, kind, ref in items[:6]:
        r = f"  <- from {ref}" if ref and ref != host else ""
        print(f"  {t(last):%m-%d %H:%M} x{n:<3} [{kind}] {path} | {title}{r}")
