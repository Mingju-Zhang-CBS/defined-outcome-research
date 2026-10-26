# Methods | Three different economic objects

## 1. Source contract and normalized target

The factual ledger records BJAN's 2026 terms and FJAN's separately dated terms. BJAN is the primary shape example; FJAN is a cross-check that product name alone does not identify dates, buffer or fees. These are research-date document snapshots, not a live product screener. Read [provenance](PROVENANCE.md) for source dates, page locators and rights.

Let the original reference be S0, terminal price ST, first-loss buffer b and gross cap c. With x = ST/S0 - 1, the stylized target return is:

```text
x + b                 if x < -b
0                     if -b <= x < 0
min(x, c)             if x >= 0
```

Its gross terminal claim is ST + (S0-ST)+ - (S0(1-b)-ST)+ - (ST-S0(1+c))+. Signed legs are a price claim, long at-the-money put, short lower-strike put and short upper-strike call. The units are dollars per normalized reference claim. The stylized claim pays b*S0 even when ST=0. That model-specific floor is not a guarantee on an actual fund, whose options, quantities, expenses and operations differ.

The BJAN factsheet uses a positive-strike deep-in-the-money call. Replacing a call of strike k with a claim paying ST changes payoff by min(ST,k) for equal quantities. Rounded strikes alone cannot recover fund shares, cash, option multipliers or initial NAV. This project therefore audits the listed strikes, but does not claim to replicate the actual fund.

## 2. Cost, interim value and dividends

European calls/puts use Black-Scholes with constant r, sigma and dividend yield q; maturity, zero volatility and zero spot have explicit boundary branches. A claim paying ST but no intervening dividends has value S*exp(-q*tau). It is different from owning a share and retaining its dividends. Default q=0 makes the price-claim interpretation simple; code supports q>0 consistently. Actual fund exposures and dividends must be checked against their documents.

Sum signed leg marks to obtain V(t,S). The quote unit is never silently converted from ETF-share dollars to this normalized claim. For each scenario, purchase cost is V(t,S), rather than an assumed 100. Cash's terminal benchmark is initial cash*exp(r*tau).

For a model budget 100, the fair-cap routine solves V(0,S0;c)=100 using a bracket [0.0000001,5]. A missing root is recorded as infeasible in that bracket; no cap or dataset is searched for attractive returns. This is a fixed-parameter pricing counterfactual, not the issuer's actual cap-setting procedure or a valuation error claim.

## 3. The fee convention is part of the model

Published gross and net product terms are recorded as separate facts. They are not estimated by the model. Subtracting a percentage of initial capital and charging a percentage of changing NAV are different operations.

In the declared scenario, fees remove claim units continuously, so remaining terminal claim units are multiplied by exp(-f*tau). This is exact for that unit-depletion convention with a constant fee rate; it is an approximation to actual fund accounting. It does not estimate daily ETF accruals, taxes, extraordinary expenses or a path of fund holdings. Prior costs are already reflected in a later entry mark; only remaining-period scenario fees are charged.

```text
entry debit per claim = V_entry * (1 + entry_half_spread_bps / 10000)
net terminal claim   = gross_payoff * exp(-f*tau) * (1 - exit_bps / 10000)
investor return      = net terminal claim / entry debit - 1
```

Default entry grids use remaining time 1, .75, .5 and .25 years; spot 80,100,120; volatility 10%,20%,40%. The rate is 3%, q=0 and source-shaped cap/buffer are fixed. These are 36 counterfactual states, not observations of a path or historical backtest. At elapsed zero, spot 80/120 represent instantaneous stress states after the original reference is fixed at 100, not literal inception observations. Fee/friction tables contain nine additional fixed combinations. Quotes do not enter these calculations.

## 4. Fully funded integer accounts

Each package contains the signed legs with multiplier 100. Purchase cost includes the full net debit, a declared spread mark-up and a $4 package commission. Packages = floor(budget/package_cost); residual cash remains visible and earns the declared cash rate. Settlement adds the fee-depleted terminal claim to accrued residual cash and compares total wealth with the original budget. Both initial and terminal conservation identities are checked.

The net-debit account assumes enforceable package netting. Standalone short-leg margin, exercise/assignment differences, broker approval, minimum tick, execution size and legging risk are outside the model. A budget that cannot fund one package gets zero packages and a visible status; it is not replaced with fractional options.

## 5. Real observations require a different channel

The optional quote CSV accepts two mutually exclusive types: `nav` and `bid_ask`. It requires an instrument, HTTPS source, explicit `USD_per_ETF_share` unit, currency, timezone-aware observation/retrieval clocks and a delayed flag. It rejects crossed quotes, non-finite values, future observations and unit ambiguity. A quote can be time-aligned and still fail to prove a fill. NAV has no bid/ask midpoint.

The published CSV contains headers only. No quote data is bundled and no issuer NAV reconciliation is performed. A proper comparison would require licensed synchronized quotes, verified option/fund quantities, share conversion, cash/accrued expenses, consistent underlying/dividend assumptions and clock alignment. The audit does not perform those missing steps automatically.

## 6. Reproducibility and tests

[protocol.json](../protocol.json) fixes scenarios before numerical results. The package carries the same protocol and minimal factual ledger inside its wheel. The report manifest fingerprints package sources, protocol, facts, outputs and environment. The command refuses to overwrite a nonempty output folder. Reproduction should compare economic tables and metrics, allowing floating-point tolerance; wall time, allocation peaks, timestamps and PNG byte encoding are environment-dependent.

Tests check payoff slopes/continuity, numerical integration independent of the leg pricer, put-call parity with dividends, boundary prices, cost normalization, fee compounding, budget roots, integer cash conservation and quote input failures. Independent numerical agreement validates the declared model only.


## Worked example and interpretation


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
