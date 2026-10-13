# -*- coding: utf-8 -*-
"""sr_checks.privacy: nothing private and no other listing reaches a page a seller could see.

Two kinds of test:
  against raw.json   every phone number, email address, full name and access code the team typed into the
                     activity sheet is looked for on the page (text, attributes and HTML comments)
  by pattern         anything shaped like a phone number, an email address, an access code, a health, family
                     or money remark, or a street address that is not this listing's

Other listings come from every other folder under the data root (their address and MLS number).
Evidence lines never repeat a private value in full.
"""
import os
import re

from . import core

PHONE = re.compile(r"(?<![\d$,.#/=\-])(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?![\d,]|\.\d)")
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
CODE_WORD = r"(?:lock\s?box|key\s?box|supra|door|gate|garage|alarm|access|entry)"
CODE_NEAR = re.compile(r"\b(?:code|combo|combination|pin)\b\s*(?:is|was|=|:|#)?\s*#?\s*(\d{3,8})\b"
                       r"|\b%s\b(?:\s+(?:code|combo|combination|number|no\.?|#))?\s*(?:is|was|=|:|#)?\s*#?\s*(\d{4,8})\b(?![,/]\d)" % CODE_WORD, re.I)
HARVEST = re.compile(r"\b(?:code|combo|combination|pin|%s)\b[^\n\d$]{0,24}?(?<![\d$,./])(\d{4,8})(?![\d,/]|\.\d)" % CODE_WORD, re.I)
STREET = re.compile(r"\b(\d{2,6})\s+((?:[NSEW]\.?\s+)?[A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+){0,3}?)\s+"
                    r"(St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ct|Court|Ln|Lane|Way|Blvd|Boulevard|Pl|Place|Cir|Circle|Ter|Terrace"
                    r"|Pkwy|Parkway|Hwy|Highway|Sq|Square|Trl|Trail|Aly|Alley|Loop|Real(?! Estate))\b\.?")
BRACKETS = re.compile(r"\([^)]*\)|\[[^\]]*\]|\([^)]*$")
SENSITIVE = (
    ("health", r"disab\w*|wheelchair|handicap\w*|cancer|chemo\w*|tumou?r|surger\w+|hospital\w*|diagnos\w*|illness\w*"
               r"|sick(?:ness)?|stroke|dementia|alzheimer\w*|parkinson\w*|diabet\w*|seizure\w*|mental health|depress\w+"
               r"|medical|medication\w*|rehab\b|hospice|caregiver\w*|pregnan\w*|miscarr\w*|injur\w+|chronic|therapy"),
    ("family", r"divorc\w*|widow\w*|passed away|died|death|funeral|deceased|custody|estranged|newborn"
               r"|expecting (?:a|their|her|his) (?:baby|child)|going through a separation|domestic (?:violence|dispute)"),
    ("money", r"bankrupt\w*|foreclos\w*|pre-?approv\w*|pre-?qualif\w*|credit score|down ?payment|lost (?:his|her|their) job"
              r"|laid off|unemploy\w*|(?:can|could)(?:no|n')t afford|financing fell through|loan (?:was |got )?denied"
              r"|in debt|inheritance|salary|their income|his income|her income"),
)


def digits(s):
    return re.sub(r"\D", "", str(s or ""))


def doc_text(ctx):
    """Everything in the file a person or a mail client could surface: title, body text (the hidden
    preheader included), attribute values and HTML comments."""
    if "doc_text" not in ctx._cache:
        parts = [ctx.page.title, ctx.page.text()]
        for n in ctx.page.elements:
            for a in ("alt", "title", "aria-label", "href", "src", "content", "value", "placeholder", "data-sr-value"):
                v = n.get(a)
                if v:
                    parts.append(v)
        parts += [c for _, c in ctx.page.comments]
        ctx._cache["doc_text"] = core.squash("\n".join(parts))
    return ctx._cache["doc_text"]


def reader_text(ctx):
    """Text and the attributes a reader sees or taps: no http addresses, so a number inside a URL is not read
    as a phone number."""
    if "reader_text" not in ctx._cache:
        parts = [ctx.page.title, ctx.page.text()]
        for n in ctx.page.elements:
            for a in ("alt", "title", "aria-label"):
                if n.get(a):
                    parts.append(n.get(a))
            h = n.get("href") or ""
            if re.match(r"(?i)(tel|sms|mailto):", h):
                parts.append(h)
        ctx._cache["reader_text"] = core.squash("\n".join(parts))
    return ctx._cache["reader_text"]


def _walk_strings(node):
    if isinstance(node, dict):
        for v in node.values():
            for x in _walk_strings(v):
                yield x
    elif isinstance(node, list):
        for v in node:
            for x in _walk_strings(v):
                yield x
    elif isinstance(node, str):
        yield node


def clean_name(raw):
    """'Invited by Dana Whitlock (Bob) 650...' -> ['Dana', 'Whitlock']. Empty when there is no full name."""
    s = re.sub(r"(?i)^\s*invited\s+by\b\s*[:\-]?\s*", "", str(raw or ""))
    s = PHONE.sub(" ", EMAIL.sub(" ", BRACKETS.sub(" ", s)))
    s = re.split(r"\s*(?:/|\||&|\+|\band\b|,|\s-\s)\s*", s)[0]
    toks = [t.strip(".,;:'\"") for t in s.split()]
    toks = [t for t in toks if re.fullmatch(r"[^\W\d_][\w'\-]*", t) and t.lower() not in
            ("mr", "mrs", "ms", "miss", "dr", "jr", "sr", "ii", "iii", "agent", "buyer", "client", "realtor")]
    return toks if len(toks) >= 2 and len(toks[-1]) >= 2 else []


def harvest(raw, extra=()):
    """Phones, emails, full names and access codes found anywhere in raw.json (and events.json)."""
    phones, emails, names, codes = set(), set(), {}, set()
    for src in [raw] + list(extra):
        if not src:
            continue
        for tab in src.get("tabs") or []:
            for row in tab.get("rows") or []:
                for p in row.get("phones") or []:
                    if len(digits(p)) >= 10:
                        phones.add(digits(p)[-10:])
                for e in row.get("emails") or []:
                    emails.add(str(e).strip().lower())
                for k in ("name_raw", "buyer_raw", "invited_by_raw"):
                    toks = clean_name(row.get(k))
                    if toks:
                        names[(toks[0].lower(), toks[-1].lower())] = "%s %s." % (toks[0], toks[-1][:1].upper())
        for ev in src.get("events") or []:
            toks = clean_name(ev.get("person_raw"))
            if toks:
                names[(toks[0].lower(), toks[-1].lower())] = "%s %s." % (toks[0], toks[-1][:1].upper())
        for s in _walk_strings(src):
            for mt in PHONE.finditer(s):
                if len(digits(mt.group(0))) >= 10:
                    phones.add(digits(mt.group(0))[-10:])
            for mt in EMAIL.finditer(s):
                emails.add(mt.group(0).lower())
            for mt in HARVEST.finditer(s):
                codes.add(mt.group(1))
    return phones, emails, names, codes


def address_core(addr):
    """'218 W Sample Glen Rd #214' -> '218 w sample glen'. The number and the street name, without suffix or unit."""
    mt = STREET.search(addr or "")
    if mt:
        return core.fold("%s %s" % (mt.group(1), mt.group(2))).replace(".", "")
    toks = re.sub(r"#\S+", " ", core.fold(addr or "")).split()
    return " ".join(toks[:3])


def other_listings(ctx):
    """[(slug, address, mls)] for every other listing folder under the data root."""
    out, root = [], ctx.data_root
    own = core.fold(ctx.address())
    if not root or not os.path.isdir(root):
        return None
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        if not os.path.isdir(folder):
            continue
        for fn, pick in (("listing.json", lambda d: d), ("ledger.json", lambda d: d.get("listing") or {})):
            p = os.path.join(folder, fn)
            if not os.path.isfile(p):
                continue
            try:
                L = pick(core.read_json(p, fn))
            except core.GateInputError:
                continue
            addr = L.get("address")
            if addr and core.fold(addr) != own:
                out.append((name, addr, L.get("mls")))
                break
    return out


def check(ctx):
    B = core.Bag("privacy")
    idn = ctx.identity
    everything, reader = doc_text(ctx), reader_text(ctx)
    low = everything.lower()
    ok_phones = set(digits(p)[-10:] for p in [idn.get("phone")] + list(ctx.opts.get("allow_phone") or []) if p)
    ok_emails = set(str(e).lower() for e in [idn.get("email")] + list(ctx.opts.get("allow_email") or []) if e)

    # ---- by pattern -----------------------------------------------------------------------
    bad = []
    for mt in PHONE.finditer(reader):
        if digits(mt.group(0))[-10:] not in ok_phones:
            bad.append("a phone number ending %s: '%s'" % (digits(mt.group(0))[-2:],
                                                           core.excerpt(reader.replace(mt.group(0), core.mask_tail(mt.group(0))), mt.start(), mt.end(), 30)))
    B.judge("phone_pattern", bad, "no phone number on the page except the one in identity.json",
            "a phone number that is not Graeham's is on the page")
    bad = ["an email address (%s)" % core.mask_email(mt.group(0)) for mt in EMAIL.finditer(everything)
           if mt.group(0).lower() not in ok_emails]
    B.judge("email_pattern", sorted(set(bad)), "no email address on the page except the one in identity.json",
            "an email address that is not Graeham's is on the page")
    bad = []
    for mt in CODE_NEAR.finditer(everything):
        code = mt.group(1) or mt.group(2)
        if mt.group(2) and re.fullmatch(r"(?:19|20)\d\d", code):
            continue                                            # 'key box ... 2026' is a year, not a code
        bad.append("'%s'" % core.excerpt(everything.replace(code, core.mask_tail(code, 1)), mt.start(), mt.end(), 20))
    B.judge("access_code_pattern", bad, "no lockbox, door, gate or alarm code wording with digits",
            "wording that reads as an access code is on the page")

    # ---- against raw.json -----------------------------------------------------------------
    if ctx.raw is None:
        B.add("raw_scan", core.FAIL,
              "raw.json was not given, so the page was not searched for the names, numbers and codes the team typed",
              ["pass --raw <listing folder>\\raw.json (a report cannot ship without this scan)"])
    else:
        phones, emails, names, codes = harvest(ctx.raw, ctx.opts.get("events") or ())
        own = (ctx.listing or ctx.ledger.get("listing") or {})
        keybox = digits(own.get("keybox_number"))
        if len(keybox) >= 4:
            codes.add(keybox)
        bad = []
        for p in sorted(phones - ok_phones):
            if re.search(r"(?<!\d)%s\D{0,3}%s\D{0,3}%s(?!\d)" % (p[:3], p[3:6], p[6:]), everything):
                bad.append("a phone number from the activity sheet, ending %s" % p[-2:])
        for e in sorted(emails - ok_emails):
            if e in low:
                bad.append("an email address from the activity sheet (%s)" % core.mask_email(e))
        B.judge("raw_contact_details", bad, "none of the %d phone numbers and %d email addresses in raw.json is on the page"
                % (len(phones), len(emails)), "contact details from the activity sheet are on the page")
        me = tuple(core.fold(idn.get("name") or "").split())
        allow = set(tuple(core.fold(n).split()) for n in ctx.opts.get("allow_name") or [])
        bad = []
        for (first, last), short in sorted(names.items()):
            if me and (first, last) == (me[0], me[-1]):
                continue
            if any(first == a[0] and last == a[-1] for a in allow if a):
                continue
            mt = re.search(r"(?<![\w'])%s\s+(?:[\w'.\-]+\s+)?%s(?![\w'])" % (re.escape(first), re.escape(last)), low)
            if mt:
                bad.append("the full name of the person shown as '%s' is printed: '%s'"
                           % (short, core.excerpt(low[:mt.start()] + short.lower() + "*" * 4 + low[mt.end():], mt.start(), mt.start() + len(short), 25)))
        B.judge("raw_full_names", bad, "none of the %d full names in raw.json is on the page (people print as First L.)"
                % len(names), "a full name from the activity sheet is on the page")
        skip = set(x for x in (digits(own.get("zip")), str(own.get("sqft") or ""), str(own.get("year_built") or ""),
                               (re.match(r"\d+", ctx.address()) or [""])[0] if ctx.address() else "") if x)
        bad, collided = [], []
        for code in sorted(codes):
            if code in skip or re.fullmatch(r"20[2-3]\d", code):
                collided.append(code)
                continue
            if re.search(r"(?<![\d,$.#])%s(?![\d,]|\.\d)" % re.escape(code), everything):
                bad.append("a %d digit number that the activity sheet uses as an access code or key-box number (ends %s)"
                           % (len(code), code[-1]))
        B.judge("raw_access_codes", bad, "none of the %d access code or key-box numbers found in raw.json is on the page"
                % len(codes), "an access code from the activity sheet is on the page")
        if collided:
            B.info("raw_access_codes_skipped", "%d code(s) in raw.json equal a public fact about the home (street number, "
                   "zip, square feet or a year) and were not searched for" % len(collided))

    # ---- health, family and money remarks ----------------------------------------------------
    text = ctx.seller_flat()
    if ctx.kind == "email":
        for o in ctx.ledger.get("offers") or []:          # offer terms belong in the email and name the financing
            if o.get("terms_summary"):
                text = re.sub(re.escape(core.squash(o["terms_summary"])), " ", text, flags=re.I)
    disclaimer = core.squash(idn.get("disclaimer") or "")
    if disclaimer:
        text = text.replace(disclaimer, " ")
    allowed = set(t.lower() for t in ctx.opts.get("allow_term") or [])
    bad = []
    for group, pattern in SENSITIVE:
        for mt in re.finditer(r"(?<![\w'])(?:%s)(?![\w'])" % pattern, text, re.I):
            if mt.group(0).lower() not in allowed:
                bad.append("%s: '%s'" % (group, core.excerpt(text, mt.start(), mt.end(), 35)))
    B.judge("sensitive_terms", bad, "no health, family or money remark about a buyer in the seller's text",
            "wording about a buyer's health, family or finances is in the seller's text", waivable=True)

    # ---- other listings -------------------------------------------------------------------
    others = other_listings(ctx)
    if others is None:
        B.add("other_listings", core.FAIL,
              "no data root was given, so the page was not searched for the other listings' addresses",
              ["pass --data-root <the seller-reports folder>"])
    else:
        bad = []
        for slug, addr, mls in others:
            if address_core(addr) and address_core(addr) in core.fold(everything).replace(".", ""):
                bad.append("the address of another listing (%s, folder '%s')" % (addr, slug))
            if mls and str(mls).lower() in low:
                bad.append("the MLS number of another listing (folder '%s')" % slug)
        B.judge("other_listings", bad, "no address or MLS number of the %d other listing folder(s) under the data root"
                % len(others), "another listing's details are on this page")
    own_core = address_core(ctx.address())
    sales = [core.fold(s.get("address") or "") for s in ((ctx.ledger.get("market") or {}).get("sales") or [])]
    market_text = core.fold(ctx.section_text("market") or "")
    bad, comps = [], 0
    for mt in STREET.finditer(everything):
        found = core.fold("%s %s" % (mt.group(1), mt.group(2))).replace(".", "")
        if own_core and (found == own_core or own_core.startswith(found) or found.startswith(own_core)):
            continue
        whole = core.fold(mt.group(0))
        if any(s and (s.startswith(whole.rstrip(".")) or whole.rstrip(".") in s) for s in sales):
            if not ctx.page.sections("market") or whole.rstrip(".") in market_text:
                comps += 1
                continue
            bad.append("a comparable sale's address outside the market section: '%s'" % mt.group(0))
            continue
        bad.append("'%s' in '%s'" % (mt.group(0), core.excerpt(everything, mt.start(), mt.end(), 25)))
    B.judge("address_pattern", bad, "every street address on the page is this listing's (%s)%s"
            % (ctx.address(), ", plus %d comparable sale(s) from the ledger's market block" % comps if comps else ""),
            "a street address that is not this listing's is on the page (say 'chose another property')", waivable=True)
    return B.results
