"""Terminal contracts, analytical marks and fully funded illustrative accounts."""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, floor, isfinite, log, sqrt
import numpy as np
from scipy.optimize import brentq
from scipy.special import ndtr


def finite(**values):
    if any(not isfinite(v) for v in values.values()):
        raise ValueError("Inputs must be finite")


@dataclass(frozen=True)
class Terms:
    reference: float = 100.0
    buffer: float = 0.09
    cap: float = 0.1646

    def __post_init__(self):
        finite(reference=self.reference, buffer=self.buffer, cap=self.cap)
        if self.reference <= 0 or not 0 <= self.buffer < 1 or self.cap <= 0:
            raise ValueError("Require positive reference/cap and buffer in [0,1)")


@dataclass(frozen=True)
class Leg:
    kind: str
    quantity: float
    strike: float = 0.0
    multiplier: float = 1.0

    def __post_init__(self):
        finite(quantity=self.quantity, strike=self.strike, multiplier=self.multiplier)
        if self.kind not in {"price_claim", "call", "put"} or self.multiplier <= 0:
            raise ValueError("Unsupported leg or multiplier")
        if (self.kind == "price_claim" and self.strike != 0) or (self.kind != "price_claim" and self.strike <= 0):
            raise ValueError("Option strike must be positive; price claim has no strike")


def legs_for(terms: Terms, strategy="buffer") -> tuple[Leg, ...]:
    """Price claim pays S_T, with no intervening dividends paid to its holder."""
    legs = (Leg("price_claim", 1),)
    if strategy == "underlying": return legs
    legs += (Leg("put", 1, terms.reference),)
    if strategy == "protective_put": return legs
    if strategy != "buffer": raise ValueError("Unknown strategy")
    return legs + (Leg("put", -1, terms.reference*(1-terms.buffer)),
                   Leg("call", -1, terms.reference*(1+terms.cap)))


def terminal(legs, spot):
    s = np.asarray(spot, dtype=float)
    if np.any(~np.isfinite(s)) or np.any(s < 0): raise ValueError("Invalid terminal spot")
    result = np.zeros_like(s)
    for leg in legs:
        payoff = s if leg.kind == "price_claim" else np.maximum(s-leg.strike, 0) if leg.kind == "call" else np.maximum(leg.strike-s, 0)
        result += leg.quantity*leg.multiplier*payoff
    return result


def target_return(spot, terms: Terms):
    """Gross, full-period reference return; never an entry-price-adjusted return."""
    x = np.asarray(spot, dtype=float)/terms.reference-1
    if np.any(~np.isfinite(x)) or np.any(x < -1): raise ValueError("Invalid spot")
    return np.where(x < -terms.buffer, x+terms.buffer,
                    np.where(x < 0, 0, np.minimum(x, terms.cap)))


def option_price(spot, strike, tau, rate, vol, dividend=0.0, kind="call"):
    finite(spot=spot, strike=strike, tau=tau, rate=rate, vol=vol, dividend=dividend)
    if spot < 0 or strike <= 0 or tau < 0 or vol < 0 or kind not in {"call", "put"}:
        raise ValueError("Invalid European option input")
    if tau == 0: return max(spot-strike, 0) if kind == "call" else max(strike-spot, 0)
    if spot == 0: return 0.0 if kind == "call" else strike*exp(-rate*tau)
    if vol == 0:
        forward = spot*exp((rate-dividend)*tau)
        return exp(-rate*tau)*(max(forward-strike, 0) if kind == "call" else max(strike-forward, 0))
    d1=(log(spot/strike)+(rate-dividend+vol*vol/2)*tau)/(vol*sqrt(tau))
    d2=d1-vol*sqrt(tau)
    if kind == "call": return spot*exp(-dividend*tau)*ndtr(d1)-strike*exp(-rate*tau)*ndtr(d2)
    return strike*exp(-rate*tau)*ndtr(-d2)-spot*exp(-dividend*tau)*ndtr(-d1)


def mark(legs, spot, tau, rate, vol, dividend=0.0):
    finite(spot=spot, tau=tau, rate=rate, vol=vol, dividend=dividend)
    if spot < 0 or tau < 0 or vol < 0: raise ValueError("Invalid mark input")
    return float(sum(l.quantity*l.multiplier*(spot*exp(-dividend*tau) if l.kind == "price_claim"
        else option_price(spot,l.strike,tau,rate,vol,dividend,l.kind)) for l in legs))


def fee_factor(annual_fee, tau):
    finite(annual_fee=annual_fee, tau=tau)
    if annual_fee < 0 or tau < 0: raise ValueError("Fee and time must be nonnegative")
    return exp(-annual_fee*tau)


def investor_return(gross_terminal, entry_mark, tau, annual_fee=0.0, half_spread_bps=0.0, exit_bps=0.0):
    """Declared scenario friction, no market quote. Fee removes proportional units."""
    finite(entry_mark=entry_mark, half_spread_bps=half_spread_bps, exit_bps=exit_bps)
    if entry_mark <= 0 or half_spread_bps < 0 or not 0 <= exit_bps < 10000:
        raise ValueError("Invalid entry mark or friction")
    value=np.asarray(gross_terminal,dtype=float)
    if np.any(~np.isfinite(value)) or np.any(value < 0): raise ValueError("Invalid terminal wealth")
    return value*fee_factor(annual_fee,tau)*(1-exit_bps/10000)/(entry_mark*(1+half_spread_bps/10000))-1


def fair_cap(reference, buffer, tau, rate, vol, dividend=0.0, budget=None):
    """Solve a declared model budget, not the issuer's actual cap-setting process."""
    finite(reference=reference, buffer=buffer, tau=tau, rate=rate, vol=vol, dividend=dividend)
    budget=reference if budget is None else budget
    finite(budget=budget)
    if budget <= 0 or tau <= 0 or vol < 0: raise ValueError("Invalid budget or market input")
    def residual(cap): return mark(legs_for(Terms(reference,buffer,cap)),reference,tau,rate,vol,dividend)-budget
    lo,hi=1e-7,5.0
    if residual(lo)*residual(hi) > 0: return None
    return float(brentq(residual,lo,hi,xtol=1e-12))


def allocate(budget, entry_mark, multiplier=100, half_spread_bps=0.0, commission=0.0):
    """Integer packages; full net package debit is reserved with no leverage.

    This assumes enforceable package netting. A broker may require extra margin.
    """
    finite(budget=budget, entry_mark=entry_mark, multiplier=multiplier,
           half_spread_bps=half_spread_bps, commission=commission)
    if budget < 0 or entry_mark <= 0 or multiplier <= 0 or half_spread_bps < 0 or commission < 0:
        raise ValueError("Invalid budget/allocation input")
    unit_cost=entry_mark*multiplier*(1+half_spread_bps/10000)+commission
    units=floor(budget/unit_cost)
    cash=budget-units*unit_cost
    return {"packages":units,"cash":cash,"initial_debit":units*unit_cost,
            "package_cost":unit_cost,"multiplier":multiplier,"budget":budget,
            "status":"funded" if units else "budget-too-small"}


def settle(allocation, terminal_per_unit, tau, rate, annual_fee=0.0, exit_bps=0.0):
    finite(terminal_per_unit=terminal_per_unit,tau=tau,rate=rate,exit_bps=exit_bps)
    if terminal_per_unit < 0 or not 0 <= exit_bps < 10000: raise ValueError("Invalid settlement")
    claim=allocation["packages"]*allocation["multiplier"]*terminal_per_unit*fee_factor(annual_fee,tau)*(1-exit_bps/10000)
    cash=allocation["cash"]*exp(rate*tau)
    return {"claim_wealth":claim,"cash_wealth":cash,"terminal_wealth":claim+cash,
            "pnl":claim+cash-allocation["budget"]}
