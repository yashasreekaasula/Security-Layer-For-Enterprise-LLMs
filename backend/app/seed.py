import sys, random, csv, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .db import Base, engine, SessionLocal, ROOT
from .models import Employee, Project, Document, PrivacyBudget

random.seed(20261012)
DEPTS=['Engineering','Human Resources','Finance','Information Technology','Operations','Sales','Marketing','Legal','Research & Development','Procurement']
TITLES={'Engineering':['Software Engineer','Staff Engineer','Engineering Manager','QA Engineer','Platform Engineer'],'Human Resources':['HR Generalist','Talent Partner','People Operations Manager','Compensation Analyst'],'Finance':['Financial Analyst','Controller','Accounts Payable Specialist','Finance Manager'],'Information Technology':['IT Support Engineer','Security Analyst','Cloud Administrator','IT Manager'],'Operations':['Operations Analyst','Program Manager','Operations Lead'],'Sales':['Account Executive','Sales Operations Analyst','Regional Sales Manager'],'Marketing':['Content Strategist','Product Marketing Manager','Campaign Analyst'],'Legal':['Legal Counsel','Compliance Analyst','Contract Manager'],'Research & Development':['Research Scientist','ML Engineer','Research Program Manager'],'Procurement':['Procurement Analyst','Vendor Manager','Sourcing Specialist']}
FIRST=['Aarav','Aditi','Ananya','Arjun','Diya','Ishaan','Kavya','Meera','Neha','Rohan','Saanvi','Vihaan','Priya','Rahul','Ira','Kabir','Maya','Dev','Nisha','Aditya','Sofia','Noah','Emma','Liam','Olivia','Amir','Zara','Ethan','Mila','Leo','Ibrahim','Aanya','Vikram','Tara','Kiran','Samira','Reyansh','Myra','Anika','Dhruv']
LAST=['Sharma','Reddy','Iyer','Patel','Nair','Rao','Gupta','Mehta','Khan','Das','Kapoor','Menon','Joshi','Verma','Pillai','Kulkarni','Singh','Chopra','Fernandes','Thomas','Bose','Malhotra','Mishra','Bhat','Shetty','Desai','Roy','Saxena','Banerjee','Naidu']
PROJECTS=['Bumblebee','Firefly','Northstar','Atlas','Orion','Meridian','Evergreen','Helios','Keystone','Bluebird','Summit','Apollo','Cedar','Falcon','Harbor','Juniper','Lighthouse','Monarch','Nimbus','Oakline','Pioneer','Quartz','Redwood','Solstice','Trailblazer','Vertex']
DOC_TYPES=['Policy','Standard Operating Procedure','Project Status Report','Meeting Summary','Technical Design','Product Requirements','Employee FAQ','Security Advisory','Procurement Brief','Operations Playbook','Research Note','Release Readiness Review','Incident Postmortem','Quarterly Business Review','Training Guide','Risk Register','Architecture Decision Record','Vendor Assessment','Data Dictionary','Audit Summary']
SUBJECTS=['data minimization','access reviews','incident response','onboarding workflow','quarterly planning','service reliability','customer feedback','vendor governance','budget controls','release management','retention schedule','business continuity','quality assurance','model monitoring','identity lifecycle','change management','project dependencies','capacity planning','employee experience','security awareness','deployment pipeline','records management','risk assessment','forecast assumptions','operational handover']
VERBS=['defines','documents','reviews','standardizes','tracks','explains','evaluates','coordinates','measures','governs','records','improves']
CONTEXTS=['for the current planning cycle','under the approved operating model','for teams in the relevant business unit','with quarterly review by the accountable owner','subject to access approval and retention controls','using the current internal workflow','for the pilot and controlled rollout','in line with the documented service objectives','with evidence recorded in the project workspace','after review by the process owner']
ROLES=['Employee','HR','Finance','IT','Project Manager','Executive','Administrator']

def gen_employees(n=3000):
    out=[]
    for i in range(1,n+1):
        dept=DEPTS[(i-1)%len(DEPTS)]
        prefix={'Human Resources':'hr','Finance':'fin','Information Technology':'it'}.get(dept,'emp')
        seq=(i-1)//len(DEPTS)+1
        email=f'{prefix}{seq:03d}@{ {'Human Resources':'hr','Finance':'fin','Information Technology':'it'}.get(dept,"emp") }.company.in'
        # The department namespace plus deterministic sequence prevents collisions.
        if dept not in ('Human Resources','Finance','Information Technology'): email=f'emp{i:04d}@emp.company.in'
        role={'Human Resources':'HR','Finance':'Finance','Information Technology':'IT'}.get(dept,'Employee')
        if i%53==0: role='Project Manager'
        if i%127==0: role='Executive'
        out.append({'employee_id':f'EMP{i:05d}','full_name':f'{FIRST[(i*7)%len(FIRST)]} {LAST[(i*11)%len(LAST)]}','email':email,'dob':(datetime(1970,1,1)+timedelta(days=(i*97)%15000)).date().isoformat(),'department':dept,'title':TITLES[dept][i%len(TITLES[dept])],'role':role,'assigned_projects':[f'Project {PROJECTS[(i-1)%len(PROJECTS)]}'] if role=='Project Manager' else []})
    # Email namespaces are made collision-free by deterministic employee IDs in the actual registry.
    seen=set()
    for i,e in enumerate(out,1):
        if e['email'] in seen: e['email']=f'emp{i:05d}@emp.company.in'
        seen.add(e['email'])
    return out

def doc_content(project, dept, typ, subject, idx):
    owner=f'{FIRST[idx%len(FIRST)]} {LAST[(idx*3)%len(LAST)]}'
    reviewer=f'{FIRST[(idx*5+3)%len(FIRST)]} {LAST[(idx*7+2)%len(LAST)]}'
    period=f'FY{2024 + (idx % 3)} Q{1 + (idx % 4)}'
    metric=random.choice(['control coverage','completion rate','mean time to resolve','forecast variance','first-pass quality','service availability','review turnaround'])
    target=random.choice(['within two business days','before the next release gate','at the monthly governance review','within the approved retention window','before the next planning cycle'])
    risks=random.choice(['dependency ownership is unclear','the evidence set is incomplete','a downstream approval is pending','capacity is constrained during peak periods','the control owner has changed'])
    decision=random.choice(['proceed with the controlled pilot','hold rollout until evidence is complete','retain the existing control and review next quarter','split the work into independently verifiable milestones','escalate the exception to the accountable owner'])
    base=f"Record ID: SYN-{idx+1:06d}\nProject: Project {project}\nFunction: {dept}\nDocument owner: {owner}\nReview partner: {reviewer}\nSynthetic record: yes"
    if typ=='Policy':
        body=f"Purpose and scope\nThis policy establishes the expected control for {subject} within Project {project} and the {dept} function. It applies to employees and approved contractors who perform the described workflow.\n\nMandatory requirements\nCollect and retain only information needed for a documented business purpose. Assign an accountable owner, use approved repositories, restrict access by role, and record the review date. Requests that exceed the stated purpose must be paused until approval is recorded.\n\nExceptions and evidence\nExceptions require a reason, named approver, expiry date, and compensating control. Evidence is reviewed {target}. The owner records decisions, remediation, and follow-up actions in the project workspace.\n\nReview cadence\nThe policy owner ({owner}) reviews the control with {reviewer}. Suggested measure: {metric}. This synthetic example does not establish real-company policy."
    elif typ=='Standard Operating Procedure':
        body=f"Purpose\nUse this procedure when a team needs to manage {subject} for Project {project}.\n\nInputs and prerequisites\nConfirm the current request, responsible owner, access scope, required approvals, and the latest approved work instruction.\n\nProcedure\n1. Validate scope and record the request reference.\n2. Confirm permissions and identify affected teams.\n3. Complete the approved workflow and capture evidence.\n4. Review exceptions with {reviewer}; do not bypass a required control.\n5. Notify the owner and record the outcome.\n\nCompletion criteria\nThe task is complete when evidence is attached, outstanding actions have owners, and the result is reviewed {target}. Owner: {owner}."
    elif typ=='Project Status Report':
        body=f"Reporting period: {period}\nExecutive summary\nProject {project} is a synthetic initiative addressing {subject}. Current status: {['On Track','In Progress','At Risk','Planning'][idx%4]}. The status is illustrative and not a real company commitment.\n\nMilestones\n- Scope and ownership: documented.\n- Dependencies: {['mapped','under review','awaiting confirmation'][idx%3]}.\n- Validation evidence: {['initial sample complete','in progress','scheduled for the next review'][idx%3]}.\n\nRisks and decisions\nPrimary risk: {risks}. Proposed decision: {decision}.\n\nNext steps\n{owner} coordinates the next checkpoint {target}; {reviewer} reviews evidence and escalates blockers. Measure progress using {metric}."
    elif typ=='Meeting Summary':
        body=f"Meeting: Project {project} {subject.title()} Review\nDate: {(datetime(2025,1,1)+timedelta(days=idx%600)).date().isoformat()}\nParticipants: {owner} (owner), {reviewer} (review partner), and representatives from {dept}.\n\nAgenda\nReview open actions, dependencies, control evidence, and upcoming milestones.\n\nDiscussion\nThe group reviewed {subject}. The main concern was that {risks}. Participants agreed to document assumptions and keep restricted information in approved systems.\n\nDecisions\nThe provisional decision is to {decision}. This decision must be revisited if the scope or risk profile changes.\n\nAction items\n- {owner}: update the work record {target}.\n- {reviewer}: verify the evidence and report exceptions."
    elif typ=='Technical Design':
        body=f"Problem statement\nProject {project} needs a maintainable approach to {subject}. The design must preserve traceability, availability, least privilege, and clear ownership.\n\nProposed components\n1. Request interface validates inputs and emits structured events.\n2. Service layer enforces policy and delegates domain logic.\n3. Persistence layer stores versioned records with indexed identifiers.\n4. Monitoring layer measures {metric} and surfaces actionable alerts.\n\nData flow and controls\nValidate identity before loading protected records; filter access before building downstream context; record a minimal audit event after the decision. Fail closed if authorization cannot be established.\n\nTrade-offs\nThe design favors a small, testable service boundary over implicit cross-service access. Owner: {owner}. Review partner: {reviewer}."
    elif typ=='Product Requirements':
        body=f"User problem\nUsers need a predictable workflow for {subject} in Project {project}, with understandable status and clear next actions.\n\nFunctional requirements\n- Validate required inputs and reject malformed requests.\n- Show the responsible owner and current workflow state.\n- Restrict protected fields according to role and purpose.\n- Preserve source references for material decisions.\n\nAcceptance criteria\nA valid request completes with a traceable outcome; an unauthorized request reveals no protected content; an incomplete request explains what is missing.\n\nNon-functional requirements\nMaintain accessible controls, measurable {metric}, and a review path {target}. Product owner: {owner}."
    elif typ=='Employee FAQ':
        body=f"Question: How should employees handle {subject}?\n\nAnswer\nStart with the approved internal workflow and confirm that the requested information is needed for the stated purpose. Use the minimum necessary fields, keep files in an approved workspace, and check recipient permissions before sharing.\n\nIf the request is unclear\nAsk the process owner for clarification. If a request involves restricted information, a personal-data disclosure, or a possible security incident, stop and use the designated approval or escalation route.\n\nWhere to get help\nContact the {dept} process owner ({owner}) or review the current SOP. This FAQ is synthetic and should be replaced by an approved company answer before production use."
    elif typ=='Security Advisory':
        body=f"Advisory scope\nThis synthetic advisory covers risks related to {subject} in Project {project}.\n\nPotential indicators\nUnexpected access prompts, unfamiliar service identities, unusual export volume, unapproved configuration changes, or missing audit evidence. These are illustrative indicators, not a report of a real incident.\n\nResponse steps\nPreserve relevant event IDs, stop unauthorized transfers, rotate exposed credentials through the approved secret manager, and notify the security owner. Do not paste credentials into tickets or chat.\n\nContainment and follow-up\n{owner} coordinates containment; {reviewer} validates restoration. Track {metric} and close the advisory only after evidence and approvals are recorded."
    elif typ=='Procurement Brief':
        body=f"Business need\nThe {dept} team requires a controlled approach to {subject} for Project {project}.\n\nEvaluation criteria\nAssess functional fit, access controls, data location, retention, integration effort, support model, exit provisions, and total cost assumptions. Require evidence for vendor claims and document any unresolved gap.\n\nApproval workflow\nProcurement validates the shortlist, Finance reviews commercial assumptions, Legal checks terms, and Security evaluates data handling where applicable. No commitment should be made before required approvals.\n\nRecommendation\nProceed only if the evidence addresses {risks}. Owner: {owner}. Review timing: {target}."
    elif typ=='Operations Playbook':
        body=f"Trigger\nUse this playbook when the team observes a deviation in {subject} or prepares a planned operational change for Project {project}.\n\nRunbook\n1. Confirm the alert or request and identify the service owner.\n2. Check recent changes and dependencies.\n3. Apply the approved diagnostic sequence; avoid unreviewed destructive actions.\n4. Communicate status to affected stakeholders.\n5. Validate recovery against the success criteria and attach evidence.\n\nRollback and escalation\nIf service health worsens, revert using the documented rollback and contact {reviewer}. Success is measured by {metric}. Owner: {owner}."
    elif typ=='Research Note':
        body=f"Research question\nWhich approach improves {subject} for Project {project} without increasing unnecessary disclosure or operational complexity?\n\nMethod\nCompare a baseline workflow with a controlled alternative using a fixed evaluation protocol, consistent inclusion criteria, and documented assumptions.\n\nObservations\nEarly synthetic observations suggest the main variable is {['input quality','review consistency','dependency readiness','coverage of edge cases'][idx%4]}. These observations are illustrative and are not validated scientific results.\n\nLimitations and next experiment\nThe sample may not represent production conditions. Repeat with held-out cases, document negative results, and review the measurement of {metric}. Research owner: {owner}."
    elif typ=='Release Readiness Review':
        body=f"Release candidate: Project {project} / {subject.title()}\nReadiness decision: {['Conditional Go','Needs Follow-up','Go for Controlled Pilot'][idx%3]} (synthetic example).\n\nRelease gates\n- Requirements and owner sign-off: tracked.\n- Test evidence and known limitations: attached to the release record.\n- Security and permission checks: reviewed.\n- Monitoring, rollback, and support coverage: confirmed before deployment.\n\nOpen items\nThe current concern is that {risks}. The release owner must resolve or explicitly accept the risk before proceeding.\n\nGo/no-go\nRecommended next step: {decision}. Review checkpoint: {target}. Owner: {owner}."
    elif typ=='Incident Postmortem':
        body=f"Incident summary\nSynthetic exercise: a workflow related to {subject} in Project {project} did not meet its expected control. No real incident or customer impact is represented.\n\nTimeline\nDetection: monitoring or a reviewer noticed an exception. Triage: the owner assessed scope. Containment: access and workflow changes were paused. Recovery: the normal control was restored after verification.\n\nContributing factors\nThe exercise highlights that {risks}. Root-cause hypothesis: ownership and evidence requirements were not sufficiently explicit.\n\nCorrective actions\n{owner} clarifies the runbook; {reviewer} validates the change; the team tracks {metric} and confirms closure {target}."
    elif typ=='Quarterly Business Review':
        body=f"Review period: {period}\nSummary\nProject {project} reviewed progress on {subject} for the {dept} function. The figures below are synthetic illustrative measures, not real company performance.\n\nOperational scorecard\n- Workflow completion: {70+(idx%25)}% against a synthetic target of 90%.\n- Review turnaround: {1+(idx%5)} business days.\n- Control evidence coverage: {75+(idx%20)}%.\n- Primary measure: {metric}.\n\nDiscussion\nProgress is influenced by whether {risks}. The team should avoid interpreting a single metric without scope, period, and denominator.\n\nActions\nConfirm assumptions, assign remediation owners, and revisit the forecast {target}. Facilitator: {owner}."
    elif typ=='Training Guide':
        body=f"Learning objectives\nAfter this guide, a team member should be able to describe {subject}, identify the responsible owner, and recognize when approval is required.\n\nLearning sequence\n1. Read the current policy and explain its purpose.\n2. Walk through the approved workflow using synthetic examples.\n3. Practice identifying unnecessary data fields and access mismatches.\n4. Record questions and request feedback from {reviewer}.\n\nKnowledge check\nWhat evidence demonstrates completion? Who approves an exception? What should happen if the request is outside the documented purpose?\n\nCompletion\nThe learner records the result and schedules a refresher {target}. Trainer: {owner}."
    elif typ=='Risk Register':
        body=f"Risk ID: RSK-{idx+1:06d}\nRisk statement\nA weakness in {subject} could affect Project {project} if {risks}.\n\nAssessment\nLikelihood: {['Low','Medium','High'][idx%3]}. Impact: {['Moderate','Major','Minor'][idx%3]}. These are synthetic ratings for demonstration only.\n\nMitigation\nClarify ownership, reduce unnecessary access, add a measurable control, test failure paths, and document residual risk. Contingency: pause the workflow and escalate to the accountable manager.\n\nOwnership and review\nRisk owner: {owner}. Reviewer: {reviewer}. Track {metric}; review {target}."
    elif typ=='Architecture Decision Record':
        body=f"ADR: Project {project} — {subject.title()}\nStatus: Proposed synthetic decision\n\nContext\nThe team needs a consistent approach to {subject}, with explicit security boundaries and maintainable operations.\n\nOptions considered\nA) Keep logic embedded in the user interface. B) Centralize validation and policy in the backend. C) Delegate decisions to a service with explicit contracts.\n\nDecision\nPrefer a backend-enforced service boundary with documented APIs, server-derived identity, and testable policy functions. This reduces reliance on client behavior.\n\nConsequences\nThe approach adds implementation and monitoring work but improves traceability. Owner: {owner}. Revisit when requirements or {metric} materially change."
    elif typ=='Vendor Assessment':
        body=f"Vendor review: Project {project} / {subject.title()}\n\nAssessment dimensions\nSecurity controls, privacy and retention, reliability, integration complexity, accessibility, support responsiveness, contract terms, and exit portability. Require evidence rather than relying on marketing statements.\n\nFindings\nThe review needs further evidence regarding {risks}. A vendor should not receive production data until data-processing terms, access boundaries, and deletion behavior are reviewed.\n\nRecommendation\nStatus: {['Pending Evidence','Conditionally Suitable','Further Review Required'][idx%3]}. Owner: {owner}. Reviewer: {reviewer}. Next checkpoint: {target}."
    elif typ=='Data Dictionary':
        body=f"Dataset: Project {project} / {subject.title()}\n\nField definitions\n- record_id: string; stable synthetic identifier; used for traceability.\n- owner_id: string; employee reference; access controlled.\n- status: enum; approved workflow state.\n- created_at: timestamp; event creation time.\n- review_note: text; exclude secrets and unnecessary personal data.\n\nGovernance\nEach field requires a business purpose, classification, permitted consumers, retention period, and validation rule. Do not add attributes solely because they are available.\n\nOwnership\nData steward: {owner}. Review partner: {reviewer}. Review schema changes {target}."
    elif typ=='Audit Summary':
        body=f"Audit scope\nThis synthetic audit summary samples controls for {subject} in Project {project}. It is not an actual audit opinion.\n\nControl objective\nVerify that access follows approved roles, records have accountable owners, and evidence supports decisions.\n\nSample observations\n- Control design: documented.\n- Evidence quality: {['satisfactory for the sample','requires follow-up','partially complete'][idx%3]}.\n- Exceptions: {['none in this synthetic sample','one illustrative exception','review pending'][idx%3]}.\n\nFollow-up\n{owner} owns remediation; {reviewer} validates closure. Track {metric}, retain only necessary evidence, and report unresolved exceptions {target}."
    else:
        body=f"{typ} for Project {project}\n\nThis synthetic record covers {subject} for the {dept} function. The owner documents the purpose, scope, responsibilities, evidence requirements, and review cadence. The team should verify permissions, record decisions, assign follow-up actions, and escalate exceptions. Owner: {owner}. Review partner: {reviewer}. Review {target}."
    return base+'\n\n'+body+'\n\nSynthetic-data notice\nThis record is generated for the Company Copilot demo. People, operational states, dates, and metrics are fictional; do not treat it as a real-company statement.'

def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 3000; nd=int(sys.argv[2]) if len(sys.argv)>2 else 50000
    (ROOT/'data'/'employees').mkdir(parents=True,exist_ok=True); (ROOT/'data'/'generated').mkdir(parents=True,exist_ok=True)
    Base.metadata.create_all(engine)
    employees=gen_employees(n)
    with open(ROOT/'data/employees/employees.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(employees[0])); w.writeheader(); w.writerows(employees)
    try:
        import pandas as pd
        pd.DataFrame(employees).to_excel(ROOT/'data/employees/employee_directory.xlsx',index=False)
    except Exception as e: print('Excel export warning:',e)
    with SessionLocal() as db:
        if db.query(Employee).count()==0:
            db.add_all([Employee(**e,registered=False,approved=True) for e in employees]); db.flush()
        if db.query(Project).count()==0:
            for i,p in enumerate(PROJECTS):
                dept=DEPTS[i%len(DEPTS)]
                db.add(Project(name=f'Project {p}',department=dept,status=['In Progress','Planning','Pilot','On Track'][i%4],summary=f'{p} is a synthetic enterprise initiative focused on {SUBJECTS[i%len(SUBJECTS)]}, with milestones, accountable owners, operational controls, and documented review cadence.'))
            db.flush()
        if db.query(Document).count()==0:
            docs=[]
            for i in range(nd):
                p=PROJECTS[i%len(PROJECTS)]; dept=DEPTS[(i//len(PROJECTS))%len(DEPTS)]; typ=DOC_TYPES[(i//7)%len(DOC_TYPES)]; subject=SUBJECTS[(i//3)%len(SUBJECTS)]
                # Explicit cross-company policy/FAQ documents help general policy retrieval.
                if i%101==0: dept='Company'; subject='data minimization'
                cls=['Public','Internal','Confidential','Restricted'][0 if i%19==0 else 3 if i%97==0 else 2 if i%17==0 else 1]
                allowed=['Employee','Project Manager','Executive'] if cls=='Internal' else ['HR'] if dept=='Human Resources' else ['Finance'] if dept=='Finance' else ['IT'] if dept=='Information Technology' else ['Project Manager','Executive']
                title=f'{p} | {typ} | {subject.title()} | Record {i+1:05d}'
                content=doc_content(p,dept,typ,subject,i)
                docs.append(Document(document_id=f'DOC-{i+1:06d}',title=title,content=content,department=dept,project=f'Project {p}',classification=cls,allowed_roles=allowed,owner=f'{FIRST[i%len(FIRST)]} {LAST[(i*3)%len(LAST)]}',doc_type=typ,synthetic=True,created_at=datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i%950)))
                if len(docs)>=1000:
                    db.add_all(docs); db.flush(); docs=[]
            if docs: db.add_all(docs)
        db.commit()
        # Export from the database after seeding so repeat runs preserve current registration status.
        registry_fields=['employee_id','full_name','email','dob','department','title','role','assigned_projects','registered','approved']
        registry=[{field:getattr(emp,field) for field in registry_fields} for emp in db.query(Employee).order_by(Employee.employee_id).all()]
        with open(ROOT/'data'/'employees'/'employees.csv','w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=registry_fields); writer.writeheader(); writer.writerows(registry)
        try:
            import pandas as pd
            pd.DataFrame(registry).to_excel(ROOT/'data'/'employees'/'employee_directory.xlsx',index=False)
        except Exception as e: print('Excel registry export warning:',e)
        print(f'Employees in database: {db.query(Employee).count()}')
        print(f'Projects in database: {db.query(Project).count()}')
        print(f'Documents in database: {db.query(Document).count()}')
    print(f'Employee exports: {ROOT / "data/employees"}')
    print(f'Database: {ROOT / "data/company_copilot.db"}')
if __name__=='__main__': main()
