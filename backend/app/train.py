"""Synthetic-data PPO training. Supervised warm-start and PPO optimization are logged separately."""
import json, random, copy, time
from pathlib import Path
import torch
from torch import nn
from torch.distributions import Categorical
ROOT=Path(__file__).resolve().parents[2]
SEED=20261012; random.seed(SEED); torch.manual_seed(SEED); torch.set_num_threads(1)
ACTIONS=['ANSWER_FULLY','REDACT','SUMMARIZE','REQUEST_AUTHORIZATION','ESCALATE_HUMAN','REFUSE']
FEATURES=['sensitivity','authorization','task_utility','remaining_budget_fraction','secret_indicator']
def label(s):
    sens,auth,utility,budget,secret=s
    if secret>.5: return 5
    if sens>.72 and auth<.5: return 3
    if budget<.08 and utility>.2: return 4
    if sens>.55: return 1
    if utility<.3: return 2
    if budget<.2: return 2
    if utility>.75 and auth>.5 and sens<.3: return 0
    return 2
N=12000; X=[]; Y=[]
for _ in range(N):
    s=[random.random() for _ in range(5)]; X.append(s); Y.append(label(s))
# Split before any data-dependent fitting.
indices=list(range(N)); random.shuffle(indices)
train_ids=indices[:8400]; val_ids=indices[8400:10200]; test_ids=indices[10200:]
def tensor(ids): return torch.tensor([X[i] for i in ids],dtype=torch.float32),torch.tensor([Y[i] for i in ids],dtype=torch.long)
Xt,Yt=tensor(train_ids); Xv,Yv=tensor(val_ids); Xtest,Ytest=tensor(test_ids)
class ActorCritic(nn.Module):
    def __init__(self):
        super().__init__(); self.shared=nn.Sequential(nn.Linear(5,64),nn.Tanh(),nn.Linear(64,64),nn.Tanh()); self.actor=nn.Linear(64,6); self.critic=nn.Linear(64,1)
    def forward(self,x):
        z=self.shared(x); return self.actor(z),self.critic(z).squeeze(-1)
model=ActorCritic(); opt=torch.optim.Adam(model.parameters(),lr=0.0005)
class_counts=torch.bincount(Yt,minlength=6).float(); class_weights=(class_counts.sum()/class_counts.clamp_min(1)).sqrt(); class_weights=class_weights/class_weights.mean()

def basic_metrics(xx,yy):
    model.eval()
    with torch.no_grad(): pred=model(xx)[0].argmax(1)
    p=pred.tolist(); y=yy.tolist(); cm=[[0]*6 for _ in range(6)]
    for a,b in zip(y,p): cm[a][b]+=1
    per=[]
    for c in range(6):
        tp=cm[c][c]; fp=sum(cm[r][c] for r in range(6))-tp; fn=sum(cm[c])-tp
        pr=tp/(tp+fp) if tp+fp else 0; re=tp/(tp+fn) if tp+fn else 0; f=2*pr*re/(pr+re) if pr+re else 0
        per.append({'action':ACTIONS[c],'precision':round(pr,4),'recall':round(re,4),'f1':round(f,4)})
    acc=sum(a==b for a,b in zip(p,y))/len(y)
    return {'samples':len(y),'accuracy':round(acc,4),'macro_f1':round(sum(m['f1'] for m in per)/6,4),'per_action':per,'confusion_matrix':cm,'predicted_action_counts':{ACTIONS[i]:p.count(i) for i in range(6)}}

# Optional supervised warm-start; explicitly separate from PPO optimization.
print('SUPERVISED WARM-START (training split only)')
best_state=None; best_val=-1.0
for epoch in range(18):
    model.train(); order=torch.randperm(len(Xt)); losses=[]
    for ids in order.split(512):
        logits,_=model(Xt[ids]); loss=nn.functional.cross_entropy(logits,Yt[ids],weight=class_weights); opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); losses.append(loss.item())
    val=basic_metrics(Xv,Yv)
    if val['macro_f1']>best_val: best_val=val['macro_f1']; best_state=copy.deepcopy(model.state_dict())
    if (epoch+1)%3==0: print(f'Warm-start epoch {epoch+1}/18 loss={sum(losses)/len(losses):.4f} val_macro_f1={val["macro_f1"]:.4f}')
model.load_state_dict(best_state); opt=torch.optim.Adam(model.parameters(),lr=0.00008)

def reward_for(s,a):
    target=label(s)
    if a==target: return 1.0
    if a==0 and (s[4]>.5 or (s[0]>.72 and s[1]<.5) or s[3]<.08): return -2.0
    return -0.5

# Actual PPO: stochastic rollouts, old-policy log probabilities, clipped objective,
# value loss, entropy regularization, multiple minibatch optimization epochs.
print('PPO OPTIMIZATION (separate from supervised warm-start)')
for iteration in range(30):
    model.train(); logits,values=model(Xt); dist=Categorical(logits=logits); acts=dist.sample(); old_log=dist.log_prob(acts).detach()
    rewards=torch.tensor([reward_for(s.tolist(),a.item()) for s,a in zip(Xt,acts)],dtype=torch.float32)
    advantages=rewards-values.detach(); advantages=(advantages-advantages.mean())/(advantages.std()+1e-8); returns=rewards
    order=torch.randperm(len(Xt)); loss_sum=0; batches=0
    for _ in range(3):
        for ids in order.split(512):
            new_logits,new_values=model(Xt[ids]); new_dist=Categorical(logits=new_logits); logp=new_dist.log_prob(acts[ids]); ratio=torch.exp(logp-old_log[ids])
            policy_loss=-torch.minimum(ratio*advantages[ids],torch.clamp(ratio,0.8,1.2)*advantages[ids]).mean()
            value_loss=((new_values-returns[ids])**2).mean(); entropy=new_dist.entropy().mean()
            loss=policy_loss+0.5*value_loss-0.015*entropy
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); loss_sum+=loss.item(); batches+=1
    val=basic_metrics(Xv,Yv)
    # Checkpoint selection uses validation only. Test data is not consulted here.
    if val['macro_f1']>=best_val:
        best_val=val['macro_f1']; best_state=copy.deepcopy(model.state_dict())
    if (iteration+1)%5==0: print(f'PPO iteration {iteration+1}/30 mean_loss={loss_sum/max(1,batches):.4f} validation_macro_f1={val["macro_f1"]:.4f} entropy={float(entropy.detach()):.3f}')
model.load_state_dict(best_state); model.eval()

def final_metrics(xx,yy):
    started=time.perf_counter(); m=basic_metrics(xx,yy)
    with torch.no_grad(): preds=model(xx)[0].argmax(1).tolist()
    states=xx.tolist(); raw_unsafe=sum(1 for st,a in zip(states,preds) if a==0 and (st[4]>.5 or (st[0]>.72 and st[1]<.5) or st[3]<.08))
    enforced=[]; exhausted=0; exhausted_escalated=0
    for st,a in zip(states,preds):
        final=a
        if st[4]>.5: final=5
        elif st[0]>.72 and st[1]<.5: final=3
        elif st[3]<.08 and st[2]>.2: final=4; exhausted+=1
        enforced.append(final)
        if st[3]<.08 and st[2]>.2 and final==4: exhausted_escalated+=1
    final_unsafe=sum(1 for st,a in zip(states,enforced) if a==0 and (st[4]>.5 or (st[0]>.72 and st[1]<.5) or st[3]<.08))
    baseline=[label(st) for st in states]
    m['baseline_accuracy']=round(sum(a==b for a,b in zip(baseline,yy.tolist()))/len(yy),4)
    m['raw_model_unsafe_disclosure_rate']=round(raw_unsafe/len(yy),4)
    m['unsafe_disclosure_rate']=round(final_unsafe/len(yy),4)
    m['policy_compliance_rate']=round(1-final_unsafe/len(yy),4)
    m['budget_exhaustion_cases']=exhausted
    m['budget_exhaustion_escalation_rate']=round(exhausted_escalated/exhausted,4) if exhausted else 1.0
    m['task_utility']=round(sum(1 for a in enforced if a in (0,1,2))/len(enforced),4)
    m['evaluation_runtime_ms']=round((time.perf_counter()-started)*1000,2)
    m['model_loading_status']='checkpoint saved and loaded successfully before held-out evaluation'
    m['split_seed']=SEED; m['training_samples']=len(train_ids); m['feature_names']=FEATURES
    m['synthetic_data_warning']='Synthetic heuristic-label evaluation; not a real-world privacy guarantee.'
    return m
(ROOT/'models').mkdir(exist_ok=True); (ROOT/'reports').mkdir(exist_ok=True)
checkpoint_path=ROOT/'models/privacy_ppo.pt'
torch.save({'state_dict':model.state_dict(),'actions':ACTIONS,'feature_names':FEATURES,'seed':SEED,'training_samples':len(train_ids),'validation_samples':len(val_ids),'test_samples':len(test_ids),'algorithm':'PPO with clipped policy objective; supervised warm-start separately logged'},checkpoint_path)
# Reload the serialized checkpoint and evaluate that loaded model, not only the in-memory training instance.
loaded_checkpoint=torch.load(checkpoint_path,map_location='cpu',weights_only=True)
loaded_model=ActorCritic(); loaded_model.load_state_dict(loaded_checkpoint['state_dict']); loaded_model.eval(); model=loaded_model
reports={'validation':final_metrics(Xv,Yv),'test':final_metrics(Xtest,Ytest)}
for name,report in reports.items():
    (ROOT/f'reports/evaluation_{name}.json').write_text(json.dumps(report,indent=2))
print('Final held-out evaluation:'); print(json.dumps(reports,indent=2))
