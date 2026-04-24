"""Page 5: Smart Alerts & Recommendations."""
import streamlit as st
from pathlib import Path
from dashboard.config import PAGE_TITLE, PAGE_ICON, URGENCY_EMOJI
from dashboard.components.tables import recommendations_table
from dashboard.components.sidebar import render_sidebar_info
from dashboard.utils.cache import cached_recommendations
from dashboard.utils.formatters import fmt_currency

st.set_page_config(page_title=f"Alerts — {PAGE_TITLE}", page_icon=PAGE_ICON, layout="wide")

css_path = Path(__file__).parent.parent / "styles" / "theme.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.sidebar.title(f"{PAGE_ICON} {PAGE_TITLE}")
limit = st.sidebar.slider("Max recommendations", 5, 50, 20)
render_sidebar_info()

st.title("🔔 Smart Alerts & Recommendations")

data = cached_recommendations()

if not data:
    st.warning("Could not load recommendations. Is the backend running?")
    st.stop()

recs = data.get("recommendations", [])
total_savings = data.get("total_potential_savings", 0)

# Summary metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Recommendations", len(recs))
critical = len([r for r in recs if r.get("urgency") == "critical"])
high = len([r for r in recs if r.get("urgency") == "high"])
c2.metric("🔴 Critical", critical)
c3.metric("🟠 High Priority", high)
c4.metric("💡 Potential Savings", fmt_currency(total_savings))

if critical > 0:
    st.error(f"⚠️ {critical} critical issue(s) require immediate attention!")
elif high > 0:
    st.warning(f"{high} high-priority recommendation(s) need your attention.")
else:
    st.success("✅ No critical issues. Review low-priority optimizations below.")

st.divider()

# Urgency filter
urgency_filter = st.multiselect(
    "Filter by urgency",
    ["critical", "high", "medium", "low"],
    default=["critical", "high", "medium", "low"],
)
type_filter = st.multiselect(
    "Filter by type",
    ["stockout_risk", "slow_mover", "overstock", "bulk_order"],
    default=["stockout_risk", "slow_mover", "overstock", "bulk_order"],
)

filtered_recs = [
    r for r in recs
    if r.get("urgency") in urgency_filter and r.get("type") in type_filter
]

st.subheader(f"📋 Recommendations ({len(filtered_recs)} shown)")
recommendations_table(filtered_recs)

st.divider()

# Action tracker (MVP: simple in-session state)
st.subheader("✅ Action Tracker")
st.caption("Track which recommendations you've acted on in this session")

if "applied" not in st.session_state:
    st.session_state.applied = set()

for r in filtered_recs:
    key = f"{r.get('type')}_{r.get('product_id')}"
    col1, col2 = st.columns([4, 1])
    status = "✅ Applied" if key in st.session_state.applied else "⬜ Pending"
    col1.write(f"{URGENCY_EMOJI.get(r.get('urgency', 'low'), '')} **{r.get('product_name')}** — {r.get('action', '')}")
    if col2.button("Mark Done", key=f"btn_{key}"):
        st.session_state.applied.add(key)
        st.rerun()
    if key in st.session_state.applied:
        col1.caption("✅ Applied")

if st.session_state.applied:
    st.success(f"You've addressed {len(st.session_state.applied)} recommendation(s) this session.")
