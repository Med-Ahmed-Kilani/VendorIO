"""Add external_id to raw_materials for MAT-001 style CSV imports."""
from alembic import op
import sqlalchemy as sa

revision = "003_raw_material_external_id"
down_revision = "002_add_external_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "raw_materials",
        sa.Column("external_id", sa.String(100), nullable=True),
    )
    op.create_index("ix_raw_materials_external_id", "raw_materials", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_raw_materials_external_id", table_name="raw_materials")
    op.drop_column("raw_materials", "external_id")
