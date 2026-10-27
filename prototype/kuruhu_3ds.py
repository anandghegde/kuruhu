import re, sqlite3, sys
from datetime import datetime
from urllib.parse import urlsplit

con = sqlite3.connect(f"file:{sys.argv[1]}?immutable=1", uri=True)
ACS = re.compile(r"(^|[.\-/])acs\d*([.\-/]|$)|3d_?secure|threedsecure|(^|[.\-/])3ds|cardinalcommerce|wibmo|enstage|securecode|verifiedbyvisa|safekey", re.I)
NOT_ACS = re.compile(r"sso|saml|login|auth|akamai|github|okta|microsoftonline", re.I)
NOISE = re.compile(r"stripe|razorpay|payu|juspay|cashfree|billdesk|ccavenue|paytm|phonepe|google\.|gmail|"
                   r"bank\.in|wibmo|enstage|cardinal|x\.com|twitter|youtube|localhost|127\.0\.0\.1|akamai|webex|microsoft", re.I)
BANKS = ["hdfc", "icici", "sbi", "axis", "kotak", "yes", "idfc", "rbl", "amex", "hsbc", "indusind", "au", "onecard", "sc"]

def ts(v): return datetime.fromtimestamp(v / 1e6 - 11644473600)
rows = [(vt, urlsplit(u).netloc, urlsplit(u).path, t or "") for vt, u, t in con.execute(
    "SELECT v.visit_time, u.url, u.title FROM visits v JOIN urls u ON u.id = v.url ORDER BY v.visit_time")]

seen = set()
for i, (vt, host, path, title) in enumerate(rows):
    if not ACS.search(host + path) or NOT_ACS.search(host) or "stripe" in host and "3d_secure" not in path:
        continue
    bank = next((b.upper() for b in BANKS if re.search(rf"(^|[.\-]){b}", host)), "?")
    gw = merchant = ""
    for pvt, ph, pp, pt in reversed(rows[max(0, i - 200):i]):
        if vt - pvt > 15 * 60e6: break
        if not gw and re.search(r"stripe|razorpay|payu|juspay|cashfree|billdesk|ccavenue|paytm", ph): gw = ph
        if not NOISE.search(ph) and ph: merchant = f"{ph} | {pt[:40]}"; break
    key = (ts(vt).strftime("%Y-%m-%d %H:%M"), merchant)
    if key in seen: continue
    seen.add(key)
    print(f"{key[0]}  bank={bank:<6} acs={host[:38]:<38} gw={gw[:18]:<18} merchant={merchant or '?'}")
