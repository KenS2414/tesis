"""add subject year_group

Revision ID: f3b1c2a4d5e6
Revises: d82b992f127d
Create Date: 2026-03-21 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3b1c2a4d5e6'
down_revision = 'd82b992f127d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subject', schema=None) as batch_op:
        batch_op.add_column(sa.Column('year_group', sa.String(length=100), nullable=True))



def downgrade():
    with op.batch_alter_table('subject', schema=None) as batch_op:
        batch_op.drop_column('year_group')
