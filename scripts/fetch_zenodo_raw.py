"""Optional passive raw-dataset download; verify checksum, do not extract or execute."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    metadata=json.loads((ROOT/'references/zenodo_metadata.json').read_text())
    record=metadata['files'][0]
    if metadata['metadata']['license']['id']!='cc-by-4.0': raise ValueError('Review changed license first')
    destination=ROOT/'references/raw'; destination.mkdir(exist_ok=True)
    final=destination/'dataset_raw.zip'
    if final.exists(): raise FileExistsError('Refuse to overwrite existing raw archive')
    part=destination/'dataset_raw.zip.part'
    with urllib.request.urlopen(record['links']['self'],timeout=120) as response, part.open('wb') as output:
        while chunk:=response.read(1024*1024): output.write(chunk)
    digest=hashlib.md5(usedforsecurity=False)
    with part.open('rb') as handle:
        while chunk:=handle.read(1024*1024): digest.update(chunk)
    if part.stat().st_size!=record['size'] or 'md5:'+digest.hexdigest()!=record['checksum']:
        raise ValueError('Size/MD5 mismatch; partial download retained for diagnosis, not accepted')
    part.rename(final)
    print('Verified passive archive only:',final,'No extraction or execution performed')

if __name__=='__main__': main()
