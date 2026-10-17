import json
from pathlib import Path
import pandas as pd
import pytest
import numpy as np
from dt083.cli import run_pipeline, demo
from dt083.learning import select_threshold, metrics

def test_threshold_uses_supplied_validation():
    threshold,metrics=select_threshold([0,0,1,1],[.1,.3,.6,.9],[.2,.5,.8])
    assert threshold==.5 and metrics['f1']==1

def test_threshold_selection_matches_metric_reference():
    rng=np.random.default_rng(42)
    y=rng.integers(0,2,300); scores=rng.random(300)
    candidates=np.linspace(0,1,101)
    def rank(t):
        result=metrics(y,scores>=t)
        return result['f1'],-(result['fpr_archive'] or 0),-abs(t-.5)
    expected=max(candidates,key=rank)
    chosen,result=select_threshold(y,scores,candidates)
    assert chosen==expected and result==metrics(y,scores>=expected)

def test_smoke_end_to_end(tmp_path):
    config=json.loads((Path(__file__).parents[1]/'configs/smoke.json').read_text())
    # Integration fixture retains the group design but makes CPU cost smaller.
    config.update(text_rows=500,image_sides=[512],max_segments_per_file=1,seeds=[42,123,2026],sampling_policies=['interior'],benchmark_segments=8,benchmark_repeats=1)
    config['rf']['n_estimators']=12
    run_pipeline(tmp_path,config)
    metrics=pd.read_csv(tmp_path/'results/metrics_raw.csv')
    assert len(metrics)==12 and set(metrics.model)=={'B0','B1','M1','M2'}
    assert set(metrics.seed)=={42,123,2026}
    pred=pd.read_csv(tmp_path/'results/test_predictions.csv')
    for seed,rows in pred.groupby('seed'):
        reference=set(rows[rows.model=='B0'].segment_id)
        assert all(set(rows[rows.model==name].segment_id)==reference for name in ['B1','M1','M2'])
    assert (tmp_path/'results/tradeoff.png').exists()
    assert (tmp_path/'results/pipeline_cost.json').exists()
    assert (tmp_path/'results/locked_42_64_interior.json').exists()
    derivatives=pd.read_csv(tmp_path/'data/manifests/derived.csv')
    file=derivatives.query('transform == "aesgcm" and size_bytes >= 73728').iloc[0].path
    result=demo(tmp_path,config,file,'M2',42,64,'interior')
    assert result['status']=='ok' and result['segments']
    tiny=tmp_path/'data/source/tiny.bin'; tiny.write_bytes(b'abc')
    assert demo(tmp_path,config,'data/source/tiny.bin','M2',42,64,'interior')['status']=='too_small'
    with pytest.raises(ValueError): demo(tmp_path,config,'results/config.json','M2',42,64,'interior')
