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
