import math
import numpy as np
import pandas as pd
import pytest
from dt083.features import extract, offsets, matrix, read_segment, ALL_FEATURES

def test_entropy_boundaries():
    assert extract(bytes(1024))['entropy']==0
    values=extract(bytes(range(256))*256)
    assert values['entropy']==8
    assert values['chi_square']==0
    assert values['bit_one_ratio']==.5

def test_small_reference():
    raw=bytes([0,1,2,3])
    values=extract(raw)
    assert values['entropy']==2
    assert values['chi_square']==252
    assert values['serial_correlation']==pytest.approx(1)
    assert values['bit_one_ratio']==4/32
    bits=''.join(f'{v:08b}' for v in raw)
    runs=1+sum(a!=b for a,b in zip(bits,bits[1:]))
    n1=bits.count('1'); n0=bits.count('0'); n=len(bits)
    expected=1+2*n1*n0/n
    variance=2*n1*n0*(2*n1*n0-n)/(n*n*(n-1))
    assert values['runs_z']==pytest.approx((runs-expected)/math.sqrt(variance))

def test_degenerate_and_empty():
    with pytest.raises(ValueError): extract(b'')
    assert extract(b'\xff')['runs_z']==0
    assert extract(b'\x00')['serial_correlation']==0
    assert all(math.isfinite(x) for x in extract(bytes(200)).values())

def test_metadata_cannot_be_features():
    values=extract(bytes(range(256)))
    frame=pd.DataFrame([{**values,'label':1,'path':'secret','transform':'aesgcm'}])
    assert matrix(frame,ALL_FEATURES).shape==(1,6)
    for field in ['label','path','transform','source_id']:
        with pytest.raises(ValueError): matrix(frame,[field])
    frame.loc[0,'entropy']=np.nan
    with pytest.raises(ValueError): matrix(frame,['entropy'])

def test_segment_boundaries_and_read_errors(tmp_path):
    assert offsets(0,65536)==[]
    assert offsets(65535,65536,policy='start')==[]
    assert offsets(65536,65536,policy='start')==[0]
    positions=offsets(240000,65536,maximum=3,margin=4096)
    assert positions[0]>=4096 and positions[-1]+65536<=240000-4096
    assert all(b-a>=65536 for a,b in zip(positions,positions[1:]))
    target=tmp_path/'file.bin'; target.write_bytes(b'abc')
    assert read_segment(tmp_path,'file.bin',1,2)==b'bc'
    with pytest.raises(ValueError): read_segment(tmp_path,'file.bin',0,4)
    with pytest.raises(FileNotFoundError): read_segment(tmp_path,'missing',0,3)
    with pytest.raises(OSError): read_segment(tmp_path,'.',0,3)
    with pytest.raises(ValueError): read_segment(tmp_path,'../outside',0,1)
