from time import perf_counter, process_time
import json
import joblib
import numpy as np
import pandas as pd
import psutil
from .features import extract, read_segment, matrix
from .common import dump_json, environment

def values_for(raw,features,zlib_level):
    if features==['entropy']:
        counts=np.bincount(np.frombuffer(raw,dtype=np.uint8),minlength=256)
        p=counts[counts>0]/len(raw)
        return {'entropy':float(-np.sum(p*np.log2(p)))}
    return extract(raw,'recompress_ratio' in features,zlib_level)

def benchmark(root,config):
    predictions=pd.read_csv(root/'results/test_predictions.csv')
    timings=[]
    for (seed,kib,policy,name),part in predictions.groupby(['seed','segment_kib','policy','model']):
        # Same deterministic rows for each model; benchmark work independent of threshold selection.
        samples=part.sort_values('segment_id').head(config['benchmark_segments'])
        bundle=joblib.load(root/f'models/{seed}_{kib}_{policy}_{name}.joblib')
        rows=samples.to_dict('records')
        for row in rows[:config['benchmark_warmup']]:
            raw=read_segment(root,row['path'],row['offset'],row['length'])
            values_for(raw,bundle['features'],config['zlib_level'])
        warm=pd.DataFrame([values_for(read_segment(root,rows[0]['path'],rows[0]['offset'],rows[0]['length']),bundle['features'],config['zlib_level'])])
        if bundle['model'] is not None: bundle['model'].predict_proba(matrix(warm,bundle['features']))
        for repeat in range(config['benchmark_repeats']):
            read_s=feature_s=0.0; features=[]; rss=psutil.Process().memory_info().rss
            begin=perf_counter(); cpu=process_time()
            for row in rows:
                t=perf_counter(); raw=read_segment(root,row['path'],row['offset'],row['length']); read_s+=perf_counter()-t
                t=perf_counter(); features.append(values_for(raw,bundle['features'],config['zlib_level'])); feature_s+=perf_counter()-t
            t=perf_counter(); values=matrix(pd.DataFrame(features),bundle['features'])
            if bundle['model'] is not None: scores=bundle['model'].predict_proba(values)[:,1]
            else: scores=values[:,0]
            _=scores>=bundle['threshold']; predict_s=perf_counter()-t
            elapsed=perf_counter()-begin; cpu_s=process_time()-cpu
            n=len(rows); mib=sum(r['length'] for r in rows)/1024**2
            result={'seed':seed,'segment_kib':int(kib),'policy':policy,'model':name,'repeat':repeat,'n_segments':n,
                    'input_mib':mib,'cpu_seconds':cpu_s,'rss_before_bytes':rss,'rss_after_bytes':psutil.Process().memory_info().rss}
            for stage,seconds in [('read',read_s),('features',feature_s),('predict',predict_s),('end_to_end',elapsed)]:
                result[f'{stage}_s']=seconds; result[f'{stage}_ms_per_segment']=seconds/n*1000
                result[f'{stage}_mib_per_s']=mib/seconds if seconds else None
            timings.append(result)
    raw=pd.DataFrame(timings); raw.to_csv(root/'results/benchmark_raw.csv',index=False)
    measures=[c for c in raw if c.endswith('_ms_per_segment') or c.endswith('_mib_per_s')]
    summary=raw.groupby(['seed','segment_kib','policy','model'])[measures].mean().reset_index()
    summary.to_csv(root/'results/benchmark_by_seed.csv',index=False)
    summary.groupby(['segment_kib','policy','model'])[measures].agg(['mean','std']).to_csv(root/'results/benchmark_summary.csv')
    dump_json(root/'results/benchmark_protocol.json',{'environment':environment(),'clock':'perf_counter',
        'batch_size_max':config['benchmark_segments'],'repeats':config['benchmark_repeats'],
        'warmup_segments':config['benchmark_warmup'],'prediction_warmup':1,'rf_threads':config['rf']['n_jobs'],
        'io_threads':1,'features_threads':1,'selection':'lexicographically sorted held-out binary test IDs; same subset for B0/B1/M1/M2',
        'limits':'Warm OS-cache microbenchmark of read -> features -> batched prediction. Does not include corpus generation/training and is not production ransomware response latency.'})
    return raw
