"""Overview Dashboard Page."""

import streamlit as st

st.set_page_config(page_title="Overview", page_icon="\U0001f4ca", layout="wide")
st.title("Overview Dashboard")

try:
    import pandas as pd
    import plotly.express as px

    from data.loader import load_all_data, load_traceability, load_data_quality_summary

    @st.cache_data(ttl=60)
    def load_data():
        return load_all_data()

    top_items, match_map, prices = load_data()

    if top_items.empty:
        st.warning("No data available. Please run the pipeline first.")
        st.stop()

    # Data quality warning
    dq = load_data_quality_summary()
    if dq and dq["status"] == "degraded":
        st.warning(f"Data Quality: {dq['message']}")
    elif dq and dq["status"] == "empty":
        st.error("No data loaded in the database.")

    # KPI Cards
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    tt_count = len(top_items[top_items["platform"] == "tiktok"])
    sh_count = len(top_items[top_items["platform"] == "shopee"])

    col1.metric("TikTok Items", tt_count)
    col2.metric("Shopee Items", sh_count)

    if not match_map.empty:
        matched = len(match_map[match_map["status"] != "no_match"])
        match_rate = matched / max(tt_count, 1) * 100
        needs_review = len(match_map[match_map["status"] == "needs_review"])
        col3.metric("Match Rate", f"{match_rate:.1f}%")
        col4.metric("Needs Review", needs_review)
    else:
        col3.metric("Match Rate", "N/A")
        col4.metric("Needs Review", "N/A")

    st.markdown("---")

    # Overlap Chart
    if not match_map.empty:
        st.subheader("Cross-Platform Overlap")
        overlap = match_map["match_type"].value_counts().reset_index()
        overlap.columns = ["Match Type", "Count"]
        fig = px.bar(
            overlap, x="Match Type", y="Count",
            color="Match Type",
            color_discrete_map={
                "exact_same": "#10b981",
                "variant_family": "#3b82f6",
                "similar": "#f59e0b",
                "no_match": "#94a3b8",
            },
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Price Band Distribution
    if not prices.empty:
        st.subheader("Price Band Distribution")
        prices_with_platform = prices.merge(
            top_items[["platform", "item_id"]].drop_duplicates(),
            on=["platform", "item_id"],
            how="inner",
        )
        prices_with_platform["price_thb"] = prices_with_platform["price"] / 100

        bins = [0, 50, 100, 200, 500, 1000, float("inf")]
        labels = ["<50", "50-100", "100-200", "200-500", "500-1K", "1K+"]
        prices_with_platform["band"] = pd.cut(
            prices_with_platform["price_thb"], bins=bins, labels=labels
        )

        band_dist = (
            prices_with_platform.groupby(["band", "platform"], observed=False)
            .size()
            .reset_index(name="count")
        )
        fig2 = px.bar(
            band_dist, x="band", y="count", color="platform",
            barmode="group",
            color_discrete_map={"tiktok": "#ff6b6b", "shopee": "#ee4d2d"},
        )
        fig2.update_layout(height=350, xaxis_title="Price Band (THB)", yaxis_title="Items")
        st.plotly_chart(fig2, use_container_width=True)

    # Top Brands
    st.subheader("Top Brands by Platform")
    if "brand_std" in top_items.columns:
        brand_counts = (
            top_items[top_items["brand_std"].notna()]
            .groupby(["brand_std", "platform"])
            .size()
            .reset_index(name="count")
        )
        brand_pivot = brand_counts.pivot_table(
            index="brand_std", columns="platform", values="count", fill_value=0
        ).reset_index()
        brand_pivot["total"] = brand_pivot.get("tiktok", 0) + brand_pivot.get("shopee", 0)
        brand_pivot = brand_pivot.sort_values("total", ascending=False).head(15)
        st.dataframe(brand_pivot, use_container_width=True, hide_index=True)

    # Traceability metadata from database
    st.markdown("---")
    trace = load_traceability()
    if trace:
        parts = [
            f"Event Date: {trace['event_date']}",
            f"Run ID: {trace['run_id'][:8]}...",
            f"Batch: {trace['batch_id']}",
            f"Rule Version: {trace['rule_version']}",
            f"Schema Version: {trace['schema_version']}",
            "Window: 14d",
            "Category: personal_care",
            "Site: TH",
        ]
        st.caption(" | ".join(parts))
    else:
        st.caption("Schema Version: 1.0.0 | Rule Version: 1.0.0 | Window: 14d | Category: personal_care | Site: TH")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure the data pipeline has been run and the database exists.")
