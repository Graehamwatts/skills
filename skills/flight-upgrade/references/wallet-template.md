# Wallet Template

Copy this to `skills/flight-upgrade/outputs/wallet.md` and fill it in. **Never fill it in here.** This template file is committed to a public repo. The copy in `outputs/` is gitignored and is the only place real values belong.

Partial is fine. The skill asks about gaps rather than demanding everything up front.

---

## Identity

```
Name as ticketed:
Known Traveler Number:
Home airports:
```

## Elite status

| Airline | Program | Tier | Expires |
|---|---|---|---|
|  |  |  |  |

Note the tier honestly. Status drives upgrade list order more than anything else, and an overstated tier produces a dashboard that lies about likelihood.

## Airline miles

| Program | Balance | Loyalty number (last 4) | Miles expire? |
|---|---|---|---|
|  |  |  |  |

## Upgrade certificates

| Type | Airline | Quantity | Expires | Used on |
|---|---|---|---|---|
|  |  |  |  |  |

United PlusPoints, Delta Global and Regional Upgrade Certificates, American systemwide upgrades. Expiry matters enormously. A certificate expiring in six weeks should be spent on a worse flight rather than hoarded for a better one that may not come.

## Bank points

| Program | Balance | Transfers to (airlines) |
|---|---|---|
| Chase Ultimate Rewards |  |  |
| Amex Membership Rewards |  |  |
| Capital One |  |  |
| Citi ThankYou |  |  |
| Bilt |  |  |

Leave the transfer column blank if unsure. The skill web-searches current partners each run anyway, since these change.

## Cards

| Card | Last 4 | Airline co-brand? | Travel credit | Lounge |
|---|---|---|---|---|
|  |  |  |  |  |

**Last four only.** Never write a full card number here, even in a gitignored file.

## Preferences

```
Miles floor (cents per mile):        1.3
Max cash for a confirmed upgrade:
Saving points for anything specific:
Cabin preference on flights under 5h:
```

The last line matters. If a three-hour domestic first class seat is not worth real money to him, the dashboard should say so instead of ranking paths to a seat he does not actually want.

## Booked flights

| Route | Date | Airline | Conf code | Fare class | Paid |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Clear rows after each trip. There is no reason to keep old confirmation codes sitting on disk.
