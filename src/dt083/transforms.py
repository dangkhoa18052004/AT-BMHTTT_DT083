import bz2
import gzip
import io
import json
import os
import logging
import zipfile
import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .common import confined, sha256, dump_json
from .corpus import validate_inventory

def transform(raw,kind,key=None,nonce=None):
    if kind=='original': return raw,{}
    if kind=='gzip': return gzip.compress(raw,compresslevel=6,mtime=0),{'level':6,'mtime':0}
    if kind=='bzip2': return bz2.compress(raw,compresslevel=9),{'level':9}
    if kind=='zip':
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as arc:
            info=zipfile.ZipInfo('payload',date_time=(2020,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            arc.writestr(info,raw,compresslevel=6)
        return buf.getvalue(),{'level':6,'member':'payload'}
    if kind=='aesgcm':
        if key is None or nonce is None: raise ValueError('AES-GCM requires key and nonce')
        sealed=AESGCM(key).encrypt(nonce,raw,b'DT083-v1')
        # Only ciphertext is classifier input; tag/nonce/AAD are out-of-band.
        return sealed[:-16],{'algorithm':'AES-256-GCM','nonce_hex':nonce.hex(),'tag_hex':sealed[-16:].hex(),'aad':'DT083-v1'}
    raise ValueError('Unknown transform')

def restore(raw,kind,parameters,key=None):
    if kind=='original': return raw
    if kind=='gzip': return gzip.decompress(raw)
    if kind=='bzip2': return bz2.decompress(raw)
    if kind=='zip':
        with zipfile.ZipFile(io.BytesIO(raw)) as arc: return arc.read('payload')
    if kind=='aesgcm':
        return AESGCM(key).decrypt(bytes.fromhex(parameters['nonce_hex']),raw+bytes.fromhex(parameters['tag_hex']),parameters['aad'].encode())
    raise ValueError('Unknown transform')

def derive(root):
    inventory=pd.read_csv(root/'data/manifests/inventory.csv',keep_default_na=False)
    validate_inventory(root,inventory)
    output=root/'data/derived'; output.mkdir(parents=True,exist_ok=True)
    if (root/'data/manifests/derived.csv').exists(): raise FileExistsError('Derived manifest already exists')
    # New key for each corpus build, cryptographic RNG; no seeded cryptographic material.
    key=AESGCM.generate_key(bit_length=256)
    dump_json(root/'data/manifests/simulation_key.json',{'key_hex':key.hex(),'purpose':'Non-production corpus decryption only; exclude from published package'})
    seen_nonces=set(); rows=[]
    for row in inventory.to_dict('records'):
        original=confined(root,row['path']).read_bytes()
        for kind in ['original','zip','gzip','bzip2','aesgcm']:
            nonce=os.urandom(12)
            while nonce in seen_nonces: nonce=os.urandom(12)
            if kind=='aesgcm': seen_nonces.add(nonce)
            data,params=transform(original,kind,key,nonce)
            if sha256(restore(data,kind,params,key))!=row['source_sha256']: raise ValueError('Round trip failed')
            identity=f'{row["source_id"]}__{kind}'
            relative=f'data/derived/{identity}.bin'
            confined(root,relative).write_bytes(data)
            if kind=='aesgcm': dump_json(output/f'{identity}.metadata.json',params)
            rows.append(dict(derived_id=identity,source_id=row['source_id'],source_group_id=row['source_group_id'],
                             source_type=row['source_type'],derived_sha256=sha256(data),transform=kind,
                             label=-1 if kind=='original' else int(kind=='aesgcm'),split='assigned by per-seed splits.csv',
                             size_bytes=len(data),parameters=json.dumps(params),path=relative))
        if len(rows)%100==0:
            logging.info('Created and round-trip verified %s/%s derivatives',len(rows),len(inventory)*5)
    result=pd.DataFrame(rows); result.to_csv(root/'data/manifests/derived.csv',index=False)
    validate_inventory(root,inventory)
    dump_json(root/'data/manifests/round_trip.json',{'verified_derivatives':len(result),'sources_unchanged':True,
                                                  'unique_encryption_nonces':len(seen_nonces),'key_bits':256})
    return result
