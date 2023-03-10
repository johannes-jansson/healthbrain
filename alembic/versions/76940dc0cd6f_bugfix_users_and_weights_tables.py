"""bugfix users and weights tables

Revision ID: 76940dc0cd6f
Revises: cec350f41b71
Create Date: 2023-02-05 23:51:29.569281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76940dc0cd6f'
down_revision = 'cec350f41b71'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('weights', sa.Column('date', sa.Date(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('weights', 'date')
    # ### end Alembic commands ###
