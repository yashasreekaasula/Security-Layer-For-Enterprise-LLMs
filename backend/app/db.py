import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DEFAULT_DB = f"sqlite:///{(ROOT / 'data' / 'company_copilot.db').as_posix()}"
DATABASE_URL = os.getenv('DATABASE_URL', DEFAULT_DB)
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
class Base(DeclarativeBase): pass

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
