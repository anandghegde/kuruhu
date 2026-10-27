import sqlite3, sys
from datetime import datetime
from urllib.parse import urlsplit

con = sqlite3.connect(f"file:{sys.argv[1]}?immutable=1", uri=True)
def chrome(ts): return int((datetime.fromisoformat(ts).timestamp() + 11644473600) * 1e6)
for win in sys.argv[2:]:
    a, b = win.split("/")
    print(f"\n=== {a} -> {b}")
    q = """SELECT v.visit_time, u.url, u.title, v.from_visit, v.opener_visit, v.transition & 0xff
             FROM visits v JOIN urls u ON u.id = v.url
            WHERE v.visit_time BETWEEN ? AND ? ORDER BY v.visit_time"""
    for vt, url, title, frm, opener, tr in con.execute(q, (chrome(a), chrome(b))):
        s = urlsplit(url)
        when = datetime.fromtimestamp(vt / 1e6 - 11644473600)
        print(f"  {when:%H:%M:%S} t{tr:<2} {s.netloc}{s.path[:60]} | {(title or '')[:50]}" + (" [new-tab]" if opener else ""))
