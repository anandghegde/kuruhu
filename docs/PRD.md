# Kuruhu — Product Requirements Document

| | |
|---|---|
| Status | Draft v0.3. Command-line tool; open questions answered 2026-10-27 (§13) |
| Date | 2026-10-27 |
| Author | Anand Hegde |
| Product | **Kuruhu – Card Trail**, a command-line tool for macOS, for my own use |
| Tagline | *Every card leaves a trace.* |
| Name | ಕುರುಹು (*kuruhu*) means a trace, a mark or a clue: what a card leaves behind on every site it's typed into. Kuruhu follows those traces back |

---

## 1. Summary

`kuruhu` keeps one ledger of every site that can take my money again without asking: where my credit card was charged or saved, which UPI AutoPay mandates I've set up, and which of them will charge next and when. It warns me a few days before a renewal.

It builds the ledger from two sources, both read on my machine and both opened read-only:

1. **Browser history.** Bank OTP pages, payment gateway pages and billing portals, each matched to the site I was on. The prototype (Appendix A) found a site I had forgotten from history alone.
2. **Email, optional.** HDFC's alerts for card charges and UPI debits, UPI AutoPay mandate emails, pre-debit notices, and merchant receipts. Card alerts name the last 4 digits. Kuruhu reads them over IMAP and matches them to history by time.

A daily background job (`launchd`) runs both and sends a macOS notification before each renewal. Everything else is a command in the terminal: `kuruhu list`, `kuruhu due`, `kuruhu at "21 Oct 21:18"`.

Kuruhu never sees a card number. It doesn't touch web pages or forms at all, so it can't leak one.

## 2. Goals and non-goals

### Goals
- G1. Answer "which sites have my card?" for each of my cards, and "which UPI AutoPay mandates are active?", with the evidence for every entry.
- G2. Answer "who will charge it next, how much, and when?", and warn me before it happens.
- G3. When a card is replaced, lost or blocked, give me the list of sites to update, each with a link to its billing page.
- G4. Work with Indian cards and Indian payment flows: HDFC, RuPay, Razorpay, PayU, Juspay, RBI e-mandates on cards, UPI AutoPay, and their pre-debit notices.
- G5. Be safe by construction: no access to pages or forms, and the browser's files and my mailbox opened read-only.

### Non-goals (v1)
- Changing, cancelling or paying anything. Kuruhu only reads and reminds.
- Capturing checkouts or reading billing pages as I browse. That needs a Chrome extension, which is an optional later add-on (§6.9).
- One-off UPI, net banking and wallet payments. Kuruhu tracks cards and UPI AutoPay mandates (§6.5), the payments that repeat.
- Importing bank or card statements, and storing card expiry dates (both decided against, §13).
- App Store, Play Store, phone and in-store charges.
- Reading Chrome's saved cards. Chrome's local database has no site column for them (Appendix A).
- Safari (its history needs Full Disk Access), Windows and Linux. macOS only: Kuruhu uses Keychain and `launchd`.
- Sync, accounts or a server.

## 3. Users and jobs to be done

| User | Job |
|---|---|
| Me, with a few HDFC cards | "I saw my card saved on some billing page last week and it's going to renew. Which site was it?" |
| Me, getting a new card | "My card is being replaced. Which sites do I update before the next renewal fails?" |
| Me, trying things | "I sign up for trials and AI tools all the time. Tell me before any of them charge me again." |
| Me, looking at a charge I don't recognise | "What is PAYU\*XYZ? Which site was I on when it went through?" |
| Me, with UPI AutoPay on a few apps | "Which mandates are still active, and which one takes money next?" |

## 4. Competitive position

| Product | What it does | Gap Kuruhu fills |
|---|---|---|
| Chrome's saved cards (`chrome://settings/payments`) | Fills cards into forms | Doesn't say where a card was used or saved |
| My bank's app, SMS and statements | Every charge, with a merchant descriptor | Descriptors are cryptic (PAYU\*, RAZ\*); no "saved at" list (HDFC's app has none); the only warning is the pre-debit notice a day before |
| UPI apps' AutoPay screens (Google Pay, PhonePe …) | Each lists the mandates made through it | One app at a time, and nothing alongside the cards |
| SMS expense trackers (e.g. Axio) | Categorise spends from bank SMS | Know charges, not which sites hold the card or when they renew |
| Each merchant's billing page | Shows its own saved card and renewal date | One site at a time, and I have to remember the site |

What sets Kuruhu apart: one list across every site, grouped by card, with the evidence and a link to each billing page, built from history and email I already have.

## 5. Product principles

1. **Never see a card number.** Kuruhu reads browser history and email, never pages or forms. From an email it keeps the last 4 digits; any other run of digits in a stored snippet is masked.
2. **Show the evidence.** Every ledger entry lists what it was inferred from (an OTP page, a billing portal, an email), with the time and the URL. Guesses are labelled as guesses (`~2026-11-12`).
3. **I confirm; Kuruhu doesn't assume.** History and email produce candidates. I confirm, dismiss or mark them cancelled, and Kuruhu remembers my choice.
4. **Read only.** Browser files are opened with SQLite's `immutable=1`. The mailbox is opened read-only, so messages are never marked as read. Kuruhu never pays, cancels or changes anything.
5. **Local and quiet.** No analytics, no telemetry. The only network connection is IMAP to `imap.gmail.com`, and only once I've set up mail.

## 6. Functional requirements

Priority: **P0** = v1.0, **P1** = v1.1, **P2** = later.

### 6.1 Command line (CLI)

```
kuruhu                          same as `kuruhu list`
kuruhu sync                     scan + mail + reminders (what the daily job runs)
kuruhu scan [--since DATE] [--browser chrome|arc|brave|edge|all]
kuruhu mail login EMAIL         store a Gmail app password in Keychain
kuruhu mail [--account EMAIL] [--since DATE]
kuruhu list [--via 1234|hdfc|upi] [--state saved|charged|recurring|mandate] [--unconfirmed] [--json]
kuruhu due [--days 30] [--json]
kuruhu show MERCHANT            every piece of evidence for one merchant
kuruhu at TIME [--window 15m]   what I was doing around TIME (e.g. an unknown charge)
kuruhu confirm|dismiss|cancel MERCHANT [--via 1234|upi]
kuruhu set MERCHANT [--renews DATE] [--amount 1600] [--every month|year] [--via 1234|upi]
kuruhu methods                  cards and UPI accounts, with nicknames
kuruhu name 1234 "HDFC Millennia"
kuruhu replace 1234 [--to 5678] card-replaced checklist
kuruhu report [--open]          HTML report
kuruhu export --csv|--json
kuruhu agent install|uninstall|status
kuruhu doctor                   check sources, Keychain, the agent, and the ledger's safety
kuruhu wipe
```

Example (merchant names changed):

```
$ kuruhu list
HDFC ••••?   bank from OTP pages, last 4 unknown until mail is set up
  MERCHANT     STATE              RENEWS        LAST SEEN          EVIDENCE
  design.example saved             ?             2026-10-21 21:18   Stripe billing portal  ✓ confirmed
  aichat.example charged            ~2026-11-12   2026-10-12 15:00   HDFC OTP page
  music.example  charged            ?             2026-09-23 23:03   HDFC OTP page (Adyen)
  …
3 unconfirmed · run `kuruhu show <merchant>` for evidence
```

| ID | Requirement | Pri |
|---|---|---|
| CLI-1 | The commands above, built with `argparse`. `kuruhu` with no arguments runs `list`. | P0 except `report`, `export`, `replace` (P1) |
| CLI-2 | Tables use colour only on a TTY and respect `NO_COLOR`. Every list-style command takes `--json`. | P0 |
| CLI-3 | Merchants can be named by domain or display name, with prefix matching (`kuruhu show des`). An ambiguous name lists the matches and exits with code 2. | P0 |
| CLI-4 | Times accept `2026-10-21 21:18`, `21 Oct 21:18`, `yesterday 14:30`, in local time. | P0 |
| CLI-5 | Exit codes: 0 ok, 1 error, 2 bad input, 3 a source is unreadable (shown by `doctor`). | P0 |

### 6.2 Ledger (LED)

The ledger holds:
- **Payment methods:** a card (brand, last 4, bank from the OTP page's host or an email) or a UPI account (bank, account last 4 from the debit alert), each with a nickname I give it. History often knows the bank but not the last 4; such a card shows as "HDFC ••••?" until an email fills it in.
- **Merchants:** registrable domain (`design.example`), display name, the billing page URL if Kuruhu has seen one, and aliases (bank descriptors, UPI payee names and VPAs).
- **Links** (payment method × merchant): states `saved`, `charged`, `recurring` and, for UPI, `mandate`, plus `renews_on`, `amount`, `cadence` and the evidence list. My overrides: `confirmed`, `dismissed`, `cancelled`, and anything I `set`.

| ID | Requirement | Pri |
|---|---|---|
| LED-1 | `list` groups by payment method and sorts merchants by next renewal, then by last seen. Each row shows the merchant, states, renewal date, last seen, the latest evidence and whether I've confirmed it. | P0 |
| LED-2 | `show` prints every evidence item: source (history, mail, me), time, URL without query string or fragment, page or mail title, and the rule that matched. It ends with the billing page link. | P0 |
| LED-3 | `confirm`, `dismiss` and `cancel`. Dismissed and cancelled links stay in the ledger, so a rescan doesn't add them back. `cancel` stops reminders. | P0 |
| LED-4 | Merchant names come from the billing portal's title ("Acme AI Billing" → Acme AI), then the page title's site part, then the domain. | P0 |
| LED-5 | `due` lists renewals in the next N days (default 30), estimates marked `~`. | P0 |
| LED-6 | `replace 1234` prints the checklist of merchants on that card with their billing links. `--to 5678` moves the links I tick to the new card. | P1 |
| LED-7 | `export` as CSV or JSON. `report` writes one self-contained HTML file (no external assets) to `~/.kuruhu/report.html`. | P1 |

### 6.3 History scan (HIS)

Proven by the prototype on 2026-10-27 (Appendix A).

| ID | Requirement | Pri |
|---|---|---|
| HIS-1 | Read every Chrome profile's `History` file (`~/Library/Application Support/Google/Chrome/*/History`) with `immutable=1`. Incremental: remember the last visit time read for each profile. | P0 |
| HIS-2 | **Charge signals:** visits to bank 3-D Secure (OTP) pages and to gateway 3DS endpoints. Bank pages are hosts under `bank.in` with an `acs` label or path (e.g. `securehdfc-acs2ui-…hdfc.bank.in/v1/acs/…`). Also a host list for ACS providers (Wibmo/Enstage, CardinalCommerce) and gateway endpoints (`hooks.stripe.com/3d_secure*`, `secure.payu.in/*/threeDSecure`, Adyen `threeDS`). Every host and path rule lives in one file (`kuruhu/rules/hosts.py`). | P0 |
| HIS-3 | The bank is the label under `bank.in` in the OTP page's host (`hdfc.bank.in` → HDFC). Signals from a gateway alone leave the bank unknown. | P0 |
| HIS-4 | The merchant is the last top-level page before the charge signal, within 15 minutes, skipping gateway, bank, mail, search and sign-in hosts. When a gateway checkout's title names the merchant (Razorpay "Acme Premium", Stripe "Acme Software, Inc."), that name is used. | P0 |
| HIS-5 | **Saved-card signals:** visits to billing portals (`billing.stripe.com/p/session*`, Chargebee and Razorpay subscription portals) and to billing paths on a merchant's own site (`/billing`, `/settings/billing*`, `/subscription`, `#settings/Billing`). A portal visit within 2 minutes of a merchant's billing page belongs to that merchant (19 seconds apart in the prototype). The merchant's billing page URL is saved for its links. | P0 |
| HIS-6 | **Success signals:** a purchase-success page right after a charge signal (`/purchase/success`, `/thank-you`, PayU's "Payment Successful") confirms the charge. | P1 |
| HIS-7 | **Exclusions:** SAML and SSO endpoints (their `acs` is a false positive), classifieds and search pages, a list of corporate hosts in the config (default: `akamai.com`), and sites that only talk about subscriptions (reddit, x.com, news). Those content hosts can only match by a billing portal or a charge signal, never by words in the path. | P0 |
| HIS-8 | Everything found in history starts unconfirmed (principle 3). | P0 |
| HIS-9 | Kuruhu keeps the visits from 15 minutes before to 2 minutes after each signal, so the evidence outlives Chrome's ~90 days. It doesn't copy the rest of my browsing history. | P0 |
| HIS-10 | `at TIME` prints the visit timeline around TIME, from Chrome's history and the kept windows: time, transition type, a new-tab marker, host and path, title (the prototype's `kuruhu_timeline.py`). | P0 |
| HIS-11 | Arc, Brave and Edge, which use the same Chromium `History` format. | P1 |
| HIS-12 | **UPI AutoPay set-up signals:** gateway checkout pages whose path or title mentions UPI AutoPay, a mandate or a subscription. The approval happens in the UPI app on my phone, so history only shows the checkout; this makes a `mandate` candidate that mail confirms (§6.5). | P1 |

### 6.4 Email (MAIL)

| ID | Requirement | Pri |
|---|---|---|
| MAIL-1 | `mail login EMAIL` stores a Gmail app password in the macOS Keychain (`security add-generic-password -s kuruhu -a EMAIL`), never in a file. Kuruhu connects to `imap.gmail.com:993` over TLS and opens folders read-only. | P1 |
| MAIL-2 | Kuruhu fetches only the messages its queries match, using Gmail's `X-GM-RAW` IMAP search (e.g. `from:<HDFC alert sender> newer_than:90d`), never the whole mailbox. Incremental by the last UID read. | P1 |
| MAIL-3 | HDFC transaction alerts: parse the amount, last 4, merchant descriptor and time. The sender and formats are confirmed in M0 from my inbox, and the parsers have fixture tests. | P1 |
| MAIL-4 | **Pre-debit notices** for card standing instructions. RBI's e-mandate rules make the bank notify me at least 24 hours before each recurring debit. Parse merchant, amount and date → `recurring` with `renews_on`. | P1 |
| MAIL-5 | Merchant receipts and renewal notices ("Visa ending in 1234", "your subscription renews on …"). | P1 |
| MAIL-6 | **Time join:** an alert within ±10 minutes of a charge signal from history links the alert's last 4 to that merchant, and saves the bank's descriptor as an alias (`PAYU*…` → `shop.example.in`). | P1 |
| MAIL-7 | **Cadence:** two or more charges from one merchant on one card at a steady interval (monthly or yearly, ±3 days) mark the link `recurring`, with the next date shown as an estimate. | P1 |
| MAIL-8 | A second Gmail account, for receipts only (some merchants' receipts go to a different address than the bank's alerts). | P2 |
| MAIL-9 | Message bodies are parsed in memory and dropped. Kuruhu stores the parsed fields, the subject, the date, the Message-ID and a masked snippet of at most 120 characters. | P1 |

### 6.5 UPI AutoPay (UPI)

UPI AutoPay mandates are approved in a UPI app on my phone, so they leave little in the browser. Kuruhu tracks them from mail. One-off UPI payments are out of scope.

| ID | Requirement | Pri |
|---|---|---|
| UPI-1 | **Mandate created:** the bank's or merchant's email when an AutoPay mandate is set up (merchant, limit, frequency, start date) → a `mandate` link on the UPI account. | P1 |
| UPI-2 | **Mandate debits:** HDFC's UPI debit alerts (amount, account last 4, payee name or VPA, time). A debit to a payee with a mandate is a renewal, and the interval between debits gives the cadence (MAIL-7). | P1 |
| UPI-3 | **Pre-debit notices:** NPCI requires one at least 24 hours before each AutoPay debit. When it arrives by email, parse merchant, amount and date → `renews_on`. When it only goes to SMS or the UPI app, Kuruhu estimates the date from the cadence and marks it `~`. | P1 |
| UPI-4 | **Merchant names:** payee VPAs and names map to merchants through an alias table in `rules/` (gateway VPAs like `razorpay.*@…` resolved by the time join with history, MAIL-6). | P1 |
| UPI-5 | **Mandate ended:** paused, revoked or expired mandate emails → `cancelled`, and reminders stop. | P1 |
| UPI-6 | The formats for UPI-1–3 are found in M0 in my alerts mailbox, along with which notices HDFC sends only by SMS. | P0 (M0) |

### 6.6 Reminders and the daily job (REM)

| ID | Requirement | Pri |
|---|---|---|
| REM-1 | `agent install` writes `~/Library/LaunchAgents/in.kuruhu.sync.plist`, which runs `kuruhu sync` every day at 09:30 and at login, and loads it. `launchd` runs a missed job when the Mac wakes. Logs go to `~/.kuruhu/sync.log`. | P0 |
| REM-2 | Notifications 3 days and 1 day before `renews_on` (configurable), once each. Sent with `terminal-notifier`, so clicking opens the merchant's billing page; `osascript` when it isn't installed. | P0 |
| REM-3 | The same reminders before a trial ends, when the trial end is known (from mail, or from `set`). | P0 |
| REM-4 | A one-line notification after `sync` finds new candidates ("2 new sites to review: `kuruhu list --unconfirmed`"). | P0 |
| REM-5 | `export --ics` writes renewal events for Calendar. | P2 |

### 6.7 Data and privacy (DATA)

| ID | Requirement | Pri |
|---|---|---|
| DATA-1 | Ledger, evidence and kept visit windows in SQLite at `~/.kuruhu/kuruhu.db`. Directory mode 700, file mode 600. Config in `~/.kuruhu/config.toml`. | P0 |
| DATA-2 | URLs are stored without query string or fragment. Snippets mask every digit outside the last 4, amounts and dates. | P0 |
| DATA-3 | The only network connection is IMAP to `imap.gmail.com`. No analytics, no telemetry, no update checks. | P0 |
| DATA-4 | `doctor` checks: each browser's `History` is readable and has the expected tables; Keychain entries exist for configured accounts; the agent is loaded and its last run succeeded; and the database has no run of 13–19 digits anywhere. | P0 |
| DATA-5 | `wipe` deletes `~/.kuruhu` and the Keychain entries, after a confirmation. | P0 |

### 6.8 Packaging (PKG)

| ID | Requirement | Pri |
|---|---|---|
| PKG-1 | Python 3.11 or later, **standard library only** at runtime (`sqlite3`, `imaplib`, `email`, `argparse`, `tomllib`). Dev tools (pytest) only for the parser fixtures. | P0 |
| PKG-2 | Installed with `uv tool install --editable .`, which puts `kuruhu` on my PATH. | P0 |
| PKG-3 | Registrable domains come from a short built-in suffix list (`co.in`, `bank.in`, `gov.in`, `co.uk` …) instead of the full Public Suffix List, to stay standard-library only. | P0 |

### 6.9 Later: companion Chrome extension (EXT)

Only if v1 leaves gaps that matter. These are the parts of v0.1 that need a browser:

| ID | Requirement | Pri |
|---|---|---|
| EXT-1 | Read billing pages as I visit them: masked cards (`•••• 1234`, `ending in 1234`) and renewal dates and amounts. | P2 |
| EXT-2 | Capture checkouts in all frames, including Stripe, Razorpay and PayU iframes: brand and last 4, the save-card or RBI tokenisation tick, and wording that says the charge repeats. The full number is reduced inside the input handler and never leaves it. | P2 |
| EXT-3 | Live charge signals from `chrome.webNavigation`, which also sees the 3DS frames history misses. | P2 |
| EXT-4 | The extension sends derived fields only to `kuruhu native-host` over Chrome native messaging, which writes them to the same ledger as evidence. | P2 |

## 7. Key user flows

1. **First run.** `uv tool install --editable .`, then `kuruhu scan`. It lists candidates: a design tool (saved card seen on its Stripe portal), an AI chat subscription (HDFC charge), a music app, a cloud provider and so on. I `confirm` or `dismiss` each one, then `kuruhu agent install`.
2. **"Which site was it?"** `kuruhu list --via hdfc`. The forgotten design tool is there with a link to its billing page.
3. **Mail.** `kuruhu mail login you@gmail.com`, paste an app password, `kuruhu mail`. HDFC alerts fill in the last 4 for each charge from history, and pre-debit notices add renewal dates.
4. **A renewal is coming.** Three days before a subscription renews, a notification. Clicking it opens that merchant's billing page.
5. **New card.** HDFC replaces my card. `kuruhu replace 1234 --to 5678` prints the checklist of sites with their billing links.
6. **A charge I don't recognise.** An alert says "PAYU\*XYZ ₹1,240 at 14:32". `kuruhu at "today 14:32"` shows which site I was on, and once mail is set up the descriptor is already linked to that merchant (MAIL-6).

## 8. Technical architecture

```
Chrome / Arc / Brave / Edge              Gmail (IMAP, read-only,
History SQLite (immutable=1)             X-GM-RAW search)
           │                                    │
           ▼                                    ▼
┌──────────────────────────────────────────────────────────────┐
│ kuruhu  (Python 3.11+, standard library only)                │
│  sources/history.py     sources/mail.py                      │
│  rules/  hosts · billing paths · alert formats · suffixes    │
│  ledger.py   SQLite  ~/.kuruhu/kuruhu.db                     │
│  cli.py · report.py · remind.py · agent.py                   │
└──────────────────────────────────────────────────────────────┘
           │                                    │
     terminal, --json, HTML report        launchd daily → notifications
```

- **Sources produce evidence; the ledger decides.** `history.py` and `mail.py` only emit evidence items (source, time, URL, rule, fields). `ledger.py` turns evidence into cards, merchants and links, applies my overrides, and is the only module that writes the database. Rerunning a scan with better rules rebuilds the candidate links from the kept evidence without touching what I confirmed or dismissed.
- **One rules file per kind** under `kuruhu/rules/`. Every Indian gateway or bank quirk goes there, not in code. The fixture tests cover these files.
- **Layout:** `src/kuruhu/`, `pyproject.toml` with `[project.scripts] kuruhu = "kuruhu.cli:main"`, `tests/fixtures/` (a small fake `History` database and saved alert emails, with numbers changed).
- **Prototype:** the scripts in `prototype/` (Appendix A) become `sources/history.py`, `rules/hosts.py` and `kuruhu at`.

## 9. Non-functional requirements

| Area | Target |
|---|---|
| First `scan`, 90 days of history | ≤ 10 s |
| Daily `sync` (incremental) | ≤ 5 s without mail, ≤ 30 s with mail |
| `list`, `due`, `show` | ≤ 200 ms |
| Database size | ≤ 20 MB for a year |
| Card data | `doctor` finds no 13–19 digit run in the database, every release |
| Browser files | Never written, never locked: Chrome keeps working while Kuruhu reads |

## 10. Milestones (each with a verification step)

| M | Scope | Verify |
|---|---|---|
| **M0** Spike | (a) Package the prototype as `kuruhu scan` and `kuruhu at`, with the rules in `rules/hosts.py`. (b) Check freshness: a visit from 5 minutes ago is readable with `immutable=1` while Chrome runs. (c) Over IMAP with `X-GM-RAW`, find in my alerts mailbox HDFC's alert senders and the formats of card alerts, UPI debit alerts, AutoPay mandate emails and pre-debit notices (UPI-6) | (a) `kuruhu scan` finds the same merchants as the prototype; (b) the 5-minute-old visit shows in `kuruhu at`; (c) formats written to `docs/email-formats.md`, including which notices come only by SMS |
| **M1** Ledger MVP | CLI-1–5 (P0 commands), LED-1–5, HIS-1–5, HIS-7–10, REM-1–4, DATA-1–5, PKG-1–3 | `kuruhu list` shows the forgotten merchant with its billing link and `kuruhu due` shows an estimated renewal; after `agent install`, a renewal set 3 days out with `kuruhu set` produces a notification on the next run; `kuruhu doctor` passes |
| **M2** Mail and UPI | MAIL-1–7, MAIL-9, UPI-1–5, HIS-6, HIS-12 | 3 months of HDFC alerts from my alerts mailbox imported; at least 5 charges from history get their last 4 from the time join; a pre-debit notice creates a renewal; my active UPI AutoPay mandates show with a next date |
| **M3** Polish and v1.0 | LED-6–7, HIS-11, README with install and agent steps | A fresh `uv tool install` works; `kuruhu replace` for my HDFC card lists every confirmed merchant and each billing link opens the right page |
| **M4** Later | MAIL-8, REM-5, EXT-1–4 if v1 leaves gaps | — |

## 11. Success metrics

- **Recall:** by the end of M2, every subscription and AutoPay mandate I pay for is in the ledger. I check by hand against 3 months of HDFC card and account statements.
- **No surprise renewals:** over a month of use, every recurring link with a known date gets its reminder before the charge.
- **Precision:** I dismiss at most 1 in 5 history candidates.
- **Safety:** `doctor` finds no card number in the database, every release.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Chrome changes the `History` schema | Rarely happens; `doctor` checks the tables; fixture database in the tests; readers in one module |
| `immutable=1` misses visits Chrome hasn't written to disk yet | M0 checks freshness; the daily job runs long after the visit; fallback is reading a copy of the file |
| The wrong merchant is blamed (another tab before the OTP page) | 15-minute window, skip lists, the evidence on every row (principle 2), and candidates stay unconfirmed until I confirm them |
| Charges that leave no trace in history (the 3DS frame wasn't recorded, or a renewal needs no OTP) | Mail covers them (alerts and pre-debit notices); the companion extension later if needed (EXT) |
| Google drops app passwords for IMAP | Fall back to the Gmail API with a desktop OAuth client, behind the same `mail.py` interface |
| History only covers about 90 days | Kuruhu keeps the windows around each signal (HIS-9), and mail covers years |
| My browsing history and mail are sensitive | Read locally only; the database keeps only signal windows and parsed fields; file mode 600; `wipe` |
| HDFC sends some notices only by SMS (UPI pre-debit notices, perhaps more) | Dates estimated from the debit cadence and marked `~`; reading SMS from Messages is an open question (§13) |
| Charges Kuruhu can't see (App Store, phone, in-store) | Non-goal; statements aren't imported (§13), so I check them by hand for the recall metric |

## 13. Decisions and open questions

**Decided 2026-10-27**
- **Name:** Kuruhu (ಕುರುಹು, "trace"), shown as "Kuruhu – Card Trail".
- **A command-line tool, not a Chrome extension** (asked). The browser parts of v0.1 (checkout capture, billing-page text, `webNavigation`) are now an optional add-on (§6.9). Kuruhu never sees a card number, and the "extension that looks like a skimmer" risk is gone.
- **Standalone and personal.**
- **Indian cards first:** HDFC OTP pages, RuPay, Razorpay, PayU and Juspay, RBI e-mandates and pre-debit notices.
- **The history scan is in v1** (HIS), based on the prototype that found the forgotten site.

**Decided 2026-10-27** (while writing; to confirm)
- **Python, standard library only**, installed with `uv` (PKG-1, PKG-2). It continues the prototype and has nothing to update or audit.
- **Mail over IMAP with an app password in Keychain**, not the Gmail API: the API's testing-mode refresh tokens expire after 7 days, which breaks a daily job.
- **Kuruhu keeps only the visit windows around signals** (HIS-9), not a copy of my whole browsing history.
- **A daily `launchd` job at 09:30 and at login**; notifications through `terminal-notifier` (already installed), so clicking opens the billing page.
- **Reminders** 3 days and 1 day before a renewal.
- **A merchant is its registrable domain** (`design.example`). Stripe portal visits belong to the merchant whose billing page came just before.

**Decided 2026-10-27** (asked, the v0.2 open questions)
- **HDFC's alerts go to one Gmail account.** M0 and M2 use that account. A second account for receipts is P2 (MAIL-8).
- **HDFC's app doesn't list the merchants holding a token for my card**, so Kuruhu's ledger is the only such list. M0's check is dropped.
- **UPI AutoPay mandates are tracked** (§6.5), mostly from mail. One-off UPI payments are not.
- **No statement import.** Kuruhu stays standard-library only.
- **No card expiry dates**, not even typed in by me.

**Still open**
- ❓ Read HDFC's SMS alerts from the Messages database (`~/Library/Messages/chat.db`), if my phone forwards texts to this Mac? UPI pre-debit notices may only come by SMS (UPI-3). It would need Full Disk Access for the terminal that runs Kuruhu.

## Appendix A — Prototype findings (2026-10-27)

The scripts in `prototype/` read Chrome's `History` SQLite file in place (`file:…?immutable=1`, safe while Chrome is running):

| Script | What it does | Becomes |
|---|---|---|
| `kuruhu_history.py` | Billing paths and gateway hosts, grouped by site | HIS-5, HIS-7 |
| `kuruhu_3ds.py` | Bank OTP pages → bank and merchant | HIS-2–4 |
| `kuruhu_timeline.py` | Every visit in a time window, with transition type and new-tab marker | `kuruhu at` (HIS-10) |

What they found in my history (2026-07-29 → 2026-10-27, about 90 days):

- **The forgotten site:** a design tool's billing page, then its Stripe portal 19 seconds later. I confirmed it.
- **HDFC OTP pages** (`securehdfc-acs2ui-…hdfc.bank.in`) right before charges at five merchants: AI subscriptions, a music app (through Adyen), a developer API (through Stripe) and an online store.
- **Other charges by gateway:** a cloud provider ("Pay now" through Juspay), two more through Stripe, an online store (PayU, 3 orders), and a Razorpay checkout with no OTP page seen.
- **Billing portals opened:** two more on Stripe, one of them on its cancel-subscription page.
- **Stripe's 3DS step often runs in a frame history doesn't record**, so the bank is unknown for those charges. Mail fills that in (MAIL-6).
- **False positives:** SAML `acs` endpoints on sign-in hosts, OLX and Google paths, and reddit and x.com pages that talk about subscriptions (HIS-7).
- **Chrome's `Web Data` card tables have no site column**, only `use_count` and `use_date`. `virtual_card_usage_data` has a merchant domain, but only for Chrome's virtual cards, and it's empty here.
- **Environment:** Chrome has one profile (`Default`); Arc, Brave and Edge are installed too (HIS-11). Python 3.14 (Homebrew), `uv` and `terminal-notifier` are installed.
