# -*- coding: utf-8 -*-
"""Tests of the ship gate (scripts/check_report.py and scripts/sr_checks).

Each case in CASES breaks one rule of an otherwise clean page and names the rule that must catch it. The
harness and the edit helpers are in gate_harness.py. The lists under "The details", the numbers table and the
week by week chart have their own file, test_checks_lists.py.

    python -m unittest tests.test_checks            (from the seller-report folder)
    python tests\test_checks.py
"""
import copy
import html
import io
import json
import os
import re
import shutil
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gate_harness import (GateHarness, UNDER, LINK_URL, swap, para, top, cell, cut, chain, other_dre, comment_of,     # noqa: E402
                          add_cases)
import check_report                                  # noqa: E402
import sr_checks                                     # noqa: E402
import sr_contract as C                              # noqa: E402  (the data contract, to rebuild a ledger a test edits)
from sr_checks import core, layout_probe, page, recount, sample_page   # noqa: E402


# ---- ledger edits -------------------------------------------------------------------------------
def led_no_keybox(d, t):
    d["report"]["tracking"]["keybox_showings"] = False
    C.finish_ledger(d)


def led_total_off(d, t):
    d["totals"]["contacted"] -= 1


def led_status_off(d, t):
    next(c for c in d["contacts"] if c["id"] == "c003")["status"] = "replied"


def led_note(d, t):
    d["report"]["as_of_note"] = "Operator note: the second inspection has not been raised with the sellers yet."


def led_price_talk(d, t):
    next(c for c in d["contacts"] if c["id"] == "c001")["feedback_safe"] = "Her clients would come back if the seller lowers the price."


def led_review_state(d, t):
    d["meta"].update(tag_review="confirmed", confirmed_by="Someone", confirmed_on=d["report"]["report_date"])


def led_build_note(d, t):
    d["data_quality"].append("Synthetic build note: two follow-ups typed twice are counted once.")


def led_real(d, t):
    d["meta"]["synthetic"] = False


CASES = []


def case(name, rule, edit=None, **kw):
    CASES.append(dict(kw, name=name, rule=rule, edit=edit))


# ---- 1. numbers ---------------------------------------------------------------------------------
case("number_in_a_hook_is_wrong", "numbers.contacted", swap('data-sr="contacted">5<', 'data-sr="contacted">6<'))
case("number_in_a_sentence_is_wrong", "numbers.followups", swap("14 follow-ups to", "15 follow-ups to"), hooks=False)
case("separate_days_wrong", "numbers.followup_days", swap("on 10 separate days", "on 12 separate days"), hooks=False)
case("answered_wrong_without_hooks", "numbers.answered", swap("3 answered", "4 answered"), hooks=False)
case("headline_number_missing", "numbers.waiting", swap("2 still waiting, 1 of them after 3 or more tries.", "More to come."), hooks=False)
case("weekly_cell_wrong", "numbers.table_weeks", cell('data-sr-row="3"', 5, "9"))
case("weekly_cell_wrong_without_hooks", "numbers.table_weeks", cell(">3 Mar 23</th>", 5, "9"), hooks=False)
case("weekly_subtotal_wrong", "numbers.table_weeks", cell('data-sr-row="sub:1150000"', 5, "70"), fx="busy")
case("weekly_total_wrong", "numbers.table_weeks", cell('data-sr-row="all"', 7, "4"))
case("week_row_missing", "numbers.table_weeks", cut(r'<tr data-sr-row="2">.*?</tr>\n'))
case("open_house_zero_when_none_held", "numbers.table_weeks", cell('data-sr-row="2"', 4, "0"))
case("week_dated_wrong", "numbers.table_weeks", swap(">3 Mar 23</th>", ">3 Mar 30</th>"))
case("scorecard_cell_wrong", "numbers.table_scorecard", cell('data-sr-row="touches_outbound"', 0, "7"))
case("scorecard_total_wrong_without_hooks", "numbers.table_scorecard", cell(">Replies we received</th>", 2, "9"), hooks=False)
case("price_row_wrong", "numbers.price_not_raised", swap('data-sr="price_not_raised">2<', 'data-sr="price_not_raised">3<'))
case("price_row_missing", "numbers.price_too_high", cut(r"<tr><td [^>]*>Said the price is too high</td>.*?</tr>\n"), hooks=False)
case("topic_count_wrong", "numbers.theme.location", swap('data-sr="theme:location">1<', 'data-sr="theme:location">4<'))
case("topic_count_wrong_without_hooks", "numbers.theme.location",
     swap("Location or surroundings</td><td %s>1<" % sample_page.CELL, "Location or surroundings</td><td %s>4<" % sample_page.CELL), hooks=False)
case("denominator_wrong", "numbers.feedback_people", swap('data-sr="feedback_people">2<', 'data-sr="feedback_people">5<'))
case("person_line_wrong", "numbers.person_lines", swap("4 days of follow-up (2 calls", "5 days of follow-up (2 calls"))
case("person_line_wrong_without_hooks", "numbers.person_lines", swap("4 days of follow-up (2 calls", "9 days of follow-up (7 calls"), hooks=False)
case("per_price_cell_wrong", "numbers.table_periods", cell('data-sr-row="conversations_with_feedback"', 0, "99"), fx="busy")
case("days_on_market_wrong", "numbers.dom", swap('data-sr="dom">32<', 'data-sr="dom">33<'))
case("list_price_wrong", "numbers.list_price", swap("$1,195,000", "$1,159,000"))
case("number_for_a_fact_not_recorded", "numbers.keybox_showings",
     swap('data-sr="keybox_showings">not recorded<', 'data-sr="keybox_showings">0<'), led=led_no_keybox)
case("count_out_of_the_wrong_number_of_people", "numbers.price_not_raised",
     swap('data-sr="price_not_raised">2</span>', 'data-sr="price_not_raised">2</span> of 9 people'))
case("marked_week_value_wrong", "numbers.marked_values", para('<span data-sr="week:inquiries">7</span> inquiries this week.'))
case("this_weeks_channels_wrong", "numbers.week_channels", para("This week: 4 follow-ups to 2 people on 2 days (3 calls, 1 text, 1 email)."))
case("scorecard_change_wrong", "numbers.table_scorecard", cell('data-sr-row="touches_outbound"', 0, "4 up 3"))
case("market_count_wrong", "numbers.market_under_contract", para("3 of the 5 comparable sales were under contract by that day."))
case("market_average_wrong", "numbers.market_average", para("Average 31 days, median 21."))
case("channel_called_running_without_a_check", "numbers.marketing_running_rule", para("Facebook and Instagram ads RUNNING"))
case("date_not_in_the_persons_record", "numbers.person_dates", swap("4 days of follow-up (2 calls", "Toured Feb 2. 4 days of follow-up (2 calls"))
case("ledger_total_does_not_match_rows", "ledger.rows_match", led=led_total_off, led_breaks=True, also=("numbers",))
case("ledger_status_does_not_match_touches", "ledger.status_follows_touches", led=led_status_off, led_breaks=True, also=("numbers",))

# ---- 2. privacy ---------------------------------------------------------------------------------
case("phone_from_the_sheet", "privacy.raw_contact_details", para("Her number is 415-555-0142."))
case("phone_in_another_format", "privacy.raw_contact_details", para("Her number is (415) 555 0142."))
case("phone_not_in_the_sheet", "privacy.phone_pattern", para("Call 510-555-0199 to book."))
case("email_of_a_stranger", "privacy.email_pattern", para("Write to someone@elsewhere.test for details."))
case("email_from_the_sheet_in_a_link", "privacy.raw_contact_details", para('<a href="mailto:tk@northgate.test">Send a note</a>'))
case("full_name", "privacy.raw_full_names", swap("Odalys V.", "Odalys Vantongeren"))
case("lockbox_code", "privacy.access_code_pattern", para("The lockbox code is 4471."))
case("code_from_the_sheet_alone", "privacy.raw_access_codes", para("Use 4471 at the side entrance."))
case("health_remark", "privacy.sensitive_terms", para("Her client uses a wheelchair."))
case("money_remark", "privacy.sensitive_terms", para("His buyers are not pre-approved yet."))
case("another_listing_of_ours", "privacy.other_listings", para("They preferred 77 Other Oak Dr."))
case("another_listing_by_mls_number", "privacy.other_listings", para("See ML00000077 for the other home."))
case("some_other_street_address", "privacy.address_pattern", para("They chose 412 Elsewhere Ave instead."))
case("name_in_an_html_comment", "privacy.raw_full_names", swap("</body>", "<!-- row for Wilhelmina Rasmussen -->\n</body>"))
case("page_without_the_raw_scan", "privacy.raw_scan", raw=False)

# ---- 3. tone ------------------------------------------------------------------------------------
case("comment_in_quote_marks", "tone.no_quoted_comments",
     swap(lambda t: "<div>%s</div>" % comment_of(t), lambda t: "<div>&quot;%s&quot;</div>" % comment_of(t)))
case("comment_in_a_blockquote", "tone.no_quoted_comments",
     swap(lambda t: "<div>%s</div>" % comment_of(t), lambda t: "<blockquote>%s</blockquote>" % comment_of(t)))
case("harsh_word", "tone.harsh_words", para("The agent said the kitchen was awful."))
case("harsh_word_in_the_preheader", "tone.harsh_words",
     swap('<body style="margin:0;padding:0;background:#F5EFDC">',
          '<body style="margin:0;padding:0;background:#F5EFDC"><div style="display:none">One agent called it a dump.</div>'))
case("comment_block_without_its_label", "tone.comment_labeled", swap("AS REPORTED TO OUR TEAM", "FEEDBACK"))
case("comment_without_a_label_no_hooks", "tone.comment_labeled", swap("AS REPORTED TO OUR TEAM", "FEEDBACK"), hooks=False)

# ---- 4. feedback only ---------------------------------------------------------------------------
case("recommendation_sentence", "feedback_only.no_recommendation", para("We recommend a price reduction."))
case("lower_the_price", "feedback_only.no_recommendation", para("It may be time to lower the price."))
case("reposition", "feedback_only.no_recommendation", para("The plan is to reposition the home after the holidays."))
case("my_recommendation_block", "feedback_only.no_advice_blocks", para("MY RECOMMENDATION</p><p>Adjust the price before the next open house."))
case("from_you_ask", "feedback_only.no_advice_blocks", para("From you this week: a time to go over the numbers."))
case("silence_means_nothing", "feedback_only.no_reading_of_silence", para("The 2 who did not bring up price tell us nothing about price either way."))
case("silence_means_the_price_is_fine", "feedback_only.no_reading_of_silence", para("Nobody thinks the price is a problem."))
case("suggested_number", "feedback_only.no_suggested_number", para("At $1,150,000 the home would sell quickly."))
case("brief_override_not_confirmed", "feedback_only.no_recommendation",
     para('</p><div data-sr-section="brief_override">I recommend we talk about price this week.</div><p>'))

# ---- 5. brand -----------------------------------------------------------------------------------
case("dre_is_not_the_one_on_file", "brand.dre", swap(lambda t: "DRE #" + t.identity["dre"], lambda t: "DRE #" + other_dre(t), 9))
case("blocked_dre_in_a_comment", "brand.blocklist", swap("</body>", lambda t: "<!-- %s -->\n</body>" % t.identity["blocklist"]["dre"][0]))
case("blocked_brand_in_the_text", "brand.blocklist", para(lambda t: "Agent with " + html.escape(t.identity["blocklist"]["brand"][0])))
case("realtor_without_the_mark", "brand.realtor_mark", swap(lambda t: html.escape(t.identity["realtor_line"]), lambda t: t.identity["title"]))
case("brokerage_line_changed", "brand.brokerage_line", swap(lambda t: html.escape(t.identity["brand_line"]), "Powered by a brokerage", 9))
case("disclaimer_cut_short", "brand.disclaimer",
     swap(lambda t: html.escape(t.identity["disclaimer"]), lambda t: html.escape(t.identity["disclaimer"][:80])))
case("phone_left_out", "brand.phone", swap(lambda t: ">%s</a>" % t.identity["phone"], ">Call</a>"))
case("email_left_out", "brand.email", swap(lambda t: ">%s</a>" % t.identity["email"], ">Email</a>"))
case("name_misspelled", "brand.name", swap(lambda t: t.identity["name"].upper(), lambda t: t.identity["name"].upper()[:-1] + "Z", 9))

# ---- 6. hygiene ---------------------------------------------------------------------------------
case("em_dash", "hygiene.no_dashes", para("A quiet week" + chr(0x2014) + "nothing new."))
case("en_dash_entity", "hygiene.no_dashes", para("Mar 9&ndash;15 was quiet."))
case("tbd", "hygiene.no_placeholders", para("Open house time: TBD."))
case("template_field", "hygiene.no_placeholders", para("Hello {{sellers}},"))
case("lorem", "hygiene.no_placeholders", para("Lorem ipsum dolor sit amet."))
case("sample_wording", "hygiene.no_placeholders", para("SAMPLE WORDING. PASTE the real note here."))
case("program_value", "hygiene.no_placeholders", para("Listed for $None."))
case("href_hash", "hygiene.links_work", swap(LINK_URL, 'href="#"'))
case("empty_href", "hygiene.links_work", swap(LINK_URL, 'href=""'))
case("relative_href", "hygiene.links_work", swap(LINK_URL, 'href="link.html"'))
case("http_link", "hygiene.links_work", swap(LINK_URL, 'href="http://seller-reports.test/record"'))
case("image_from_this_computer", "hygiene.links_work",
     para('<img src="C:/Users/someone/Pictures/front.jpg" alt="Front of the home" width="600" height="200">'))
case("a_draft_notice_on_the_page", "hygiene.no_working_material", para("DRAFT. Not for the seller."))
case("a_do_not_send_line", "hygiene.no_working_material", para("Do not send."))
case("a_line_about_unconfirmed_tags", "hygiene.no_working_material", para("Tags not yet confirmed."))
case("the_word_tagged", "hygiene.no_working_material", para("3 comments were tagged this week."))
case("a_reviewer_panel_on_the_page", "hygiene.no_working_material",
     edit=swap("</table>\n</body>", '<tr><td bgcolor="#FFF7CC" style="color:#333333">FOR THE REVIEWER. REMOVED BEFORE SENDING.</td></tr></table>\n</body>'))
case("a_block_hooked_as_a_draft_notice", "hygiene.no_working_material",
     edit=swap("</table>\n</body>", '<tr><td data-sr-section="draft_notice" bgcolor="#FFFFFF" style="color:#333333">A note.</td></tr></table>\n</body>'))
case("a_block_hooked_as_a_reviewer_panel", "hygiene.no_working_material",
     edit=swap("</table>\n</body>", '<tr><td data-sr-section="reviewer_panel" bgcolor="#FFFFFF" style="color:#333333">A note.</td></tr></table>\n</body>'))
case("page_names_a_build_kind", "hygiene.no_working_material", swap("</head>", '<meta name="sr:build" content="draft"></head>'))
case("build_note_printed", "hygiene.internal_notes", led=led_build_note,
     edit=para("Synthetic build note: two follow-ups typed twice are counted once."))
case("operator_note_printed", "hygiene.internal_notes", led=led_note,
     edit=para("Operator note: the second inspection has not been raised with the sellers yet."))
case("contact_id_printed", "hygiene.internal_notes", para("Follow up with c001 on Friday."))
case("field_name_printed", "hygiene.internal_notes", para("Status: awaiting_reply."))
case("link_copy_offer_price", "hygiene.link_copy_offers", para("One offer came in at $1,120,000."), fx="busy", kind="link")
case("link_copy_offer_percent", "hygiene.link_copy_offers", para("It came in at 97.4% of the list price."), fx="busy", kind="link")
case("link_copy_offer_terms", "hygiene.link_copy_offers", para("Conventional loan, 20% down, 21 day close."), fx="busy", kind="link")
case("link_copy_names_an_offer_agent", "hygiene.link_copy_offers", para("Alder A. toured twice."), fx="busy", kind="link")
case("link_copy_card_for_an_offer_agent", "hygiene.link_copy_offers", para('<span data-sr-person="c001">A returning agent</span>'), fx="busy", kind="link")
case("link_copy_who_may_write_an_offer", "hygiene.link_copy_offers", para("Delphine B. may write an offer next week."), fx="busy", kind="link")
case("link_copy_still_deciding_row", "hygiene.link_copy_offers", para("Still deciding: 8"), fx="busy", kind="link")
case("link_copy_next_week_names_a_lead", "hygiene.link_copy_offers", fx="busy", kind="link",
     edit=swap("<li>Keep trying the people", "<li>Check back with Emrys J. on Friday.</li><li>Keep trying the people"))
case("link_copy_without_noindex", "hygiene.noindex", swap('<meta name="robots" content="noindex, nofollow">\n', ""), fx="busy", kind="link")
case("email_leans_on_noindex", "hygiene.email_noindex", para("This page is not indexed by search engines."))
case("email_links_to_another_copy", "hygiene.email_noindex", manifest={"link_url": "https://seller-reports.test/other"})

# ---- 7. email safety ----------------------------------------------------------------------------
case("email_too_big", "email_safety.size", swap("</body>", "<!--\n" + ("x" * 900 + "\n") * 90 + "-->\n</body>"))
case("script_tag", "email_safety.tags", para("<script>var a = 1;</script>"))
case("svg_tag", "email_safety.tags", para('<svg width="10" height="10"></svg>'))
case("form_tag", "email_safety.tags", para('<form action="https://seller-reports.test/a"><input type="text" name="q"></form>'))
case("css_position", "email_safety.css", para('<span style="position:relative">A note</span>'))
case("css_flex", "email_safety.css", para('<span style="display:flex">A note</span>'))
case("css_grid", "email_safety.css", para('<span style="display:inline-grid">A note</span>'))
case("css_background_image", "email_safety.css", para('<span style="background-image:url(https://seller-reports.test/x.png)">A note</span>'))
case("cell_with_no_background", "email_safety.cell_colors", swap("</body>", '<table role="presentation"><tr><td>Loose cell</td></tr></table>\n</body>'))
case("image_without_a_size", "email_safety.images", para('<img src="https://seller-reports.test/hero.jpg" alt="Front of the home">'))
case("image_without_alt", "email_safety.images", para('<img src="https://seller-reports.test/hero.jpg" width="600" height="200">'))
case("text_under_12_px", "email_safety.font_size", para('<span style="font-size:11px">Fine print here</span>'))
case("text_under_12_px_in_points", "email_safety.font_size", para('<span style="font:400 8pt/1.2 Arial">Fine print here</span>'))
case("text_under_12_px_in_a_style_block", "email_safety.font_size", swap("</head>", "<style>.fine{font-size:10px}</style></head>"))

# ---- 8. wrong file ------------------------------------------------------------------------------
case("file_named_sample", "wrong_file.file_name", file="SAMPLE-email.html")
case("page_titled_draft", "wrong_file.file_name", swap("<title>Weekly", "<title>DRAFT Weekly"), also=("hygiene",))
case("address_is_not_listing_json", "wrong_file.address", listing=lambda L: L.update(address="219 Sample Glen Ct"), also=("privacy",))
case("issue_number_wrong", "wrong_file.issue", swap('data-sr="issue">05<', 'data-sr="issue">06<'))
case("issue_number_wrong_in_the_title", "wrong_file.issue", swap("<title>Weekly Seller Report No. 05", "<title>Weekly Seller Report No. 04"))
case("week_wrong", "wrong_file.week", swap("Apr 6 to Apr 12", "Mar 30 to Apr 5"))
case("week_end_wrong", "wrong_file.week", swap("Apr 6 to Apr 12", "Apr 6 to Apr 13"), hooks=False)
case("issued_date_wrong", "wrong_file.week", swap("Issued Monday, Apr 13", "Issued Monday, Apr 14"))
case("page_says_it_is_another_kind", "wrong_file.kind_and_listing", swap('name="sr:kind" content="email"', 'name="sr:kind" content="link"'))
case("greeting_names_another_seller", "wrong_file.greeting", top("Hi Jordan, here is this week."))
case("ledger_still_carries_a_review_state", "wrong_file.one_build_mode", led=led_review_state, led_breaks=True, also=("ledger",))
case("manifest_still_names_a_build_kind", "wrong_file.one_build_mode", manifest={"build_kind": "draft"})
case("page_in_a_draft_folder", "wrong_file.file_name", subfolder="draft")
case("page_from_test_data", "wrong_file.synthetic", allow_synthetic=False)
case("real_data_inside_a_repository", "wrong_file.synthetic", led=led_real, git=True, led_breaks=True)
case("file_changed_after_the_snapshot", "wrong_file.manifest", manifest={"tamper": True})


class GateTests(GateHarness):
    # ---- clean pages ------------------------------------------------------------------------
    def test_clean_pages_pass_in_every_combination(self):
        for fx in ("small", "busy"):
            for kind in ("email", "link", "print"):
                for hooks in (True, False):
                    with self.subTest(fx=fx, kind=kind, hooks=hooks):
                        rep = self.gate(fx=fx, kind=kind, hooks=hooks)
                        shutil.rmtree(os.path.join(self.tmp, "root"))
                        self.assertClean(rep)
                        self.assertEqual(rep.count(core.WARN), 0, rep.as_text())

    def test_clean_page_with_its_manifest(self):
        rep = self.gate(manifest={"link_url": "https://seller-reports.test/record"})
        self.assertClean(rep)
        self.assertIn("wrong_file.manifest", [r.id for r in rep.results if r.level == core.PASS])

    def test_every_family_reports(self):
        rep = self.gate()
        self.assertEqual(sorted(set(r.family for r in rep.results)), sorted(sr_checks.FAMILIES))
        self.assertTrue(all(r.level in core.LEVELS and r.message for r in rep.results))

    def test_hooks_are_the_stronger_test(self):
        hooked = self.gate()
        shutil.rmtree(os.path.join(self.tmp, "root"))
        plain = self.gate(hooks=False)
        self.assertNotIn("numbers.hooks", [r.id for r in hooked.results])
        self.assertIn("numbers.hooks", [r.id for r in plain.results if r.level == core.INFO])
        self.assertIn("(hook", next(r.message for r in hooked.results if r.id == "numbers.contacted"))
        self.assertIn("sentence", next(r.message for r in plain.results if r.id == "numbers.contacted"))

    # ---- the switches a person decides --------------------------------------------------------
    def test_brief_override_needs_the_operator_to_confirm(self):
        edit = para('</p><div data-sr-section="brief_override">I recommend we talk about price this week.</div><p>')
        self.assertFalse(self.gate(edit=edit).ok)
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(edit=edit, args=["--confirm-brief-override"])
        self.assertClean(rep)
        self.assertIn("feedback_only.brief_override", [r.id for r in rep.results if r.level == core.INFO])

    def test_brief_override_from_a_file(self):
        brief = os.path.join(self.tmp, "brief.txt")
        with open(brief, "w", encoding="utf-8") as f:
            f.write("I recommend we talk about price this week.\n")
        edit = para("I recommend we talk about price this week.")
        self.assertFalse(self.gate(edit=edit, args=["--brief-override-file", brief]).ok)
        shutil.rmtree(os.path.join(self.tmp, "root"))
        self.assertClean(self.gate(edit=edit, args=["--brief-override-file", brief, "--confirm-brief-override"]))
        shutil.rmtree(os.path.join(self.tmp, "root"))
        other = para("I recommend we talk about price this week. We recommend a price reduction.")
        self.assertFalse(self.gate(edit=other, args=["--brief-override-file", brief, "--confirm-brief-override"]).ok)

    def test_reported_price_talk_is_a_warning_not_a_failure(self):
        rep = self.gate(led=led_price_talk)
        self.assertClean(rep)
        self.assertIn("feedback_only.price_talk_as_reported", [r.id for r in rep.results if r.level == core.WARN])

    def test_waiver_needs_a_reason_and_a_waivable_rule(self):
        edit = para("Her client uses a wheelchair.")
        rep = self.gate(edit=edit, args=["--waive", "privacy.sensitive_terms=the seller asked about access"])
        self.assertClean(rep)
        self.assertEqual(next(r for r in rep.results if r.id == "privacy.sensitive_terms").waived, "the seller asked about access")
        shutil.rmtree(os.path.join(self.tmp, "root"))
        self.assertFalse(self.gate(edit=edit, args=["--waive", "privacy.sensitive_terms="]).ok)
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(edit=para("Her number is 415-555-0142."), args=["--waive", "privacy.raw_contact_details=it is fine"])
        self.assertIn("gate.waiver_refused", [r.id for r in rep.blocking])

    def test_allowed_values(self):
        edit = para("Call 510-555-0199 or write to care@seller-reports.test. Odalys Vantongeren hosted.")
        self.assertFalse(self.gate(edit=edit).ok)
        shutil.rmtree(os.path.join(self.tmp, "root"))
        self.assertClean(self.gate(edit=edit, args=["--allow-phone", "510-555-0199", "--allow-email", "care@seller-reports.test",
                                                    "--allow-name", "Odalys Vantongeren"]))

    def test_greeting_with_the_right_sellers(self):
        rep = self.gate(edit=top("Hi Pat and Sam, here is this week."))
        self.assertClean(rep)
        self.assertIn("wrong_file.greeting", [r.id for r in rep.results if r.level == core.PASS])

    def test_supporting_numbers_pass_when_right(self):
        rep = self.gate(edit=chain(
            para("Apr 13 is day 32 on the market. 4 of the 5 comparable sales were under contract by that day. Average 24 days, median 21."),
            para("This week: 4 follow-ups to 2 people on 2 days (2 calls, 1 text, 1 email)."),
            para('<span data-sr="week:inquiries">1</span> inquiry this week, <span data-sr="total:inquiries">1</span> since we listed.'),
            cell('data-sr-row="touches_outbound"', 0, "4 up 1")))
        self.assertClean(rep)
        passed = [r.id for r in rep.results if r.level == core.PASS]
        for rule in ("numbers.market_under_contract", "numbers.market_average", "numbers.week_channels", "numbers.marked_values",
                     "numbers.person_dates", "numbers.page_dates"):
            self.assertIn(rule, passed)

    def test_no_final_answer_said_as_all_of_one_kind_is_still_checked(self):
        def both_interested(d, t):
            for c in d["contacts"]:
                if C.is_counted(c) and c["status"] == "replied":
                    c["interest"] = "warm"
            C.finish_ledger(d)
        rep = self.gate(led=both_interested, edit=para("No final answer (2): all interested."))
        self.assertClean(rep)
        self.assertIn("numbers.no_final_interested", [r.id for r in rep.results if r.level == core.PASS])
        shutil.rmtree(os.path.join(self.tmp, "root"))
        # the same sentence on a page whose ledger says otherwise does not pass
        rep = self.gate(edit=para("No final answer (2): all undecided."))
        self.assertIn("numbers.no_final_undecided", [r.id for r in rep.blocking], rep.as_text())

    def test_weeks_folded_into_one_row(self):
        def fold(off):
            def edit(h, t):
                s = recount.sum_weeks(t.ledger["weeks"][:2])
                vals = [s["showings"], s["agent_reported_tours"], s["inquiries"], s["disclosure_contacts_new"],
                        s["open_house_groups"], s["touches_outbound"] + off, "&nbsp;", s["replies_inbound"],
                        s["conversations_with_feedback"], "%d / %d" % (s["price_too_high"], s["price_fair_or_positive"]), s["offers"]]
                row = '<tr data-sr-row="block:1-2"><th scope="row" %s>1 to 2 Mar 9</th>%s</tr>\n' % (
                    sample_page.CELL, "".join("<td %s>%s</td>" % (sample_page.CELL, v) for v in vals))
                h = cut(r'<tr data-sr-row="1">.*?</tr>\n')(h, t)
                return re.sub(r'<tr data-sr-row="2">.*?</tr>\n', lambda m: row, h, count=1, flags=re.S)
            return edit
        self.assertClean(self.gate(edit=fold(0)))
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(edit=fold(1))
        self.assertEqual([r.id for r in rep.blocking], ["numbers.table_weeks"], rep.as_text())
        self.assertIn("weeks 1 to 2 in one row", " ".join(rep.blocking[0].evidence))

    def test_every_build_is_held_to_the_standard_of_a_report_that_ships(self):
        rep = self.gate(edit=chain(para("Open house time: TBD."), swap(LINK_URL, 'href="link.html"')))
        failed = [r.id for r in rep.blocking]
        self.assertIn("hygiene.no_placeholders", failed)
        self.assertIn("hygiene.links_work", failed)
        self.assertFalse(hasattr(core, "BUILDS"))
        self.assertNotIn("build", rep.as_dict())
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            check_report.parse_args([self.path, "--ledger", os.path.join(self.folder, "ledger.json"), "--build", "draft"])

    def test_the_clean_page_has_no_notice_and_no_panel(self):
        for kind in ("email", "link", "print"):
            page = sample_page.build(self.fixtures["small"], self.identity, kind=kind)
            for word in ("DRAFT", "REVIEWER", "sr:build", "draft_notice", "reviewer_panel", "Tags"):
                self.assertNotIn(word, page)

    def test_long_line_is_a_note_for_the_sender(self):
        rep = self.gate(edit=lambda h, t: h.replace("\n", " "))
        self.assertClean(rep)
        note = next(r for r in rep.results if r.id == "email_safety.line_length")
        self.assertEqual(note.level, core.WARN)
        self.assertIn("quoted-printable", note.message)

    def test_a_check_that_cannot_run_is_a_failure(self):
        from unittest import mock
        from sr_checks import brand
        rep = self.gate()
        with mock.patch.object(brand, "check", side_effect=RuntimeError("boom")):
            crashed = sr_checks.run(rep.ctx, families=["brand"])
        self.assertEqual([r.id for r in crashed.blocking], ["brand.crashed"])
        ctx = rep.ctx
        ctx.ledger, ctx._cache = {"report": {}, "listing": {}}, {}
        unreadable = sr_checks.run(ctx, families=["ledger", "numbers"])
        self.assertEqual(sorted(r.id for r in unreadable.blocking), ["ledger.readable", "numbers.recount"])

    # ---- the command line ---------------------------------------------------------------------
    def cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = check_report.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_cli_exit_codes_and_json(self):
        self.gate()
        code, out, _ = self.cli(self.argv)
        self.assertEqual(code, 0, out)
        self.assertIn("SHIP GATE: passed", out)
        report = os.path.join(self.tmp, "gate.json")
        code, out, _ = self.cli(self.argv + ["--json", report])
        with open(report, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["ok"])
        self.assertEqual(data["pages"][0]["kind"], "email")
        self.assertTrue(all(set(r) >= set(("id", "level", "message", "evidence")) for r in data["pages"][0]["results"]))
        shutil.rmtree(os.path.join(self.tmp, "root"))
        self.gate(edit=swap('data-sr="contacted">5<', 'data-sr="contacted">6<'))
        code, out, _ = self.cli(self.argv)
        self.assertEqual(code, 1)
        self.assertIn("FAIL  numbers.contacted", out)
        self.assertIn("BLOCKED", out)
        code, out, _ = self.cli(self.argv + ["--json", "-"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["ok"])
        code, out, _ = self.cli(self.argv + ["--only", "brand"])
        self.assertEqual(code, 0, out)

    def test_cli_input_errors_exit_2(self):
        code, _, err = self.cli(["--issue", os.path.join(self.tmp, "nowhere")])
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err)
        self.gate(file="email.html")
        code, _, err = self.cli([self.path, "--ledger", os.path.join(self.folder, "ledger.json"), "--allow-synthetic",
                                 "--today", self.ledger["report"]["report_date"]])
        self.assertEqual(code, 0)                                   # the listing folder is found from the issue folder
        loose = os.path.join(self.tmp, "loose.html")
        shutil.copy(self.path, loose)
        with self.assertRaises(SystemExit):                         # there is no --build: one build mode
            self.cli([loose, "--ledger", os.path.join(self.folder, "ledger.json"), "--build", "draft"])
        code, _, err = self.cli([loose, "--ledger", os.path.join(self.folder, "ledger.json"), "--only", "nonsense"])
        self.assertEqual(code, 2)

    def test_cli_checks_every_page_in_the_issue_folder(self):
        self.gate(fx="busy")
        with open(os.path.join(self.folder, "link.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(sample_page.build(self.ledger, self.identity, kind="link").replace(
                UNDER, UNDER + "<p>One offer came in at $1,120,000.</p>"))
        code, out, _ = self.cli(self.argv + ["--json", "-"])
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual([p["kind"] for p in data["pages"]], ["email", "link"])
        self.assertEqual([p["ok"] for p in data["pages"]], [True, False])

    # ---- the parts ----------------------------------------------------------------------------
    def test_recount_agrees_with_the_fixtures_and_the_contract(self):
        for key, d in self.fixtures.items():
            mine = recount.recount(d)
            self.assertEqual(recount.differences(d, mine), [], key)
            theirs = C.recount(d)["totals"]
            for k, v in mine["totals"].items():
                if k in theirs:
                    self.assertEqual(v, theirs[k], "%s totals.%s" % (key, k))
        d = copy.deepcopy(self.fixtures["small"])
        d["contacts"][0]["touches"].pop()
        self.assertTrue(recount.differences(d, recount.recount(d)))

    def test_page_reader(self):
        p = page.Page('<html><head><title>T</title><style>p{color:red}</style></head><body><div style="display:none">pre</div>'
                      '<table data-sr-table="weeks"><tr><th data-sr-col="LABEL">Week</th><th>Tours</th></tr>'
                      '<tr data-sr-row="1"><td>1 Mar 9</td><td><span data-sr="x">1,176</span> sq ft</td></tr></table>'
                      '<p data-sr-section="footer">A&nbsp;B<br>C</p><!-- note --></body></html>')
        self.assertEqual(p.title, "T")
        self.assertEqual(page.numbers_in(p.flat(root=p.hooks("x")[0])), [1176])
        self.assertEqual(page.numbers_in("$798,888 on 3 days, 2.5 baths, 101.6%, No. 07, #214"), [3, 7])
        self.assertEqual(p.hidden_text(), "pre")
        self.assertIn("A B\nC", p.text())
        self.assertNotIn("color:red", p.text())
        self.assertEqual(p.comments[0][1].strip(), "note")
        self.assertEqual([c.text for c in p.named_table("weeks")[0].rows[1][1]], ["1 Mar 9", "1,176 sq ft"])
        self.assertEqual(p.section_names(), ["footer"])

    def test_evidence_never_repeats_a_private_value(self):
        rep = self.gate(edit=para("Her number is 415-555-0142. Write to odalys@harborlight.test. The lockbox code is 4471."))
        text = json.dumps(rep.as_dict())
        for secret in ("415-555-0142", "odalys@harborlight.test", "4471"):
            self.assertNotIn(secret, text)
        blocked = self.identity["blocklist"]["dre"][0]
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(edit=swap("</body>", "<!-- %s -->\n</body>" % blocked))
        self.assertNotIn(blocked, json.dumps(rep.as_dict()))

    def test_layout_probe_is_off_unless_asked(self):
        rep = self.gate()
        self.assertEqual([r.level for r in rep.results if r.family == "layout"], [core.SKIP])

    @unittest.skipUnless(layout_probe.find_browser(), "Edge or Chrome is not installed")
    def test_layout_probe_measures_a_real_render(self):
        fluid = ('<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                 '<title>Probe</title></head><body style="margin:0"><table width="100%%" bgcolor="#FFFFFF"><tr><td style="font-size:15px">'
                 'A short line of text that wraps on a phone without trouble.%s</td></tr></table></body></html>')
        rep = self.gate(args=["--probe", "--only", "layout"], edit=lambda h, t: fluid % '<div style="width:700px">A very wide block</div>')
        self.assertIn("layout.no_sideways_scroll", [r.id for r in rep.blocking], rep.as_text())
        shutil.rmtree(os.path.join(self.tmp, "root"))
        rep = self.gate(args=["--probe", "--only", "layout"], edit=lambda h, t: fluid % '<span style="font-size:10px">tiny</span>')
        self.assertIn("layout.no_sideways_scroll", [r.id for r in rep.results if r.level == core.PASS], rep.as_text())
        self.assertIn("layout.rendered_font_size", [r.id for r in rep.blocking], rep.as_text())


add_cases(GateTests, CASES)


if __name__ == "__main__":
    unittest.main()
