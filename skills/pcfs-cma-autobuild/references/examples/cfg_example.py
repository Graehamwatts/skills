"""Example WORK/cfg_<key>.py. One file per client. Every dollar figure in the prose must come from
`build.py <key> --facts`. The client named here is made up."""
from comps import COMPS

CFG = dict(
    key='abc', mkt='epa', file='CMA_123_Example_St.html',
    first='Jordan', client='Jordan Sample', email='client@example.com', due='Wed, Oct 14, 2026',
    addr_full='123 Example Street, East Palo Alto, CA 94303', street='123 Example Street', city='East Palo Alto',
    paid=625000, paid_label='Apr 2016',
    # Three ranges that do not overlap. val_mid must be the exact midpoint of r_mid.
    val_mid=1040000, r_low=(950000, 1000000), r_mid=(1010000, 1070000), r_top=(1090000, 1150000),
    # Optional when the value is flat against the purchase price:
    # gain_text='About even', gain_label='With what you paid',
    subj=dict(bdba='3/2', sf=1119, lot=6413, yb=1951, cond='Maintained (2016 listing)'),
    subj_note='Owned since 2016. 3 bed, 2 bath on a 6,413 sq ft lot.',
    home_rows=[
        ('Address', '123 Example Street, East Palo Alto, CA 94303'),
        ('Parcel', '000-000-000'),
        ('Configuration', '3 bed / 2 bath, single story, 1,119 sq ft on a 6,413 sq ft lot'),
        ('Year built', '1951'),
        ('Owned since', 'Apr 2016 (purchased for $625,000, 10.5 years ago)'),
        ('Location', 'The Gardens, East Palo Alto, east of Highway 101'),
        ('On record', 'Listed at $598,888 in March 2016 and sold $26,112 over asking.'),
    ],
    lead=("Hi Jordan, here is an update on your home, just keeping you informed. Short version: going by the sales around you over the last six months, "
          "your home is most likely worth about <strong>$1,040,000</strong> today. You bought it in April 2016 for $625,000, so you're up roughly <strong>$415,000</strong>, "
          "about 66 percent, before loan payoff or selling costs."),
    story=[
        "Paragraph 1: the two or three sales that say the most about this home, with address, size, price and month.",
        "Paragraph 2: what pulled other sales higher or lower (condition, lot, baths, a second unit).",
        "Paragraph 3: how pricing played out, including a home that is sitting or was cut.",
        "Paragraph 4: the market in numbers (sale to list, days to an offer, share over asking, months of inventory, the trailing median and its range).",
        "Paragraph 5: one or two sentences on where that leaves the owner.",
    ],
    comps_intro='I went through every single-family sale within about half a mile of you over the last six months and split them by how closely they match your home.',
    sim_card='3-bedroom homes of 1,010 to 1,310 square feet within a third of a mile of you, sorted by price. Your home is shown in the table at its most-likely value.',
    sim_scope='Single-family sales east of Highway 101 within a third of a mile of your home, 3 bedrooms, 1,010 to 1,310 sq ft',
    # sim_note_extra=' 123 Other St is not in the tier medians.',
    ref_card="These show the edges: a bigger renovated home and two fixers. Useful context, not the right yardstick for yours.",
    ref_left_out='Left out: sales over 1,750 sq ft and multi-unit properties.',
    act_card='What buyers near you can choose from today.',
    # act_left_out='Not shown: 2-bedroom homes and homes over 1,750 sq ft.',
    trend_intro='The price chart covers every single-family sale in East Palo Alto since October 2023. The other three charts cover the last 12 to 13 months.',
    trend_geo='East Palo Alto single-family homes',
    rate_par='Two or three sentences: the rate figures with dates, then what they have meant for buyers of homes like this one. End with the dates the rates carry.',
    cuts_par='How pricing played out on the closest sales: who sold fast near asking, who started high and gave ground. Days are days to an accepted offer.',
    journey_cap=("From your April 2016 purchase at $625,000 to today's most-likely value of $1,040,000. Dashed lines run to the bottom of the likely range ($950,000) "
                 "and the top of the strong-condition range ($1,150,000)."),
    # psf_cap='Override only when the subject size needs explaining, for example a main house plus a cottage.',
    cards=(
        "Likely range: the condition this assumes (mostly original kitchen and baths) and the sales that set it.",
        "Most likely value: the condition this assumes and the comps on either side of it. Midpoint about $1,040,000.",
        "Top of range: what would have to be true, and the sales that show it.",
    ),
    equity_par=("For perspective: you bought in April 2016 for $625,000. At about $1,040,000 today, that's roughly $415,000 of appreciation, about 66 percent, before loan payoff and selling costs. "
                "If you ever want to talk through what a sale would actually net you, I'm here."),
    bub_scope='within six-tenths of a mile of you, east of Highway 101, 700 to 2,100 sq ft',
    # replace=[('Most similar sales', 'Closest recent sales')],   # rare: rename table titles when the comps are a tier above the subject
    mail=dict(
        subj_line='A quick update on your East Palo Alto home',
        qc=[
            "Ownership checked: the last recorded sale is the client's own purchase. No sale since.",
            "Condition is unknown since 2016. The middle range assumes a well-kept home with some updating.",
        ],
        body=[
            "Hope you're doing well. Just sending over a quick comparative market analysis to keep you updated on Example Street.",
            "Short version: the market has been good to you. Based on the recent sales, your place is most likely worth about $1,040,000 today, with room toward $1,150,000 if it shows in top shape. You bought in 2016 for $625,000, so that's roughly $415,000 of appreciation.",
            "I put together a visual breakdown with the recent sales, the charts and where your home lands:",
        ]),
)
CFG.update(COMPS['abc'])
