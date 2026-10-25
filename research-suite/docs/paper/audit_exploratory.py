"""Independent saved-output audit; this does not validate scientific conclusions."""
from pathlib import Path
import gzip
import hashlib
import json
import numpy as np
from scipy.stats import rankdata
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'results/validation'
r=json.loads((D/'exploratory-analysis.json').read_text())
p=json.loads(gzip.decompress((D/'exploratory-analysis-resamples.json.gz').read_bytes()))
plan=(ROOT/'docs/paper/EXPLORATORY_ANALYSIS_PLAN.md').read_bytes()
assert hashlib.sha256(plan).hexdigest()==r['plan_sha256']
for name,expected in r['inputs_sha256'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==expected
expected_draws=np.random.default_rng(20261025).integers(0,150,size=(5000,150))
assert np.array_equal(p['draw_indices'],expected_draws)
checks=0
for pop,detail in p['populations'].items():
    rows=detail['rows']; y=np.array([x['label'] for x in rows]); group=np.array([x['source_id'] for x in rows])
    gen=np.array([x['generator'] for x in rows]); length=np.array([x['length'] for x in rows]);nli=np.array([x['nli'] for x in rows])
    fold=np.array([x['fold'] for x in rows]);prob={k:np.array([x[k] for x in rows]) for k in ['M0','M1']}
    assert len(rows)==r['populations'][pop]['n'] and int(y.sum())==r['populations'][pop]['positives']
    for g in set(group):assert len(set(fold[group==g]))==1
    def measure(labels,score):
        if len(set(labels))<2:return np.array([np.nan,np.nan])
        return np.array([average_precision_score(labels,score),roc_auc_score(labels,score)])
    # Original estimates plus 100 fixed, evenly spaced draws. Library oracles are
    # independent of the compact metric implementation used by the run.
    for draw_index in [-1,*np.linspace(0,4999,100,dtype=int).tolist()]:
        ix=np.arange(len(rows)) if draw_index<0 else np.concatenate([np.flatnonzero(group==p['group_ids'][j]) for j in expected_draws[draw_index]])
        ly,ll,ln,lg=y[ix],length[ix],nli[ix],gen[ix]
        lr=np.empty(len(ix));nr=np.empty(len(ix));macro=[];actual={}
        for g in sorted(set(lg)):
            sel=lg==g
            lr[sel]=rankdata(ll[sel],method='average')/sel.sum()
            nr[sel]=rankdata(ln[sel],method='average')/sel.sum()
            value=measure(ly[sel],ll[sel])-measure(ly[sel],ln[sel])
            actual['generator/'+g]=value;macro.append(value)
        actual['raw_length_minus_coverage']=measure(ly,ll)-measure(ly,ln)
        actual['rank_length_minus_coverage']=measure(ly,lr)-measure(ly,nr)
        actual['macro_length_minus_coverage']=np.mean(macro,axis=0)
        actual['increment_M1_minus_M0']=measure(ly,prob['M1'][ix])-measure(ly,prob['M0'][ix])
        for name,value in actual.items():
            saved=r['populations'][pop]['contrasts'][name]
            expected=[saved['ap_difference'],saved['auc_difference']] if draw_index<0 else detail['bootstrap_contrasts'][name][draw_index]
            np.testing.assert_allclose(value,np.array(expected,dtype=float),atol=1e-12,rtol=0,equal_nan=True)
            checks+=1
    for name,samples in detail['bootstrap_contrasts'].items():
        data=np.array(samples,dtype=float);valid=np.isfinite(data).all(axis=1)
        saved=r['populations'][pop]['contrasts'][name]
        assert saved['valid_draws']==int(valid.sum()) and saved['invalid_draws']==5000-int(valid.sum())
        if valid.sum()>=1000:
            ci=np.quantile(data[valid],[.025,.975],axis=0,method='linear')
            np.testing.assert_allclose(ci[:,0],saved['ap_ci95'],atol=1e-14)
            np.testing.assert_allclose(ci[:,1],saved['auc_ci95'],atol=1e-14)
        else:assert saved['ap_ci95'] is None and saved['auc_ci95'] is None
print(f'PASS: {checks} independent point/draw contrasts; all 5,000 draws, CIs, group folds and hashes reconciled. Statistical conclusions are not validated by this audit.')

# Token-rate summaries can be checked without redistributing the source text.
rate=json.loads((D/'token-rate-analysis.json').read_text())
boot=json.loads(gzip.decompress((D/'token-rate-resamples.json.gz').read_bytes()))
for name,summary in rate['generators'].items():
    rows=[x for x in rate['rows'] if x['generator']==name]
    assert len(rows)==summary['n']
    assert sum(x['answer_tokens'] for x in rows)==summary['answer_tokens']
    assert sum(x['annotated_tokens'] for x in rows)==summary['annotated_tokens']
    assert all(0<=x['annotated_tokens']<=x['answer_tokens'] for x in rows)
    np.testing.assert_allclose(summary['ratio_of_totals'],summary['annotated_tokens']/summary['answer_tokens'])
    data=np.array(boot[name],dtype=float);valid=np.isfinite(data).all(axis=1)
    assert valid.sum()==summary['valid_draws']
    np.testing.assert_allclose(np.quantile(data[valid],[.025,.975],axis=0,method='linear'),summary['ci95_columns_slope_p25_p50_p75'])
print('PASS: token totals and saved-fit intervals reconcile; boundary instability remains a scientific limitation.')
