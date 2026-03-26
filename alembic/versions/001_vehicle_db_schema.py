"""vehicle_db: vehicles, vehicle_images, vehicle_documents, vehicle_status_logs.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-27

Enums: fuel_type_enum, vehicle_status_enum, vehicle_doc_enum.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    fuel_type_enum = postgresql.ENUM(
        "petrol",
        "diesel",
        "electric",
        "hybrid",
        name="fuel_type_enum",
        create_type=True,
    )
    fuel_type_enum.create(op.get_bind(), checkfirst=True)

    vehicle_status_enum = postgresql.ENUM(
        "active",
        "inactive",
        "in_service",
        "delivered",
        name="vehicle_status_enum",
        create_type=True,
    )
    vehicle_status_enum.create(op.get_bind(), checkfirst=True)

    vehicle_doc_enum = postgresql.ENUM(
        "rc",
        "insurance",
        "pollution",
        "other",
        name="vehicle_doc_enum",
        create_type=True,
    )
    vehicle_doc_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        # External reference to User MS (intentionally no FK constraint).
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("fuel_type", fuel_type_enum, nullable=False),
        sa.Column("plate_number", sa.String(20), nullable=False),
        sa.Column("vin_number", sa.String(50), nullable=True),
        sa.Column("color", sa.String(50), nullable=True),
        sa.Column("status", vehicle_status_enum, nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("vehicle_id"),
        sa.UniqueConstraint("plate_number", name="vehicles_plate_number_key"),
    )

    op.create_index("idx_vehicles_user_id", "vehicles", ["user_id"])
    op.create_index("idx_vehicles_plate_number", "vehicles", ["plate_number"])
    op.create_index("idx_vehicles_status", "vehicles", ["status"])

    op.create_table(
        "vehicle_images",
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("image_id"),
    )
    op.create_index("idx_vehicle_images_vehicle_id", "vehicle_images", ["vehicle_id"])

    op.create_table(
        "vehicle_documents",
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", vehicle_doc_enum, nullable=False),
        sa.Column("doc_url", sa.Text(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("doc_id"),
    )

    op.create_table(
        "vehicle_status_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", vehicle_status_enum, nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("log_id"),
    )


def downgrade() -> None:
    op.drop_table("vehicle_status_logs")
    op.drop_table("vehicle_documents")
    op.drop_index("idx_vehicle_images_vehicle_id", table_name="vehicle_images")
    op.drop_table("vehicle_images")

    op.drop_index("idx_vehicles_status", table_name="vehicles")
    op.drop_index("idx_vehicles_plate_number", table_name="vehicles")
    op.drop_index("idx_vehicles_user_id", table_name="vehicles")
    op.drop_table("vehicles")

    op.execute("DROP TYPE IF EXISTS vehicle_doc_enum")
    op.execute("DROP TYPE IF EXISTS vehicle_status_enum")
    op.execute("DROP TYPE IF EXISTS fuel_type_enum")

