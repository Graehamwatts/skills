# -*- coding: utf-8 -*-
"""sr_checks.brand: the brand facts on the page are the ones in identity.json, character for character.

Everything is read from shared-references/identity.json at run time: the name, the REALTOR line with the
registered mark, the brokerage line, the DRE number, the phone, the email and the Compass disclaimer, plus
the blocklist of values that must never appear. No brand value and no blocked value is typed in this file.
"""
import re

from . import core
from .privacy import doc_text


def check(ctx):
    B = core.Bag("brand")
    idn = ctx.identity
    text = ctx.seller_flat()
    low = text.lower()
    everything = doc_text(ctx)

    def present(rule, label, value, fold_case=False):
        if not value:
            B.fail(rule, "identity.json has no %s to compare the page with" % label)
            return
        v = core.squash(value)
        if (v.lower() in low) if fold_case else (v in text):
            B.ok(rule, "%s matches identity.json" % label)
        else:
            B.fail(rule, "%s from identity.json is not on the page, or is printed differently" % label,
                   ["expected exactly: %s" % (v if len(v) < 90 else v[:87] + "...")])

    present("name", "the name", idn.get("name"), fold_case=True)
    present("brokerage_line", "the brokerage line", idn.get("brand_line"))
    present("phone", "the phone number", idn.get("phone"))
    present("email", "the email address", idn.get("email"))
    present("disclaimer", "the Compass disclaimer", idn.get("disclaimer"))

    # REALTOR always carries the registered mark
    title = idn.get("title") or "REALTOR"
    marked = idn.get("realtor_line") or (title + core.REG)
    bare = [core.excerpt(text, mt.start(), mt.end(), 25)                       # 'Realtor.com' is a site name, not the title
            for mt in re.finditer(r"\b%s\b(?!S?\s*%s|\.(?:com|org)\b)" % (re.escape(title), core.REG), text, re.I)]
    if marked not in text:
        B.fail("realtor_mark", "'%s' with the registered mark is not on the page" % title, ["expected: " + marked])
    elif bare:
        B.fail("realtor_mark", "'%s' is printed without the registered mark" % title, ["'%s'" % b for b in bare[:5]])
    else:
        B.ok("realtor_mark", "%s carries the registered mark everywhere it is printed" % title)

    # the DRE number: present, and no other licence number beside the letters DRE
    dre = idn.get("dre") or ""
    found = re.findall(r"\bDRE\b[^\d]{0,12}(\d{6,9})", everything, re.I)
    wrong = sorted(set(x for x in found if x != dre))
    if not dre:
        B.fail("dre", "identity.json has no DRE number")
    elif wrong:
        B.fail("dre", "a DRE number on the page is not the one in identity.json",
               ["%d number(s) beside 'DRE' differ from identity.json (shown masked: %s)"
                % (len(wrong), ", ".join(core.mask_tail(x, 2) for x in wrong))])
    elif dre not in found:
        B.fail("dre", "the DRE number from identity.json is not printed beside 'DRE'")
    else:
        B.ok("dre", "the DRE number matches identity.json (%d place%s)" % (len(found), "" if len(found) == 1 else "s"))

    # the blocklist: read at run time, searched everywhere in the file
    bl = idn.get("blocklist") or {}
    src = ctx.source
    src_low = src.lower()
    hits = []
    for i, v in enumerate(bl.get("dre") or []):
        if v and v in src:
            hits.append("blocked DRE value no. %d from identity.json (%d place%s)" % (i + 1, src.count(v), "" if src.count(v) == 1 else "s"))
    for i, v in enumerate(bl.get("brand") or []):
        if v and v.lower() in src_low:
            hits.append("blocked brand value no. %d from identity.json (%d place%s). Another agent's brokerage prints "
                        "through sr_contract.display_brokerage" % (i + 1, src_low.count(v.lower()), "" if src_low.count(v.lower()) == 1 else "s"))
    n = len(bl.get("dre") or []) + len(bl.get("brand") or [])
    if not n:
        B.fail("blocklist", "identity.json gave no blocklist, so the page could not be searched for blocked values")
    else:
        B.judge("blocklist", hits, "none of the %d blocked values in identity.json is anywhere in the file" % n,
                "a value on identity.json's blocklist is in the file")

    retired = [t for t in idn.get("retired_taglines") or [] if core.squash(t).lower() in low]
    B.judge("retired_taglines", ["retired tagline no. %d from identity.json" % (i + 1) for i, _ in enumerate(retired)],
            "no retired tagline is printed", "a tagline that identity.json marks retired is printed")

    site = idn.get("website") or ""
    if site:
        base = site.lower().split("/")[0]
        stray = sorted(set(mt.group(0) for mt in re.finditer(r"\b[\w\-]*%s[\w\-]*\.(?:com|net|org|co|io)\b" % re.escape(base.split(".")[0]), low)
                           if mt.group(0) != base and not mt.group(0).endswith("." + base)))
        if stray:
            B.warn("website", "a web address close to the one in identity.json, but not the same", stray[:5])
    return B.results
