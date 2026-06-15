"""Add external_id to final_products and recipes for string-ID CSV imports."""
from alembic import op
import sqlalchemy as sa

revision = "002_add_external_ids"
down_revision = "001_recipe_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "final_products",
        sa.Column("external_id", sa.String(100), nullable=True),
    )
    op.create_index("ix_final_products_external_id", "final_products", ["external_id"], unique=True)

    op.add_column(
        "recipes",
        sa.Column("external_id", sa.String(100), nullable=True),
    )
    op.create_index("ix_recipes_external_id", "recipes", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_recipes_external_id", table_name="recipes")
    op.drop_column("recipes", "external_id")

    op.drop_index("ix_final_products_external_id", table_name="final_products")
    op.drop_column("final_products", "external_id")
