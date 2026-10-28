import re, os
from dataclasses import dataclass
ACTIONS=('ANSWER_FULLY','REDACT','SUMMARIZE','REQUEST_AUTHORIZATION','ESCALATE_HUMAN','REFUSE')
COSTS={'ANSWER_FULLY':1.0,'REDACT':0.35,'SUMMARIZE':0.5,'REQUEST_AUTHORIZATION':0.0,'ESCALATE_HUMAN':0.0,'REFUSE':0.0}
SECRET_RE=re.compile(r'\b(api[_ -]?key|password|secret|access token|private key|credential)\b',re.I)
SENSITIVE_RE=re.compile(r'\b(salary|performance review|date of birth|dob|medical record|bank account|personal address|tax identifier|financial details|financial information|compensation|payroll details)\b',re.I)
PERSON_TARGET_RE=re.compile(r"\b(?:details|information|profile|records?|background|contact details|financial details|financial information|salary|compensation|payroll details|performance review|bank account|tax identifier|date of birth|medical record)\s+(?:of|for|about|belonging to)\s+[a-z][a-z .'-]{1,80}",re.I)
PERSONAL_RECORD_RE=PERSON_TARGET_RE
GENERIC_FINANCE_RE=re.compile(r'\b(financial details|financial information|finance details|financials|finance|payroll|budget details)\b',re.I)
def requires_personal_record_authorization(q:str)->bool:
    # Any named-person profile or personal-record request requires explicit approved workflow.
    return bool(PERSON_TARGET_RE.search(q.strip()))
def classify_intent(q:str)->str:
    t=q.strip().lower()
    if t in {'hi','hello','hey','good morning','good afternoon','good evening','thanks','thank you'}: return 'greeting'
    if t in {'it','that','tell me more','what about it','explain more','help','can you help','do it','which one'}: return 'ambiguous'
    if PERSON_TARGET_RE.search(t): return 'sensitive'
    # Bare financial-details requests lack a report or scope; clarify rather than searching arbitrary documents.
    if GENERIC_FINANCE_RE.search(t) and not re.search(r'\b(of|for|about|company|project|quarter|q[1-4]|year|annual|report|forecast|expenses|revenue|costs?|spend|spending|funds? raised|funding)\b',t): return 'ambiguous'
    if SECRET_RE.search(t) and any(x in t for x in ['reveal','show','give','tell','what is','print','dump','expose']): return 'credential'
    if any(x in t for x in ['def ','python','javascript','typescript','sql query','write code','debug','function to','reverse a string','program to']): return 'coding'
    if SENSITIVE_RE.search(t) or PERSONAL_RECORD_RE.search(t): return 'sensitive'
    return 'company'
def can_read(user, doc):
    role=user.role; dept=user.department
    if role=='Project Manager' and doc.classification!='Public' and doc.department not in ('Company','General') and doc.project not in (user.assigned_projects or []): return False
    if doc.classification=='Public': return True
    if role=='Administrator': return doc.classification!='Restricted' and (doc.department in ('Company','General',dept) or role in (doc.allowed_roles or []))
    if doc.classification=='Internal': return doc.department in ('Company','General') or dept==doc.department or role in (doc.allowed_roles or [])
    if doc.classification=='Confidential': return dept==doc.department and (role in (doc.allowed_roles or []) or role=={'Human Resources':'HR','Finance':'Finance','Information Technology':'IT'}.get(dept))
    if doc.classification=='Restricted': return role in (doc.allowed_roles or []) and dept==doc.department
    return False
def detect_secret_request(q): return bool(SECRET_RE.search(q) and re.search(r'\b(reveal|show|give|tell|print|dump|expose)\b',q,re.I))
RESPONSE_SECRET_RE=re.compile(r'(?i)(sk-[A-Za-z0-9]{20,}|api[_ -]?key\s*[:=]|password\s*[:=]|-----BEGIN [A-Z ]*PRIVATE KEY-----|bearer\s+[A-Za-z0-9._~-]{24,})')
def response_has_secret(text): return bool(RESPONSE_SECRET_RE.search(text or ''))
def enforce(user, q, intent, budget, recommended='SUMMARIZE'):
    if intent=='credential': return 'REFUSE','Credential requests are never disclosed.'
    if intent=='sensitive' and user.role not in ('HR','Administrator','Executive'): return 'REQUEST_AUTHORIZATION','Sensitive employee information requires an authorized workflow.'
    if budget<=float(os.getenv('MIN_REMAINING_BUDGET','0.0')) and intent not in ('greeting','coding'): return 'ESCALATE_HUMAN','Disclosure allowance exhausted or minimum balance reached.'
    if intent in ('greeting','coding'): return 'ANSWER_FULLY','General assistance does not require company retrieval.'
    if recommended not in ACTIONS: recommended='SUMMARIZE'
    return recommended,'Policy checks passed; answer only from authorized evidence.'
