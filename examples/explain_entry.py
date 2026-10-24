"""A complete synthetic purchase, cost and expiry calculation; no issuer quote."""
from defined_outcome_research.core import Terms, legs_for, mark, terminal, allocate, settle

terms=Terms();legs=legs_for(terms)
entry=mark(legs,120,.5,.03,.2)
allocation=allocate(25000,entry,100,10,4)
result=settle(allocation,float(terminal(legs,100)),.5,.03,.0079)
assert allocation['packages'] == 2
assert abs(allocation['initial_debit']+allocation['cash']-25000)<1e-9
assert abs(result['terminal_wealth']-result['claim_wealth']-result['cash_wealth'])<1e-9
print({'synthetic_entry_mark':entry,'allocation':allocation,'settlement_if_reference_ends_at_100':result})
