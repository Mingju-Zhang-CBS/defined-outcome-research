# Sources, scope and contribution

## Public issuer facts

The [machine-readable ledger](../defined_outcome_research/data/issuer_terms.json) records exact URLs, retrieval timestamps, source SHA-256, document dates and locators. URLs can be overwritten by issuers, so a later download may differ. The original downloaded documents are retained in the author's private audit cache, not redistributed here.

| Source | Date / locator | Use |
|---|---|---|
| [BJAN summary prospectus](https://www.innovatoretfs.com/pdf/bjan_summary_prospectus.pdf) | February 27, 2026; PDF pp.1-2,4,8-9 | Period, gross/net terms, fee and conventions |
| [BJAN factsheet](https://www.innovatoretfs.com/pdf/bjan_factsheet.pdf) | June 30, 2026; PDF p.2 | Rounded strikes and exposure |
| [FJAN issuer page](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=FJAN) | Retrieved October 23, 2026; objective/outcome table | Separate period and terms cross-check |

The factsheet's embedded font initially produced damaged digits during text extraction. Its holdings page was rendered and visually checked; a second parser recovered the same listed strikes. No issuer chart, page image, full prose, full holding feed or copyrighted market-data feed is included.

BJAN's public product page offers NAV and delayed market fields. No synchronized licensed observation set was established for this study. The quote channel is empty by design. A source link alone does not transform delayed display data into executable prices or grant a feed redistribution license.

## Personal implementation

This is a new independent public implementation by Mingju Zhang, developed with AI assistance. It includes the factual ledger, signed-leg model, boundary-safe European pricer, cost reconciliation, fixed scenario protocol, fee conventions, budget solver, cash account, quote validator, tests, figures and explanations. Public mathematical models and library code retain their respective authorship.

The adjacent [Derivatives Pricing Lab](https://github.com/Mingju-Zhang-CBS/derivatives-pricing-lab) is an earlier independent portfolio project. Both use standard public European pricing mathematics; neither claims authorship of Black-Scholes or issuer product design. The present implementation adds product and investor-entry logic rather than transferring confidential workbooks.

## Exclusions and limits

Employer workbooks, client portfolios, internal assumptions, vendor data, original course templates, recruiting questions, and prior internship reconciliation figures are excluded. A historical privately reported basis-point result is not a score for this new study. No issuer NAV fit, live execution, investment performance, product suitability recommendation or competition entry is claimed.

Code and newly authored figures are MIT-licensed; factual extracts have the separate [data notice](../DATA_LICENSE.md). Publisher materials, trademarks and dependencies keep their own rights. The package requires no credentials, company services, GPU or paid data/model calls.
