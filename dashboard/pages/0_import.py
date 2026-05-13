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
    {"name": "lead_time_days", "label": "Lead Time (days)", "required": False,
     "aliases": ["lead_time", "days_lead_time", "supplier_lead_time"]},
]

# Inventory (stock update for existing products)
INVENTORY_FIELDS = [
    {"name": "product_name",   "label": "Product Name",     "required": True,
     "aliases": ["name", "product", "item", "title", "item_name", "product_title"]},
    {"name": "current_stock",  "label": "Current Stock",    "required": True,
     "aliases": ["stock", "stock_quantity", "qty", "inventory", "stock_level",
                 "units_in_stock", "quantity_on_hand", "on_hand"]},
    {"name": "reorder_point",  "label": "Reorder Point",    "required": False,
     "aliases": ["min_stock", "reorder_level", "minimum_stock", "safety_stock", "min_quantity"]},
    {"name": "cost_per_unit",  "label": "Cost Per Unit",    "required": False,
     "aliases": ["cost", "cogs", "purchase_price", "buy_price", "cost_price", "unit_cost"]},
    {"name": "category",       "label": "Category",         "required": False,
     "aliases": ["product_category", "type", "dept", "department", "subcategory"]},
    {"name": "lead_time_days", "label": "Lead Time (days)", "required": False,
     "aliases": ["lead_time", "days_lead_time", "supplier_lead_time"]},
    {"name": "unit_price",     "label": "Unit Price",       "required": False,
     "aliases": ["price", "sale_price", "selling_price", "retail_price"]},
]

INVENTORY_TEMPLATE = pd.DataFrame([
    {"product_name": "Americano", "current_stock": 150, "reorder_point": 30,
     "cost_per_unit": 0.80, "category": "Coffee", "lead_time_days": 3},
    {"product_name": "Flat White", "current_stock": 120, "reorder_point": 25,
     "cost_per_unit": 1.20, "category": "Coffee", "lead_time_days": 3},
])

# Flat single-file orders
ORDERS_FLAT_FIELDS = [
    {"name": "order_date",     "label": "Order Date",     "required": True,
     "aliases": ["date", "created_at", "invoice_date", "purchase_date", "order_created", "transaction_date"]},
    {"name": "product_name",   "label": "Product Name",   "required": True,
     "aliases": ["name", "product", "item", "description", "item_name", "product_title", "sku", "product_id"]},
    {"name": "quantity",       "label": "Quantity",       "required": True,
     "aliases": ["qty", "units", "amount", "ordered_quantity", "order_qty", "units_ordered"]},
    {"name": "order_id",       "label": "Order ID",       "required": False,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "id", "transaction_id", "reference"]},
    {"name": "customer_email", "label": "Customer Email", "required": False,
     "aliases": ["email", "customer", "buyer_email", "user_email", "customer_email_address"]},
    {"name": "unit_price",     "label": "Unit Price",     "required": False,
     "aliases": ["price", "sale_price", "item_price", "unit_cost", "selling_price", "unit_sale_price"]},
    {"name": "status",         "label": "Status",         "required": False,
     "aliases": ["order_status", "state", "fulfillment_status"]},
]

# Two-file relational: order headers file
ORDERS_HEADER_FIELDS = [
    {"name": "order_id",       "label": "Order ID",       "required": True,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "id", "transaction_id", "reference", "name"]},
    {"name": "order_date",     "label": "Order Date",     "required": True,
     "aliases": ["date", "created_at", "invoice_date", "purchase_date", "order_created", "transaction_date"]},
    {"name": "customer_email", "label": "Customer Email", "required": False,
     "aliases": ["email", "customer", "buyer_email", "user_email"]},
    {"name": "status",         "label": "Status",         "required": False,
     "aliases": ["order_status", "state", "fulfillment_status"]},
]

# Two-file relational: line items file
ORDER_ITEMS_FIELDS = [
    {"name": "order_id",     "label": "Order ID (join key)", "required": True,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "id", "transaction_id", "reference", "name"]},
    {"name": "product_name", "label": "Product Name",        "required": True,
     "aliases": ["name", "product", "item", "description", "item_name", "sku", "product_id", "product_title"]},
    {"name": "quantity",     "label": "Quantity",             "required": True,
     "aliases": ["qty", "units", "amount", "ordered_quantity", "order_qty", "units_ordered", "line_quantity"]},
    {"name": "unit_price",   "label": "Unit Price",           "required": False,
     "aliases": ["price", "sale_price", "item_price", "unit_cost", "selling_price", "line_price"]},
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

ORDERS_FLAT_TEMPLATE = pd.DataFrame([
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com",
     "product_name": "Arabica Coffee Beans 1kg", "quantity": 2, "unit_price": 24.99, "status": "completed"},
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com",
     "product_name": "Green Tea 200g", "quantity": 1, "unit_price": 8.99, "status": "completed"},
    {"order_id": "ORD-002", "order_date": "2025-01-16", "customer_email": "bob@example.com",
     "product_name": "Arabica Coffee Beans 1kg", "quantity": 3, "unit_price": 24.99, "status": "completed"},
])

ORDERS_HEADER_TEMPLATE = pd.DataFrame([
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com", "status": "completed"},
    {"order_id": "ORD-002", "order_date": "2025-01-16", "customer_email": "bob@example.com",   "status": "completed"},
])

ORDER_ITEMS_TEMPLATE = pd.DataFrame([
    {"order_id": "ORD-001", "product_name": "Arabica Coffee Beans 1kg", "quantity": 2, "unit_price": 24.99},
    {"order_id": "ORD-001", "product_name": "Green Tea 200g",           "quantity": 1, "unit_price": 8.99},
    {"order_id": "ORD-002", "product_name": "Arabica Coffee Beans 1kg", "quantity": 3, "unit_price": 24.99},
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _auto_detect(field_name: str, aliases: list[str], csv_cols: list[str]) -> Optional[str]:
    cols_lower = {c.lower().strip(): c for c in csv_cols}
    for candidate in [field_name] + aliases:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def _parse_upload(uploaded_file) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
    except Exception as e:
        st.error(f"Could not read '{uploaded_file.name}': {e}")
        return None


def _render_column_mapper(
    df: pd.DataFrame,
    field_defs: list[dict],
    key_prefix: str,
) -> Optional[pd.DataFrame]:
    """
    Renders column mapping selects. Returns renamed DataFrame or None if
    required fields are still unmapped.
    """
    csv_cols = list(df.columns)
    SKIP = "— skip —"
    UNSET = "— select column —"

    required_fields = [f for f in field_defs if f["required"]]
    optional_fields = [f for f in field_defs if not f["required"]]

    col_req, col_opt = st.columns(2)
    mapping: dict[str, str] = {}
    unmapped_required: list[str] = []

    with col_req:
        st.markdown("**Required**")
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
        st.markdown("**Optional**")
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
        st.warning(f"Map required fields before continuing: **{', '.join(unmapped_required)}**")
        return None

    mapped_df = df[list(mapping.keys())].rename(columns=mapping)
    return mapped_df


def _render_result_badges(result: dict, mode: str) -> None:
    st.success("Import complete!")
    cols = st.columns(3)
    if mode == "products":
        badges = [
            ("created", result.get("created", 0),  "#16A34A"),
            ("updated", result.get("updated", 0),  "#2563EB"),
            ("skipped", result.get("skipped", 0),  "#CA8A04"),
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

# Welcome banner — only shown when the database is empty
inventory = cached_inventory_status()
if not inventory:
    st.info(
        "**Welcome to VendorIO!** No data yet.  \n"
        "Upload a products CSV first, then an orders CSV. "
        "The rest of the dashboard unlocks automatically once products are imported.",
        icon="👋",
    )
else:
    st.caption(
        "Upload any CSV — use the column mapper to match your headers to the required fields."
    )

tab_products, tab_inventory, tab_orders, tab_manage = st.tabs(
    ["📦 Products", "📊 Inventory", "🛒 Orders", "⚙️ Manage Data"]
)

# ── Products ─────────────────────────────────────────────────────────────────
with tab_products:
    col_hd, col_dl = st.columns([3, 1])
    with col_hd:
        st.subheader("Products CSV")
        st.caption("One row per product. Existing products are **updated by name**; new names are created.")
    with col_dl:
        st.download_button(
            "⬇️ Download template", data=_to_csv_bytes(PRODUCTS_TEMPLATE),
            file_name="products_template.csv", mime="text/csv", use_container_width=True,
        )

    st.divider()

    uploaded_products = st.file_uploader("Upload products CSV", type=["csv"], key="products_upload")

    if uploaded_products:
        df = _parse_upload(uploaded_products)
        if df is not None:
            st.markdown(f"**File preview** — {len(df):,} rows · {len(df.columns)} columns")
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
            st.divider()

            mapped_df = _render_column_mapper(df, PRODUCTS_FIELDS, key_prefix="p")

            if mapped_df is not None:
                st.divider()
                st.markdown(f"**Mapped preview** ({len(mapped_df.columns)} fields)")
                st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

                if "import_products_result" in st.session_state:
                    _render_result_badges(st.session_state.pop("import_products_result"), "products")

                if st.button("✅ Import Products", type="primary", use_container_width=True):
                    st.cache_data.clear()
                    with st.spinner("Importing products…"):
                        result = api_client.import_products_csv(
                            _to_csv_bytes(mapped_df), "products_mapped.csv"
                        )
                    if result:
                        st.session_state["import_products_result"] = result
                    st.rerun()

# ── Inventory ────────────────────────────────────────────────────────────────
with tab_inventory:
    col_hd, col_dl = st.columns([3, 1])
    with col_hd:
        st.subheader("Inventory / Stock CSV")
        st.caption(
            "Updates stock levels and cost data for **existing products** matched by name. "
            "Import products first, then use this tab to set their stock levels."
        )
    with col_dl:
        st.download_button(
            "⬇️ Download template", data=_to_csv_bytes(INVENTORY_TEMPLATE),
            file_name="inventory_template.csv", mime="text/csv", use_container_width=True,
        )

    st.info(
        "**Tip — recommended import order:**  \n"
        "1. 📦 **Products** — name, price, category  \n"
        "2. 📊 **Inventory** *(this tab)* — stock levels, reorder points, costs  \n"
        "3. 🛒 **Orders** — transaction history",
        icon="💡",
    )

    st.divider()

    uploaded_inventory = st.file_uploader(
        "Upload inventory CSV", type=["csv"], key="inventory_upload"
    )

    if uploaded_inventory:
        df = _parse_upload(uploaded_inventory)
        if df is not None:
            st.markdown(f"**File preview** — {len(df):,} rows · {len(df.columns)} columns")
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
            st.divider()

            mapped_df = _render_column_mapper(df, INVENTORY_FIELDS, key_prefix="inv")

            if mapped_df is not None:
                st.divider()
                st.markdown(f"**Mapped preview** ({len(mapped_df.columns)} fields)")
                st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

                if "import_inventory_result" in st.session_state:
                    r = st.session_state.pop("import_inventory_result")
                    st.success(f"Import complete — **{r.get('updated', 0)}** products updated.")
                    if r.get("not_found"):
                        with st.expander(f"⚠️ {len(r['not_found'])} products not found in DB"):
                            for n in r["not_found"]:
                                st.caption(n)
                    if r.get("errors"):
                        with st.expander(f"⚠️ {len(r['errors'])} row errors"):
                            for e in r["errors"]:
                                st.caption(e)

                if st.button("✅ Update Inventory", type="primary", use_container_width=True):
                    st.cache_data.clear()
                    with st.spinner("Updating inventory…"):
                        result = api_client.import_inventory_csv(
                            _to_csv_bytes(mapped_df), "inventory_mapped.csv"
                        )
                    if result:
                        st.session_state["import_inventory_result"] = result
                    st.rerun()

# ── Orders ───────────────────────────────────────────────────────────────────
with tab_orders:
    st.subheader("Orders CSV")

    import_mode = st.radio(
        "File format",
        ["Single file (flat)", "Two files — orders + items (relational)"],
        horizontal=True,
        key="orders_mode",
    )

    # ── Single file ──────────────────────────────────────────────────────────
    if import_mode == "Single file (flat)":
        col_hd, col_dl = st.columns([3, 1])
        with col_hd:
            st.caption(
                "Each row is one line item. Rows sharing the same **Order ID** "
                "are grouped into one order."
            )
        with col_dl:
            st.download_button(
                "⬇️ Download template", data=_to_csv_bytes(ORDERS_FLAT_TEMPLATE),
                file_name="orders_flat_template.csv", mime="text/csv", use_container_width=True,
            )

        st.caption(
            "• `order_date` format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`  \n"
            "• Products not in the catalogue are auto-created  \n"
            "• `status` defaults to `completed` if omitted"
        )

        st.divider()

        uploaded_orders = st.file_uploader(
            "Upload orders CSV", type=["csv"], key="orders_flat_upload"
        )

        if uploaded_orders:
            df = _parse_upload(uploaded_orders)
            if df is not None:
                st.markdown(f"**File preview** — {len(df):,} rows · {len(df.columns)} columns")
                st.dataframe(df.head(5), use_container_width=True, hide_index=True)
                st.divider()

                mapped_df = _render_column_mapper(df, ORDERS_FLAT_FIELDS, key_prefix="of")

                if mapped_df is not None:
                    st.divider()
                    st.markdown(f"**Mapped preview** ({len(mapped_df.columns)} fields)")
                    st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

                    if "import_orders_flat_result" in st.session_state:
                        _render_result_badges(st.session_state.pop("import_orders_flat_result"), "orders")

                    if st.button("✅ Import Orders", type="primary", use_container_width=True):
                        st.cache_data.clear()
                        with st.spinner("Importing orders…"):
                            result = api_client.import_orders_csv(
                                _to_csv_bytes(mapped_df), "orders_mapped.csv"
                            )
                        if result:
                            st.session_state["import_orders_flat_result"] = result
                        st.rerun()

    # ── Two files ─────────────────────────────────────────────────────────────
    else:
        st.caption(
            "Upload two separate files: one with order headers and one with line items. "
            "They are joined on the **Order ID** column."
        )

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "⬇️ Orders template", data=_to_csv_bytes(ORDERS_HEADER_TEMPLATE),
                file_name="orders_headers_template.csv", mime="text/csv", use_container_width=True,
            )
        with col_dl2:
            st.download_button(
                "⬇️ Items template", data=_to_csv_bytes(ORDER_ITEMS_TEMPLATE),
                file_name="order_items_template.csv", mime="text/csv", use_container_width=True,
            )

        st.divider()

        col_up1, col_up2 = st.columns(2)
        with col_up1:
            st.markdown("**1 — Orders file** *(one row per order)*")
            uploaded_hdr = st.file_uploader(
                "Orders CSV (headers)", type=["csv"], key="orders_hdr_upload"
            )
        with col_up2:
            st.markdown("**2 — Items file** *(one row per line item)*")
            uploaded_items = st.file_uploader(
                "Items CSV (line items)", type=["csv"], key="orders_items_upload"
            )

        if uploaded_hdr:
            hdr_df = _parse_upload(uploaded_hdr)
            if hdr_df is not None:
                with st.expander(
                    f"Orders file preview — {len(hdr_df):,} rows · {len(hdr_df.columns)} columns"
                ):
                    st.dataframe(hdr_df.head(5), use_container_width=True, hide_index=True)

        if uploaded_items:
            items_df = _parse_upload(uploaded_items)
            if items_df is not None:
                with st.expander(
                    f"Items file preview — {len(items_df):,} rows · {len(items_df.columns)} columns"
                ):
                    st.dataframe(items_df.head(5), use_container_width=True, hide_index=True)

        if uploaded_hdr and uploaded_items:
            hdr_df = _parse_upload(uploaded_hdr)
            items_df = _parse_upload(uploaded_items)

            if hdr_df is not None and items_df is not None:
                st.divider()

                st.markdown("**Map orders file columns**")
                mapped_hdr = _render_column_mapper(hdr_df, ORDERS_HEADER_FIELDS, key_prefix="oh")

                st.divider()

                st.markdown("**Map items file columns**")
                mapped_items = _render_column_mapper(items_df, ORDER_ITEMS_FIELDS, key_prefix="oi")

                if mapped_hdr is not None and mapped_items is not None:
                    # ── Merge ──────────────────────────────────────────────
                    # Left join: items drive the rows, orders supply the metadata.
                    # Use suffixes to handle any unexpected shared columns.
                    merged = mapped_items.merge(
                        mapped_hdr,
                        on="order_id",
                        how="left",
                        suffixes=("", "_hdr"),
                    )
                    # Drop any _hdr duplicate columns that snuck in
                    merged = merged[[c for c in merged.columns if not c.endswith("_hdr")]]

                    # ── Validation warnings ────────────────────────────────
                    orphan_items = merged["order_date"].isna().sum()
                    all_order_ids = set(mapped_hdr["order_id"].dropna().unique())
                    matched_order_ids = set(merged["order_id"].dropna().unique())
                    empty_orders = all_order_ids - matched_order_ids

                    if orphan_items:
                        st.warning(
                            f"⚠️ **{orphan_items} line items** have an Order ID not found in the "
                            f"orders file and will be skipped."
                        )
                    if empty_orders:
                        st.info(
                            f"ℹ️ **{len(empty_orders)} orders** have no matching line items "
                            f"and will not be imported."
                        )

                    # Filter out orphan items
                    valid = merged[merged["order_date"].notna()].copy()

                    if valid.empty:
                        st.error("No valid rows after joining — check that Order IDs match between files.")
                    else:
                        st.divider()
                        st.markdown(
                            f"**Merged preview** — {len(valid):,} valid rows "
                            f"across {len(all_order_ids - empty_orders):,} orders"
                        )
                        st.dataframe(valid.head(8), use_container_width=True, hide_index=True)

                        if "import_orders_rel_result" in st.session_state:
                            _render_result_badges(st.session_state.pop("import_orders_rel_result"), "orders")

                        if st.button(
                            "✅ Import Orders", type="primary", use_container_width=True,
                            key="import_relational",
                        ):
                            st.cache_data.clear()
                            with st.spinner("Importing orders…"):
                                result = api_client.import_orders_csv(
                                    _to_csv_bytes(valid), "orders_relational_merged.csv"
                                )
                            if result:
                                st.session_state["import_orders_rel_result"] = result
                            st.rerun()

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
        confirm_text = st.text_input(
            "Type DELETE to confirm", placeholder="DELETE", key="confirm_clear"
        )
        if "clear_data_result" in st.session_state:
            d = st.session_state.pop("clear_data_result")
            st.success(
                f"Cleared: {d.get('orders', 0)} orders · {d.get('order_items', 0)} items · "
                f"{d.get('products', 0)} products · {d.get('customers', 0)} customers."
            )

        if st.button("🗑️ Clear all data", type="primary", disabled=(confirm_text != "DELETE")):
            st.cache_data.clear()
            with st.spinner("Deleting all data…"):
                result = api_client.clear_all_data()
            if result:
                st.session_state["clear_data_result"] = result.get("deleted", {})
            st.rerun()
