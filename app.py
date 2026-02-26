import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Growth Funnel Lab", layout="wide")

st.title("Growth Funnel Lab")
st.caption("Funnel drop-offs, channel performance, and business-ready insights")

@st.cache_data
def load_sample():
    return pd.read_csv("sample_data.csv")

with st.sidebar:
    st.header("Load data")
    use_sample = st.button("Load sample dataset")
    uploaded = st.file_uploader("Or upload a CSV", type=["csv"])

if uploaded is not None:
    df = pd.read_csv(uploaded)
elif use_sample:
    df = load_sample()
else:
    st.info("Click **Load sample dataset** or upload a CSV to start.")
    st.stop()

df.columns = [c.lower().strip() for c in df.columns]

required = {"date","channel","visits","signup","add_to_cart","checkout","purchase","spend","revenue"}
missing = required - set(df.columns)
if missing:
    st.error(f"Missing columns: {sorted(list(missing))}")
    st.stop()

df["date"] = pd.to_datetime(df["date"])

# Filters
c1, c2 = st.columns(2)
with c1:
    start = st.date_input("Start date", df["date"].min().date())
with c2:
    end = st.date_input("End date", df["date"].max().date())

mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
df = df[mask].copy()

channels = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
df = df[df["channel"].isin(channels)]

# KPIs
spend = df["spend"].sum()
revenue = df["revenue"].sum()
purchases = df["purchase"].sum()
visits = df["visits"].sum()

roas = revenue / spend if spend else 0
cac = spend / purchases if purchases else 0
cvr = purchases / visits if visits else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Spend", f"${spend:,.0f}")
k2.metric("Revenue", f"${revenue:,.0f}")
k3.metric("ROAS", f"{roas:.2f}x")
k4.metric("Conversion Rate", f"{cvr:.2%}")

st.divider()

# Funnel
st.subheader("Funnel")
funnel = pd.DataFrame({
    "stage": ["Visits","Signup","Add to Cart","Checkout","Purchase"],
    "count": [df["visits"].sum(), df["signup"].sum(), df["add_to_cart"].sum(), df["checkout"].sum(), df["purchase"].sum()]
})
fig = px.funnel(funnel, x="count", y="stage")
st.plotly_chart(fig, use_container_width=True)

# Drop-off table
funnel["next"] = funnel["count"].shift(-1)
funnel["dropoff_%"] = ((funnel["count"] - funnel["next"]) / funnel["count"]).round(4)
st.subheader("Drop-off by step")
st.dataframe(funnel[["stage","count","dropoff_%"]], use_container_width=True)

# Trend
st.subheader("Weekly Trend (Spend / Revenue / Purchases)")
trend = df.groupby("date", as_index=False)[["spend","revenue","purchase"]].sum()
fig2 = px.line(trend, x="date", y=["spend","revenue","purchase"])
st.plotly_chart(fig2, use_container_width=True)

# Channel performance
st.subheader("Channel Performance")
by_ch = df.groupby("channel", as_index=False).agg(
    spend=("spend","sum"),
    revenue=("revenue","sum"),
    purchase=("purchase","sum"),
    visits=("visits","sum")
)
by_ch["roas"] = (by_ch["revenue"] / by_ch["spend"]).round(2)
by_ch["cac"] = (by_ch["spend"] / by_ch["purchase"].replace({0: pd.NA})).round(2)
by_ch["cvr"] = (by_ch["purchase"] / by_ch["visits"].replace({0: pd.NA})).round(4)

st.dataframe(by_ch.sort_values("roas", ascending=False), use_container_width=True)

# Insights
st.subheader("Executive Insights")
best = by_ch.sort_values("roas", ascending=False).head(1)
worst = by_ch.sort_values("roas", ascending=True).head(1)

# biggest drop
drop = funnel.dropna().sort_values("dropoff_%", ascending=False).head(1)

st.write(f"✅ Best ROAS channel: **{best['channel'].iloc[0]}** ({best['roas'].iloc[0]}x)")
st.write(f"⚠️ Lowest ROAS channel: **{worst['channel'].iloc[0]}** ({worst['roas'].iloc[0]}x)")
st.write(f"📉 Biggest funnel drop: **{drop['stage'].iloc[0]} → next step** ({drop['dropoff_%'].iloc[0]:.0%} drop-off)")
st.write("👉 Recommendation: prioritize fixing the biggest drop-off step first, then reallocate spend toward higher-ROAS channels.")
