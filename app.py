from datetime import datetime
from zoneinfo import ZoneInfo
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from compute_monitor.model import build_database,read_ledger,effective_capacity,compute_equivalent
from compute_monitor.accounting import latest_snapshot
from compute_monitor.scenarios import revenue_implied_tokens,price_response,unit_economics,matched_tightness

TODAY=datetime.now(ZoneInfo('Australia/Sydney')).date()
st.set_page_config(page_title='Global AI Compute Monitor',layout='wide')
st.title('Global AI Compute Monitor')
st.caption('Research release 0.2 • public evidence, guarded accounting and explicit scenarios')
con=build_database()
df=con.execute('SELECT * FROM daily_demand ORDER BY provider,as_of').fetchdf()
supply=con.execute('SELECT i.*,s.url,s.published_on,s.retrieved_on FROM latest_infrastructure i JOIN sources s USING(source_id)').fetchdf()
meta=con.execute('SELECT * FROM metadata').fetchdf()
sources=con.execute('SELECT * FROM sources').fetchdf()
gaps=con.execute('SELECT * FROM research_gaps').fetchdf()
relations=con.execute('SELECT * FROM relationships').fetchdf()
con.close()
st.warning('Selected, unaudited public reports; not a current global total. Provider, national and router ledgers overlap. Unknown input/output and model mix prevent a measured global compute-demand or tightness estimate.')
providers=st.multiselect('Providers / reporting entities',sorted(df.provider.unique()),default=sorted(df.provider.unique()))
view=df[df.provider.isin(providers)].copy()
a,b,c=st.columns(3)
a.metric('Covered reporting entities',len(providers));b.metric('Disclosures selected',len(view))
c.metric('Latest selected publication',str(view.published_on.max().date()) if len(view) else 'None')
if view.empty:
    st.info('Select at least one provider or reporting entity.');st.stop()
view['trillion_tokens_day']=view.tokens_per_day/1e12
view['publication_age_days']=view.published_on.map(lambda d:(TODAY-d.date()).days)
view['verification_age_days']=view.retrieved_on.map(lambda d:(TODAY-d.date()).days)
view['observation_age_days']=view.as_of.map(lambda d:(TODAY-d.date()).days)
view['stale_90_days']=view.observation_age_days>90

demand_tab,supply_tab,scenario_tab,quality_tab=st.tabs(['Demand evidence','Infrastructure','Scenario lab','Research quality'])
with demand_tab:
    st.subheader('Historical raw token throughput')
    ledgers=st.multiselect('Ledger types',sorted(view.ledger.unique()),default=sorted(view.ledger.unique()))
    history=view[view.ledger.isin(ledgers)]
    if not history.empty:
        fig=px.scatter(history,x='as_of',y='trillion_tokens_day',color='series_id',symbol='ledger',hover_data=['provider','scope','qualifier','unit','period_start','period_end'],labels={'as_of':'Observation/publication anchor','trillion_tokens_day':'Trillion raw tokens/day','series_id':'Separate accounting series'})
        st.plotly_chart(fig,width='stretch')
    st.caption('No connecting lines, interpolation or carry-forward. Minute/week/month rates are daily equivalents, not measured daily counts. Google APIs and all-surfaces are different series. National and router reports are not additive to provider reports.')
    st.subheader('Latest report per accounting series')
    cutoff=st.date_input('Evidence cutoff (publication-eligible; not an archived real-time backtest)',value=TODAY)
    snapshot=pd.DataFrame(latest_snapshot(read_ledger(),cutoff))
    if not snapshot.empty:
        snapshot=snapshot[snapshot.provider.isin(providers)]
        st.dataframe(snapshot[['provider','scope','ledger','as_of','tokens_per_day','qualifier','stale']],hide_index=True)
    else: st.info('No eligible disclosures before this cutoff.')
    st.subheader('Uncertainty and original accounting')
    st.info('No statistical demand intervals are supplied. The 28–31 day monthly sensitivity is only a denominator check. Nearly/approximately is not a hard lower bound; over remains a threshold.')
    st.dataframe(history[['provider','reported_value','unit','qualifier','tokens_per_day','calendar_sensitivity_lower','calendar_sensitivity_upper','period_status','notes','url']],hide_index=True)
    st.download_button('Download selected demand evidence',history.to_csv(index=False),'demand-evidence.csv','text/csv')
with supply_tab:
    st.subheader('Infrastructure evidence: stocks, flows and commitments')
    st.caption('This ledger is independent of the demand entity filter. GW, MW, physical chips and H100-equivalents are different units. Announced access, additions and targets are not installed inference stock; training and inference allocations remain unknown.')
    status=st.multiselect('Capacity statuses',sorted(supply.status.unique()),default=sorted(supply.status.unique()))
    selected=supply[supply.status.isin(status)]
    estimates=selected[(selected.unit=='H100_equivalent') & (selected.evidence_class=='estimated')].copy()
    if not estimates.empty:
        estimates['error_plus']=estimates.uncertainty_upper-estimates.reported_value
        estimates['error_minus']=estimates.reported_value-estimates.uncertainty_lower
        fig=px.scatter(estimates,x='entity',y='reported_value',error_y='error_plus',error_y_minus='error_minus',hover_data=['as_of','workload'],labels={'reported_value':'Estimated H100-equivalent compute use'})
        st.plotly_chart(fig,width='stretch')
        st.caption('Epoch AI estimates for December 2025, with source-reported 90% intervals. Includes research, training and inference; not physical H100 counts or current effective inference capacity. Josh You / Epoch AI, CC BY attribution; source links below.')
    st.dataframe(selected[['entity','metric','status','evidence_class','reported_value','qualifier','unit','as_of','hardware','workload','uncertainty_lower','uncertainty_upper','notes','url']],hide_index=True)
    st.download_button('Download infrastructure evidence',selected.to_csv(index=False),'infrastructure-evidence.csv','text/csv')
with scenario_tab:
    st.subheader('Explicit assumption scenarios')
    st.warning('All values entered here are hypothetical assumptions. No automatic conversion of ledger totals into compute demand or global utilization. Outputs are not investment recommendations or forecasts.')
    scenario_name=st.text_input('Scenario name',value='User assumptions')
    installed=st.number_input('Installed accelerators (assumption)',min_value=0,value=0)
    inference=st.slider('Fraction allocated to inference',0.,1.,.5)
    available=st.slider('Available fraction after outages/reservations',0.,1.,.8)
    util=st.slider('Active duty fraction of available capacity',0.,1.,.5)
    throughput=st.number_input('Matched-workload raw tokens/second/accelerator',min_value=0.,value=0.)
    capacity=effective_capacity(installed,inference,available,util,throughput)
    st.metric('Hypothetical tokens/day',f'{capacity:,.0f}')
    scenario={'name':scenario_name,'classification':'hypothetical_user_assumptions','generated_on':TODAY.isoformat(),'model_version':'0.2.0','capacity_inputs':dict(installed=installed,inference_fraction=inference,available_fraction=available,utilization=util,throughput=throughput),'capacity_tokens_day':capacity}
    with st.expander('Compute-equivalent workload accounting'):
        st.caption('Enter known prefill/decode costs and token split for one defined workload. FLOP equivalents omit memory, bandwidth and latency constraints.')
        it=st.number_input('Input tokens for the defined window',min_value=0.,value=0.)
        ot=st.number_input('Output tokens for the same window',min_value=0.,value=0.)
        ic=st.number_input('FLOPs per input token (assumption)',min_value=0.,value=0.)
        oc=st.number_input('FLOPs per output token (assumption)',min_value=0.,value=0.)
        rc=st.number_input('FLOPs per reference token (assumption)',min_value=0.,value=0.)
        if min(ic,oc,rc)>0:
            equivalent=compute_equivalent(it,ot,ic,oc,rc)
            st.metric('Reference-token equivalent for this window',f'{equivalent:,.0f}')
            scenario['compute_equivalent']=dict(input_tokens=it,output_tokens=ot,input_flops=ic,output_flops=oc,reference_flops=rc,result=equivalent)
        else: st.info('Supply positive measured or justified cost coefficients to calculate an equivalent.')
    with st.expander('Matched-scope tightness'):
        workload=st.text_input('Defined workload ID (model, context, cache, precision, SLA)',value='')
        geo=st.text_input('Geography for this scenario',value='')
        deployment=st.selectbox('Deployment perimeter',['public_cloud','captive','private_cloud'])
        basis=st.text_input('Token accounting basis (input/output, modality)',value='')
        period=st.date_input('Scenario window',value=(TODAY,TODAY),key='scenario_window')
        assumed_demand=st.number_input('Assumed completed demand tokens/day for this exact scope',min_value=0.,value=0.)
        if workload and geo and basis and len(period)==2 and capacity>0:
            shared=dict(workload_id=workload,geography=geo,deployment=deployment,token_basis=basis,period_start=period[0].isoformat(),period_end=period[1].isoformat())
            comparison=matched_tightness(dict(shared,tokens_per_day=assumed_demand,qualifier='equal'),dict(shared,tokens_per_day=capacity,status='scenario_available'))
            st.metric('Assumed demand / hypothetical capacity',f"{comparison['ratio']:.1%}")
            scenario['tightness']=dict(scope=shared,demand_tokens_day=assumed_demand,**comparison)
        else: st.info('A positive capacity and complete matching scope/window are required. No published aggregate demand row meets these conditions yet.')
    with st.expander('Revenue-implied throughput and economic demand'):
        st.caption('Revenue divided by a realized blended price is an estimate, not a throughput observation. Subscriptions, training and non-token revenue must be excluded. Elasticity is assumed, not identified from this ledger.')
        rev=st.number_input('Annual revenue USD (assumption)',min_value=0.,value=0.)
        share=st.slider('Share attributable to the modeled billed tokens',0.,1.,0.)
        low=st.number_input('Low realized USD per million total tokens',min_value=0.,value=0.)
        high=st.number_input('High realized USD per million total tokens',min_value=0.,value=0.)
        if low>0 and high>=low:
            implied=revenue_implied_tokens(rev,share,low,high)
            st.write(f"Scenario band: {implied['lower']:,.0f} to {implied['upper']:,.0f} tokens/day")
            scenario['revenue_implied']=dict(annual_revenue=rev,token_revenue_share=share,price_low=low,price_high=high,**implied)
        elif low or high: st.info('Require ordered positive realized price assumptions.')
        base=st.number_input('Base economic demand tokens/day (assumption)',min_value=0.,value=0.)
        bp=st.number_input('Base price (consistent units)',min_value=0.,value=0.)
        np=st.number_input('Counterfactual price (same units)',min_value=0.,value=0.)
        elasticity=st.number_input('Assumed absolute price elasticity',min_value=0.,value=0.)
        if min(bp,np)>0:
            response=price_response(base,bp,np,elasticity)
            st.write(f'Unconstrained counterfactual demand: {response:,.0f} tokens/day')
            scenario['price_response']=dict(base_tokens=base,base_price=bp,new_price=np,elasticity=elasticity,result=response)
    with st.expander('Infrastructure operating economics'):
        price=st.number_input('Realized USD per million processed tokens',min_value=0.,value=0.)
        capex=st.number_input('All-in allocated capex per accelerator, USD',min_value=0.,value=0.)
        life=st.number_input('Depreciation life, years (assumption)',min_value=.1,value=4.)
        idle=st.number_input('Idle system kW per allocated accelerator',min_value=0.,value=0.)
        active=st.number_input('Active system kW per allocated accelerator',min_value=0.,value=0.)
        pue=st.number_input('Facility PUE (assumption)',min_value=1.,value=1.)
        power=st.number_input('Electricity USD/kWh',min_value=0.,value=0.)
        other=st.number_input('Other annual allocated operating cost, USD',min_value=0.,value=0.)
        if active>=idle:
            inputs=dict(installed=installed,inference_fraction=inference,available_fraction=available,utilization=util,throughput=throughput,price_per_million=price,capex_per_accelerator=capex,life_years=life,idle_kw=idle,active_kw=active,pue=pue,power_price=power,other_annual_cost=other)
            econ=unit_economics(**inputs)
            st.dataframe(pd.DataFrame([{'metric':k,'value':v} for k,v in econ.items() if isinstance(v,(int,float)) or v is None]),hide_index=True)
            st.caption(econ['exclusions'])
            scenario['economics']=dict(inputs=inputs,outputs=econ)
            sensitivity=[]
            for duty in (.2,.5,.8):
                result=unit_economics(**dict(inputs,utilization=duty))
                sensitivity.append(dict(assumed_utilization=duty,operating_profit=result['operating_profit'],break_even_price=result['break_even_price_per_million']))
            st.caption('Hypothetical sensitivity grid; these utilization levels are assumptions, not observations.')
            st.dataframe(pd.DataFrame(sensitivity),hide_index=True)
        else: st.error('Active power must be at least idle power.')
    st.download_button('Download scenario assumptions and outputs (JSON)',json.dumps(scenario,indent=2,allow_nan=False),'scenario.json','application/json')
with quality_tab:
    st.subheader('Freshness and accounting')
    st.dataframe(view[['provider','scope','ledger','as_of','publication_age_days','verification_age_days','stale_90_days']],hide_index=True)
    st.caption('A 90-day stale flag is a display policy. Re-checking an old source does not refresh its observation. Updated pages cannot substantiate an earlier real-time backtest without an archive.')
    st.dataframe(relations,hide_index=True)
    st.subheader('Search outcomes and unresolved gaps')
    st.dataframe(gaps,hide_index=True)
    st.subheader('Source register')
    st.dataframe(sources,hide_index=True)
    st.subheader('Reproducibility')
    st.dataframe(meta,hide_index=True)
    st.write('Network checks detect source-page changes but never promote new numbers automatically. No defensible worldwide current total, effective inference stock or investment return is supplied by this evidence alone.')
