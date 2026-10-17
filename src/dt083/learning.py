import json
import logging
from pathlib import Path
from time import perf_counter
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
from .features import MODEL_FEATURES, matrix
from .common import dump_json, sha256
from .splits import make_splits, assert_no_leakage

def metrics(y,p,groups=None):
    y=np.asarray(y,dtype=int); p=np.asarray(p,dtype=int)
    cm=confusion_matrix(y,p,labels=[0,1])
    negative=int((y==0).sum()); positive=int((y==1).sum())
    return {'precision':float(precision_score(y,p,zero_division=0)),
            'recall':float(recall_score(y,p,zero_division=0)), 'f1':float(f1_score(y,p,zero_division=0)),
            'macro_f1':float(f1_score(y,p,labels=[0,1],average='macro',zero_division=0)),
            'accuracy':float(accuracy_score(y,p)), 'fpr_archive':float(cm[0,1]/negative) if negative else None,
            'tn':int(cm[0,0]),'fp':int(cm[0,1]),'fn':int(cm[1,0]),'tp':int(cm[1,1]),
            'n_samples':len(y),'n_compressed':negative,'n_encrypted':positive,
            'n_source_groups':int(pd.Series(groups).nunique()) if groups is not None else None}

def select_threshold(y,scores,candidates):
    y=np.asarray(y,dtype=int); scores=np.asarray(scores,dtype=float)
    ranked=[]
    for threshold in candidates:
        pred=scores>=threshold
        tp=int(np.sum(pred&(y==1))); fp=int(np.sum(pred&(y==0)))
        fn=int(np.sum(~pred&(y==1))); negative=int(np.sum(y==0))
        denom=2*tp+fp+fn
        f1=2*tp/denom if denom else 0.0
        fpr=fp/negative if negative else 0.0
        ranked.append(((f1,-fpr,-abs(threshold-.5)),float(threshold)))
    _,threshold=max(ranked,key=lambda v:v[0])
    return threshold,metrics(y,scores>=threshold)

def split_stage(root,config):
    inventory=pd.read_csv(root/'data/manifests/inventory.csv',keep_default_na=False)
    for seed in config['seeds']:
        split=make_splits(inventory,seed)
        split.to_csv(root/f'data/manifests/splits_{seed}.csv',index=False)
        derived=pd.read_csv(root/'data/manifests/derived.csv',keep_default_na=False).drop(columns='split')
        derived=derived.merge(split[['source_id','split']],on='source_id',validate='many_to_one')
        assert_no_leakage(derived)
        derived.to_csv(root/f'data/manifests/derived_seed_{seed}.csv',index=False)

def scores_for(bundle,frame):
    values=matrix(frame,bundle['features'])
    if bundle['model_name']=='B0': return values[:,0]
    return bundle['model'].predict_proba(values)[:,1]

def evaluate(root,config):
    segments=pd.read_csv(root/'data/features/segments.csv')
    output=root/'results'; output.mkdir(parents=True,exist_ok=True)
    model_dir=root/'models'; model_dir.mkdir(parents=True,exist_ok=True)
    all_metrics=[]; subgroup=[]; predictions=[]; counts=[]; skipped=[]
    for seed in config['seeds']:
        split=pd.read_csv(root/f'data/manifests/splits_{seed}.csv')
        groups=split[['source_group_id','split']].drop_duplicates()
        assigned=segments.merge(groups,on='source_group_id',validate='many_to_one')
        assert_no_leakage(assigned)
        exclusions=pd.read_csv(root/'data/features/excluded.csv')
        if not exclusions.empty:
            exclusions=exclusions.merge(groups,on='source_group_id',validate='many_to_one')
            excluded_counts=exclusions.groupby(['split','segment_kib','policy','transform','source_type']).size().reset_index(name='excluded_files')
            excluded_counts['seed']=seed; skipped.append(excluded_counts)
        for (kib,policy),data in assigned.groupby(['segment_kib','policy'],sort=True):
            binary=data.loc[data.label.isin([0,1])]
            for split_name,chunk in data.groupby('split'):
                for label,part in chunk.groupby('label'):
                    counts.append(dict(seed=seed,segment_kib=kib,policy=policy,split=split_name,label=label,
                                       n_samples=len(part),n_source_groups=part.source_group_id.nunique(),n_files=part.derived_id.nunique()))
            train=binary.loc[binary.split=='train']; val=binary.loc[binary.split=='validation']; test=binary.loc[binary.split=='test']
            if any(len(part)==0 or part.label.nunique()<2 for part in [train,val,test]):
                logging.warning('Skip insufficient classes seed=%s size=%s policy=%s',seed,kib,policy)
                dump_json(output/f'skipped_{seed}_{kib}_{policy}.json',{'reason':'One split lacks both classes','sizes':{s:len(binary[binary.split==s]) for s in ['train','validation','test']}})
                continue
            candidates={}; locked={}
            # Test rows are not used until every candidate is frozen below.
            for name,features in MODEL_FEATURES.items():
                started=perf_counter()
                model=None
                if name=='B0':
                    values=np.sort(train.entropy.unique())
                    thresholds=np.unique(np.r_[values-1e-12,values+1e-12])
                    if len(thresholds)>1000: thresholds=np.quantile(thresholds,np.linspace(0,1,1000))
                    threshold,validation=select_threshold(val.label,val.entropy,thresholds)
                else:
                    model=RandomForestClassifier(random_state=seed,**config['rf'])
                    model.fit(matrix(train,features),train.label.to_numpy())
                    scores=model.predict_proba(matrix(val,features))[:,1]
                    threshold,validation=select_threshold(val.label,scores,config['score_threshold_candidates'])
                train_s=perf_counter()-started
                identity=f'{seed}_{kib}_{policy}_{name}'
                bundle={'model_name':name,'model':model,'features':features,'threshold':threshold,
                        'seed':seed,'segment_kib':int(kib),'policy':policy,'config':config}
                joblib.dump(bundle,model_dir/f'{identity}.joblib')
                candidates[name]=(bundle,train_s)
                locked[name]={'features':features,'threshold':threshold,'validation_metrics':validation,
                              'rf':config['rf'] if model is not None else None,'model_sha256':sha256((model_dir/f'{identity}.joblib').read_bytes())}
            dump_json(output/f'locked_{seed}_{kib}_{policy}.json',{'selection':'Validation encrypted F1; ties lower FPR then threshold closest to 0.5; RF parameters predeclared',
                       'test_segment_ids_sha256':sha256('\n'.join(test.segment_id).encode()),'models':locked})
            for name,(bundle,train_s) in candidates.items():
                started=perf_counter(); scores=scores_for(bundle,test); predict_s=perf_counter()-started
                pred=(scores>=bundle['threshold']).astype(int)
                result=metrics(test.label,pred,test.source_group_id)
                context={'seed':seed,'segment_kib':int(kib),'policy':policy,'model':name}
                result.update(context,threshold=bundle['threshold'],train_validation_s=train_s,predict_batch_s=predict_s)
                all_metrics.append(result)
                records=test.copy(); records['score']=scores; records['prediction']=pred
                records['seed']=seed; records['model']=name
                predictions.append(records)
                for field in ['source_type','transform']:
                    for value,part in records.groupby(field):
                        subgroup.append({**context,'grouping':field,'value':value,**metrics(part.label,part.prediction,part.source_group_id)})
                originals=data.loc[(data.split=='test')&(data.label==-1)]
                if len(originals):
                    original_scores=scores_for(bundle,originals)
                    flagged=original_scores>=bundle['threshold']
                    subgroup.append({**context,'grouping':'original_supplement','value':'benign',
                                     'n_samples':len(originals),'n_source_groups':originals.source_group_id.nunique(),
                                     'flagged_encrypted_fraction':float(np.mean(flagged))})
            logging.info('Evaluated seed %s, %s KiB, %s (%s test segments)',seed,kib,policy,len(test))
    if not all_metrics: raise ValueError('No valid experiments')
    raw=pd.DataFrame(all_metrics); raw.to_csv(output/'metrics_raw.csv',index=False)
    pd.DataFrame(subgroup).to_csv(output/'metrics_subgroups.csv',index=False)
    pd.concat(predictions,ignore_index=True).to_csv(output/'test_predictions.csv',index=False)
    pd.DataFrame(counts).to_csv(output/'sample_counts.csv',index=False)
    if skipped: pd.concat(skipped,ignore_index=True).to_csv(output/'excluded_by_split.csv',index=False)
    measures=['precision','recall','f1','macro_f1','accuracy','fpr_archive','train_validation_s','predict_batch_s']
    summary=raw.groupby(['segment_kib','policy','model'])[measures].agg(['mean','std'])
    summary.columns=['_'.join(pair) for pair in summary.columns]
    summary=summary.reset_index()
    runs=raw.groupby(['segment_kib','policy','model']).size().reset_index(name='n_seeds')
    summary.merge(runs).to_csv(output/'metrics_summary.csv',index=False)
    return raw
