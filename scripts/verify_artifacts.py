"""Read-only audit of the corpus, manifests, locks and fair evaluation rows."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
import numpy as np
from dt083.common import confined, sha256, dump_json
from dt083.corpus import validate_inventory
from dt083.splits import assert_no_leakage
from dt083.features import ALL_FEATURES
from dt083.learning import select_threshold

ROOT=Path(__file__).resolve().parents[1]

def audit(run):
    root=ROOT/'runs'/run
    source=pd.read_csv(root/'data/manifests/inventory.csv'); validate_inventory(root,source)
    derived=pd.read_csv(root/'data/manifests/derived.csv')
    for row in derived.to_dict('records'):
        if sha256(confined(root,row['path']).read_bytes())!=row['derived_sha256']: raise ValueError('Corrupt derived file')
    segments=pd.read_csv(root/'data/features/segments.csv')
    if not np.isfinite(segments[ALL_FEATURES].to_numpy()).all(): raise ValueError('Nonfinite features')
    if (segments.length!=segments.segment_kib*1024).any(): raise ValueError('Unexpected segment length')
    config=json.loads((root/'results/config.json').read_text())
    for seed in config['seeds']:
        split=pd.read_csv(root/f'data/manifests/splits_{seed}.csv')
        groups=split[['source_group_id','split']].drop_duplicates()
        merged=segments.merge(groups,on='source_group_id',validate='many_to_one'); assert_no_leakage(merged)
        derived_seed=pd.read_csv(root/f'data/manifests/derived_seed_{seed}.csv'); assert_no_leakage(derived_seed)
    pred=pd.read_csv(root/'results/test_predictions.csv')
    for (seed,kib,policy),part in pred.groupby(['seed','segment_kib','policy']):
        reference=set(part.loc[part.model=='B0','segment_id'])
        if any(set(part.loc[part.model==model,'segment_id'])!=reference for model in ['B1','M1','M2']): raise ValueError('Unequal test samples')
        locked=json.loads((root/f'results/locked_{seed}_{kib}_{policy}.json').read_text())
        split=pd.read_csv(root/f'data/manifests/splits_{seed}.csv')
        assigned=segments.merge(split[['source_group_id','split']].drop_duplicates(),on='source_group_id',validate='many_to_one')
        context=assigned[(assigned.segment_kib==kib)&(assigned.policy==policy)&assigned.label.isin([0,1])]
        train=context[context.split=='train']; validation=context[context.split=='validation']
        values=np.sort(train.entropy.unique()); candidates=np.unique(np.r_[values-1e-12,values+1e-12])
        if len(candidates)>1000: candidates=np.quantile(candidates,np.linspace(0,1,1000))
        threshold,_=select_threshold(validation.label,validation.entropy,candidates)
        if threshold!=locked['models']['B0']['threshold']: raise ValueError('Threshold implementation differs from saved validation selection')
        for name,item in locked['models'].items():
            if sha256((root/f'models/{seed}_{kib}_{policy}_{name}.joblib').read_bytes())!=item['model_sha256']: raise ValueError('Model changed after lock')
    metrics=pd.read_csv(root/'results/metrics_raw.csv')
    summary=pd.read_csv(root/'results/metrics_summary.csv')
    if not (summary.n_seeds==len(config['seeds'])).all(): raise ValueError('Missing seeds')
    for row in metrics.to_dict('records'):
        if row['n_samples']!=sum(row[k] for k in ['tn','fp','fn','tp']): raise ValueError('Confusion counts mismatch')
        if abs(row['fpr_archive']-row['fp']/(row['tn']+row['fp']))>1e-12: raise ValueError('Incorrect FPR')
    return {'run':run,'source_files':len(source),'source_groups':int(source.source_group_id.nunique()),
            'derived_files':len(derived),'segments_all_labels_sizes_policies':len(segments),
            'evaluations':len(metrics),'fair_test_sample_sets':True,'sources_unchanged':True,
            'hash_checks':True,'no_group_or_content_leakage':True,'model_lock_checks':True,
            'optimized_B0_threshold_matches_saved_validation':True}

def main():
    results=[audit(name) for name in ['smoke','full']]
    dump_json(ROOT/'results/verification.json',results)
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
