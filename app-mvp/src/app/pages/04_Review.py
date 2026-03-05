"""Review Queue Page."""

import json
import uuid

import requests
import streamlit as st

st.set_page_config(page_title="Review Queue", page_icon="\u2705", layout="wide")
st.title("Review Queue")

API_BASE = "http://localhost:8080/api/v1"

try:
    import pandas as pd

    from data.loader import load_review_queue as _load_review_queue

    @st.cache_data(ttl=30)
    def load_review_queue():
        return _load_review_queue()

    queue = load_review_queue()

    if queue.empty:
        st.success("No items pending review! All matches have been processed.")
        st.stop()

    st.markdown(f"**{len(queue)} pairs awaiting review**")
    st.markdown("---")

    # Review each pair
    for idx, pair in queue.iterrows():
        with st.container():
            st.subheader(f"Pair #{idx + 1} - Confidence: {pair['confidence']:.3f}")

            col_tt, col_mid, col_sh = st.columns([4, 2, 4])

            with col_tt:
                st.markdown("**TikTok Item**")
                st.markdown(f"**ID:** `{pair['tiktok_item_id']}`")
                st.markdown(f"**Title:** {pair.get('tiktok_title', 'N/A')}")
                st.markdown(f"**Brand:** {pair.get('tiktok_brand', 'N/A')}")
                size = pair.get("tiktok_size", "")
                unit = pair.get("tiktok_unit", "")
                st.markdown(f"**Spec:** {size} {unit}" if size else "**Spec:** N/A")

            with col_mid:
                st.markdown("**Match Info**")
                confidence = pair["confidence"]
                st.progress(confidence)
                st.markdown(f"**Type:** `{pair['match_type']}`")
                st.markdown(f"**Score:** {confidence:.3f}")

                # Parse and display reasons
                try:
                    reasons = json.loads(pair.get("reasons", "{}"))
                    if reasons.get("strong_evidence"):
                        for ev in reasons["strong_evidence"]:
                            st.markdown(f"\u2705 {ev}")
                    if reasons.get("weak_evidence"):
                        for ev in reasons["weak_evidence"]:
                            st.markdown(f"\U0001f7e1 {ev}")
                except (json.JSONDecodeError, TypeError):
                    pass

            with col_sh:
                st.markdown("**Shopee Item**")
                st.markdown(f"**ID:** `{pair['shopee_item_id']}`")
                st.markdown(f"**Title:** {pair.get('shopee_title', 'N/A')}")
                st.markdown(f"**Brand:** {pair.get('shopee_brand', 'N/A')}")
                size = pair.get("shopee_size", "")
                unit = pair.get("shopee_unit", "")
                st.markdown(f"**Spec:** {size} {unit}" if size else "**Spec:** N/A")

            # Decision form
            col_d1, col_d2, col_d3 = st.columns([2, 2, 6])
            decision = col_d1.selectbox(
                "Decision",
                ["accept", "reject", "change_type"],
                key=f"decision_{idx}",
            )
            new_type = None
            if decision == "change_type":
                new_type = col_d2.selectbox(
                    "New Type",
                    ["exact_same", "variant_family", "similar", "no_match"],
                    key=f"new_type_{idx}",
                )
            comment = col_d3.text_input("Comment", key=f"comment_{idx}")

            if st.button("Submit Decision", key=f"submit_{idx}"):
                tiktok_id = pair["tiktok_item_id"]
                shopee_id = pair["shopee_item_id"]
                url = f"{API_BASE}/review/{tiktok_id}/{shopee_id}/decision"
                payload = {"decision": decision, "comment": comment or ""}
                if new_type:
                    payload["new_match_type"] = new_type

                try:
                    resp = requests.post(
                        url,
                        json=payload,
                        headers={"Idempotency-Key": str(uuid.uuid4())},
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        st.success(
                            f"Decision submitted: {decision}"
                            + (f" -> {new_type}" if new_type else "")
                            + (f" ({comment})" if comment else "")
                        )
                    else:
                        st.error(f"API returned {resp.status_code}: {resp.text}")
                except requests.ConnectionError:
                    st.warning(
                        "Could not reach API backend at localhost:8080. "
                        "Decision saved locally only."
                    )
                except Exception as e:
                    st.error(f"Error submitting decision: {e}")

            st.markdown("---")

except Exception as e:
    st.error(f"Error loading review queue: {e}")
