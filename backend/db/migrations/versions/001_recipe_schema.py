"""Recipe-based schema migration

Revision ID: 001_recipe_schema
Revises:
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_recipe_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create new tables
    # ------------------------------------------------------------------
    op.create_table(
        "raw_materials",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("cost_per_unit", sa.Numeric(10, 2), nullable=True),
        sa.Column("reorder_point", sa.Integer, nullable=True),
        sa.Column("lead_time_days", sa.Integer, server_default="7", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_raw_materials_category", "raw_materials", ["category"])

    op.create_table(
        "raw_material_inventory",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "material_id",
            sa.Integer,
            sa.ForeignKey("raw_materials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_stock", sa.Integer, server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_rmi_material_id", "raw_material_inventory", ["material_id"])

    op.create_table(
        "final_products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_final_products_category", "final_products", ["category"])

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("final_products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("size", sa.String(10), nullable=True),
        sa.Column("unit_cost", sa.Numeric(10, 4), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_recipes_product_id", "recipes", ["product_id"])

    op.create_table(
        "recipe_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "recipe_id",
            sa.Integer,
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "material_id",
            sa.Integer,
            sa.ForeignKey("raw_materials.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity_needed", sa.Numeric(10, 4), nullable=False),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
    )
    op.create_index("idx_recipe_items_recipe_id", "recipe_items", ["recipe_id"])
    op.create_index("idx_recipe_items_material_id", "recipe_items", ["material_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_transactions_order_id", "transactions", ["order_id"])

    # ------------------------------------------------------------------
    # 2. Migrate products → final_products + raw_materials
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO final_products (id, name, category, unit_price, created_at, updated_at)
        SELECT id, name, category, unit_price, created_at, updated_at
        FROM products
        WHERE deleted_at IS NULL
    """)

    # Sync the final_products sequence so new rows don't collide
    op.execute("""
        SELECT setval(
            pg_get_serial_sequence('final_products', 'id'),
            COALESCE((SELECT MAX(id) FROM final_products), 1)
        )
    """)

    # One raw material per product (1:1 seed; users can refine via CSV later)
    op.execute("""
        INSERT INTO raw_materials (name, category, unit, cost_per_unit, reorder_point, lead_time_days, created_at, updated_at)
        SELECT name, category, 'units', cost_per_unit, reorder_point, lead_time_days, created_at, updated_at
        FROM products
        WHERE deleted_at IS NULL
        ON CONFLICT (name) DO NOTHING
    """)

    # Seed raw_material_inventory with current_stock from products
    op.execute("""
        INSERT INTO raw_material_inventory (material_id, current_stock)
        SELECT rm.id, p.current_stock
        FROM products p
        JOIN raw_materials rm ON rm.name = p.name
        WHERE p.deleted_at IS NULL
    """)

    # ------------------------------------------------------------------
    # 3. Create one default recipe per product (size = NULL)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO recipes (product_id, size, unit_cost)
        SELECT id, NULL, COALESCE(cost_per_unit, 0)
        FROM products
        WHERE deleted_at IS NULL
    """)

    # Seed recipe_items: each recipe references its matching raw material (1 unit)
    op.execute("""
        INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
        SELECT r.id, rm.id, 1, 'units'
        FROM recipes r
        JOIN final_products fp ON r.product_id = fp.id
        JOIN raw_materials rm ON rm.name = fp.name
    """)

    # ------------------------------------------------------------------
    # 4. Alter order_items
    #    a. Drop old FK + unique constraint referencing products
    #    b. Add new columns
    #    c. Add new FK to final_products and recipes
    #    d. Add new unique constraint
    # ------------------------------------------------------------------
    # Drop old unique constraint — name differs depending on how DB was created:
    # - Via SQLAlchemy model: "uq_order_product"
    # - Via seed_data.sql UNIQUE(…) without a name: "order_items_order_id_product_id_key"
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_order_product'
                  AND conrelid = 'order_items'::regclass
            ) THEN
                ALTER TABLE order_items DROP CONSTRAINT uq_order_product;
            ELSIF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'order_items_order_id_product_id_key'
                  AND conrelid = 'order_items'::regclass
            ) THEN
                ALTER TABLE order_items DROP CONSTRAINT order_items_order_id_product_id_key;
            END IF;
        END $$;
    """)

    # Drop old FK to products — name also varies by creation method
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'order_items_product_id_fkey'
                  AND conrelid = 'order_items'::regclass
            ) THEN
                ALTER TABLE order_items DROP CONSTRAINT order_items_product_id_fkey;
            END IF;
        END $$;
    """)

    op.add_column("order_items", sa.Column("size", sa.String(10), nullable=True))
    op.add_column("order_items", sa.Column("recipe_id", sa.Integer, nullable=True))
    op.add_column("order_items", sa.Column("unit_cost", sa.Numeric(10, 4), nullable=True))

    # Backfill recipe_id: match by product_id (default recipe has size = NULL)
    op.execute("""
        UPDATE order_items oi
        SET recipe_id = r.id,
            unit_cost  = r.unit_cost
        FROM recipes r
        WHERE r.product_id = oi.product_id
          AND r.size IS NULL
    """)

    op.create_foreign_key(
        "fk_order_items_product_id",
        "order_items",
        "final_products",
        ["product_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_order_items_recipe_id",
        "order_items",
        "recipes",
        ["recipe_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_order_product_size", "order_items", ["order_id", "product_id", "size"]
    )

    # ------------------------------------------------------------------
    # 5. Drop legacy tables
    # ------------------------------------------------------------------
    op.drop_table("inventory_snapshots")
    op.drop_table("products")


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade not supported: old products table was dropped. "
        "Restore from backup to roll back."
    )
