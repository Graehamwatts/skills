# Changes to the data contract

What changed in the contract (`data-contract.md`) and when: first against the approved mockup's two dataset
shapes, then with each later decision. It is a record for anyone reading an older ledger or an older note.
The current shape is in `data-contract.md`; nothing here is needed to build a report.

## Against the approved mockup shape

The mockup carried two dialects (the first listing's file and the richer file of the second) and the generator
bridged them. This contract picks one. Every change:

**Removed (feedback only):** `recommendation`, `decision_log`, `seller_ask`, and
`pricing_tally.statement_safe` (it explained what silence on price means).

**Removed after the design review (2026-10-13):** the review step, with `meta.tag_review`, `confirmed_by`,
`confirmed_on`, `contacts[].tag_source(s)`, the draft folder, `manifest.build_kind`, the notice, the panel and
the `--draft`, `--final` and `--allow-unreviewed` switches. One build mode replaces them.

**Added, as asked:** per-contact `themes` with `theme_other`, `liked` with `liked_other`, `price_asked`,
`next_followup_date`; top-level `themes_vocabulary`; `is_open_house_host`, `phone_out_of_service` and the
separate-day fields; `report.since_week_closed`; `sources_used`; `data_quality`. Provenance is in `raw.json`
and `curation.json` only and is rejected in a ledger.

**Unified, because one renderer needs one shape:**

1. `schema_version` and a required `meta` block (`slug`, `built_at`).
2. Counts are buyer side in the ledger (the mockup subtracted hosts on the page). New `contacts[].team_side`
   and `totals.team_side_set_aside`.
3. `keybox_showings` and `agent_reported_tours` are stored apart everywhere. `showings_undated` and
   `showings_approximate_date` became `tours_undated`, `tours_approximate_date`, plus `tours_unconfirmed`.
4. New engagement type `disclosure_on_list` (on the disclosure tab, no record of sent or opened). Buyers an
   agent shared the package with are `disclosure_shared_by_agent` and moved out of `disclosure_contacts` into
   `totals.disclosure_shared_buyers`.
5. `report.tracking` plus nulls replaces the implicit "is this recorded" tests.
6. One reply rule: an inbound touch or a call that reached the person, once per person per day
   (`sr_contract.is_reply`). `got_response` is gone and `responses` became `replies_inbound`.
7. `direction` null became `unknown`. New outcome `did_not_connect`.
8. `feedback_log` is required on every contact, with entry-level `price_reaction`, `price_asked`, `themes`,
   `liked`, `source`, `counts_as_conversation`. A conversation is one person on one day.
9. `pricing_tally.people_with_feedback` is the one denominator. Added `price_asked_recorded`, `asked_directly`.
10. `objection_tally` and top-level `themes` became `themes_tally`. `price` is not a theme. New `liked_tally`.
11. `price_periods` and `offer_watch` (with `lead_state`) are derived blocks in the ledger.
12. `since_week_end` moved to `report.since_week_closed`. The flags `in_report_week` and `after_week_end` are
    gone, because nothing after the week end is in the ledger body.
13. `represented_by` holds a contact id in every listing (`via_agent_id`, `party_id` and `counts_in_totals`
    are gone). New status `through_agent`.
14. `attempts` became `followup.outbound_days`. `awaiting_reply_3plus_attempts` counts days since the last answer.
15. Smaller renames and additions: `price_history[].event` is `listed` or `price_change`; open houses gain
    `counted_unit`, `date_quality`, `host_contact_id`; offers gain `id`, `contact_id`, `note_safe`; marketing
    `status` is a key, not a display string; `definitions` is gone (see `counting-rules.md`); `status_note`
    became `status_note_safe`; `tag_notes` moved to `curation.json`.
16. New totals: `contact_records`, `team_side_people`, `contacted_through_host`, `awaiting_reply_quiet`,
    `awaiting_reply_answered_before`, `open_no_final_answer` (and `_quiet`), `calls_not_connected`,
    `people_with_feedback`, `offers_by_state`. New per week: `outbound_people`, `outbound_distinct_days`,
    `open_house_sessions_without_count`.

**Changed with the summary-on-top layout (2026-10-13):**

17. `showings` is one derived number (key-box showings plus tours agents reported) in every week, price
    period and the totals. The two kinds are still stored apart, and an inquiry is never a showing.
18. New derived fields on every contact: `lists`, `primary_list`, `offer_word`, `active_this_week`. New totals:
    `showings`, `lists`, `lists_active_this_week`, `online_views`, `online_saves`. New per week: `showings`,
    `online_views`, `online_saves`.
19. New optional top-level blocks `online` and `nearby` (null until collected).
20. People are in the four lists under "The details" (no "conversations", "still waiting", "adds up" or
    directory sections). The gate's hooks for people are `data-sr-list` and `data-sr-entry="<form>:<id>"`.

**Added with the optional sections (2026-10-13):**

21. Per-listing files `online_views.json` and `nearby.json`, and `listing.json` `extras`. `ledger.online` gains
    `since_listing`; `ledger.nearby.homes[]` gains `change_date_approximate`; a marketing channel gains `ends_on`.
22. `totals.online_views` and `online_saves` are the count since listing (a site's running count where one was
    read), no longer only the weeks added up.
23. New source kinds `portal_page`, `operator_numbers`, `nearby_lookup`. New limits for the lookups
    (`sr_contract.LIMITS`). A marketing block with nothing on and nothing checked for the issue is left out.

**Added after the first two real issues (2026-10-13, late):**

24. `listing.json` may carry `subject_address` (the address as the seller's subject line writes it) and
    `tracking.lockbox` (a combination lockbox, so no electronic showing record). `hero_photo` is an https
    address or null, never a local path.
25. `nearby.json` gains `watch_site` (`mlslistings` or `redfin`) and `candidates.site`. `plan` follows the watch
    list's site; a watch result from the other site is refused.
26. `ledger.online` is built only when a reading for the issue's week is on file. `build_ledger.py` drops a
    nearby sale's day count when the market chart gives the same sale a different one (`one_day_count`).
27. `issues\NN\manifest.json` gains `subject`. `freeze` removes an old `email_gmail.html` when an email is kept
    without a new one.
