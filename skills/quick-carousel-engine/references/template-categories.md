# Quick Carousel Template Categories

Three categories, reverse-engineered from proven formats (not copied
verbatim — the whole point is Graeham's own numbers, own brand, own
markets). Pick ONE per post.

## Why these three, and not a straight clone of `kenny_fast`

Graeham pointed at the `kenny_fast` Instagram account (2026-09-09) as an
example of a realtor posting a steady stream of easy, engaging carousels —
data infographics ("Where People Are Moving") mixed with light pop-culture
tie-ins ("If Fairytale Princesses Had Boundaries..."). Neither of those two
specific posts carries any Kenny Truong branding — no logo, no contact
info — which is itself the tell: these are unbranded, repostable content,
not custom-designed-for-him templates. Confirmed via web research
(2026-09-09): **Coffee & Contracts** (~$54/mo) is the best-documented match
for "that company" — a real estate social-media subscription whose monthly
library explicitly includes both branded templates AND unbranded
"viral-ready"/meme content (their own marketing calls out "The Broke Agent
memes that give everyone shared, viral-ready content" — see
[coffeecontracts.com/blog](https://coffeecontracts.com/blog)). Graeham
explicitly declined to subscribe to one (2026-09-09): "we can now basically
build everything we need to with you." So instead of cloning that specific
company's templates, this skill reverse-engineers the underlying
*structure* that makes each format work and rebuilds it in Graeham's own
brand with his own data — the data/comparison carousel structure was
already independently documented in `viral-hook-library`'s reference notes
from unrelated real viral examples, which turned out to match the
`kenny_fast` reference closely once rebuilt (see Category 1's
`editorial_rank_list_card`).

**Not yet built: the illustrated pop-culture/meme category** ("Fairytale
Princesses" style). That's a different production problem — it needs
AI-generated illustration (character art, painterly style), not typography
on a data card, so it doesn't fit this skill's PIL-based engine. The
`https_mcp_higgsfield_ai_mcp` connector's `generate_image` tool can produce
that kind of illustration on request; flag to Graeham as a possible
Category 4 if he wants it pursued, but don't build it speculatively.

## Category 1 — Trend/Stat Editorial Carousel

**Source:** `viral-hook-library/references/notes/15_sfgate-rent-carousel.md`
(SFGate's "Rent in SF's Alamo Square is up 42%" carousel — 1.7K likes, 181
comments, real editorial data journalism packaged for swiping).

**Two ways to ship this — pick based on the topic, not by default:**

**1A — Standalone editorial post (usually the right default).**
`editorial_rank_list_card` — ONE image, not a multi-slide carousel. This is
the direct, faithful analog of the exact reference Graeham pointed to
("Where People Are Moving": light background, bold black headline with one
gold accent word, a small `sub_text` line of context, and a two-column
tinted ranked list — muted red "Leaving" vs. muted green "Moving To", 10
rows each, numbered badges). It's the fastest thing in this whole skill:
one function call, one data pull (a real ranked list with a real source),
done. Use this whenever the topic genuinely IS a ranked list or two-sided
comparison — it doesn't need a swipe to land.

**1B — Multi-card carousel (when the topic needs more room).**
Reverse-engineered from `viral-hook-library/references/notes/15_sfgate-rent-carousel.md`.
5-7 cards:
1. `quick_title_card` — the single most shocking stat as the hook, e.g.
   "RENT IN REDWOOD CITY IS UP 18%." Kicker line: "It signals a larger
   trend →."
2. `impact_takeover_stat_card` (or `quick_title_card` again) — one line of
   context: why this is happening (rate environment, AI-boom hiring,
   inventory, etc.)
3. `quick_table_card` — a short data barrage by neighborhood/sub-market
   (3-5 rows). This is the card type that does the most work — hyper-local
   names trigger recognition and comment-section debate from locals, per
   the source note.
4. `quick_rank_card` or `quick_table_card` — zoom out to the region-wide
   version of the same stat.
5. `quick_cta_card` — "Comment [KEYWORD] for the full breakdown."

**Data sources (pick what's actually current — never invent a number):**
Zumper/Apartment List rent data, Redfin/Zillow migration or price data,
Windsor's own Search Console pull (`content-calendar` Source 2) if the topic
overlaps a rising query, or a fresh web search at build time for anything
newer than what's already in the repo. Cite the source and month on every
stat card via the `source_note` param — never ship an uncited number.

**Cadence:** this is the TOFU/MOFU reach play — closest analog to
`content-pillars.md`'s Pillar 3 (Market Data & Analysis) and Pillar 5
(Development & Local News), just in carousel form instead of video.

## Category 2 — Price/Market Comparison Carousel

**Source:** `viral-hook-library/references/notes/13_2m-across-america-carousel.md`
("$2M in America looks wildly different depending on where you are" —
price-anchoring comparison content, inherently debate-generating, evergreen).

**Structure (5-6 cards):**
1. `quick_title_card` — "WHAT $[X] GETS YOU ACROSS THE PENINSULA."
2. `quick_rank_card` × 4-5 — one per sub-market (East Palo Alto, Redwood
   City, Palo Alto, Menlo Park, San Mateo County), SAME layout every card
   (city name, beds/baths/sqft, price) so the swiper's eye only registers
   what changed. This is the exact discipline the source note calls out as
   the reason the format works.
3. `quick_cta_card` — "Which one would you pick? Comment below" (comment
   farming is the point — the source caption explicitly asks this).

**Data sources:** `mls-matrix-scraper` for real current listings at a
comparable price point, or Windsor/Search Console median-price data per
sub-market if doing a "median home price" version instead of a specific
listing comparison. Never invent bed/bath/sqft/price combinations — pull
real active or recently-closed comps.

**Fair Housing note:** compare on price/sqft/beds/baths/lot size/property
type only — never frame a sub-market comparison around who lives there,
school quality, or "which is nicer/safer." This is the same guardrail
`content-creation-engine/CLAUDE.md`'s Fair Housing section already states
repo-wide; it applies here just as much as to scripted content.

## Category 3 — PropCast Listing Snapshot ("This Week on the Peninsula")

**Not reverse-engineered from anyone else's account** — this one is
Graeham's own listing intelligence turned into a fast recurring format,
per his 2026-09-09 direction to "take the intelligence in our listings...
that we have coming up and use that."

**Structure (3-4 cards):**
1. `quick_title_card` — "[N] NEW LISTINGS JUST HIT THE PENINSULA."
2. `quick_table_card` — breakdown by price band or sub-market (real counts
   only, pulled fresh for the week being posted).
3. `quick_cta_card` — "Comment LISTINGS and I'll send the full sheet."

**Data source:** Graeham's own PropCast / `mls-matrix-scraper` output for
the current week. This is the one category where "the real numbers" means
literally counting what's live right now — don't reuse last week's counts.

**Cadence:** pairs naturally with the Monday weekly-plan email cadence in
`content-calendar`'s locked "Email Delivery" section — the same week's data
that goes into the weekly calendar can seed this carousel with almost no
extra research.
