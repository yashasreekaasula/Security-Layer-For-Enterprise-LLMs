from pathlib import Path
import torch
from torch import nn
from .db import ROOT
ACTIONS=['ANSWER_FULLY','REDACT','SUMMARIZE','REQUEST_AUTHORIZATION','ESCALATE_HUMAN','REFUSE']
_model=None
class ActorCritic(nn.Module):
    def __init__(self):
        super().__init__(); self.shared=nn.Sequential(nn.Linear(5,64),nn.Tanh(),nn.Linear(64,64),nn.Tanh()); self.actor=nn.Linear(64,6); self.critic=nn.Linear(64,1)
    def forward(self,x):
        z=self.shared(x); return self.actor(z),self.critic(z).squeeze(-1)
def _load_model():
    global _model
    if _model is not None: return _model
    p=ROOT/'models'/'privacy_ppo.pt'
    if not p.exists(): return None
    ck=torch.load(p,map_location='cpu',weights_only=True)
    candidate=ActorCritic(); candidate.load_state_dict(ck['state_dict']); candidate.eval(); _model=candidate
    return _model
def checkpoint_ready():
    try: return _load_model() is not None
    except Exception: return False
def recommend(s):
    try:
        model=_load_model()
        if model is None: return 'SUMMARIZE',True
        with torch.no_grad(): logits,_=model(torch.tensor([s],dtype=torch.float32)); action=int(logits.argmax(1).item())
        return ACTIONS[action],False
    except Exception: return 'SUMMARIZE',True
