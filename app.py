from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from compute_monitor.model import build_database, effective_capacity

st.set_page_config(page_title="Global AI Compute Monitor", layout="wide")
st.title("Global AI Compute Monitor")
st.caption("Phase 1 • selected public disclosures • no global total or live meter")
con = build_database()
df = con.execute("SELECT * FROM daily_demand ORDER BY provider,as_of").fetchdf()
meta = con.execute("SELECT * FROM metadata").fetchdf()
con.close()
st.warning("Historical evidence sample, not current global demand. Provider figures are self-reported and unaudited. Scope overlap is unresolved; do not sum rows.")
providers = st.multiselect("Providers", sorted(df.provider.unique()), default=sorted(df.provider.unique()))
view = df[df.provider.isin(providers)].copy()
a,b,c = st.columns(3)
a.metric("Covered providers", len(providers))
b.metric("Disclosures selected", len(view))
c.metric("Latest source publication", str(view.published_on.max().date()) if len(view) else "None")
if not len(view):
    st.info("Select at least one provider.")
    st.stop()
view["trillion_tokens_day"] = view.tokens_per_day / 1e12
view["publication_age_days"] = view.published_on.map(lambda d: (date.today()-d.date()).days)
view["verification_age_days"] = view.retrieved_on.map(lambda d: (date.today()-d.date()).days)
view["observation_age_days"] = view.as_of.map(lambda d: (date.today()-d.date()).days)
view["stale_90_days"] = view.observation_age_days > 90
st.subheader("Historical disclosed throughput, normalized")
fig = px.scatter(view, x="as_of", y="trillion_tokens_day", color="provider", symbol="reporting_frequency",
    hover_data=["scope","qualifier","period_status","period_start","period_end"],
    labels={"as_of":"Observation anchor (publication date for unspecified run-rate periods)","trillion_tokens_day":"Trillion raw tokens/day"})
st.plotly_chart(fig, width="stretch")
st.caption("Points are separate disclosures, without interpolation or extrapolation. Quarterly and monthly averages describe different windows. 'Over' remains a lower threshold. A publication anchor does not identify the measurement window.")
st.subheader("Coverage and freshness")
st.dataframe(view[["provider","scope","deployment","geography","token_direction","period_status","as_of","publication_age_days","verification_age_days","stale_90_days"]], hide_index=True)
st.caption("Geography describes consumption/serving coverage, not headquarters. Global_unspecified does not provide a country allocation. Fresh verification of an old disclosure does not make its observation current.")
st.subheader("Uncertainty and evidence")
st.info("No statistical confidence intervals are disclosed. Unknown upper bounds remain null. The monthly 28–31 day band below is a denominator sensitivity only; it excludes measurement, scope and model uncertainty.")
st.dataframe(view[["observation_id","reported_value","unit","qualifier","calendar_sensitivity_lower","calendar_sensitivity_upper","uncertainty_lower","uncertainty_upper","uncertainty_basis","url","notes"]], hide_index=True)
st.download_button("Download selected normalized evidence (CSV)",view.to_csv(index=False),"evidence.csv","text/csv")
with st.expander("Hypothetical effective capacity scenario"):
    st.caption("Illustrative assumptions only. No fleet estimate or observed capacity is supplied. Benchmark throughput must match the workload and input/output accounting. No demand/capacity ratio is calculated from this heterogeneous evidence.")
    installed = st.number_input("Installed accelerators (assumption)", min_value=0, value=0)
    fraction = st.slider("Fraction assigned to inference",0.0,1.0,0.5)
    available = st.slider("Fraction available after outages/reservations",0.0,1.0,0.8)
    util = st.slider("Active service duty fraction of available capacity",0.0,1.0,0.5)
    throughput = st.number_input("Benchmark raw tokens/second/accelerator (assumption)",min_value=0.0,value=0.0)
    st.metric("Hypothetical workload-specific tokens/day",f"{effective_capacity(installed,fraction,available,util,throughput):,.0f}")
st.subheader("Research boundaries")
st.write("Economic demand includes willingness to pay and unmet workloads; observed throughput measures completed processing. Raw tokens cannot identify compute demand without model, modality, context, caching and input/output costs. Training, effective supply, tightness and investment returns are not estimated in Phase 1.")
with st.expander("Reproducibility metadata"):
    st.dataframe(meta,hide_index=True)
