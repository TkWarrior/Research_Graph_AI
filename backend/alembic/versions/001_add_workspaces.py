"""Add workspaces table and migrate document_id scoping to workspace_id.

Revision ID: 001_add_workspaces
Revises: (initial migration — no prior revision)
Create Date: 2026-05-14

Summary of changes:
  1. CREATE TABLE workspaces
  2. ALTER TABLE documents  — ADD workspace_id FK (NOT NULL)
  3. ALTER TABLE chat_sessions — DROP document_id FK, ADD workspace_id FK (NOT NULL)
  4. ALTER TABLE graph_snapshots — ADD workspace_id FK (NOT NULL), make document_id nullable

Backfill strategy:
  - A default "Default Workspace" is inserted before NOT NULL constraints
    are added, and all existing rows are assigned to it.
  - After the migration all pre-existing data is preserved under one workspace.

Downgrade:
  - Reverses every step in order (workspace_id removed, document_id restored).
  - NOTE: the backfilled workspace row is removed, which means any data
    created during the migrated state will lose its workspace association.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ──────────────────────────────────────────────
revision: str = "001_add_workspaces"
down_revision: str | None = None   # set to previous revision ID if one exists
branch_labels: str | None = None
depends_on: str | None = None

# ── Shared helpers ────────────────────────────────────────────────────
DEFAULT_WS_ID = str(uuid.uuid4())   # stable UUID used for the backfill row
NOW = datetime.now(timezone.utc)


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────
    # 1. CREATE TABLE workspaces
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ─────────────────────────────────────────────────────────────────
    # 2. INSERT a default workspace so we can backfill existing rows
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        f"""
        INSERT INTO workspaces (id, name, description, created_at, updated_at)
        VALUES (
            '{DEFAULT_WS_ID}',
            'Default Workspace',
            'Auto-created during workspace migration to hold pre-existing data.',
            NOW(),
            NOW()
        )
        """
    )

    # ─────────────────────────────────────────────────────────────────
    # 3. ALTER TABLE documents — add workspace_id FK
    # ─────────────────────────────────────────────────────────────────
    # Add as nullable first so existing rows don't violate the constraint
    op.add_column(
        "documents",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,   # temporarily nullable for backfill
        ),
    )
    # Backfill existing documents → default workspace
    op.execute(
        f"UPDATE documents SET workspace_id = '{DEFAULT_WS_ID}' WHERE workspace_id IS NULL"
    )
    # Now tighten to NOT NULL
    op.alter_column("documents", "workspace_id", nullable=False)
    # Add FK constraint
    op.create_foreign_key(
        "fk_documents_workspace_id",
        "documents", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )

    # ─────────────────────────────────────────────────────────────────
    # 4. ALTER TABLE chat_sessions — swap document_id → workspace_id
    # ─────────────────────────────────────────────────────────────────
    # Drop old FK constraint (name may vary — use IF EXISTS via raw SQL)
    op.execute(
        "ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_document_id_fkey"
    )
    # Drop old column
    op.drop_column("chat_sessions", "document_id")

    # Add workspace_id (nullable for backfill)
    op.add_column(
        "chat_sessions",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    # Backfill existing sessions → default workspace
    op.execute(
        f"UPDATE chat_sessions SET workspace_id = '{DEFAULT_WS_ID}' WHERE workspace_id IS NULL"
    )
    # Tighten to NOT NULL
    op.alter_column("chat_sessions", "workspace_id", nullable=False)
    # Add FK constraint
    op.create_foreign_key(
        "fk_chat_sessions_workspace_id",
        "chat_sessions", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )

    # ─────────────────────────────────────────────────────────────────
    # 5. ALTER TABLE graph_snapshots — add workspace_id, keep document_id nullable
    # ─────────────────────────────────────────────────────────────────
    # Drop the old NOT NULL FK on document_id, keep column as nullable
    op.execute(
        "ALTER TABLE graph_snapshots DROP CONSTRAINT IF EXISTS graph_snapshots_document_id_fkey"
    )
    op.alter_column("graph_snapshots", "document_id", nullable=True)

    # Add workspace_id (nullable for backfill)
    op.add_column(
        "graph_snapshots",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    # Backfill existing snapshots → default workspace
    op.execute(
        f"UPDATE graph_snapshots SET workspace_id = '{DEFAULT_WS_ID}' WHERE workspace_id IS NULL"
    )
    # Tighten to NOT NULL
    op.alter_column("graph_snapshots", "workspace_id", nullable=False)
    # Add FK constraint
    op.create_foreign_key(
        "fk_graph_snapshots_workspace_id",
        "graph_snapshots", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )
    # Restore nullable FK on document_id for traceability
    op.create_foreign_key(
        "fk_graph_snapshots_document_id",
        "graph_snapshots", "documents",
        ["document_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Reverse every upgrade step in reverse order."""

    # ── graph_snapshots ──────────────────────────────────────────────
    op.drop_constraint("fk_graph_snapshots_document_id", "graph_snapshots", type_="foreignkey")
    op.drop_constraint("fk_graph_snapshots_workspace_id", "graph_snapshots", type_="foreignkey")
    op.drop_column("graph_snapshots", "workspace_id")
    op.alter_column("graph_snapshots", "document_id", nullable=False)
    op.create_foreign_key(
        "graph_snapshots_document_id_fkey",
        "graph_snapshots", "documents",
        ["document_id"], ["id"],
    )

    # ── chat_sessions ────────────────────────────────────────────────
    op.drop_constraint("fk_chat_sessions_workspace_id", "chat_sessions", type_="foreignkey")
    op.drop_column("chat_sessions", "workspace_id")
    op.add_column(
        "chat_sessions",
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "chat_sessions_document_id_fkey",
        "chat_sessions", "documents",
        ["document_id"], ["id"],
    )

    # ── documents ────────────────────────────────────────────────────
    op.drop_constraint("fk_documents_workspace_id", "documents", type_="foreignkey")
    op.drop_column("documents", "workspace_id")

    # ── workspaces table ─────────────────────────────────────────────
    op.drop_table("workspaces")
