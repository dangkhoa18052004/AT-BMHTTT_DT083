"""Synthetic corpus. Variants share a group with their procedural template."""
from pathlib import Path
import io
import csv
import logging
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .common import sha256, confined, now, dump_json

FAMILIES = ['waves','radial','grid','terrain','rings','diagonal','checker','mosaic','bands','spiral','contour','blocks']
TOPICS = ['ocean weather station temperature current tide salt sensor',
          'hospital inventory supply equipment ward stock delivery patient',
          'rail transport station vehicle arrival route distance ticket',
          'forest species habitat leaf tree ecology water canopy',
          'finance invoice balance revenue account interest payment market',
          'astronomy planet orbit spectrum telescope star galaxy exposure',
          'agriculture soil crop harvest rainfall field nutrition growth',
          'energy turbine voltage battery power capacity solar current',
          'education course student lesson library teacher score research',
          'manufacturing part inspection machine defect assembly batch pressure',
          'city map street junction building park zone travel pedestrian',
          'laboratory trial reagent sample control assay concentration reaction']

def image_for(family, variant, rng, side):
    y,x=np.mgrid[0:side,0:side]/side
    k=family
    if k == 0: signal=np.sin(35*x)+np.cos(23*y)
    elif k == 1: signal=np.sin(50*np.hypot(x-.45,y-.55))
    elif k == 2: signal=(np.sin(60*x)>0).astype(float)+(np.sin(40*y)>0)
    elif k == 3: signal=np.sin(7*x+np.sin(18*y))+np.cos(12*y+np.sin(22*x))
    elif k == 4: signal=np.cos(80*((x-.5)**2+(y-.5)**2))
    elif k == 5: signal=np.sin(45*(x+y))+.6*np.cos(17*(x-y))
    elif k == 6: signal=((x*16).astype(int)+(y*24).astype(int))%2
    elif k == 7: signal=np.sin((x*18).astype(int)*2.1+(y*16).astype(int)*1.7)
    elif k == 8: signal=np.sin(70*y+.5*np.sin(18*x))
    elif k == 9: signal=np.sin(8*np.arctan2(y-.5,x-.5)+45*np.hypot(x-.5,y-.5))
    elif k == 10: signal=np.sin(22*x)*np.cos(19*y)+.6*np.cos(36*x+15*y)
    else: signal=((x*11).astype(int)%3-(y*9).astype(int)%4)/3
    # Bounded texture plus structured signal, rather than random-noise-only images.
    texture=rng.normal(0,[0,4,12,24,8,18][variant%6],(side,side))
    channels=[np.clip(118+52*signal+texture+25*np.sin(x*(c+1)*5+y*8),0,255).astype('uint8') for c in range(3)]
    image=Image.fromarray(np.stack(channels,axis=2))
    draw=ImageDraw.Draw(image)
    for j in range(16):
        a=int(rng.integers(0,side-80)); b=int(rng.integers(0,side-80))
        draw.rectangle((a,b,a+60+j*2,b+45),outline=(30+j*12,90,180),width=3)
    draw.text((20,20),f'{FAMILIES[family]} experimental scene {variant}',fill=(255,255,255))
    return image

def generate(root, config):
    root=Path(root)
    destination=confined(root,'data/source')
    destination.mkdir(parents=True,exist_ok=True)
    manifest=root/'data/manifests/inventory.csv'
    if manifest.exists():
        raise FileExistsError('Inventory exists. Reuse it with later CLI stages or choose a new --run.')
    rows=[]; seen=set(); acquisition=now()
    variants=config['variants_per_family']
    families=config.get('families',list(range(12)))
    for family in families:
        for variant in range(variants):
            seed=config['corpus_seed']+family*100+variant
            rng=np.random.default_rng(seed)
            words=TOPICS[family].split()
            line_count=config['text_rows']
            # Variable repetition is a content property; no padding to segment sizes.
            vocab=words+['measurement','record','review','summary','observed','change','study']
            sentences=[]; table=[]
            for j in range(line_count):
                numbers=rng.normal(family*10+variant,20,6)
                chosen=rng.choice(vocab,size=8 if variant%3 else 3)
                if family%3==0:
                    sentence=f'Observation {j}: '+ ' '.join(chosen)+f'. Value {numbers[0]:.8f}; trend {numbers[1]:.6f}.\n'
                elif family%3==1:
                    sentence=' | '.join(chosen)+f' | batch {j:06d} | {numbers[0]:.10f} | inspected={j%7}.\n'
                else:
                    sentence=f'<record index="{j}"><topic>{chosen[0]}</topic><reading>{numbers[0]:.9f}</reading><notes>'+ ' '.join(chosen[1:])+'</notes></record>\n'
                sentences.append(sentence)
                table.append([j,chosen[0],*list(numbers),j%[2,7,19][variant%3]])
            text=''.join(sentences).encode('utf-8')
            buffer=io.StringIO(); writer=csv.writer(buffer,lineterminator='\n')
            writer.writerow(['record','category','x1','x2','x3','x4','x5','x6','status']); writer.writerows(table)
            image=image_for(family,variant,rng,config['image_sides'][variant%len(config['image_sides'])])
            png=io.BytesIO(); image.save(png,format='PNG',compress_level=[1,6,9][variant%3])
            jpeg=io.BytesIO(); image.save(jpeg,format='JPEG',quality=[65,85,95][variant%3],subsampling=0)
            pdf=io.BytesIO(); doc=canvas.Canvas(pdf,pagesize=(595,842),invariant=1,pageCompression=1)
            for page in range(4):
                doc.setFont('Helvetica',13); doc.drawString(35,805,f'Research {FAMILIES[family]} / section {page+1}')
                doc.drawImage(ImageReader(io.BytesIO(jpeg.getvalue())),35,300,width=520,height=450,preserveAspectRatio=True)
                doc.setFont('Helvetica',8)
                for j in range(22): doc.drawString(35,280-j*10,sentences[page*22+j].strip()[:105])
                for j in range(6):
                    doc.rect(35+j*85,30,85,26); doc.drawString(39+j*85,40,f'{table[page][j+2]:.3f}')
                doc.showPage()
            doc.save()
            blobs={'txt':text,'csv':buffer.getvalue().encode(),'png':png.getvalue(),'jpeg':jpeg.getvalue(),'pdf':pdf.getvalue()}
            for kind,raw in blobs.items():
                digest=sha256(raw)
                if digest in seen: continue
                seen.add(digest)
                source_id=f'{FAMILIES[family]}_{variant:02d}_{kind}'
                relative=f'data/source/{source_id}.{kind}'
                confined(root,relative).write_bytes(raw)
                rows.append(dict(source_id=source_id,source_group_id=f'template_{FAMILIES[family]}',source_sha256=digest,
                                 source_type=kind,size_bytes=len(raw),source_url='',license='CC0-1.0 (project-generated synthetic bytes)',
                                 acquisition_date=acquisition,generation_method=f'synthetic-v1/{FAMILIES[family]}',
                                 generation_seed=seed,path=relative))
        logging.info('Generated family %s (%s variants)',FAMILIES[family],variants)
    frame=pd.DataFrame(rows)
    manifest.parent.mkdir(parents=True,exist_ok=True); frame.to_csv(manifest,index=False)
    dump_json(root/'data/manifests/corpus_summary.json',{'source_files':len(frame),'source_groups':frame.source_group_id.nunique(),
              'source_types':frame.source_type.value_counts().to_dict(),'bytes':int(frame.size_bytes.sum()),
              'independence_note':'All variants/formats from the same procedural family are grouped. Source file count is NOT independent group count.',
              'corpus':'synthetic only; public supplements not acquired'})
    return frame

def validate_inventory(root,frame):
    if frame.source_sha256.duplicated().any(): raise ValueError('Duplicate source contents')
    for row in frame.to_dict('records'):
        if sha256(confined(root,row['path']).read_bytes()) != row['source_sha256']:
            raise ValueError(f'Source was changed: {row["source_id"]}')
