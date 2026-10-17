"""Selective notebook reproduction on author feature CSVs, NOT grouped evaluation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import ast
import argparse
import json
import zipfile
from time import perf_counter
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from dt083.learning import metrics
from dt083.common import dump_json, environment

ROOT=Path(__file__).resolve().parents[1]

def parse_features(df):
    # Labels explicitly documented in notebook cell 12/39: 0 compressed, 1 encrypted.
    y=df['Filetype'].astype(int)
    if set(y.unique())!={0,1}: raise ValueError('Unexpected Filetype codes')
    x=pd.DataFrame(index=df.index)
    x['Entropy']=df['Entropy'].astype(float)
    x['Jarque-Bera']=df['jarque-bera'].astype(float)
    x['Shapiro-Wilk']=df['shapiro'].astype(float)
    for source,target in [('Block Frequency','Block_freq'),('Frequency','Freq_average'),('Cumulative Sums','Cumu_sum'),('Overlapping Template','Ov_temp')]:
        x[target]=df[source].map(lambda text:sum(float(value) for value in ast.literal_eval(text)[0]))
    x['Chi_score']=(df['Chi-score'].astype(float)<255+22*2).astype(int)
    x['Monobit_']=df.Monobit.map(lambda text:int(all(9725<=int(value)<=10275 for value in json.loads(text))))
    if x.isna().any().any(): raise ValueError('Missing feature values')
    return x,y

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sizes',type=int,nargs='+',default=[64,128,256,512,1024])
    parser.add_argument('--folds',type=int,default=10)
    parser.add_argument('--seeds',type=int,nargs='+',default=[42,123,2026])
    args=parser.parse_args()
    output=ROOT/'results/author_reference'; output.mkdir(parents=True,exist_ok=True)
    raw=[]; predictions=[]; source_audit=[]
    dump_json(output/'protocol.json',{'environment':environment(),'seeds':args.seeds,'folds':args.folds,
        'label_evidence':'Ransomware_clean.ipynb cells 12/39, comments Filetype 0 compressed / 1 encrypted',
        'features':'nine notebook-derived features; gamma_fips=0 and gamma_hedge=2',
        'differences':'stratified shuffled row-level CV, seed 42/123/2026, no global minmax fit (RF does not need scaling); no hyperparameter search; sklearn version differs',
        'limits':'NO source_group_id, source-byte hashes, transform IDs or raw corpus. Cannot establish file independence or end-to-end detection speed. Only reference CSV classification.',
        'rf':{'n_estimators':100,'max_depth':10,'max_features':9,'n_jobs':4},
        'notebook_security':'Parsed values with ast.literal_eval / json.loads; did not execute upstream notebook or eval dataset text.'})
    for kib in args.sizes:
        with zipfile.ZipFile(ROOT/f'references/author/datasets/final{kib}.zip') as arc:
            with arc.open(f'final{kib}.csv') as handle: df=pd.read_csv(handle)
        x,y=parse_features(df)
        # Remove exact feature+label duplicate rows before splitting; source-level duplicates remain unknown.
        keep=~pd.concat([x,y],axis=1).duplicated()
        source_audit.append({'segment_kib':kib,'rows_input':len(df),'exact_feature_label_duplicates_removed':int((~keep).sum()),
                             'rows_evaluated':int(keep.sum()),'byte_size_values':sorted(df[' size'].unique().astype(int).tolist()),
                             'source_group_id_present':False})
        original_rows=df.index[keep].to_numpy(); x=x.loc[keep].reset_index(drop=True); y=y.loc[keep].reset_index(drop=True)
        for seed in args.seeds:
            cv=StratifiedKFold(n_splits=args.folds,shuffle=True,random_state=seed)
            for fold,(train,test) in enumerate(cv.split(x,y)):
                # Upstream Table 4 parameters; max_features=all as notebook cross_validate cells.
                model=RandomForestClassifier(n_estimators=100,max_depth=10,max_features=x.shape[1],random_state=seed,n_jobs=4)
                start=perf_counter(); model.fit(x.iloc[train],y.iloc[train]); train_s=perf_counter()-start
                start=perf_counter(); scores=model.predict_proba(x.iloc[test])[:,1]; prediction_s=perf_counter()-start
                pred=(scores>=.5).astype(int)
                raw.append({'seed':seed,'fold':fold,'segment_kib':kib,'train_s':train_s,'predict_from_csv_s':prediction_s,**metrics(y.iloc[test],pred)})
                predictions.append(pd.DataFrame({'seed':seed,'fold':fold,'segment_kib':kib,'csv_row_index':original_rows[test],
                                                 'label':y.iloc[test].to_numpy(),'score':scores,'prediction':pred}))
            print(f'Completed author CSV {kib} KiB seed {seed}',flush=True)
    frame=pd.DataFrame(raw); frame.to_csv(output/'metrics_folds.csv',index=False)
    per_seed=frame.groupby(['segment_kib','seed'])[['precision','recall','f1','macro_f1','accuracy','fpr_archive']].mean().reset_index()
    per_seed.to_csv(output/'metrics_by_seed.csv',index=False)
    summary=per_seed.groupby('segment_kib')[['precision','recall','f1','macro_f1','accuracy','fpr_archive']].agg(['mean','std'])
    summary.columns=['_'.join(pair) for pair in summary.columns]
    summary.reset_index().to_csv(output/'metrics_summary.csv',index=False)
    pd.concat(predictions,ignore_index=True).to_csv(output/'out_of_fold_predictions.csv',index=False)
    dump_json(output/'quality_audit.json',source_audit)
    dump_json(output/'finished.json',{'sizes':args.sizes,'seeds':args.seeds,'folds':args.folds,'experiments':len(frame)})

if __name__=='__main__': main()
