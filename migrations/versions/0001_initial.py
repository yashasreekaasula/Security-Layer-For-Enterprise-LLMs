"""Initial Company Copilot schema, generated from ORM metadata."""
from alembic import op
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))
from app.db import Base
from app import models  # noqa: F401
revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None
def upgrade(): Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
