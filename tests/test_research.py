"""Economic identities, independent integration and quote-boundary controls."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import math
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from defined_outcome_research.core import Terms, Leg, legs_for, terminal, target_return, option_price, mark, fair_cap, investor_return, allocate, settle, fee_factor
from defined_outcome_research.quotes import Quote, read_quotes


def test_piecewise_contract_at_economic_boundaries():
    terms=Terms();s=np.array([0,50,91,95,100,110,116.46,150])
    expected=np.array([9,59,100,100,100,110,116.46,116.46])
    np.testing.assert_allclose(terminal(legs_for(terms),s),expected,atol=1e-12)
    np.testing.assert_allclose(1+target_return(s,terms),expected/100,atol=1e-12)


def test_payoff_continuity_and_one_sided_slopes():
    legs=legs_for(Terms());h=1e-5
    for boundary,left,right in [(91,1,0),(100,0,1),(116.46,1,0)]:
        middle=terminal(legs,boundary)
        assert (middle-terminal(legs,boundary-h))/h == pytest.approx(left,abs=1e-8)
        assert (terminal(legs,boundary+h)-middle)/h == pytest.approx(right,abs=1e-8)


def test_mark_agrees_with_independent_risk_neutral_integration():
    # Integrate the independent piecewise payoff, not the leg valuation function.
    s,t,r,sigma,q=107,.65,.025,.31,.012
    def integrand(z):
        st=s*math.exp((r-q-sigma*sigma/2)*t+sigma*math.sqrt(t)*z)
        wealth=st+9 if st<91 else 100 if st<100 else st if st<116.46 else 116.46
        return wealth*norm.pdf(z)*math.exp(-r*t)
    splits=[-12]+[math.log(k/s)/(sigma*math.sqrt(t))-(r-q-sigma*sigma/2)*t/(sigma*math.sqrt(t)) for k in [91,100,116.46]]+[12]
    value=sum(quad(integrand,a,b,epsabs=1e-9)[0] for a,b in zip(splits[:-1],splits[1:]))
    assert mark(legs_for(Terms()),s,t,r,sigma,q)==pytest.approx(value,abs=1e-8)


def test_put_call_parity_with_dividends():
    s,k,t,r,v,q=95,103,.7,.03,.24,.02
    c=option_price(s,k,t,r,v,q,'call');p=option_price(s,k,t,r,v,q,'put')
    assert c-p==pytest.approx(s*math.exp(-q*t)-k*math.exp(-r*t),abs=1e-12)


def test_price_only_claim_does_not_collect_dividends():
    leg=(Leg('price_claim',1),)
    assert mark(leg,100,1,.03,.2,.02)==pytest.approx(100*math.exp(-.02))


def test_maturity_zero_spot_and_zero_volatility():
    for kind in ['call','put']:
        assert option_price(100,90,0,.03,.2,kind=kind)==(10 if kind=='call' else 0)
        assert option_price(0,90,.5,.03,.2,kind=kind)==pytest.approx(0 if kind=='call' else 90*math.exp(-.015))
        assert option_price(100,100,1,.03,0,kind=kind)==pytest.approx(max(100-100*math.exp(-.03),0) if kind=='call' else 0)


def test_strike_strip_is_not_assumed_budget_balanced():
    cost=mark(legs_for(Terms()),100,1,.03,.2)
    assert abs(cost-100)>.1
    assert float(investor_return(100,cost,1))==pytest.approx(100/cost-1)


def test_budget_cap_solver_and_more_expensive_buffer():
    c=fair_cap(100,.09,1,.03,.2)
    assert mark(legs_for(Terms(100,.09,c)),100,1,.03,.2)==pytest.approx(100,abs=1e-9)
    assert fair_cap(100,.15,1,.03,.2)<c
    assert fair_cap(100,.09,1,.03,.2,budget=500) is None


def test_fees_and_frictions_reduce_wealth_and_never_reset_strikes():
    gross=terminal(legs_for(Terms()),100)
    base=investor_return(gross,110,.5)
    fee=investor_return(gross,110,.5,.0079)
    spread=investor_return(gross,110,.5,.0079,10,10)
    assert spread<fee<base<0
    assert fee_factor(.0079,.5)**2==pytest.approx(fee_factor(.0079,1))


def test_published_arithmetic_net_and_fee_units_are_distinct():
    assert .1646-.0079==pytest.approx(.1567)
    assert (1+.1646)*fee_factor(.0079,1)-1 != pytest.approx(.1567,abs=1e-5)


def test_integer_cash_account_and_small_budget():
    a=allocate(25000,110,100,10,4)
    assert a['packages']==2
    assert a['cash']+a['initial_debit']==pytest.approx(25000)
    z=settle(a,100,.5,.03,.0079)
    expected=200*100*math.exp(-.0079*.5)+a['cash']*math.exp(.03*.5)
    assert z['terminal_wealth']==pytest.approx(expected)
    assert z['pnl']+25000==pytest.approx(expected)
    small=allocate(5000,110)
    assert small['status']=='budget-too-small' and small['packages']==0
    assert settle(small,100,1,.03)['terminal_wealth']==pytest.approx(5000*math.exp(.03))


def test_positive_deep_call_is_not_the_zero_strike_claim():
    t=Terms();s=np.array([0,.5,50,100,150])
    shadow=(Leg('call',1,1),)+legs_for(t)[1:]
    difference=terminal(legs_for(t),s)-terminal(shadow,s)
    np.testing.assert_allclose(difference,np.minimum(s,1))


@pytest.mark.parametrize('factory',[lambda:Terms(buffer=1),lambda:Terms(cap=float('nan')),
    lambda:Leg('call',1,0),lambda:mark(legs_for(Terms()),-1,1,.03,.2),
    lambda:investor_return(100,0,1),lambda:investor_return(100,100,1,-.01),
    lambda:allocate(5000,100,half_spread_bps=-1)])
def test_illegal_economic_inputs_fail(factory):
    with pytest.raises(ValueError):factory()


def observation(**overrides):
    now=datetime(2026,10,23,16,tzinfo=timezone.utc)
    row=dict(instrument='TEST_ONLY',kind='bid_ask',observed_at=now,retrieved_at=now+timedelta(minutes=1),
             source_url='https://example.org/test-only',unit='USD_per_ETF_share',currency='USD',bid=99,ask=101,delayed=True)
    row.update(overrides);return Quote(**row)


def test_quote_midpoint_is_not_nav_or_proven_execution():
    q=observation();audit=q.summary(q.retrieved_at)
    assert audit['midpoint']==100 and audit['spread_bps']==200 and audit['nav'] is None
    assert audit['execution_proven'] is False
    assert q.summary(q.retrieved_at+timedelta(hours=1))['time_aligned'] is False


def test_nav_has_no_spread_or_bid_ask():
    q=observation(kind='nav',bid=None,ask=None,nav=100)
    assert q.summary(q.retrieved_at)['midpoint'] is None
    with pytest.raises(ValueError):observation(kind='nav',nav=100)


def test_quote_requires_clock_order_units_and_uncrossed_values():
    for changes in [dict(observed_at=datetime(2026,10,23)),dict(bid=102),dict(bid=float('nan')),
                    dict(unit='normalized_claim'),dict(retrieved_at=datetime(2026,1,1,tzinfo=timezone.utc))]:
        with pytest.raises(ValueError):observation(**changes)


def test_quote_csv_is_empty_by_design_and_rejects_schema_error(tmp_path):
    root=Path(__file__).resolve().parents[1]
    assert read_quotes(root/'examples/quotes.schema.csv')==[]
    p=tmp_path/'bad.csv';p.write_text('instrument,bid,ask\nTEST,99,101\n')
    with pytest.raises(ValueError):read_quotes(p)


def test_installed_protocol_and_factual_terms_are_explicit():
    import defined_outcome_research
    package=Path(defined_outcome_research.__file__).parent
    protocol=json.loads((package/'protocol.json').read_text())
    terms=json.loads((package/'data/issuer_terms.json').read_text())
    assert protocol['data_kind']=='public-terms-with-simulated-scenarios'
    assert terms['quotes']['bundled_observations']==0
    assert len(terms['sources'])==3
    assert terms['products'][0]['published_buffer_net']==.0821
