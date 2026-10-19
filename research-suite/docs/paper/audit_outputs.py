"""Independently reconcile saved predictions with aggregate confusion/AP results."""
from pathlib import Path
import hashlib,json,gzip
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'results/validation'
checks=[]
def check(y,p,cut,r,label):
 y=np.array(y);p=np.array(p);f=p>=cut
 expected={'average_precision':float(average_precision_score(y,p)),'roc_auc':float(roc_auc_score(y,p)),'recall':float(f[y==1].mean()),'false_positive_rate':float(f[y==0].mean())}
 for k,v in expected.items():
  if not np.isclose(v,r[k],rtol=0,atol=1e-12):raise ValueError(label+': '+k)
 c={'tn':int(((y==0)&~f).sum()),'fp':int(((y==0)&f).sum()),'fn':int(((y==1)&~f).sum()),'tp':int(((y==1)&f).sum())}
 if c!=r['confusion']:raise ValueError(label+': confusion')
 checks.append(label)
s=json.loads((D/'external-support-scores.json').read_text());r=json.loads((D/'external-support.json').read_text())
assert len(set(x['source_id'] for x in s['records']))==150
assert len(s['labels'])==900 and sum(s['labels'])==160
for row in r['experiments']:
 name=row['policy'];source=row['source_policy']
 p=s['lexical_by_source'][source] if name=='learned_lexical' else s[name] if name in ['bounded_nli','coverage_nli'] else [int(name=='review_all')]*900
 check(s['labels'],p,row['threshold'],row,source+'/'+name)
packed=json.loads(gzip.decompress((D/'visual-phishing-scores.json.gz').read_bytes()));v=[dict(seed=f['seed'],ids=f['ids'],groups=f['groups'],labels=f['labels'],policy=name,**scores) for f in packed['splits'] for name,scores in f['policies'].items()];r=json.loads((D/'visual-phishing.json').read_text())
for row in r['experiments']:
 score=next(x for x in v if x['seed']==row['seed'] and x['policy']==row['policy'])
 check(score['labels'],score['risk'],score['threshold'],row,str(row['seed'])+'/'+row['policy'])
 for other in [x for x in v if x['seed']==row['seed']]:assert other['ids']==score['ids'] and other['labels']==score['labels']
report={'status':'passed','reconciled_policies':len(checks),'checks':checks,'tolerance':1e-12,'scope':'independent metric/confusion recomputation from saved risk vectors, not new labels or independent peer review','file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'external-support.json',D/'external-support-scores.json',D/'visual-phishing.json',D/'visual-phishing-scores.json.gz']}}
(D/'output-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
