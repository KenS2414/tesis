"""add student current year group

Revision ID: a7d9e4c2b1f0
Revises: f3b1c2a4d5e6
Create Date: 2026-03-21 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7d9e4c2b1f0'
down_revision = 'f3b1c2a4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_year_group', sa.String(length=100), nullable=True))



def downgrade():
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_column('current_year_group')
