"""Summarize existing subgroup metrics without changing any test predictions."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def main():
    for run in ['smoke','full']:
        folder=ROOT/'runs'/run/'results'
        frame=pd.read_csv(folder/'metrics_subgroups.csv')
        names=['precision','recall','f1','macro_f1','accuracy','fpr_archive','n_samples','n_source_groups','n_compressed','n_encrypted','flagged_encrypted_fraction']
        summary=frame.groupby(['segment_kib','policy','model','grouping','value'])[names].agg(['mean','std'])
        summary.columns=['_'.join(pair) for pair in summary.columns]
        summary=summary.reset_index()
        counts=frame.groupby(['segment_kib','policy','model','grouping','value']).seed.nunique().reset_index(name='n_seeds')
        summary.merge(counts).to_csv(folder/'metrics_subgroups_summary.csv',index=False)

if __name__=='__main__': main()
