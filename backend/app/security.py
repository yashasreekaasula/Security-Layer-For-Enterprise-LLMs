import os, hashlib, hmac, secrets, time
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db import get_db, SessionLocal
from .models import Employee, AuthSession

JWT_SECRET=os.getenv('JWT_SECRET','dev-only-change-this-secret-before-deploying')
ALGORITHM='HS256'; bearer=HTTPBearer(auto_error=False)
def hash_password(password:str)->str:
    salt=secrets.token_bytes(16); digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,310000)
    return salt.hex()+':'+digest.hex()
def verify_password(password:str, encoded:str|None)->bool:
    if not encoded or ':' not in encoded: return False
    salt,digest=encoded.split(':',1)
    try: got=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),310000).hex()
    except ValueError: return False
    return hmac.compare_digest(got,digest)
def create_token(employee:Employee)->str:
    jti=secrets.token_urlsafe(24); exp=int(time.time())+int(os.getenv('ACCESS_TOKEN_MINUTES','60'))*60
    token=jwt.encode({'sub':str(employee.id),'jti':jti,'iat':int(time.time()),'exp':exp},JWT_SECRET,algorithm=ALGORITHM)
    with SessionLocal() as db:
        db.add(AuthSession(employee_id=employee.id,token_id=jti,revoked=False)); db.commit()
    return token
def current_user(creds:HTTPAuthorizationCredentials|None=Depends(bearer), db:Session=Depends(get_db))->Employee:
    if not creds: raise HTTPException(401,'Authentication required')
    try: payload=jwt.decode(creds.credentials,JWT_SECRET,algorithms=[ALGORITHM]); uid=int(payload['sub']); jti=payload['jti']
    except Exception: raise HTTPException(401,'Session invalid or expired')
    session=db.query(AuthSession).filter_by(token_id=jti,employee_id=uid,revoked=False).first()
    user=db.get(Employee,uid)
    if not session: raise HTTPException(401,'Session revoked or expired')
    if not user or not user.registered or not user.approved: raise HTTPException(401,'Account inactive')
    return user
def require_admin(user:Employee=Depends(current_user))->Employee:
    if user.role!='Administrator': raise HTTPException(403,'Administrator access required')
    return user
