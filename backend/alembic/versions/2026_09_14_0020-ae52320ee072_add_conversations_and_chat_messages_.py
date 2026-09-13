"""add_conversations_and_chat_messages_tables

Revision ID: ae52320ee072
Revises: abf76fb66fa3
Create Date: 2026-09-14 00:20:18.022772

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae52320ee072'
down_revision: Union[str, None] = 'abf76fb66fa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_conversations_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_conversations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_conversations_updated_at'), ['updated_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_conversations_user_id'), ['user_id'], unique=False)
        batch_op.create_index('ix_conversations_user_id_updated_at', ['user_id', 'updated_at'], unique=False)

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_messages_conversation_id'), ['conversation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chat_messages_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_chat_messages_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chat_messages_user_id'), ['user_id'], unique=False)
        batch_op.create_index('ix_chat_messages_conv_created', ['conversation_id', 'created_at'], unique=False)
        batch_op.create_index('ix_chat_messages_user_created', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.drop_index('ix_chat_messages_user_created')
        batch_op.drop_index('ix_chat_messages_conv_created')
        batch_op.drop_index(batch_op.f('ix_chat_messages_user_id'))
        batch_op.drop_index(batch_op.f('ix_chat_messages_id'))
        batch_op.drop_index(batch_op.f('ix_chat_messages_created_at'))
        batch_op.drop_index(batch_op.f('ix_chat_messages_conversation_id'))

    op.drop_table('chat_messages')

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_index('ix_conversations_user_id_updated_at')
        batch_op.drop_index(batch_op.f('ix_conversations_user_id'))
        batch_op.drop_index(batch_op.f('ix_conversations_updated_at'))
        batch_op.drop_index(batch_op.f('ix_conversations_status'))
        batch_op.drop_index(batch_op.f('ix_conversations_id'))

    op.drop_table('conversations')

