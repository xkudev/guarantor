"""create identities table

Revision ID: 5f5a44b3dcad
Revises: 
Create Date: 2022-06-12 16:22:14.621261

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision      = '5f5a44b3dcad'
down_revision = None
branch_labels = None
depends_on    = None


def upgrade() -> None:
    op.create_table(
        'identities',
        sa.Column('dbid'   , sa.Integer, primary_key=True),
        sa.Column('address', sa.String(100), nullable=False),
        sa.Column('props'  , sa.Text),
    )


def downgrade():
    op.drop_table('identities')
