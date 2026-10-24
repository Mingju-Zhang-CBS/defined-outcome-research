"""Run a frozen scenario study; no live feeds, fund-return backtest or fitting."""
from __future__ import annotations
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import tracemalloc
import numpy as np
import pandas as pd
import scipy
import matplotlib
from .core import Terms, legs_for, terminal, target_return, mark, investor_return, fair_cap, allocate, settle, fee_factor
from .plots import create_figures

PACKAGE=Path(__file__).resolve().parent


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output):
    out=Path(output)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be absent or empty; existing results are immutable")
    out.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();tracemalloc.start()
    protocol=json.loads((PACKAGE/'protocol.json').read_text(encoding='utf-8'))
    issuer=json.loads((PACKAGE/'data/issuer_terms.json').read_text(encoding='utf-8'))
    terms=Terms(protocol['reference'],protocol['buffer'],protocol['cap'])
    r,q,vol=protocol['rate'],protocol['dividend'],protocol['volatility']
    tenor=protocol['tenor_years'];fee=issuer['products'][0]['annual_fee']
    legs=legs_for(terms)
    initial={name:mark(legs_for(terms,name),terms.reference,tenor,r,vol,q)
             for name in ['underlying','protective_put','buffer']}
    g=protocol['terminal_grid']
    grid=np.unique(np.r_[np.arange(g['start'],g['end']+g['step']/2,g['step']),
                        terms.reference*(1-terms.buffer),terms.reference*(1+terms.cap)])
    gross=terminal(legs,grid)
    payoff=pd.DataFrame({'terminal_spot':grid,'reference_return':grid/terms.reference-1,
        'target_return':target_return(grid,terms),'buffer_payoff':gross,
        'cash_return':np.full_like(grid,np.exp(r*tenor)-1),
        'funded_buffer_return':investor_return(gross,initial['buffer'],tenor),
        'funded_protective_return':investor_return(terminal(legs_for(terms,'protective_put'),grid),initial['protective_put'],tenor)})
    payoff.to_csv(out/'terminal_payoffs.csv',index=False,float_format='%.12g')
    entries=[]
    for elapsed,s,sigma in product(protocol['elapsed_years'],protocol['entry_spots'],protocol['volatilities']):
        tau=tenor-elapsed;entry=mark(legs,s,tau,r,sigma,q)
        vals={f'return_at_terminal_{int(st)}':float(investor_return(terminal(legs,st),entry,tau,fee)) for st in [80,100,120]}
        entries.append(dict(elapsed_years=elapsed,remaining_years=tau,entry_spot=s,volatility=sigma,entry_mark=entry,
            max_return_net=float(investor_return(terms.reference*(1+terms.cap),entry,tau,fee)),
            flat_original_return_net=float(investor_return(terms.reference,entry,tau,fee)),
            reference_decline_to_buffer_end=terms.reference*(1-terms.buffer)/s-1,**vals))
    entries=pd.DataFrame(entries);entries.to_csv(out/'entry_scenarios.csv',index=False,float_format='%.12g')
    fee_rows=[]
    for f,spread in product(protocol['fees'],protocol['entry_half_spread_bps']):
        fee_rows.append({'annual_fee':f,'half_spread_bps':spread,
                        'max_return':float(investor_return(terms.reference*(1+terms.cap),initial['buffer'],tenor,f,spread)),
                        'flat_original_return':float(investor_return(terms.reference,initial['buffer'],tenor,f,spread))})
    fee_rows=pd.DataFrame(fee_rows);fee_rows.to_csv(out/'fee_friction.csv',index=False,float_format='%.12g')
    fair_rows=[]
    for b,sigma in product(protocol['fair_cap_buffers'],protocol['volatilities']):
        cap=fair_cap(terms.reference,b,tenor,r,sigma,q)
        fair_rows.append({'buffer':b,'volatility':sigma,'fair_cap':cap,
                         'status':'solved' if cap is not None else 'infeasible-in-bracket'})
    fair_rows=pd.DataFrame(fair_rows);fair_rows.to_csv(out/'model_budget_caps.csv',index=False,float_format='%.12g')
    marks=pd.DataFrame([{'remaining_years':tau,'spot':s,'value':mark(legs,s,tau,r,vol,q)}
                       for tau,s in product([1,.5,.25,0],grid)])
    marks.to_csv(out/'interim_marks.csv',index=False,float_format='%.12g')
    allocations=[]
    for budget in protocol['budgets']:
        a=allocate(budget,initial['buffer'],protocol['contract_multiplier'],10,protocol['commission_per_package'])
        settlement=settle(a,float(terminal(legs,80)),tenor,r,fee)
        allocations.append(dict(a,**{f'terminal_80_{k}':v for k,v in settlement.items()}))
    allocations=pd.DataFrame(allocations);allocations.to_csv(out/'integer_accounts.csv',index=False,float_format='%.12g')
    pd.DataFrame(issuer['products']).to_csv(out/'issuer_terms.csv',index=False)
    strike=issuer['rounded_strikes'];s0=strike['reference_level']
    rounded={f"{l['side']}_{l['kind']}":l['strike'] for l in strike['legs']}
    costs=[]
    for name in ['underlying','protective_put','buffer']:
        for leg in legs_for(terms,name):
            costs.append({'strategy':name,'kind':leg.kind,'quantity':leg.quantity,'strike':leg.strike,
                          'gross_mark':mark((leg,),terms.reference,tenor,r,vol,q)})
    pd.DataFrame(costs).to_csv(out/'initial_costs.csv',index=False,float_format='%.12g')
    metrics={'data_kind':protocol['data_kind'],'entry_scenarios':len(entries),'fee_friction_scenarios':len(fee_rows),
        'budget_cap_scenarios':len(fair_rows),'terminal_grid_points':len(grid),'initial_costs':initial,
        'issuer_cap_gross':terms.cap,'issuer_cap_net':issuer['products'][0]['published_cap_net'],
        'issuer_buffer_gross':terms.buffer,'issuer_buffer_net':issuer['products'][0]['published_buffer_net'],
        'unit_depletion_target_cap':(1+terms.cap)*fee_factor(fee,tenor)-1,
        'target_vs_leg_payoff_max_abs_error':float(np.max(np.abs(gross/terms.reference-1-target_return(grid,terms)))),
        'model_budget_cap_base':fair_cap(terms.reference,terms.buffer,tenor,r,vol,q),
        'model_initial_target_cost_gap':initial['buffer']-terms.reference,
        'rounded_strike_implied_buffer':1-rounded['short_put']/s0,
        'rounded_strike_implied_cap':rounded['short_call']/s0-1,
        'deep_call_strike_fraction':rounded['long_call']/s0,
        'quote_observations':0,'issuer_nav_reconciliation':'not-performed',
        'example_mid_entry':entries[(entries.elapsed_years==.5)&(entries.entry_spot==120)&(entries.volatility==.2)].iloc[0].to_dict(),
        'example_low_budget':allocations.iloc[0].to_dict()}
    create_figures(out,payoff,entries,fee_rows,fair_rows,marks,allocations,metrics)
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    metrics['performance']={'wall_seconds':time.perf_counter()-started,'peak_python_allocation_bytes':peak,
        'measurement':'perf_counter and tracemalloc, including five figures; not RSS, exchange latency or a portable speed benchmark'}
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    report=make_report(metrics,issuer,entries,fair_rows,fee_rows,allocations)
    (out/'REPORT.md').write_text(report,encoding='utf-8')
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'data_kind':protocol['data_kind'],
        'protocol_sha256':digest(PACKAGE/'protocol.json'),'issuer_terms_sha256':digest(PACKAGE/'data/issuer_terms.json'),
        'source_sha256':{p.name:digest(p) for p in sorted(PACKAGE.glob('*.py'))},
        'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'machine':platform.machine(),
                       'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},
        'scope':'Issuer factual terms plus deterministic model scenarios; no empirical P&L, real fund NAV valuation or executable quotes.',
        'files_sha256':{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return metrics


def make_report(m,issuer,entries,fair_rows,fees,accounts):
    e=m['example_mid_entry'];cost=m['initial_costs']['buffer']
    text=f'''# Defined-Outcome Research | Results

**Evidence:** issuer-published factual terms, followed by synthetic, deterministic European-claim scenarios. No fund-performance backtest or executable quote comparison. Configuration: [protocol](../../protocol.json); exact figures and environment: [metrics](metrics.json) and [manifest](manifest.json).

## 1. Terms before modeling

| Case | Outcome period | Gross cap / buffer | Published net cap / buffer | Annual fee |
|---|---|---|---|---|
'''
    for p in issuer['products']:
        text+=f"| {p['ticker']} | {p['start']} to {p['end']} | {p['cap_gross']:.2%} / {p['buffer_gross']:.2%} | {p['published_cap_net']:.2%} / {p['published_buffer_net']:.2%} | {p['annual_fee']:.2%} |\n"
    text+=f'''
Sources: [BJAN summary prospectus, February 27, 2026](https://www.innovatoretfs.com/pdf/bjan_summary_prospectus.pdf), [BJAN factsheet, June 30, 2026](https://www.innovatoretfs.com/pdf/bjan_factsheet.pdf), [FJAN issuer snapshot, retrieved October 23, 2026](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=FJAN). FJAN is a terms cross-check, not a performance comparison; its dates and buffer differ. Published net figures exclude some investor costs and are not promised realized returns. Source hashes and locators are in the [fact ledger](../../defined_outcome_research/data/issuer_terms.json).

## 2. The cost of the payoff

![Payoff identity versus funded returns](payoff_and_cost.png)

The BJAN-shaped stylized strip costs **{cost:.6f}**, versus reference 100, under 3% rate, 20% volatility, zero dividend yield and one year. A gross payoff plateau at 100 therefore does not imply a zero return on that model purchase. The price-only claim costs {m['initial_costs']['underlying']:.6f}; the protective put costs {m['initial_costs']['protective_put']:.6f}. Cash grows at the declared 3% continuous rate. Compare full costs in [initial_costs.csv](initial_costs.csv).

The direct piecewise target and independent signed-leg payoff agree to **{m['target_vs_leg_payoff_max_abs_error']:.3g}** return units on {m['terminal_grid_points']} grid points including strikes. This validates the mathematical identity, not a fund replication. The factsheet's deep call has a positive strike of {m['deep_call_strike_fraction']:.4%} of the starting reference; replacing it with a zero-strike price claim changes the terminal economics. Rounded strikes imply buffer {m['rounded_strike_implied_buffer']:.6%} and cap {m['rounded_strike_implied_cap']:.6%}. Fund quantities, cash, accrued fees and contract details are not reconciled, so no issuer NAV or cap-pricing error is claimed.

## 3. A later buyer gets a different payoff relative to cost

![Entry-time scenarios](entry_time.png)

At six months elapsed, reference 120 and volatility 20%, the gross model entry value is **{e['entry_mark']:.6f}**. With 0.79% annual proportional-unit fees for the remaining half-year, the maximum terminal return is **{e['max_return_net']:.2%}**. If the reference finishes at its original 100, this buyer loses **{-e['flat_original_return_net']:.2%}**. The 9% original buffer is not measured from this buyer's entry price. All {m['entry_scenarios']} predeclared combinations remain in [entry_scenarios.csv](entry_scenarios.csv); the example is explanatory, not a selected trading rule. At elapsed zero, spot 80/120 are instantaneous stress states after fixing the reference at 100, not alternative actual inception observations.

## 4. Interim value is a model mark

![Time-value curves](interim_value.png)

The payoff is piecewise only at expiry. Before expiry, option time value, discounting and volatility smooth the shape. This study does not imply that these marks are the ETF's NAV, a dealer's price, or an executable option quote. Dividend yield discounts the claim paying only S_T; actual stock holdings would also have dividend cash flows. Constant parameters, European exercise and frictionless pricing omit skew, smile, liquidity and fund operations.

## 5. Fees and the option budget

![Separate fee conventions and budget-balanced caps](fees_and_option_budget.png)

The issuer publishes 16.46% gross and 15.67% net cap. A separate unit-depletion scenario gives **{m['unit_depletion_target_cap']:.4%}** on a hypothetical 100 entry and gross terminal wealth 116.46. Subtracting an annual percentage of initial capital and charging a proportional NAV fee are different calculations. The latter is not a reconstruction of actual ETF accounting. On the actually priced strip, returns divide by {cost:.6f}, not by 100; see [fee_friction.csv](fee_friction.csv).

Solving a model budget of 100 gives cap **{m['model_budget_cap_base']:.4%}** for a 9% buffer at 20% volatility. This is a model counterfactual under fixed assumptions, not a fair-value verdict on the issuer's cap. [Nine fixed buffer/volatility cases](model_budget_caps.csv) retain infeasible roots if any; cap is not chosen to maximize a historical return.

## 6. Integer packages and settlement

![Budget allocation](integer_budget.png)

The package multiplier is 100; entry half-spread is an assumed 10 bps and commission $4 per package. A $5,000 budget buys zero packages. [integer_accounts.csv](integer_accounts.csv) records residual cash, funded debit and settlement at reference 80; the unspent cash earns the model cash rate. Full package debit is reserved and exact netting is assumed; broker margin, short-leg approval and legging risk could make a theoretical package unavailable.

## 7. Quote channel and decision boundary

**Bundled quote observations: 0. Actual fund NAV reconciliation: not performed.** Public issuer pages display NAV and delayed market fields with different clocks. No synchronized licensed quote snapshot is included or fabricated. The empty [quote schema](../../examples/quotes.schema.csv) accepts separately typed, timezone-aware NAV or bid/ask observations. Its audit never labels a displayed quote as a proven fill. ETF-share dollars cannot be compared directly with a normalized option claim; conversion requires verified holdings, quantities, cash and matched times.

The useful result is a decision checklist: identify the original outcome reference, pay the actual entry cost, distinguish fee conventions, preserve the cash account, and verify real market data before discussing a trade. This study does not rank ETFs or claim achievable investment returns.

[Methods](../../docs/METHODS.md) · [Worked example](../../docs/WALKTHROUGH.md) · [Sources and contribution](../../docs/PROVENANCE.md) · [Research directory](https://github.com/Mingju-Zhang-CBS/Quant)
'''
    return text
