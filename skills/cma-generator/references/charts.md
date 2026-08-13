# Chart and Visualization Guide for CMA Reports

Generate all charts using matplotlib in Python, save as PNG images, then embed into the PDF using ReportLab's ImageRun or canvas.drawImage. Use the brand colors from branding.md.

## Required Charts (generate ALL of these for every CMA)

### 1. Comp Price Comparison Bar Chart
- Horizontal bar chart showing each comp's sold price
- Subject property shown as a dashed vertical reference line
- Bars colored gold (#C5A55A), subject line in black
- Sort by price descending
- Label each bar with address (abbreviated) and sold price
- Title: "COMPARABLE SALES — SOLD PRICES"

### 2. Price Per Square Foot Comparison
- Horizontal bar chart or dot plot showing $/sqft for each comp
- Subject's estimated $/sqft range shown as a shaded band
- Gold bars, black labels
- Title: "PRICE PER SQUARE FOOT ANALYSIS"

### 3. Days on Market Distribution
- Bar chart showing DOM for each comp
- Color-code: green (<15 days), gold (15-30 days), red (>30 days)
- Add a horizontal line for median DOM
- Title: "DAYS ON MARKET — COMPARABLE SALES"

### 4. List-to-Sale Price Ratio
- Bar chart showing the % over/under asking for each comp
- Bars above 100% in gold (sold over asking), below in a muted tone
- Add horizontal reference line at 100%
- Title: "LIST-TO-SALE PRICE RATIO"

### 5. Pricing Strategy Outcomes
- Grouped or stacked bar chart showing:
  - Strategy 1 (Above Market): avg DOM, avg list-to-sale ratio
  - Strategy 2 (Below Market): avg DOM, avg list-to-sale ratio
  - Strategy 3 (At Market): avg DOM, avg list-to-sale ratio
- Makes it visually obvious which strategy performs best
- Title: "PRICING STRATEGY PERFORMANCE"

### 5b. Over/Under Original-List Split (headline of the pricing-behavior section)
- Single horizontal stacked bar: % of comps that sold OVER / AT / UNDER their ORIGINAL ask
- Green = over, gray = at (±1%), coral = under; label each segment with its %
- Pair with one big stat callout, e.g. "71% sold over original ask; median 103% of original list"
- Title: "HOW THIS MARKET PRICES"

### 5c. List-to-Sale % vs Days on Market — CORRELATION SCATTER (required when original-list data exists)
- Scatter, one dot per sale: x = list-to-sale % (sold ÷ ORIGINAL list), y = days on market
- Add a least-squares trendline (compute slope/intercept in Python; draw as a 2-point line dataset)
- Color dots by bucket: green (sold over), gray (at), coral (under)
- Caption states the Pearson r and reads it in plain words ("r = -0.58: the further over asking, the fewer days")
- This is the single most persuasive chart in a listing CMA. Title: "PRICE SHARP, SELL FAST — LIST-TO-SALE % vs DAYS ON MARKET"
- See `references/pricing-behavior-analysis.md` for the full spec, metrics, and narrative.

### 6. Market Trend Chart (MANDATORY, not optional — hard rule added 2026-08-13 after the third repeated failure on this exact point)

**Do not hand-plot this from your own comp set.** A line connecting 2-4 comps you happened to pull is not a market trend chart, it is a handful of dots with a line drawn between them, and it has been called out as wrong three separate times now. A real trend chart comes from the MLS's own Stats module, which aggregates the full population of listings (hundreds to tens of thousands), not the handful you individually verified for the comp table.

**Why the previous version of this rule still failed:** an earlier draft of this rule told the agent to pull the MLS Stats data and *retype it* into a new Chart.js chart. That transcription step is exactly what kept getting silently skipped under time pressure, because nothing forced it to happen — a hand-plotted 2-4 point line and a "reproduced" chart look identical in the final HTML, so a rushed pass can't tell the difference and the step just gets dropped. The fix is to make the MLS chart itself the artifact, not data the agent re-types.

**How to source it, every time, no exceptions:**
1. In MLS Matrix, go to Search → Stats (not Residential Search).
2. Customize tab: set **Time Frame** (default Past 3 Years unless the report calls for a different window), **Statistic** = Sale Price, Average (or Median if that's what the client's own reference chart used), **Chart Type** = Smooth Line, **Group By** = Month.
3. Set the search criteria to match the report's geography and property type as narrowly as is still statistically meaningful (Postal City, or Zip Code, or MLS Area — property sub type filtered the same way as the comp search, e.g. "Duplex" or "Single Family Home").
4. Open the **Chart** tab to see the rendered line. **Take an actual screenshot of this rendered chart** (the browser tool's screenshot/zoom action, not a description of it) — this screenshot is the required evidence the step happened, the same way a comp's individual listing page is the required evidence for a verified sold date.
5. **Embed that screenshot directly in the report as the market trend chart** (as an `<img>` for the interactive HTML, or the same PNG re-embedded as base64 for the email-safe version). This is the default and preferred method — it guarantees the chart the client sees is the literal chart MLS produced, with zero transcription risk.
6. Only recreate the series as a Chart.js chart instead of embedding the screenshot when the report's design genuinely requires brand-matched styling AND the underlying screenshot has already been taken and kept as the source of truth to check the recreation against before delivering. Do not skip straight to recreation without first having taken the screenshot.
7. Caption the chart with the exact criteria shown at the bottom of the MLS Stats page (time frame, geography, property type, listing count), the same way MLS itself captions it — this caption is what makes the chart verifiable rather than decorative.
8. If MLS Stats access is genuinely unavailable for a given geography (e.g., no reciprocal data), do not silently fall back to a hand-plotted line. Say so explicitly in the report and in your response to the user, and use a clearly-labeled third-party source (Redfin, Zillow) instead, captioned as such.

**Before delivering any CMA, confirm out loud (in your own response to the user, not just in the file) that a real MLS Stats screenshot was taken and is embedded or was used as the check against a recreation.** This is the check that has been skipped three times; saying it explicitly, backed by an actual screenshot action in the tool log, is the fix.

- Title: "MARKET TREND — [CITY/ZIP] — [STATISTIC] SALE PRICE"

### 7. Subject Property Positioning Map
- A visual showing where the subject falls within the comp range
- Can be a number line / gauge style visual
- Show conservative, competitive, and stretch ranges as colored bands
- Arrow or marker showing recommended offer point
- Title: "RECOMMENDED OFFER POSITIONING"

## Chart Styling Rules

```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Brand colors
BLACK = '#1A1A1A'
GOLD = '#C5A55A'
DARK_GOLD = '#A88B3D'
LIGHT_GOLD = '#F5EFDC'
WHITE = '#FFFFFF'
GRAY = '#666666'
GREEN = '#4CAF50'
RED = '#E57373'

# Standard chart setup
def setup_chart(fig, ax, title):
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    ax.set_title(title, fontsize=12, fontweight='bold', color=BLACK, pad=12, fontfamily='sans-serif')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRAY)
    ax.spines['bottom'].set_color(GRAY)
    ax.tick_params(colors=GRAY, labelsize=8)
    return fig, ax

# Save chart
def save_chart(fig, filename, dpi=200):
    fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor=WHITE, edgecolor='none')
    plt.close(fig)
```

## Email Chart Embedding

For email HTML output, charts must be embedded as base64 data URIs:

```python
import base64
from io import BytesIO

def chart_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'data:image/png;base64,{img_base6