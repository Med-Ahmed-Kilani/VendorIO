"""Page 0: Import Data — upload products and orders via CSV."""
import io
from typing import Optional
import streamlit as st
import pandas as pd
from dashboard.utils import api_client
from dashboard.utils.cache import cached_inventory_status

# ---------------------------------------------------------------------------
# Field definitions with auto-detection aliases
# ---------------------------------------------------------------------------

PRODUCTS_FIELDS = [
    {"name": "name",           "label": "Product Name",    "required": True,
     "aliases": ["product_name", "title", "product", "item_name", "product_title", "item", "description"]},
    {"name": "unit_price",     "label": "Unit Price",      "required": True,
     "aliases": ["price", "sale_price", "selling_price", "retail_price", "list_price"]},
    {"name": "category",       "label": "Category",        "required": False,
     "aliases": ["product_category", "type", "dept", "department", "subcategory"]},
    {"name": "cost_per_unit",  "label": "Cost Per Unit",   "required": False,
     "aliases": ["cost", "cogs", "purchase_price", "buy_price", "cost_price"]},
    {"name": "current_stock",  "label": "Current Stock",   "required": False,
     "aliases": ["stock", "stock_quantity", "qty", "inventory", "stock_level", "units_in_stock", "quantity"]},
    {"name": "reorder_point",  "label": "Reorder Point",   "required": False,
     "aliases": ["min_stock", "reorder_level", "min_quantity", "safety_stock"]},
    {"name": "lead_time_days", "label": "Lead Time (days)","required": False,
     "aliases": ["lead_time", "days_lead_time", "supplier_lead_time"]},
]

ORDERS_FIELDS = [
    {"name": "order_date",      "label": "Order Date",      "required": True,
     "aliases": ["date", "created_at", "invoice_date", "purchase_date", "order_created", "transaction_date"]},
    {"name": "product_name",    "label": "Product Name",    "required": True,
     "aliases": ["name", "product", "item", "description", "item_name", "product_title", "sku", "product_id"]},
    {"name": "quantity",        "label": "Quantity",        "required": True,
     "aliases": ["qty", "units", "amount", "ordered_quantity", "order_qty", "units_ordered"]},
    {"name": "order_id",        "label": "Order ID",        "required": False,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "id", "transaction_id", "reference"]},
    {"name": "customer_email",  "label": "Customer Email",  "required": False,
     "aliases": ["email", "customer", "buyer_email", "user_email", "customer_email_address"]},
    {"name": "unit_price",      "label": "Unit Price",      "required": False,
     "aliases": ["price", "sale_price", "item_price", "unit_cost", "selling_price", "unit_sale_price"]},
    {"name": "status",          "label": "Status",          "required": False,
     "aliases": ["order_status", "state", "fulfillment_status"]},
]

# ---------------------------------------------------------------------------
# CSV templates
# ---------------------------------------------------------------------------

PRODUCTS_TEMPLATE = pd.DataFrame([
    {"name": "Arabica Coffee Beans 1kg", "category": "Coffee", "unit_price": 24.99,
     "cost_per_unit": 9.50, "current_stock": 80, "reorder_point": 20, "lead_time_days": 7},
    {"name": "Green Tea 200g", "category": "Tea", "unit_price": 8.99,
     "cost_per_unit": 2.50, "current_stock": 5, "reorder_point": 15, "lead_time_days": 5},
])

ORDERS_TEMPLATE = pd.DataFrame([
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com",
     "product_name": "Arabica Coffee Beans 1kg", "quantity": 2, "unit_price": 24.99, "status": "completed"},
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com",
     "product_name": "Green Tea 200g", "quantity": 1, "unit_price": 8.99, "status": "completed"},
    {"order_id": "ORD-002", "order_date": "2025-01-16", "customer_email": "bob@example.com",
     "product_name": "Arabica Coffee Beans 1kg", "quantity": 3, "unit_price": 24.99, "status": "completed"},
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _auto_detect(field_name: str, aliases: list[str], csv_cols: list[str]) -> Optional[str]:
    """Return the first CSV column that matches the field name or any alias (case-insensitive)."""
    cols_lower = {c.lower().strip(): c for c in csv_cols}
    for candidate in [field_name] + aliases:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def _render_column_mapper(
    df: pd.DataFrame,
    field_defs: list[dict],
    key_prefix: str,
) -> Optional[pd.DataFrame]:
    """
    Renders a column mapping UI. Returns a renamed DataFrame ready to send,
    or None if required fields are still unmapped.
    """
    csv_cols = list(df.columns)
    SKIP = "— skip —"
    UNSET = "— select column —"

    st.markdown("**Map your CSV columns to the required fields:**")

    required_fields = [f for f in field_defs if f["required"]]
    optional_fields = [f for f in field_defs if not f["required"]]

    col_req, col_opt = st.columns(2)
    mapping: dict[str, str] = {}   # csv_col → standard_name
    unmapped_required: list[str] = []

    with col_req:
        st.markdown("**Required fields**")
        for field in required_fields:
            auto = _auto_detect(field["name"], field["aliases"], csv_cols)
            options = [UNSET] + csv_cols
            default = options.index(auto) if auto in options else 0
            selected = st.selectbox(
                f"⬡ {field['label']}",
                options=options,
                index=default,
                key=f"{key_prefix}_{field['name']}",
            )
            if selected != UNSET:
                mapping[selected] = field["name"]
            else:
                unmapped_required.append(field["label"])

    with col_opt:
        st.markdown("**Optional fields**")
        for field in optional_fields:
            auto = _auto_detect(field["name"], field["aliases"], csv_cols)
            options = [SKIP] + csv_cols
            default = options.index(auto) if auto in options else 0
            selected = st.selectbox(
                field["label"],
                options=options,
                index=default,
                key=f"{key_prefix}_{field['name']}",
            )
            if selected != SKIP:
                mapping[selected] = field["name"]

    if unmapped_required:
        st.warning(f"Map required fields before importing: **{', '.join(unmapped_required)}**")
        return None

    # Warn if the same CSV column is mapped to two different fields
    if len(set(mapping.keys())) < len(mapping):
        st.error("The same CSV column is mapped to multiple fields. Please fix the mapping.")
        return None

    mapped_df = df[list(mapping.keys())].rename(columns=mapping)
    return mapped_df


def _render_result_badges(result: dict, mode: str) -> None:
    st.success("Import complete!")
    cols = st.columns(3)
    if mode == "products":
        badges = [
            ("created",  result.get("created", 0),  "#16A34A"),
            ("updated",  result.get("updated", 0),  "#2563EB"),
            ("skipped",  result.get("skipped", 0),  "#CA8A04"),
        ]
    else:
        badges = [
            ("orders created", result.get("orders_created", 0), "#16A34A"),
            ("line items",     result.get("items_created", 0),  "#2563EB"),
            ("skipped",        result.get("skipped", 0),        "#CA8A04"),
        ]
    for col, (label, value, color) in zip(cols, badges):
        with col:
            st.markdown(
                f"<div style='background:{color}22;border:1px solid {color}55;"
                f"border-radius:6px;padding:8px 14px;text-align:center'>"
                f"<div style='font-size:1.6rem;font-weight:700;color:{color}'>{value}</div>"
                f"<div style='font-size:.85rem'>{label}</div></div>",
                unsafe_allow_html=True,
            )
    if result.get("errors"):
        with st.expander(f"⚠️ {len(result['errors'])} row errors"):
            for e in result["errors"]:
                st.caption(e)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("📥 Import Data")
st.caption(
    "Upload any CSV file — use the column mapper to match your headers to the "
    "required fields. Import products first, then orders."
)

tab_products, tab_orders, tab_manage = st.tabs(["📦 Products", "🛒 Orders", "⚙️ Manage Data"])

# ── Products ─────────────────────────────────────────────────────────────────
with tab_products:
    col_hd, col_dl = st.columns([3, 1])
    with col_hd:
        st.subheader("Products CSV")
        st.caption("One row per product. Existing products are **updated by name**; new names are created.")
    with col_dl:
        st.download_button(
            "⬇️ Download template",
            data=_to_csv_bytes(PRODUCTS_TEMPLATE),
            file_name="products_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Show expected columns"):
        st.dataframe(PRODUCTS_TEMPLATE, use_container_width=True, hide_index=True)

    st.divider()

    uploaded_products = st.file_uploader("Upload products CSV", type=["csv"], key="products_upload")

    if uploaded_products:
        raw = uploaded_products.getvalue()
        try:
            df = pd.read_csv(io.BytesIO(raw))
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.markdown(f"**File preview** — {len(df):,} rows · {len(df.columns)} columns")
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

        st.divider()

        mapped_df = _render_column_mapper(df, PRODUCTS_FIELDS, key_prefix="p")

        if mapped_df is not None:
            st.divider()
            st.markdown(f"**Mapped preview** — {len(mapped_df.columns)} fields selected")
            st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

            if st.button("✅ Import Products", type="primary", use_container_width=True):
                mapped_bytes = _to_csv_bytes(mapped_df)
                with st.spinner("Importing products…"):
                    result = api_client.import_products_csv(mapped_bytes, "products_mapped.csv")
                if result:
                    _render_result_badges(result, "products")
                    st.cache_data.clear()

# ── Orders ───────────────────────────────────────────────────────────────────
with tab_orders:
    col_hd, col_dl = st.columns([3, 1])
    with col_hd:
        st.subheader("Orders CSV")
        st.caption(
            "Each row is one order line item. Rows sharing the same **Order ID** "
            "are grouped into one order."
        )
    with col_dl:
        st.download_button(
            "⬇️ Download template",
            data=_to_csv_bytes(ORDERS_TEMPLATE),
            file_name="orders_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Show expected columns"):
        st.dataframe(ORDERS_TEMPLATE, use_container_width=True, hide_index=True)
        st.caption(
            "• `order_date` format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`  \n"
            "• Products not found in your catalogue are auto-created  \n"
            "• `status` defaults to `completed` if omitted"
        )

    st.divider()

    uploaded_orders = st.file_uploader("Upload orders CSV", type=["csv"], key="orders_upload")

    if uploaded_orders:
        raw = uploaded_orders.getvalue()
        try:
            df = pd.read_csv(io.BytesIO(raw))
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.markdown(f"**File preview** — {len(df):,} rows · {len(df.columns)} columns")
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

        st.divider()

        mapped_df = _render_column_mapper(df, ORDERS_FIELDS, key_prefix="o")

        if mapped_df is not None:
            st.divider()
            st.markdown(f"**Mapped preview** — {len(mapped_df.columns)} fields selected")
            st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

            if st.button("✅ Import Orders", type="primary", use_container_width=True):
                mapped_bytes = _to_csv_bytes(mapped_df)
                with st.spinner("Importing orders… (large files may take a moment)"):
                    result = api_client.import_orders_csv(mapped_bytes, "orders_mapped.csv")
                if result:
                    _render_result_badges(result, "orders")
                    st.cache_data.clear()

# ── Manage ────────────────────────────────────────────────────────────────────
with tab_manage:
    st.subheader("⚙️ Data Management")

    inventory = cached_inventory_status()
    if inventory:
        st.info(f"Database contains **{len(inventory)} products** in inventory.")
    else:
        st.info("No products in database yet.")

    st.divider()

    with st.expander("🗑️ Clear all data (danger zone)", expanded=False):
        st.warning(
            "Permanently deletes **all** products, orders, order items, and customers. "
            "Re-import or re-run `scripts/load_sample_data.py` to restore."
        )
        confirm_text = st.text_input("Type DELETE to confirm", placeholder="DELETE", key="confirm_clear")
        if st.button("🗑️ Clear all data", type="primary", disabled=(confirm_text != "DELETE")):
            with st.spinner("Deleting all data…"):
                result = api_client.clear_all_data()
            if result:
                deleted = result.get("deleted", {})
                st.success(
                    f"Cleared: {deleted.get('orders', 0)} orders · "
                    f"{deleted.get('order_items', 0)} items · "
                    f"{deleted.get('products', 0)} products · "
                    f"{deleted.get('customers', 0)} customers."
                )
                st.cache_data.clear()
