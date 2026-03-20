import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="", layout="wide")

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cleaned_dataset.csv")
    df = pd.read_csv(path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["date"] = df["Timestamp"].dt.date
    df["Net"] = df["Sales Count"] - df["Redemption Count"]
    df["period"] = df["hour"].apply(lambda h: "Peak" if 8 <= h <= 20 else "Off-Peak")
    return df

df = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.title("Real-Time Ferry Ticket Sales & Redemption Analytics  for Tornoto Island Park ")

#---------------------LOGO-----------------------------------
import base64
with open("Screenshot 2026-03-11 181227.png", "rb") as f:
    logo = base64.b64encode(f.read()).decode()
st.sidebar.markdown(f'<img src="data:image/png;base64,{logo}" width="200"/>', unsafe_allow_html=True)

# USER ROLE SELECTOR
st.sidebar.subheader("👤 Select User Role")
role = st.sidebar.radio(
    "Role",
    ["Operations Team", "Policy Planners", "Management Stakeholders"],
    index=0
)

role_desc = {
    "Operations Team":           "Real-time hourly monitoring & anomaly detection",
    "Policy Planners":           "Trend analysis & seasonal planning insights",
    "Management Stakeholders":   "Executive summary & high-level KPI overview",
}
st.sidebar.caption(role_desc[role])
st.sidebar.markdown("---")

# FILTERS
st.sidebar.subheader("🔧 Filters")

years = sorted(df["year"].unique(), reverse=True)
sel_years = st.sidebar.multiselect("Year", years, default=years[:3])

months = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
          7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
sel_months = st.sidebar.multiselect("Month", list(months.keys()),
                                    default=list(months.keys()),
                                    format_func=lambda x: months[x])

hour_range = st.sidebar.slider("Hour Range", 0, 23, (0, 23))

days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
sel_days = st.sidebar.multiselect("Day of Week", days, default=days)

period_filter = st.sidebar.radio("Period", ["All", "Peak Only (8-20)", "Off-Peak Only"])

# ── Apply Filters ──────────────────────────────────────────────────────────────
filt = df[
    df["year"].isin(sel_years) &
    df["month"].isin(sel_months) &
    df["hour"].between(*hour_range) &
    df["day_of_week"].isin(sel_days)
]
if period_filter == "Peak Only (8-20)":
    filt = filt[filt["period"] == "Peak"]
elif period_filter == "Off-Peak Only":
    filt = filt[filt["period"] == "Off-Peak"]

if filt.empty:
    st.warning("No data for selected filters.")
    st.stop()

# ── KPI Calculations ───────────────────────────────────────────────────────────
total_sales   = int(filt["Sales Count"].sum())
total_reedm   = int(filt["Redemption Count"].sum())
net_movement  = int(filt["Net"].sum())
avg_sold_hr   = round(filt.groupby(["date","hour"])["Sales Count"].sum().mean(), 1)
avg_reedm_hr  = round(filt.groupby(["date","hour"])["Redemption Count"].sum().mean(), 1)
reedm_rate    = round(total_reedm / max(total_sales, 1) * 100, 1)
peak_hour     = int(filt.groupby("hour")["Sales Count"].sum().idxmax())
peak_sales    = int(filt[filt["period"]=="Peak"]["Sales Count"].sum())
offpeak_sales = int(filt[filt["period"]=="Off-Peak"]["Sales Count"].sum())
offseason_idx = round(offpeak_sales / max(peak_sales, 1) * 100, 1)

day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
mon_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
             7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

# ── Session state ──────────────────────────────────────────────────────────────
if "kpi" not in st.session_state:
    st.session_state.kpi = "kpi1"

# ══════════════════════════════════════════════════════════════════════════════
# ROLE: OPERATIONS TEAM
# Focus: Real-time hourly trends, anomalies, peak windows, live comparison
# ══════════════════════════════════════════════════════════════════════════════
if role == "Operations Team":
    st.title("Toronto — Operations Team View")
    st.caption("Real-time monitoring · Peak window tracking · Hourly anomaly detection")
    st.markdown("---")

    # KPIs relevant to operations
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🎫 Avg Sold/Hr",      f"{avg_sold_hr:,}",   f"Total: {total_sales:,}")
    c2.metric("🔄 Avg Redeemed/Hr",  f"{avg_reedm_hr:,}",  f"Rate: {reedm_rate}%")
    c3.metric("🚶 Net Movement",      f"{net_movement:,}",  "Sales − Redemptions")
    c4.metric("⚡ Peak Hour",         f"{peak_hour}:00",    "Highest demand hour")
    c5.metric("📉 Off-Season Index",  f"{offseason_idx}%",  f"Off-Pk: {offpeak_sales:,}")
    st.markdown("---")

    # KPI navigation
    st.subheader("📊 Explore by KPI")
    st.caption("Click a button to switch chart view")
    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("🎫 Tickets Sold/Hr",    use_container_width=True): st.session_state.kpi = "kpi1"; st.rerun()
    if b2.button("🔄 Redeemed/Hr",        use_container_width=True): st.session_state.kpi = "kpi2"; st.rerun()
    if b3.button("🚶 Net Movement",        use_container_width=True): st.session_state.kpi = "kpi3"; st.rerun()
    if b4.button("⚡ Peak Demand",         use_container_width=True): st.session_state.kpi = "kpi4"; st.rerun()
    if b5.button("📉 Off-Season Index",    use_container_width=True): st.session_state.kpi = "kpi5"; st.rerun()
    st.markdown("---")

    kpi = st.session_state.kpi

    if kpi == "kpi1":
        st.subheader("🎫 Tickets Sold per Hour")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Avg Tickets Sold by Hour**")
            hd = filt.groupby("hour")["Sales Count"].mean().reset_index()
            st.plotly_chart(px.bar(hd, x="hour", y="Sales Count", labels={"hour":"Hour","Sales Count":"Avg Tickets"}), use_container_width=True)
        with r1c2:
            st.markdown("**Hourly Sales: Weekday vs Weekend**")
            hd2 = filt.groupby(["hour","weekend"])["Sales Count"].mean().reset_index()
            hd2["Type"] = hd2["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.line(hd2, x="hour", y="Sales Count", color="Type", markers=True, labels={"hour":"Hour","Sales Count":"Avg Sales"}), use_container_width=True)
        with r2c1:
            st.markdown("**Sales Heatmap: Day × Hour**")
            pivot = filt.groupby(["day_of_week","hour"])["Sales Count"].mean().reset_index()
            pvt = pivot.pivot(index="day_of_week", columns="hour", values="Sales Count").reindex(day_order)
            st.plotly_chart(px.imshow(pvt, labels=dict(x="Hour",y="Day",color="Avg Sales"), color_continuous_scale="Blues", aspect="auto"), use_container_width=True)
        with r2c2:
            st.markdown("**Z-Score Distribution (Anomaly Detection)**")
            st.plotly_chart(px.histogram(filt, x="zscore", nbins=50, labels={"zscore":"Z-Score"}).update_traces(marker_color="steelblue"), use_container_width=True)

    elif kpi == "kpi2":
        st.subheader("🔄 Tickets Redeemed per Hour")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Avg Sold vs Redeemed per Hour**")
            hd = filt.groupby("hour")[["Sales Count","Redemption Count"]].mean().reset_index()
            fig = go.Figure()
            fig.add_bar(x=hd["hour"], y=hd["Sales Count"], name="Sold")
            fig.add_bar(x=hd["hour"], y=hd["Redemption Count"], name="Redeemed")
            fig.update_layout(barmode="group", xaxis_title="Hour")
            st.plotly_chart(fig, use_container_width=True)
        with r1c2:
            st.markdown("**Redemption Heatmap: Day × Hour**")
            pivot = filt.groupby(["day_of_week","hour"])["Redemption Count"].mean().reset_index()
            pvt = pivot.pivot(index="day_of_week", columns="hour", values="Redemption Count").reindex(day_order)
            st.plotly_chart(px.imshow(pvt, color_continuous_scale="Oranges", aspect="auto", labels=dict(x="Hour",y="Day",color="Avg Redeem")), use_container_width=True)
        with r2c1:
            st.markdown("**1-Hour Rolling Sales Avg**")
            roll = filt.dropna(subset=["sales_rolling_1h"]).sort_values("Timestamp").iloc[::50]
            st.plotly_chart(px.line(roll, x="Timestamp", y="sales_rolling_1h", labels={"sales_rolling_1h":"Rolling Avg"}), use_container_width=True)
        with r2c2:
            st.markdown("**Redemption Share: Weekday vs Weekend**")
            wk = filt.groupby("weekend")["Redemption Count"].sum().reset_index()
            wk["label"] = wk["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.pie(wk, names="label", values="Redemption Count", hole=0.4), use_container_width=True)

    elif kpi == "kpi3":
        st.subheader("🚶 Net Passenger Movement")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Avg Net Movement by Hour**")
            hd = filt.groupby("hour")["Net"].mean().reset_index()
            st.plotly_chart(px.bar(hd, x="hour", y="Net", color="Net", color_continuous_scale="RdYlGn", labels={"hour":"Hour","Net":"Avg Net"}), use_container_width=True)
        with r1c2:
            st.markdown("**Net Movement by Day of Week**")
            dow = filt.groupby("day_of_week")["Net"].mean().reset_index()
            dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(dow.sort_values("day_of_week"), x="day_of_week", y="Net", labels={"day_of_week":"Day","Net":"Avg Net"}), use_container_width=True)
        with r2c1:
            st.markdown("**Sales vs Redemptions Scatter**")
            sample = filt.sample(min(2000, len(filt)), random_state=42)
            st.plotly_chart(px.scatter(sample, x="Sales Count", y="Redemption Count", color="Net", color_continuous_scale="RdYlGn", opacity=0.5), use_container_width=True)
        with r2c2:
            st.markdown("**4-Hour Rolling Sales Avg**")
            roll = filt.dropna(subset=["sales_rolling_4h"]).sort_values("Timestamp").iloc[::50]
            st.plotly_chart(px.line(roll, x="Timestamp", y="sales_rolling_4h", labels={"sales_rolling_4h":"4h Rolling Avg"}), use_container_width=True)

    elif kpi == "kpi4":
        st.subheader("⚡ Peak Demand Windows")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        filt2 = filt.copy()
        filt2["Period"] = filt2["hour"].apply(lambda h: "Peak (8-20)" if 8<=h<=20 else "Off-Peak")
        with r1c1:
            st.markdown("**Peak vs Off-Peak Volume**")
            comp = filt2.groupby("Period")[["Sales Count","Redemption Count"]].sum().reset_index()
            fig = go.Figure()
            fig.add_bar(x=comp["Period"], y=comp["Sales Count"], name="Sales")
            fig.add_bar(x=comp["Period"], y=comp["Redemption Count"], name="Redemptions")
            fig.update_layout(barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        with r1c2:
            st.markdown("**Hourly Sales (Peak Window Shaded)**")
            hd = filt.groupby("hour")["Sales Count"].sum().reset_index()
            fig = px.area(hd, x="hour", y="Sales Count", labels={"hour":"Hour","Sales Count":"Total Sales"})
            fig.add_vrect(x0=7.5, x1=20.5, fillcolor="yellow", opacity=0.07, line_width=0, annotation_text="Peak Window")
            st.plotly_chart(fig, use_container_width=True)
        with r2c1:
            st.markdown("**Sales Distribution: Peak vs Off-Peak**")
            fig = go.Figure()
            for p in ["Peak (8-20)", "Off-Peak"]:
                fig.add_box(y=filt2[filt2["Period"]==p]["Sales Count"], name=p, boxmean=True)
            st.plotly_chart(fig, use_container_width=True)
        with r2c2:
            st.markdown("**Peak Sales Share by Day**")
            peak_dow = filt2[filt2["Period"]=="Peak (8-20)"].groupby("day_of_week")["Sales Count"].sum().reset_index()
            peak_dow["day_of_week"] = pd.Categorical(peak_dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.pie(peak_dow.sort_values("day_of_week"), names="day_of_week", values="Sales Count", hole=0.35), use_container_width=True)

    elif kpi == "kpi5":
        st.subheader("📉 Off-Season Utilization Index")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Utilization Index by Month**")
            md = filt.groupby(["month","period"])["Sales Count"].sum().reset_index()
            peak_m = md[md["period"]=="Peak"].set_index("month")["Sales Count"]
            off_m  = md[md["period"]=="Off-Peak"].set_index("month")["Sales Count"]
            idx_df = pd.DataFrame({"Peak":peak_m,"Off-Peak":off_m}).fillna(0).reset_index()
            idx_df["Index (%)"] = idx_df["Off-Peak"] / idx_df["Peak"].replace(0,1) * 100
            idx_df["Month"] = idx_df["month"].map(mon_names)
            fig = px.bar(idx_df, x="Month", y="Index (%)")
            fig.add_hline(y=50, line_dash="dash", annotation_text="50% baseline")
            st.plotly_chart(fig, use_container_width=True)
        with r1c2:
            st.markdown("**Peak vs Off-Peak Stacked Area**")
            md2 = filt.groupby(["month","period"])["Sales Count"].sum().reset_index()
            md2["Month"] = md2["month"].map(mon_names)
            st.plotly_chart(px.area(md2, x="Month", y="Sales Count", color="period"), use_container_width=True)
        with r2c1:
            st.markdown("**Off-Peak Heatmap: Year × Month**")
            ym = filt[filt["period"]=="Off-Peak"].groupby(["year","month"])["Sales Count"].sum().reset_index()
            pvt = ym.pivot(index="year", columns="month", values="Sales Count").fillna(0)
            pvt.columns = [mon_names[c] for c in pvt.columns]
            st.plotly_chart(px.imshow(pvt, color_continuous_scale="Purples", aspect="auto", labels=dict(x="Month",y="Year",color="Sales")), use_container_width=True)
        with r2c2:
            st.markdown("**Off-Peak: Weekday vs Weekend**")
            wk = filt[filt["period"]=="Off-Peak"].groupby("weekend")["Sales Count"].sum().reset_index()
            wk["label"] = wk["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.pie(wk, names="label", values="Sales Count", hole=0.4), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROLE: POLICY PLANNERS
# Focus: Long-term trends, seasonal patterns, year-over-year, utilization
# ══════════════════════════════════════════════════════════════════════════════
elif role == "Policy Planners":
    st.title("📋 Toronto Transit — Policy Planners View")
    st.caption("Seasonal trends · Year-over-year analysis · Utilization planning")
    st.markdown("---")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📅 Total Sales",       f"{total_sales:,}",   f"{len(sel_years)} yrs selected")
    c2.metric("🔄 Total Redemptions", f"{total_reedm:,}",   f"Rate: {reedm_rate}%")
    c3.metric("🚶 Net Movement",       f"{net_movement:,}",  "Sales − Redemptions")
    c4.metric("📉 Off-Season Index",  f"{offseason_idx}%",  "Off-Pk / Peak ratio")
    c5.metric("⚡ Peak Hour",          f"{peak_hour}:00",    "Highest demand hour")
    st.markdown("---")

    st.subheader("📊 Explore by KPI")
    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("🎫 Tickets Sold/Hr",   use_container_width=True): st.session_state.kpi = "kpi1"; st.rerun()
    if b2.button("🔄 Redeemed/Hr",       use_container_width=True): st.session_state.kpi = "kpi2"; st.rerun()
    if b3.button("🚶 Net Movement",       use_container_width=True): st.session_state.kpi = "kpi3"; st.rerun()
    if b4.button("⚡ Peak Demand",        use_container_width=True): st.session_state.kpi = "kpi4"; st.rerun()
    if b5.button("📉 Off-Season Index",   use_container_width=True): st.session_state.kpi = "kpi5"; st.rerun()
    st.markdown("---")

    kpi = st.session_state.kpi

    if kpi == "kpi1":
        st.subheader("🎫 Tickets Sold — Seasonal & Long-Term Trends")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Monthly Sales Trend**")
            md = filt.groupby("month")["Sales Count"].sum().reset_index()
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.line(md, x="Month", y="Sales Count", markers=True), use_container_width=True)
        with r1c2:
            st.markdown("**Year-over-Year Sales**")
            yr = filt.groupby("year")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Sales Count", labels={"year":"Year","Sales Count":"Total"}), use_container_width=True)
        with r2c1:
            st.markdown("**Sales by Month & Year (Heatmap)**")
            ym = filt.groupby(["year","month"])["Sales Count"].sum().reset_index()
            pvt = ym.pivot(index="year", columns="month", values="Sales Count").fillna(0)
            pvt.columns = [mon_names[c] for c in pvt.columns]
            st.plotly_chart(px.imshow(pvt, color_continuous_scale="Blues", aspect="auto", labels=dict(x="Month",y="Year",color="Sales")), use_container_width=True)
        with r2c2:
            st.markdown("**Weekday vs Weekend Sales**")
            wk = filt.groupby("weekend")["Sales Count"].sum().reset_index()
            wk["label"] = wk["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.pie(wk, names="label", values="Sales Count", hole=0.4), use_container_width=True)

    elif kpi == "kpi2":
        st.subheader("🔄 Redemption Trends — Policy View")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Monthly Redemption Rate (%)**")
            md = filt.groupby("month").agg(S=("Sales Count","sum"), R=("Redemption Count","sum")).reset_index()
            md["Rate"] = md["R"] / md["S"].replace(0,1) * 100
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.line(md, x="Month", y="Rate", markers=True, labels={"Rate":"Rate (%)"}), use_container_width=True)
        with r1c2:
            st.markdown("**Year-over-Year Redemptions**")
            yr = filt.groupby("year")["Redemption Count"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Redemption Count", labels={"year":"Year"}), use_container_width=True)
        with r2c1:
            st.markdown("**Redemption Rate by Day of Week**")
            rd = filt.groupby("day_of_week").agg(S=("Sales Count","sum"), R=("Redemption Count","sum")).reset_index()
            rd["Rate (%)"] = rd["R"] / rd["S"].replace(0,1) * 100
            rd["day_of_week"] = pd.Categorical(rd["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(rd.sort_values("day_of_week"), x="day_of_week", y="Rate (%)", labels={"day_of_week":"Day"}), use_container_width=True)
        with r2c2:
            st.markdown("**Redemptions by Month & Year (Heatmap)**")
            ym = filt.groupby(["year","month"])["Redemption Count"].sum().reset_index()
            pvt = ym.pivot(index="year", columns="month", values="Redemption Count").fillna(0)
            pvt.columns = [mon_names[c] for c in pvt.columns]
            st.plotly_chart(px.imshow(pvt, color_continuous_scale="Oranges", aspect="auto", labels=dict(x="Month",y="Year",color="Redemptions")), use_container_width=True)

    elif kpi == "kpi3":
        st.subheader("🚶 Net Passenger Movement — Policy View")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Monthly Net Movement**")
            md = filt.groupby("month")["Net"].sum().reset_index()
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.bar(md, x="Month", y="Net", labels={"Net":"Net Movement"}), use_container_width=True)
        with r1c2:
            st.markdown("**Cumulative Net by Month**")
            md2 = filt.groupby("month")["Net"].sum().reset_index().sort_values("month")
            md2["Cumulative"] = md2["Net"].cumsum()
            md2["Month"] = md2["month"].map(mon_names)
            st.plotly_chart(px.line(md2, x="Month", y="Cumulative", markers=True, labels={"Cumulative":"Cumulative Net"}), use_container_width=True)
        with r2c1:
            st.markdown("**Net Movement: Year-over-Year**")
            yr = filt.groupby("year")["Net"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Net", labels={"year":"Year","Net":"Net Movement"}), use_container_width=True)
        with r2c2:
            st.markdown("**Net by Day of Week**")
            dow = filt.groupby("day_of_week")["Net"].mean().reset_index()
            dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(dow.sort_values("day_of_week"), x="day_of_week", y="Net", labels={"day_of_week":"Day","Net":"Avg Net"}), use_container_width=True)

    elif kpi == "kpi4":
        st.subheader("⚡ Peak Demand — Policy Planning")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        filt2 = filt.copy()
        filt2["Period"] = filt2["hour"].apply(lambda h: "Peak (8-20)" if 8<=h<=20 else "Off-Peak")
        with r1c1:
            st.markdown("**Peak vs Off-Peak by Year**")
            yrp = filt2.groupby(["year","Period"])["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(yrp, x="year", y="Sales Count", color="Period", barmode="group", labels={"year":"Year"}), use_container_width=True)
        with r1c2:
            st.markdown("**Monthly Peak Sales Trend**")
            mp = filt2[filt2["Period"]=="Peak (8-20)"].groupby("month")["Sales Count"].sum().reset_index()
            mp["Month"] = mp["month"].map(mon_names)
            st.plotly_chart(px.line(mp, x="Month", y="Sales Count", markers=True), use_container_width=True)
        with r2c1:
            st.markdown("**Peak Sales Share by Day of Week**")
            peak_dow = filt2[filt2["Period"]=="Peak (8-20)"].groupby("day_of_week")["Sales Count"].sum().reset_index()
            peak_dow["day_of_week"] = pd.Categorical(peak_dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(peak_dow.sort_values("day_of_week"), x="day_of_week", y="Sales Count", labels={"day_of_week":"Day"}), use_container_width=True)
        with r2c2:
            st.markdown("**Peak vs Off-Peak Volume (Pie)**")
            comp = filt2.groupby("Period")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.pie(comp, names="Period", values="Sales Count", hole=0.4), use_container_width=True)

    elif kpi == "kpi5":
        st.subheader("📉 Off-Season Utilization — Policy View")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Utilization Index by Month**")
            md = filt.groupby(["month","period"])["Sales Count"].sum().reset_index()
            peak_m = md[md["period"]=="Peak"].set_index("month")["Sales Count"]
            off_m  = md[md["period"]=="Off-Peak"].set_index("month")["Sales Count"]
            idx_df = pd.DataFrame({"Peak":peak_m,"Off-Peak":off_m}).fillna(0).reset_index()
            idx_df["Index (%)"] = idx_df["Off-Peak"] / idx_df["Peak"].replace(0,1) * 100
            idx_df["Month"] = idx_df["month"].map(mon_names)
            fig = px.bar(idx_df, x="Month", y="Index (%)")
            fig.add_hline(y=50, line_dash="dash", annotation_text="50% baseline")
            st.plotly_chart(fig, use_container_width=True)
        with r1c2:
            st.markdown("**Off-Peak Heatmap: Year × Month**")
            ym = filt[filt["period"]=="Off-Peak"].groupby(["year","month"])["Sales Count"].sum().reset_index()
            pvt = ym.pivot(index="year", columns="month", values="Sales Count").fillna(0)
            pvt.columns = [mon_names[c] for c in pvt.columns]
            st.plotly_chart(px.imshow(pvt, color_continuous_scale="Purples", aspect="auto", labels=dict(x="Month",y="Year",color="Sales")), use_container_width=True)
        with r2c1:
            st.markdown("**Peak vs Off-Peak Stacked Area**")
            md2 = filt.groupby(["month","period"])["Sales Count"].sum().reset_index()
            md2["Month"] = md2["month"].map(mon_names)
            st.plotly_chart(px.area(md2, x="Month", y="Sales Count", color="period"), use_container_width=True)
        with r2c2:
            st.markdown("**Off-Peak Utilization: Year-over-Year**")
            yr_off = filt[filt["period"]=="Off-Peak"].groupby("year")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.line(yr_off, x="year", y="Sales Count", markers=True, labels={"year":"Year","Sales Count":"Off-Peak Sales"}), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROLE: MANAGEMENT STAKEHOLDERS
# Focus: High-level summary, totals, simple comparisons, no deep drill-down
# ══════════════════════════════════════════════════════════════════════════════
elif role == "Management Stakeholders":
    st.title("📊 Toronto Transit — Management Overview")
    st.caption("Executive summary · High-level KPIs · Key comparisons")
    st.markdown("---")

    # Larger, prominent KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("🎫 Total Tickets Sold",       f"{total_sales:,}")
    c2.metric("🔄 Total Tickets Redeemed",   f"{total_reedm:,}",  f"Redemption Rate: {reedm_rate}%")
    c3.metric("🚶 Net Passenger Movement",    f"{net_movement:,}", "Sales − Redemptions")

    c4, c5, _ = st.columns(3)
    c4.metric("⚡ Peak Demand Hour",          f"{peak_hour}:00",   "Highest volume hour of day")
    c5.metric("📉 Off-Season Util. Index",   f"{offseason_idx}%", f"Peak: {peak_sales:,} · Off-Pk: {offpeak_sales:,}")
    st.markdown("---")

    st.subheader("📊 Explore by KPI")
    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("🎫 Tickets Sold",       use_container_width=True): st.session_state.kpi = "kpi1"; st.rerun()
    if b2.button("🔄 Redeemed",           use_container_width=True): st.session_state.kpi = "kpi2"; st.rerun()
    if b3.button("🚶 Net Movement",        use_container_width=True): st.session_state.kpi = "kpi3"; st.rerun()
    if b4.button("⚡ Peak Demand",         use_container_width=True): st.session_state.kpi = "kpi4"; st.rerun()
    if b5.button("📉 Off-Season Index",    use_container_width=True): st.session_state.kpi = "kpi5"; st.rerun()
    st.markdown("---")

    kpi = st.session_state.kpi

    if kpi == "kpi1":
        st.subheader("🎫 Tickets Sold — Executive Summary")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Annual Sales Totals**")
            yr = filt.groupby("year")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Sales Count", labels={"year":"Year","Sales Count":"Total Sold"}), use_container_width=True)
        with r1c2:
            st.markdown("**Monthly Sales Overview**")
            md = filt.groupby("month")["Sales Count"].sum().reset_index()
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.bar(md, x="Month", y="Sales Count"), use_container_width=True)
        with r2c1:
            st.markdown("**Sales by Day of Week**")
            dow = filt.groupby("day_of_week")["Sales Count"].sum().reset_index()
            dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(dow.sort_values("day_of_week"), x="day_of_week", y="Sales Count", labels={"day_of_week":"Day"}), use_container_width=True)
        with r2c2:
            st.markdown("**Weekday vs Weekend Split**")
            wk = filt.groupby("weekend")["Sales Count"].sum().reset_index()
            wk["label"] = wk["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.pie(wk, names="label", values="Sales Count", hole=0.4), use_container_width=True)

    elif kpi == "kpi2":
        st.subheader("🔄 Redemptions — Executive Summary")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Annual Redemption Totals**")
            yr = filt.groupby("year")["Redemption Count"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Redemption Count", labels={"year":"Year"}), use_container_width=True)
        with r1c2:
            st.markdown("**Monthly Redemption Rate (%)**")
            md = filt.groupby("month").agg(S=("Sales Count","sum"), R=("Redemption Count","sum")).reset_index()
            md["Rate"] = md["R"] / md["S"].replace(0,1) * 100
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.line(md, x="Month", y="Rate", markers=True, labels={"Rate":"Rate (%)"}), use_container_width=True)
        with r2c1:
            st.markdown("**Sold vs Redeemed (Total)**")
            totals = pd.DataFrame({"Category":["Sold","Redeemed"], "Count":[total_sales, total_reedm]})
            st.plotly_chart(px.bar(totals, x="Category", y="Count"), use_container_width=True)
        with r2c2:
            st.markdown("**Redemption Share: Weekday vs Weekend**")
            wk = filt.groupby("weekend")["Redemption Count"].sum().reset_index()
            wk["label"] = wk["weekend"].map({True:"Weekend", False:"Weekday"})
            st.plotly_chart(px.pie(wk, names="label", values="Redemption Count", hole=0.4), use_container_width=True)

    elif kpi == "kpi3":
        st.subheader("🚶 Net Passenger Movement — Executive Summary")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Annual Net Movement**")
            yr = filt.groupby("year")["Net"].sum().reset_index()
            st.plotly_chart(px.bar(yr, x="year", y="Net", labels={"year":"Year","Net":"Net Movement"}), use_container_width=True)
        with r1c2:
            st.markdown("**Monthly Net Movement**")
            md = filt.groupby("month")["Net"].sum().reset_index()
            md["Month"] = md["month"].map(mon_names)
            st.plotly_chart(px.bar(md, x="Month", y="Net"), use_container_width=True)
        with r2c1:
            st.markdown("**Net by Day of Week**")
            dow = filt.groupby("day_of_week")["Net"].mean().reset_index()
            dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=day_order, ordered=True)
            st.plotly_chart(px.bar(dow.sort_values("day_of_week"), x="day_of_week", y="Net", labels={"day_of_week":"Day"}), use_container_width=True)
        with r2c2:
            st.markdown("**Sales vs Redemptions Summary**")
            totals = pd.DataFrame({"Type":["Sales","Redemptions","Net"], "Count":[total_sales, total_reedm, net_movement]})
            st.plotly_chart(px.bar(totals, x="Type", y="Count"), use_container_width=True)

    elif kpi == "kpi4":
        st.subheader("⚡ Peak Demand — Executive Summary")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        filt2 = filt.copy()
        filt2["Period"] = filt2["hour"].apply(lambda h: "Peak (8-20)" if 8<=h<=20 else "Off-Peak")
        with r1c1:
            st.markdown("**Peak vs Off-Peak Total Sales**")
            comp = filt2.groupby("Period")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(comp, x="Period", y="Sales Count"), use_container_width=True)
        with r1c2:
            st.markdown("**Peak Sales Share (Pie)**")
            st.plotly_chart(px.pie(comp, names="Period", values="Sales Count", hole=0.4), use_container_width=True)
        with r2c1:
            st.markdown("**Monthly Peak Sales**")
            mp = filt2[filt2["Period"]=="Peak (8-20)"].groupby("month")["Sales Count"].sum().reset_index()
            mp["Month"] = mp["month"].map(mon_names)
            st.plotly_chart(px.line(mp, x="Month", y="Sales Count", markers=True), use_container_width=True)
        with r2c2:
            st.markdown("**Annual Peak vs Off-Peak**")
            yrp = filt2.groupby(["year","Period"])["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(yrp, x="year", y="Sales Count", color="Period", barmode="group", labels={"year":"Year"}), use_container_width=True)

    elif kpi == "kpi5":
        st.subheader("📉 Off-Season Utilization — Executive Summary")
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        with r1c1:
            st.markdown("**Utilization Index by Month**")
            md = filt.groupby(["month","period"])["Sales Count"].sum().reset_index()
            peak_m = md[md["period"]=="Peak"].set_index("month")["Sales Count"]
            off_m  = md[md["period"]=="Off-Peak"].set_index("month")["Sales Count"]
            idx_df = pd.DataFrame({"Peak":peak_m,"Off-Peak":off_m}).fillna(0).reset_index()
            idx_df["Index (%)"] = idx_df["Off-Peak"] / idx_df["Peak"].replace(0,1) * 100
            idx_df["Month"] = idx_df["month"].map(mon_names)
            fig = px.bar(idx_df, x="Month", y="Index (%)")
            fig.add_hline(y=50, line_dash="dash", annotation_text="50% baseline")
            st.plotly_chart(fig, use_container_width=True)
        with r1c2:
            st.markdown("**Annual Off-Peak Sales**")
            yr_off = filt[filt["period"]=="Off-Peak"].groupby("year")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.bar(yr_off, x="year", y="Sales Count", labels={"year":"Year","Sales Count":"Off-Peak Sales"}), use_container_width=True)
        with r2c1:
            st.markdown("**Peak vs Off-Peak Split (Pie)**")
            comp = filt.groupby("period")["Sales Count"].sum().reset_index()
            st.plotly_chart(px.pie(comp, names="period", values="Sales Count", hole=0.4), use_container_width=True)
        with r2c2:
            st.markdown("**Off-Peak Sales by Month**")
            off_md = filt[filt["period"]=="Off-Peak"].groupby("month")["Sales Count"].sum().reset_index()
            off_md["Month"] = off_md["month"].map(mon_names)
            st.plotly_chart(px.bar(off_md, x="Month", y="Sales Count"), use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"City of Toronto · Transit Operations Dashboard · Role: {role} · Data: Cleaned_dataset.csv")
