# Interview discussion guide

## A two-minute route

1. Start with the question: does the original buffer describe a later buyer's loss? Use the real issuer terms to identify the period and reference, then separate the investor's entry cost.
2. Derive the piecewise terminal claim with a put spread and short call. Explain why a protective put alone costs more and why capped upside supplies financing.
3. Show the initial-cost table. A model claim costing something other than 100 cannot be assigned the original 100-based target return.
4. Walk through the six-month/reference-120 example. Read its actual cost and terminal cash flow from the report; do not turn the scenario into a historical trade.
5. Finish with evidence limits: no reconciled fund NAV, executable quote or realized return.

## Questions to be ready for

- Why is the lower-strike short put a source of tail loss? What is the difference between a buffer and a floor?
- Why is a price-only claim discounted for dividend yield? What changes if the basket actually owns stock and collects dividends?
- Why does a positive-strike deep call matter? Why are rounded strikes insufficient for fund replication?
- Which economic quantity is 16.46%: a contract/reference cap, a model purchase return, or a dealer quote?
- How does remaining time change value while leaving terminal strikes fixed?
- Why does issuer-published arithmetic net cap differ from continuous proportional-unit depletion?
- How do the fair-cap solver and a historical strategy optimizer differ?
- What happens when a budget funds zero integer packages? Where is residual cash recorded?
- What additional inputs are required to reconcile model value to NAV or compare a real bid/ask?
- Why is put-call parity insufficient to validate the entire study? Explain the independent integration and account tests.

## Claims to avoid

Do not describe the study as ETF tracking, NAV replication, achieved returns, portfolio protection or issuer cap mispricing. Do not reuse private internship numbers. Describe independently implemented scenario analysis, mathematical consistency and decision boundaries. Review and understand the AI-assisted implementation before using these explanations in an interview.
