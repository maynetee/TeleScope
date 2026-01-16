"""add collections extensions alerts and shares

Revision ID: 2b7f2dca2b5e
Revises: 0f3c3a5c8f2a
Create Date: 2025-01-16 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b7f2dca2b5e'
down_revision = '0f3c3a5c8f2a'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.add_column('collections', sa.Column('color', sa.String(length=7), nullable=True))
    op.add_column('collections', sa.Column('icon', sa.String(length=50), nullable=True))
    op.add_column('collections', sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('collections', sa.Column('is_global', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('collections', sa.Column('parent_id', sa.UUID(), nullable=True))
    op.add_column('collections', sa.Column('auto_assign_languages', sa.JSON(), nullable=True))
    op.add_column('collections', sa.Column('auto_assign_keywords', sa.JSON(), nullable=True))
    op.add_column('collections', sa.Column('auto_assign_tags', sa.JSON(), nullable=True))
    op.create_foreign_key('fk_collections_parent', 'collections', 'collections', ['parent_id'], ['id'], ondelete='SET NULL')

    op.add_column('channels', sa.Column('tags', sa.JSON(), nullable=True))

    op.add_column('summaries', sa.Column('collection_id', sa.UUID(), nullable=True))
    op.create_index('ix_summaries_collection_id', 'summaries', ['collection_id'], unique=False)
    op.create_foreign_key('fk_summaries_collection', 'summaries', 'collections', ['collection_id'], ['id'], ondelete='SET NULL')

    if 'alerts' not in inspector.get_table_names():
        op.create_table(
            'alerts',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('collection_id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('keywords', sa.JSON(), nullable=True),
            sa.Column('entities', sa.JSON(), nullable=True),
            sa.Column('min_threshold', sa.Integer(), server_default='1'),
            sa.Column('frequency', sa.String(length=20), server_default='daily'),
            sa.Column('notification_channels', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )

    if 'alert_triggers' not in inspector.get_table_names():
        op.create_table(
            'alert_triggers',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('alert_id', sa.UUID(), nullable=False),
            sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('message_ids', sa.JSON(), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        )

    if 'collection_shares' not in inspector.get_table_names():
        op.create_table(
            'collection_shares',
            sa.Column('collection_id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('permission', sa.String(length=20), server_default='viewer'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('collection_id', 'user_id'),
        )


def downgrade():
    op.drop_table('collection_shares')
    op.drop_table('alert_triggers')
    op.drop_table('alerts')

    op.drop_constraint('fk_summaries_collection', 'summaries', type_='foreignkey')
    op.drop_index('ix_summaries_collection_id', table_name='summaries')
    op.drop_column('summaries', 'collection_id')

    op.drop_column('channels', 'tags')

    op.drop_constraint('fk_collections_parent', 'collections', type_='foreignkey')
    op.drop_column('collections', 'auto_assign_tags')
    op.drop_column('collections', 'auto_assign_keywords')
    op.drop_column('collections', 'auto_assign_languages')
    op.drop_column('collections', 'parent_id')
    op.drop_column('collections', 'is_global')
    op.drop_column('collections', 'is_default')
    op.drop_column('collections', 'icon')
    op.drop_column('collections', 'color')
