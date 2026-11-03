"""Deterministic user-assumption tools; never production measurements."""
import math
from .model import effective_capacity

def nonnegative(**values):
    for key,value in values.items():
        if value is None or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0: raise ValueError(f'{key} must be finite and nonnegative')

def revenue_implied_tokens(annual_revenue,revenue_share,price_low,price_high):
    nonnegative(annual_revenue=annual_revenue,revenue_share=revenue_share,price_low=price_low,price_high=price_high)
    if revenue_share>1 or price_low<=0 or price_high<price_low: raise ValueError('Require share <=1 and ordered positive realized prices')
    dollars=annual_revenue*revenue_share/365.25
    return dict(lower=dollars/price_high*1e6,upper=dollars/price_low*1e6,classification='revenue_implied_scenario',basis='realized blended USD per million total billed tokens; not list price')

def price_response(base_tokens,base_price,new_price,elasticity):
    nonnegative(base_tokens=base_tokens,base_price=base_price,new_price=new_price,elasticity=elasticity)
    if min(base_price,new_price)<=0: raise ValueError('Prices must be positive')
    try: result=base_tokens*(new_price/base_price)**(-elasticity)
    except (OverflowError,ZeroDivisionError): raise ValueError('Demand overflow') from None
    if not math.isfinite(result): raise ValueError('Demand overflow')
    return result

def matched_tightness(demand,capacity):
    for key in ('workload_id','geography','period_start','period_end','token_basis','deployment'):
        if not demand.get(key) or demand.get(key)!=capacity.get(key) or 'unspecified' in str(demand.get(key)):
            raise ValueError('Demand and capacity must match known '+key)
    from datetime import date
    if date.fromisoformat(str(demand['period_start']))>date.fromisoformat(str(demand['period_end'])): raise ValueError('Reversed scenario period')
    if demand.get('qualifier')!='equal': raise ValueError('Threshold demand does not establish point tightness')
    if capacity.get('status') not in ('reported_available','scenario_available'): raise ValueError('Announced/planned capacity is not available supply')
    nonnegative(demand=demand['tokens_per_day'],capacity=capacity['tokens_per_day'])
    if capacity['tokens_per_day']==0: raise ValueError('Positive capacity required')
    return dict(ratio=demand['tokens_per_day']/capacity['tokens_per_day'],classification='matched_scope_scenario' if capacity['status']=='scenario_available' else 'matched_scope_comparison')

def unit_economics(installed,inference_fraction,available_fraction,utilization,throughput,price_per_million,capex_per_accelerator,life_years,idle_kw,active_kw,pue,power_price,other_annual_cost):
    nonnegative(price=price_per_million,capex=capex_per_accelerator,life=life_years,idle_kw=idle_kw,active_kw=active_kw,pue=pue,power_price=power_price,other_cost=other_annual_cost)
    if life_years<=0 or pue<1 or active_kw<idle_kw: raise ValueError('Positive life, PUE >=1 and active power >= idle power required')
    tokens=effective_capacity(installed,inference_fraction,available_fraction,utilization,throughput)*365.25
    allocated=installed*inference_fraction
    revenue=tokens/1e6*price_per_million
    # Idle power applies to the entire allocated fleet, including unavailable machines.
    kwh=allocated*(idle_kw+(active_kw-idle_kw)*available_fraction*utilization)*pue*8766
    energy=kwh*power_price
    depreciation=allocated*capex_per_accelerator/life_years
    cash_cost=energy+other_annual_cost
    operating_profit=revenue-cash_cost-depreciation
    return dict(annual_tokens=tokens,annual_revenue=revenue,annual_energy_kwh=kwh,annual_energy_cost=energy,annual_depreciation=depreciation,annual_other_cost=other_annual_cost,operating_profit=operating_profit,operating_margin=operating_profit/revenue if revenue>0 else None,break_even_price_per_million=(cash_cost+depreciation)/tokens*1e6 if tokens>0 else None,classification='hypothetical_pre_tax_unlevered_operating_scenario',exclusions='financing, taxes, networking/server capex unless included, customer acquisition, model development, working capital and residual value')
