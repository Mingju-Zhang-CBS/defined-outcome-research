# Worked example | Purchase price changes the outcome

**Every valuation in this example is synthetic.** The cap/buffer shape is motivated by public issuer terms; the example is not a trade in an ETF.

## 1. Fix the original contract

Original reference 100, lower put 91, long put 100 and short call 116.46. Hold one price-only claim, buy the 100 put, sell the 91 put and sell the 116.46 call. At terminal reference 80, the signed payoff is `80 + 20 - 11 - 0 = 89`. At 100 it is 100; at 120 it is 116.46. These are dollar claim payoffs, before a purchase denominator or fees.

## 2. Value a later entry

Six months remain; current reference is 120, annual volatility 20%, continuously compounded rate 3%, dividend yield zero. The sum of European marks is **110.880029**. The buyer pays for remaining option time value; the payoff strikes remain anchored to the original reference.

With proportional-unit fee 0.79% annually, remaining claim units at expiry are `exp(-0.0079*0.5)`. At a final reference of 100, net claim wealth is `100*exp(-0.0079*0.5)` = 99.605779. Dividing by 110.880029 gives **-10.1680%**. At or above the cap strike, return is **4.6184%**. Neither calculation uses 100 as this buyer's entry cost.

The original 91 buffer-end reference is 24.17% below current reference 120. That price distance is not a percentage guarantee on the purchased claim. Read the payoff and denominator together.

## 3. Fund the account

Run `python examples/explain_entry.py` for a $25,000 budget with multiplier 100, a declared 10-bp entry half-spread and $4 commission per package. The account buys two complete packages, preserves the unspent cash and accrues it at 3%. Settlement adds fee-depleted claim wealth to cash wealth and checks the initial and terminal conservation identities. Commissions are per package; they are not a claim about broker option fees.

Compare the base-time accounts in [integer_accounts.csv](../reports/demo/integer_accounts.csv). The base package costs $10,003.77, so a $10,000 account cannot buy one. Treating it as a fractional package would conceal an implementation constraint.

## 4. Compare fee definitions carefully

The published net cap is a source fact. The continuous fee illustration is a separately declared convention. Applying unit depletion to a target wealth of 116.46 on a hypothetical 100 entry gives **15.5436%**. The actual model strip starts at 99.897781; its investor return uses that denominator. Do not mix these examples into a fund-reconciliation claim.

## 5. Keep real observations separate

The public [quote CSV](../examples/quotes.schema.csv) has headers and zero observations. To audit your own legally obtained observations:

```bash
python -m defined_outcome_research --quotes private-data/observations.csv --as-of 2026-10-23T20:00:00+00:00
```

The input must contain timezone-aware `observed_at` and `retrieved_at`, explicit USD-per-ETF-share units, a source, a delayed flag, and either NAV or bid/ask. The output reports age and type. It does not calculate a model-to-ETF price difference or prove execution. Such a comparison requires verified fund holdings and conversion units as well as matched clocks.

## 6. What would change the decision?

A later purchase denominator, different remaining time, implied volatility, dividend convention, fees, actual spread, margin or rounding can change an investor outcome. This project isolates those assumptions. It does not choose an investment or estimate an actual ETF return.

[Full report](../reports/demo/REPORT.md) · [Methods](METHODS.md) · [Sources](PROVENANCE.md)
