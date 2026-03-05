"""Alerts & Opportunities Page."""

import streamlit as st

st.set_page_config(page_title="Alerts & Opportunities", page_icon="\U0001f514", layout="wide")
st.title("Alerts & Opportunities")

try:
    import pandas as pd

    from data.loader import load_alerts as _load_alerts

    @st.cache_data(ttl=60)
    def load_alerts():
        return _load_alerts()

    alerts = load_alerts()

    if alerts.empty:
        st.info("No alerts generated yet. Run the pipeline to generate alerts based on ranking changes and price anomalies.")

        # Show example alerts
        st.subheader("Example Alert Types")
        st.markdown("""
        - **Rank Jump**: Item jumped 50+ positions in rankings
        - **Proxy Spike**: Review count or sales proxy increased significantly
        - **Platform Gap**: Item is top-selling on one platform but absent/low on another
        - **Price Anomaly**: Price deviates significantly from category median
        """)
        st.stop()

    # Filters
    col1, col2, col3 = st.columns(3)
    alert_types = ["All"] + sorted(alerts["alert_type"].unique().tolist())
    selected_type = col1.selectbox("Alert Type", alert_types)

    severities = ["All"] + ["critical", "high", "medium", "low"]
    selected_severity = col2.selectbox("Severity", severities)

    statuses = ["All"] + sorted(alerts["status"].unique().tolist())
    selected_status = col3.selectbox("Status", statuses)

    # Apply filters
    filtered = alerts.copy()
    if selected_type != "All":
        filtered = filtered[filtered["alert_type"] == selected_type]
    if selected_severity != "All":
        filtered = filtered[filtered["severity"] == selected_severity]
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    # Summary
    st.markdown(f"**{len(filtered)} alerts**")

    severity_colors = {
        "critical": "\U0001f534",
        "high": "\U0001f7e0",
        "medium": "\U0001f7e1",
        "low": "\U0001f535",
    }

    # Display alerts
    for _, alert in filtered.iterrows():
        severity_icon = severity_colors.get(alert.get("severity", ""), "\u26aa")
        with st.expander(
            f"{severity_icon} [{alert.get('alert_type', 'unknown')}] {alert.get('title', 'Alert')} - {alert.get('severity', 'unknown')}"
        ):
            st.markdown(f"**Description:** {alert.get('description', 'N/A')}")
            st.markdown(f"**Severity:** {alert.get('severity', 'N/A')}")
            st.markdown(f"**Status:** {alert.get('status', 'N/A')}")
            st.markdown(f"**Date:** {alert.get('event_date', 'N/A')}")
            if alert.get("suggested_action"):
                st.success(f"**Suggested Action:** {alert['suggested_action']}")
            if alert.get("item_ids"):
                st.markdown(f"**Affected Items:** {alert['item_ids']}")

except Exception as e:
    st.error(f"Error loading alerts: {e}")
