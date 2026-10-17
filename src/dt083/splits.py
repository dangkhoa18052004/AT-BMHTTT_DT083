import numpy as np
import pandas as pd

def assert_no_leakage(frame):
    if (frame.groupby('source_group_id').split.nunique()>1).any(): raise ValueError('Group leakage')
    for name in ['source_sha256','derived_sha256','segment_sha256']:
        if name in frame and (frame.groupby(name).split.nunique()>1).any(): raise ValueError(f'Content leakage: {name}')

def make_splits(inventory,seed):
    groups=inventory[['source_group_id']].drop_duplicates().source_group_id.sort_values().to_numpy()
    if len(groups)<5: raise ValueError('At least five source groups required')
    rng=np.random.default_rng(seed); rng.shuffle(groups)
    n=len(groups); n_train=max(1,int(round(n*.6))); n_val=max(1,int(round(n*.2)))
    n_train=min(n_train,n-n_val-1)
    assignments={g:'train' if i<n_train else 'validation' if i<n_train+n_val else 'test' for i,g in enumerate(groups)}
    frame=inventory.copy(); frame['split']=frame.source_group_id.map(assignments)
    assert_no_leakage(frame)
    return frame
