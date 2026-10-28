from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now(): return datetime.now(timezone.utc)
class AuthSession(Base):
    __tablename__='auth_sessions'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    token_id: Mapped[str]=mapped_column(String(80), unique=True, index=True)
    revoked: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Employee(Base):
    __tablename__='employees'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str]=mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str]=mapped_column(String(160))
    email: Mapped[str]=mapped_column(String(190), unique=True, index=True)
    dob: Mapped[str]=mapped_column(String(10), default='')
    department: Mapped[str]=mapped_column(String(80), index=True)
    title: Mapped[str]=mapped_column(String(120))
    role: Mapped[str]=mapped_column(String(40), default='Employee', index=True)
    assigned_projects: Mapped[list]=mapped_column(JSON, default=list)
    registered: Mapped[bool]=mapped_column(Boolean, default=False)
    approved: Mapped[bool]=mapped_column(Boolean, default=True)
    password_hash: Mapped[str|None]=mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class Project(Base):
    __tablename__='projects'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    name: Mapped[str]=mapped_column(String(100), unique=True, index=True)
    department: Mapped[str]=mapped_column(String(80))
    status: Mapped[str]=mapped_column(String(40))
    summary: Mapped[str]=mapped_column(Text)
class Document(Base):
    __tablename__='documents'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    document_id: Mapped[str]=mapped_column(String(40), unique=True, index=True)
    title: Mapped[str]=mapped_column(String(240), index=True)
    content: Mapped[str]=mapped_column(Text)
    department: Mapped[str]=mapped_column(String(80), index=True)
    project: Mapped[str]=mapped_column(String(100), index=True)
    classification: Mapped[str]=mapped_column(String(30), index=True)
    allowed_roles: Mapped[list]=mapped_column(JSON)
    owner: Mapped[str]=mapped_column(String(190))
    doc_type: Mapped[str]=mapped_column(String(80))
    synthetic: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    __table_args__=(Index('ix_doc_department_project','department','project'),)
class Conversation(Base):
    __tablename__='conversations'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    title: Mapped[str]=mapped_column(String(200), default='New conversation')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class Message(Base):
    __tablename__='messages'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int]=mapped_column(ForeignKey('conversations.id'), index=True)
    role: Mapped[str]=mapped_column(String(20))
    content: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class PrivacyBudget(Base):
    __tablename__='privacy_budgets'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), unique=True, index=True)
    remaining: Mapped[float]=mapped_column(Float, default=10.0)
    initial: Mapped[float]=mapped_column(Float, default=10.0)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, onupdate=now)
class BudgetTransaction(Base):
    __tablename__='budget_transactions'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    action: Mapped[str]=mapped_column(String(40))
    cost: Mapped[float]=mapped_column(Float)
    before: Mapped[float]=mapped_column(Float)
    after: Mapped[float]=mapped_column(Float)
    reason: Mapped[str]=mapped_column(String(300))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class PPODecision(Base):
    __tablename__='ppo_decisions'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    conversation_id: Mapped[int]=mapped_column(ForeignKey('conversations.id'), index=True)
    intent: Mapped[str]=mapped_column(String(60))
    state_features: Mapped[list]=mapped_column(JSON, default=list)
    recommended_action: Mapped[str]=mapped_column(String(40))
    final_action: Mapped[str]=mapped_column(String(40))
    model_status: Mapped[str]=mapped_column(String(80))
    fallback_used: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class AuditEvent(Base):
    __tablename__='audit_events'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int|None]=mapped_column(ForeignKey('employees.id'), nullable=True, index=True)
    request_type: Mapped[str]=mapped_column(String(60))
    recommended_action: Mapped[str]=mapped_column(String(40))
    final_action: Mapped[str]=mapped_column(String(40))
    policy_outcome: Mapped[str]=mapped_column(String(100))
    source_ids: Mapped[list]=mapped_column(JSON, default=list)
    budget_before: Mapped[float]=mapped_column(Float, default=0)
    budget_after: Mapped[float]=mapped_column(Float, default=0)
    fallback_used: Mapped[bool]=mapped_column(Boolean, default=True)
    detail: Mapped[str]=mapped_column(String(300), default='')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class AuthorizationRequest(Base):
    __tablename__='authorization_requests'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    request_text: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30), default='pending')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class HumanReview(Base):
    __tablename__='human_reviews'
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int]=mapped_column(ForeignKey('employees.id'), index=True)
    request_text: Mapped[str]=mapped_column(Text)
    reason: Mapped[str]=mapped_column(String(300))
    status: Mapped[str]=mapped_column(String(30), default='pending')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
