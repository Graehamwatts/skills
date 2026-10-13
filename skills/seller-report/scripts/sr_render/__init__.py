# -*- coding: utf-8 -*-
"""sr_render: turns a seller-report ledger into the email, the link copy and the print layout.

    from sr_render import render, RenderRefused
    result = render(ledger, mode="email")          # result["html"], result["info"]

The renderer prints the ledger's numbers and never counts anything itself (see references/data-contract.md).
One module, one job:

    tokens            every color, font, size, limit and fixed phrase
    htmlkit           email-safe table, card, chip, bar and chart builders
    model             reads the ledger once and answers questions about it; cross-checks before a build
    text              what a seller may read: link-copy scrubbing, names, roles, chips
    people            one person on the page: the full entry, the one-line entry, the pointer, the day by day log
    sections_top      masthead, this week in brief
    sections_numbers  the numbers table, the line under it, the week by week charts
    sections_saying   what people are saying, every price comment, the record at each list price
    sections_lists    the details: offers and likely offers, then people grouped by what they did
    sections_more     similar homes nearby, time on the market, online ads and marketing, next week
    sections_record   the running record: follow-up since we listed, the weekly table, how we count, footer
    assemble          section order, the document wrapper, the checks on the finished page
    fit               the fit ladder that keeps the email under the size ceiling
    api               render(): one build mode, every page ready to send
"""
import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)          # sr_contract lives beside this package

from .api import render, RenderRefused, MODES        # noqa: E402,F401
