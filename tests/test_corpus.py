import json
import os
import numpy as np
import pandas as pd
import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dt083.transforms import transform, restore, derive
from dt083.splits import make_splits, assert_no_leakage
from dt083.common import confined, sha256
from dt083.corpus import generate, validate_inventory

@pytest.mark.parametrize('kind',['original','zip','gzip','bzip2','aesgcm'])
@pytest.mark.parametrize('raw',[b'',b'hello'*2000,bytes(range(256))*256],ids=['empty','text','uniform'])
def test_round_trips(kind,raw):
    key=AESGCM.generate_key(bit_length=256); nonce=os.urandom(12)
    data,params=transform(raw,kind,key,nonce)
    assert restore(data,kind,params,key)==raw
    if kind=='aesgcm':
        assert len(data)==len(raw)
        assert len(bytes.fromhex(params['tag_hex']))==16

def test_tampering_and_corrupt_archive():
    key=AESGCM.generate_key(bit_length=256); nonce=os.urandom(12)
    data,params=transform(b'payload','aesgcm',key,nonce)
    with pytest.raises(InvalidTag): restore(bytes([data[0]^1])+data[1:],'aesgcm',params,key)
    for kind in ['zip','gzip','bzip2']:
        with pytest.raises(Exception): restore(b'corrupt archive',kind,{})

def test_source_group_split_and_duplicate_checks():
    inventory=pd.DataFrame([{'source_id':f'{i}-{j}','source_group_id':f'g{i}','source_sha256':f'h{i}-{j}'} for i in range(12) for j in range(5)])
    splits=make_splits(inventory,42); assert_no_leakage(splits)
    assert set(splits.split)=={'train','validation','test'}
    assert splits.equals(make_splits(inventory,42))
    tampered=splits.copy(); group=tampered.source_group_id.iloc[0]
    tampered.loc[tampered.source_group_id==group,'split']='train'; tampered.loc[0,'split']='test'
    with pytest.raises(ValueError,match='Group'): assert_no_leakage(tampered)
    tampered=splits.copy(); a=tampered.index[tampered.split=='train'][0]; b=tampered.index[tampered.split=='test'][0]
    tampered.loc[b,'source_sha256']=tampered.loc[a,'source_sha256']
    with pytest.raises(ValueError,match='Content'): assert_no_leakage(tampered)

def test_path_confinement(tmp_path):
    assert confined(tmp_path,'data/file').is_relative_to(tmp_path)
    with pytest.raises(ValueError): confined(tmp_path,'../file')
    with pytest.raises(ValueError): confined(tmp_path,tmp_path.parent/'elsewhere')

def test_generation_preserves_sources(tmp_path):
    config={'variants_per_family':1,'corpus_seed':4,'text_rows':100,'image_sides':[256],'families':[0,1]}
    frame=generate(tmp_path,config); before={r['path']:confined(tmp_path,r['path']).read_bytes() for r in frame.to_dict('records')}
    assert len(frame)==10; validate_inventory(tmp_path,frame)
    result=derive(tmp_path)
    assert len(result)==50 and result.label.value_counts().to_dict()=={0:30,-1:10,1:10}
    params=[json.loads(p)['nonce_hex'] for p in result[result['transform']=='aesgcm'].parameters]
    assert len(params)==len(set(params))
    assert all(confined(tmp_path,p).read_bytes()==raw for p,raw in before.items())
    with pytest.raises(FileExistsError): generate(tmp_path,config)
    target=confined(tmp_path,frame.iloc[0].path); target.write_bytes(b'changed')
    with pytest.raises(ValueError): validate_inventory(tmp_path,frame)
