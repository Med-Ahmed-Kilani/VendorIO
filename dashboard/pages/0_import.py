"""Page 0: Import Data — upload CSVs for all 8 schema tables."""
import io
from typing import Optional
import streamlit as st
import pandas as pd
from dashboard.utils import api_client
from dashboard.utils.cache import cached_inventory_status

# ---------------------------------------------------------------------------
# Field definitions
# ---------------------------------------------------------------------------

RAW_MATERIALS_FIELDS = [
    {"name": "name",           "label": "Material Name",    "required": True,
     "aliases": ["material_name", "ingredient", "item", "material"]},
    {"name": "category",       "label": "Category",         "required": False,
     "aliases": ["type", "dept", "group"]},
    {"name": "unit",           "label": "Unit",             "required": False,
     "aliases": ["unit_of_measure", "uom", "measurement_unit"]},
    {"name": "cost_per_unit",  "label": "Cost per Unit",    "required": False,
     "aliases": ["cost", "unit_cost", "purchase_price", "buy_price"]},
    {"name": "current_stock",  "label": "Current Stock",    "required": False,
     "aliases": ["stock", "qty", "quantity", "inventory", "stock_level"]},
    {"name": "reorder_point",  "label": "Reorder Point",    "required": False,
     "aliases": ["min_stock", "reorder_level", "safety_stock"]},
    {"name": "lead_time_days", "label": "Lead Time (days)", "required": False,
     "aliases": ["lead_time", "days_lead_time", "supplier_lead_time"]},
]

PRODUCTS_FIELDS = [
    {"name": "name",       "label": "Product Name", "required": True,
     "aliases": ["product_name", "title", "item_name", "product_title"]},
    {"name": "unit_price", "label": "Unit Price",   "required": True,
     "aliases": ["price", "sale_price", "selling_price", "retail_price"]},
    {"name": "category",   "label": "Category",     "required": False,
     "aliases": ["product_category", "type", "dept"]},
]

RECIPES_FIELDS = [
    {"name": "product_id", "label": "Product ID",   "required": True,
     "aliases": ["product", "final_product_id"]},
    {"name": "unit_cost",  "label": "Recipe Cost",  "required": True,
     "aliases": ["cost", "cost_per_unit", "recipe_cost", "total_cost"]},
    {"name": "size",       "label": "Size (S/M/L)", "required": False,
     "aliases": ["variant", "portion_size", "drink_size"]},
]

RECIPE_ITEMS_FIELDS = [
    {"name": "recipe_id",        "label": "Recipe ID",          "required": True,
     "aliases": ["recipe"]},
    {"name": "material_id",      "label": "Material ID",        "required": True,
     "aliases": ["ingredient_id", "raw_material_id", "material"]},
    {"name": "quantity_needed",  "label": "Quantity Needed",    "required": True,
     "aliases": ["qty", "quantity", "amount", "quantity_per_unit"]},
    {"name": "unit",             "label": "Unit",               "required": False,
     "aliases": ["unit_of_measure", "uom"]},
    {"name": "notes",            "label": "Notes",              "required": False,
     "aliases": ["note", "comment", "description"]},
]

ORDERS_FIELDS = [
    {"name": "order_date",     "label": "Order Date",     "required": True,
     "aliases": ["date", "created_at", "invoice_date", "transaction_date"]},
    {"name": "product_id",    "label": "Product ID",     "required": True,
     "aliases": ["product", "final_product_id", "item_id"]},
    {"name": "quantity",      "label": "Quantity",       "required": True,
     "aliases": ["qty", "units", "ordered_quantity"]},
    {"name": "order_id",      "label": "Order ID",       "required": False,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "transaction_id"]},
    {"name": "size",          "label": "Size (S/M/L)",   "required": False,
     "aliases": ["variant", "drink_size", "portion_size"]},
    {"name": "customer_email","label": "Customer Email", "required": False,
     "aliases": ["email", "buyer_email", "user_email"]},
    {"name": "unit_price",    "label": "Unit Price",     "required": False,
     "aliases": ["price", "sale_price", "selling_price"]},
    {"name": "status",        "label": "Status",         "required": False,
     "aliases": ["order_status", "state", "fulfillment_status"]},
]

TRANSACTIONS_FIELDS = [
    {"name": "order_id",       "label": "Order ID",        "required": True,
     "aliases": ["order", "invoice_id", "order_no"]},
    {"name": "amount_paid",    "label": "Amount Paid",     "required": True,
     "aliases": ["amount", "payment_amount", "total_paid", "paid"]},
    {"name": "payment_method", "label": "Payment Method",  "required": False,
     "aliases": ["method", "payment_type", "payment_mode"]},
]

RAW_MATERIAL_INVENTORY_FIELDS = [
    {"name": "material_id",   "label": "Material ID",    "required": False,
     "aliases": ["id", "ingredient_id", "mat_id"]},
    {"name": "material_name", "label": "Material Name",  "required": False,
     "aliases": ["name", "ingredient", "item", "material"]},
    {"name": "current_stock", "label": "Current Stock",  "required": True,
     "aliases": ["stock", "qty", "quantity", "inventory", "stock_level", "on_hand"]},
]

ORDER_ITEMS_FIELDS = [
    {"name": "order_id",    "label": "Order ID",      "required": True,
     "aliases": ["invoice_no", "invoice_id", "order_no", "order_number", "transaction_id"]},
    {"name": "product_id",  "label": "Product ID",    "required": True,
     "aliases": ["product", "final_product_id", "item_id"]},
    {"name": "quantity",    "label": "Quantity",      "required": True,
     "aliases": ["qty", "units", "ordered_quantity"]},
    {"name": "size",        "label": "Size (S/M/L)",  "required": False,
     "aliases": ["variant", "drink_size", "portion_size"]},
    {"name": "unit_price",  "label": "Unit Price",    "required": False,
     "aliases": ["price", "sale_price", "selling_price", "item_price"]},
]

# ---------------------------------------------------------------------------
# CSV templates
# ---------------------------------------------------------------------------

RAW_MATERIALS_TEMPLATE = pd.DataFrame([
    {"name": "Arabica Beans",    "category": "Coffee", "unit": "grams", "cost_per_unit": 0.0095, "current_stock": 20000, "reorder_point": 5000, "lead_time_days": 7},
    {"name": "Whole Milk",       "category": "Dairy",  "unit": "ml",    "cost_per_unit": 0.0012, "current_stock": 20000, "reorder_point": 5000, "lead_time_days": 2},
    {"name": "Matcha Powder",    "category": "Tea",    "unit": "grams", "cost_per_unit": 0.0500, "current_stock": 3000,  "reorder_point": 1000, "lead_time_days": 7},
])

PRODUCTS_TEMPLATE = pd.DataFrame([
    {"name": "Espresso",     "category": "Coffee", "unit_price": 3.50},
    {"name": "Flat White",   "category": "Coffee", "unit_price": 4.20},
    {"name": "Matcha Latte", "category": "Tea",    "unit_price": 4.50},
])

RECIPES_TEMPLATE = pd.DataFrame([
    {"product_id": 1, "unit_cost": 0.60, "size": ""},
    {"product_id": 2, "unit_cost": 0.90, "size": ""},
    {"product_id": 2, "unit_cost": 0.80, "size": "S"},
    {"product_id": 2, "unit_cost": 1.05, "size": "L"},
])

RECIPE_ITEMS_TEMPLATE = pd.DataFrame([
    {"recipe_id": 1, "material_id": 1, "quantity_needed": 18,  "unit": "grams", "notes": ""},
    {"recipe_id": 2, "material_id": 1, "quantity_needed": 18,  "unit": "grams", "notes": ""},
    {"recipe_id": 2, "material_id": 2, "quantity_needed": 150, "unit": "ml",    "notes": "steamed"},
])

ORDERS_TEMPLATE = pd.DataFrame([
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com", "product_id": 1, "quantity": 2, "unit_price": 3.50, "status": "completed"},
    {"order_id": "ORD-001", "order_date": "2025-01-15", "customer_email": "alice@example.com", "product_id": 2, "quantity": 1, "unit_price": 4.20, "status": "completed"},
    {"order_id": "ORD-002", "order_date": "2025-01-16", "customer_email": "bob@example.com",   "product_id": 3, "size": "L",  "quantity": 1, "unit_price": 4.80, "status": "completed"},
])

TRANSACTIONS_TEMPLATE = pd.DataFrame([
    {"order_id": 1, "amount_paid": 11.90, "payment_method": "card"},
    {"order_id": 2, "amount_paid":  4.80, "payment_method": "cash"},
])

RAW_MATERIAL_INVENTORY_TEMPLATE = pd.DataFrame([
    {"material_id": 1, "material_name": "Arabica Beans", "current_stock": 20000},
    {"material_id": 2, "material_name": "Whole Milk",    "current_stock": 15000},
    {"material_id": 3, "material_name": "Matcha Powder", "current_stock": 2500},
])

ORDER_ITEMS_TEMPLATE = pd.DataFrame([
    {"order_id": 1, "product_id": 1, "quantity": 2, "unit_price": 3.50, "size": ""},
    {"order_id": 1, "product_id": 2, "quantity": 1, "unit_price": 4.20, "size": ""},
    {"order_id": 2, "product_id": 3, "quantity": 1, "unit_price": 4.80, "size": "L"},
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

    return df[list(mapping.keys())].rename(columns=mapping)


def _render_upsert_badges(result: dict) -> None:
    st.success("Import complete!")
    cols = st.columns(3)
    badges = [
        ("created", result.get("created", 0), "#16A34A"),
        ("updated", result.get("updated", 0), "#2563EB"),
        ("skipped", result.get("skipped", 0), "#CA8A04"),
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


def _render_orders_badges(result: dict) -> None:
    st.success("Import complete!")
    cols = st.columns(3)
    badges = [
        ("orders created", result.get("orders_created", 0), "#16A34A"),
        ("line items",     result.get("items_created", 0),  "#2563EB"),
        ("skipped groups", result.get("skipped", 0),        "#CA8A04"),
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
        with st.expander(f"⚠️ {len(result['errors'])} row errors (recipe missing? import recipes first)"):
            for e in result["errors"]:
                st.caption(e)


def _upload_section(
    tab_key: str,
    field_defs: list[dict],
    template_df: pd.DataFrame,
    template_filename: str,
    description: str,
    import_fn,
    import_result_key: str,
    button_label: str = "✅ Import",
    badge_fn=_render_upsert_badges,
) -> None:
    """Reusable upload + map + import widget."""
    col_hd, col_dl = st.columns([3, 1])
    with col_hd:
        st.caption(description)
    with col_dl:
        st.download_button(
            "⬇️ Download template",
            data=_to_csv_bytes(template_df),
            file_name=template_filename,
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    uploaded = st.file_uploader("Upload CSV", type=["csv"], key=f"{tab_key}_upload")

    if uploaded:
        df = _parse_upload(uploaded)
        if df is not None:
            st.markdown(f"**Preview** — {len(df):,} rows · {len(df.columns)} columns")
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
            st.divider()

            mapped_df = _render_column_mapper(df, field_defs, key_prefix=tab_key)

            if mapped_df is not None:
                st.divider()
                st.markdown(f"**Mapped preview** ({len(mapped_df.columns)} fields)")
                st.dataframe(mapped_df.head(5), use_container_width=True, hide_index=True)

                if import_result_key in st.session_state:
                    badge_fn(st.session_state.pop(import_result_key))

                if st.button(button_label, type="primary", use_container_width=True, key=f"{tab_key}_btn"):
                    st.cache_data.clear()
                    with st.spinner("Importing…"):
                        result = import_fn(_to_csv_bytes(mapped_df), f"{tab_key}_mapped.csv")
                    if result:
                        st.session_state[import_result_key] = result
                    st.rerun()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("📥 Import Data")

inventory = cached_inventory_status()
if not inventory:
    st.info(
        "**Welcome to VendorIO!** No data yet.  \n"
        "Follow the recommended import order below to get started.",
        icon="👋",
    )

(
    tab_bulk,
    tab_materials, tab_inventory,
    tab_products,
    tab_recipes, tab_recipe_items,
    tab_orders, tab_order_items,
    tab_transactions, tab_manage,
) = st.tabs([
    "⚡ Bulk Upload",
    "🧪 Raw Materials",
    "📦 Inventory",
    "🏷️ Products",
    "📋 Recipes",
    "🔗 Recipe Items",
    "🛒 Orders",
    "🗂️ Order Items",
    "💳 Transactions",
    "⚙️ Manage",
])

# ---------------------------------------------------------------------------
# File-name → (import_fn, friendly_label) registry
# Processed in this exact dependency order.
# ---------------------------------------------------------------------------

_BULK_REGISTRY = [
    ("raw_materials",           api_client.import_raw_materials_csv,          "Raw Materials"),
    ("raw_material_inventory",  api_client.import_raw_material_inventory_csv, "Inventory Levels"),
    ("products",                api_client.import_products_csv,               "Products"),
    ("final_products",          api_client.import_products_csv,               "Products"),
    ("recipes",                 api_client.import_recipes_csv,                "Recipes"),
    ("recipe_items",            api_client.import_recipe_items_csv,           "Recipe Items"),
    ("orders",                  api_client.import_orders_csv,                 "Orders"),
    ("order_items",             api_client.import_order_items_csv,            "Order Items"),
    ("transactions",            api_client.import_transactions_csv,           "Transactions"),
]

# Ordered keys for processing (dependency-safe)
_BULK_ORDER = [
    "raw_materials", "raw_material_inventory",
    "products", "final_products",
    "recipes", "recipe_items",
    "orders", "order_items",
    "transactions",
]


def _match_file(filename: str):
    """Return (key, import_fn, label) for a given filename, or None if unrecognised."""
    stem = filename.lower().rsplit(".", 1)[0]          # drop extension
    stem = stem.replace("-", "_").replace(" ", "_")    # normalise separators
    # strip common suffixes like _template, _data, _export, _2024 etc.
    for suffix in ("_template", "_data", "_export", "_import", "_sample"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    for key, fn, label in _BULK_REGISTRY:
        if stem == key or stem.startswith(key + "_") or stem.endswith("_" + key):
            return key, fn, label
    return None


# ── Bulk Upload ───────────────────────────────────────────────────────────────
with tab_bulk:
    st.subheader("⚡ Bulk Upload")
    st.caption(
        "Drop all your CSV files at once. Files are matched by name and imported "
        "in the correct dependency order automatically."
    )

    st.info(
        "**Expected filenames** (any prefix/suffix is stripped):  \n"
        "`raw_materials.csv` · `raw_material_inventory.csv` · `products.csv` · "
        "`recipes.csv` · `recipe_items.csv` · `orders.csv` · `order_items.csv` · "
        "`transactions.csv`",
        icon="📋",
    )

    uploaded_bulk = st.file_uploader(
        "Upload all CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="bulk_upload",
    )

    if uploaded_bulk:
        # Match & classify each uploaded file
        matched: dict[str, object] = {}   # key → file object
        unrecognised: list[str] = []

        for f in uploaded_bulk:
            result = _match_file(f.name)
            if result:
                key, _, _ = result
                if key not in matched:
                    matched[key] = f
                else:
                    st.warning(f"Duplicate match for '{key}' — keeping first file, ignoring **{f.name}**.")
            else:
                unrecognised.append(f.name)

        # Show recognition summary
        st.divider()
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"**{len(matched)} file(s) recognised**")
            for key in _BULK_ORDER:
                if key in matched:
                    _, _, label = next(t for t in _BULK_REGISTRY if t[0] == key)
                    st.markdown(f"✅ `{matched[key].name}` → **{label}**")
        with cols[1]:
            if unrecognised:
                st.markdown(f"**{len(unrecognised)} file(s) not recognised**")
                for name in unrecognised:
                    st.markdown(f"❌ `{name}`")
                st.caption("Rename to match an expected filename (e.g. `products.csv`).")

        if not matched:
            st.error("No files matched. Check filenames and try again.")
        else:
            st.divider()

            if "bulk_import_results" in st.session_state:
                results = st.session_state.pop("bulk_import_results")
                total_created = sum(r.get("created", 0) + r.get("orders_created", 0) for r in results.values())
                total_updated = sum(r.get("updated", 0) + r.get("items_created", 0) for r in results.values())
                total_skipped = sum(r.get("skipped", 0) for r in results.values())
                total_errors  = sum(len(r.get("errors", [])) for r in results.values())

                st.success(f"Bulk import complete — {len(results)} file(s) processed.")
                kpi_cols = st.columns(4)
                for col, (label, value, color) in zip(kpi_cols, [
                    ("records created",  total_created, "#16A34A"),
                    ("records updated",  total_updated, "#2563EB"),
                    ("rows skipped",     total_skipped, "#CA8A04"),
                    ("row errors",       total_errors,  "#DC2626"),
                ]):
                    with col:
                        st.markdown(
                            f"<div style='background:{color}22;border:1px solid {color}55;"
                            f"border-radius:6px;padding:8px 14px;text-align:center'>"
                            f"<div style='font-size:1.6rem;font-weight:700;color:{color}'>{value}</div>"
                            f"<div style='font-size:.75rem'>{label}</div></div>",
                            unsafe_allow_html=True,
                        )

                for key in _BULK_ORDER:
                    if key in results:
                        _, _, label = next(t for t in _BULK_REGISTRY if t[0] == key)
                        r = results[key]
                        err_count = len(r.get("errors", []))
                        icon = "✅" if err_count == 0 else "⚠️"
                        with st.expander(f"{icon} {label} — {matched[key].name}"):
                            detail_cols = st.columns(3)
                            for dc, (dl, dv) in zip(detail_cols, [
                                ("created",  r.get("created", r.get("orders_created", 0))),
                                ("updated",  r.get("updated", r.get("items_created", 0))),
                                ("skipped",  r.get("skipped", 0)),
                            ]):
                                dc.metric(dl, dv)
                            if r.get("errors"):
                                st.caption("Row errors:")
                                for e in r["errors"][:10]:
                                    st.caption(f"  • {e}")
                                if len(r["errors"]) > 10:
                                    st.caption(f"  … and {len(r['errors']) - 10} more")

            if st.button("⚡ Import All Files", type="primary", use_container_width=True, key="bulk_btn"):
                st.cache_data.clear()
                results = {}
                progress = st.progress(0, text="Starting import…")
                steps = [k for k in _BULK_ORDER if k in matched]

                for idx, key in enumerate(steps):
                    _, fn, label = next(t for t in _BULK_REGISTRY if t[0] == key)
                    f = matched[key]
                    progress.progress((idx) / len(steps), text=f"Importing {label} ({f.name})…")
                    content = f.getvalue()
                    result = fn(content, f.name)
                    if result:
                        results[key] = result
                    else:
                        results[key] = {"created": 0, "updated": 0, "skipped": 0, "errors": [f"Request failed for {f.name}"]}

                progress.progress(1.0, text="Done!")
                st.session_state["bulk_import_results"] = results
                st.rerun()

# ── Raw Materials ─────────────────────────────────────────────────────────────
with tab_materials:
    st.subheader("Raw Materials CSV")
    _upload_section(
        tab_key="materials",
        field_defs=RAW_MATERIALS_FIELDS,
        template_df=RAW_MATERIALS_TEMPLATE,
        template_filename="raw_materials_template.csv",
        description=(
            "One row per ingredient or stock item. "
            "Existing materials are **updated by name**; new names are created. "
            "`current_stock` seeds the live inventory."
        ),
        import_fn=api_client.import_raw_materials_csv,
        import_result_key="import_materials_result",
        button_label="✅ Import Raw Materials",
    )

# ── Raw Material Inventory ────────────────────────────────────────────────────
with tab_inventory:
    st.subheader("Inventory Update CSV")
    st.caption(
        "Update **stock levels only** for existing raw materials without re-importing specs.  \n"
        "Use `material_id` (numeric) or `material_name` to identify each row."
    )

    def _render_inventory_result(result: dict) -> None:
        st.success("Stock levels updated!")
        cols = st.columns(3)
        badges = [
            ("updated",   result.get("updated", 0),  "#16A34A"),
            ("skipped",   result.get("skipped", 0),  "#CA8A04"),
            ("not found", len(result.get("not_found", [])), "#DC2626"),
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
        if result.get("not_found"):
            with st.expander(f"⚠️ {len(result['not_found'])} materials not found"):
                for n in result["not_found"]:
                    st.caption(n)
        if result.get("errors"):
            with st.expander(f"⚠️ {len(result['errors'])} row errors"):
                for e in result["errors"]:
                    st.caption(e)

    _upload_section(
        tab_key="rmi",
        field_defs=RAW_MATERIAL_INVENTORY_FIELDS,
        template_df=RAW_MATERIAL_INVENTORY_TEMPLATE,
        template_filename="raw_material_inventory_template.csv",
        description=(
            "Provide either `material_id` (numeric) or `material_name`, plus `current_stock`. "
            "**Raw materials must already exist** — import Raw Materials first."
        ),
        import_fn=api_client.import_raw_material_inventory_csv,
        import_result_key="import_rmi_result",
        button_label="✅ Update Inventory",
        badge_fn=_render_inventory_result,
    )

# ── Products ──────────────────────────────────────────────────────────────────
with tab_products:
    st.subheader("Products CSV")
    _upload_section(
        tab_key="products",
        field_defs=PRODUCTS_FIELDS,
        template_df=PRODUCTS_TEMPLATE,
        template_filename="products_template.csv",
        description=(
            "One row per sellable product. "
            "Cost lives in Recipes — **not** here. "
            "Existing products are **updated by name**."
        ),
        import_fn=api_client.import_products_csv,
        import_result_key="import_products_result",
        button_label="✅ Import Products",
    )

# ── Recipes ───────────────────────────────────────────────────────────────────
with tab_recipes:
    st.subheader("Recipes CSV")
    st.caption(
        "Each row defines the cost for one (product, size) combination.  \n"
        "Leave `size` blank for products without size variants. "
        "Valid sizes: **S**, **M**, **L**."
    )
    _upload_section(
        tab_key="recipes",
        field_defs=RECIPES_FIELDS,
        template_df=RECIPES_TEMPLATE,
        template_filename="recipes_template.csv",
        description=(
            "Import recipe headers. **Products must be imported first.** "
            "`product_id` must match an existing product's numeric ID."
        ),
        import_fn=api_client.import_recipes_csv,
        import_result_key="import_recipes_result",
        button_label="✅ Import Recipes",
    )

# ── Recipe Items ──────────────────────────────────────────────────────────────
with tab_recipe_items:
    st.subheader("Recipe Items CSV")
    st.caption(
        "Links recipes to raw materials with exact quantities.  \n"
        "**Recipes and Raw Materials must be imported first.**"
    )
    _upload_section(
        tab_key="recipe_items",
        field_defs=RECIPE_ITEMS_FIELDS,
        template_df=RECIPE_ITEMS_TEMPLATE,
        template_filename="recipe_items_template.csv",
        description=(
            "`recipe_id` and `material_id` must reference existing records. "
            "Duplicate (recipe_id, material_id) pairs are **updated**."
        ),
        import_fn=api_client.import_recipe_items_csv,
        import_result_key="import_recipe_items_result",
        button_label="✅ Import Recipe Items",
    )

# ── Orders ────────────────────────────────────────────────────────────────────
with tab_orders:
    st.subheader("Orders CSV")
    st.warning(
        "**Recipes must exist before importing orders.** "
        "Any row whose `product_id` (+ `size`) has no recipe will be rejected.",
        icon="⚠️",
    )
    _upload_section(
        tab_key="orders",
        field_defs=ORDERS_FIELDS,
        template_df=ORDERS_TEMPLATE,
        template_filename="orders_template.csv",
        description=(
            "Each row is one line item. Rows sharing the same **Order ID** "
            "are grouped into one order. `unit_cost` is snapshotted from the "
            "recipe at import time for historical accuracy."
        ),
        import_fn=api_client.import_orders_csv,
        import_result_key="import_orders_result",
        button_label="✅ Import Orders",
        badge_fn=_render_orders_badges,
    )

# ── Order Items ───────────────────────────────────────────────────────────────
with tab_order_items:
    st.subheader("Order Items CSV")
    st.info(
        "**Two-file workflow:** Use this tab when you have orders and their line items "
        "in separate files. Import the **Orders** tab first (header file), then come here "
        "to import the matching line items.",
        icon="ℹ️",
    )
    st.warning(
        "**Recipes must exist before importing order items.** "
        "Any row whose `product_id` (+ `size`) has no recipe will be rejected.",
        icon="⚠️",
    )
    _upload_section(
        tab_key="order_items",
        field_defs=ORDER_ITEMS_FIELDS,
        template_df=ORDER_ITEMS_TEMPLATE,
        template_filename="order_items_template.csv",
        description=(
            "One row per line item. `order_id` must match an order already in the database. "
            "`unit_cost` is snapshotted from the recipe at import time."
        ),
        import_fn=api_client.import_order_items_csv,
        import_result_key="import_order_items_result",
        button_label="✅ Import Order Items",
    )

# ── Transactions ──────────────────────────────────────────────────────────────
with tab_transactions:
    st.subheader("Transactions CSV")
    _upload_section(
        tab_key="transactions",
        field_defs=TRANSACTIONS_FIELDS,
        template_df=TRANSACTIONS_TEMPLATE,
        template_filename="transactions_template.csv",
        description=(
            "Optional payment records. "
            "`order_id` must match an existing order's numeric ID."
        ),
        import_fn=api_client.import_transactions_csv,
        import_result_key="import_transactions_result",
        button_label="✅ Import Transactions",
    )

# ── Manage ────────────────────────────────────────────────────────────────────
with tab_manage:
    st.subheader("⚙️ Data Management")

    inventory = cached_inventory_status()
    if inventory:
        st.info(f"Database has **{len(inventory)} raw materials** tracked in inventory.")
    else:
        st.info("No inventory data yet.")

    st.divider()

    with st.expander("🗑️ Clear all data (danger zone)", expanded=False):
        st.warning(
            "Permanently deletes **all** raw materials, products, recipes, orders, "
            "customers, and transactions."
        )
        confirm_text = st.text_input(
            "Type DELETE to confirm", placeholder="DELETE", key="confirm_clear"
        )

        if "clear_data_result" in st.session_state:
            d = st.session_state.pop("clear_data_result")
            st.success(
                f"Cleared: {d.get('orders', 0)} orders · "
                f"{d.get('order_items', 0)} items · "
                f"{d.get('final_products', 0)} products · "
                f"{d.get('raw_materials', 0)} materials · "
                f"{d.get('customers', 0)} customers."
            )

        if st.button("🗑️ Clear all data", type="primary", disabled=(confirm_text != "DELETE")):
            st.cache_data.clear()
            with st.spinner("Deleting all data…"):
                result = api_client.clear_all_data()
            if result:
                st.session_state["clear_data_result"] = result.get("deleted", {})
            st.rerun()
