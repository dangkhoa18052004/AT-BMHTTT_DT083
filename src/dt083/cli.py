import argparse
import json
import logging
from pathlib import Path
from time import perf_counter
import joblib
import pandas as pd
import psutil
from .common import confined, dump_json, environment
from .corpus import generate, validate_inventory
from .transforms import derive
from .extraction import run_extract
from .learning import split_stage, evaluate
from .benchmark import benchmark, values_for
from .reporting import report
from .features import offsets, read_segment, matrix

PROJECT=Path(__file__).resolve().parents[2]

def run_pipeline(root,config):
    started=perf_counter(); cpu=psutil.Process().cpu_times()
    dump_json(root/'results/config.json',config)
    dump_json(root/'results/environment.json',environment())
    stages={}
    for name,function in [('prepare',lambda:generate(root,config)),('derive',lambda:derive(root)),
                          ('split',lambda:split_stage(root,config)),('extract',lambda:run_extract(root,config)),
                          ('train',lambda:evaluate(root,config)),('benchmark',lambda:benchmark(root,config)),('report',lambda:report(root,config))]:
        t=perf_counter(); logging.info('Stage %s',name); function(); stages[name]=perf_counter()-t
    validate_inventory(root,pd.read_csv(root/'data/manifests/inventory.csv'))
    after=psutil.Process().cpu_times()
    dump_json(root/'results/pipeline_cost.json',{'wall_s':perf_counter()-started,'stages_seconds':stages,
              'process_cpu_s':after.user+after.system-cpu.user-cpu.system,'final_rss_bytes':psutil.Process().memory_info().rss,
              'note':'Whole experiment wall time includes corpus construction, train/validation/test and artifact rendering. Not detection latency.'})

def demo(root,config,file,model,seed,kib,policy):
    # User input is bounded to managed source/derived corpus, not arbitrary project files.
    target=confined(root,file)
    if not any(target.is_relative_to(confined(root,p)) for p in ['data/source','data/derived']):
        raise ValueError('Demo accepts only files under this run data/source or data/derived')
    if not target.is_file(): raise FileNotFoundError(file)
    bundle=joblib.load(root/f'models/{seed}_{kib}_{policy}_{model}.joblib')
    positions=offsets(target.stat().st_size,kib*1024,config['max_segments_per_file'],policy,config['interior_margin_bytes'])
    results=[]
    for offset in positions:
        started=perf_counter(); raw=read_segment(root,file,offset,kib*1024)
        values=values_for(raw,bundle['features'],config['zlib_level']); x=matrix(pd.DataFrame([values]),bundle['features'])
        score=float(bundle['model'].predict_proba(x)[0,1]) if bundle['model'] is not None else float(x[0,0])
        results.append({'offset':offset,'length':len(raw),'features':values,'score':score,
                        'predicted_class':'encrypted' if score>=bundle['threshold'] else 'compressed','elapsed_ms':(perf_counter()-started)*1000})
    return {'file':file,'model':model,'segments':results,'status':'ok' if positions else 'too_small',
            'notice':'Score is a model output (B0: entropy); not a probability that this file is ransomware. No file-level aggregation.'}

def main(argv=None):
    parser=argparse.ArgumentParser(description='DT083 controlled compressed/encrypted corpus experiment')
    parser.add_argument('stage',choices=['pipeline','prepare','derive','split','extract','train','benchmark','report','demo'])
    parser.add_argument('--config',type=Path,default=PROJECT/'configs/smoke.json')
    parser.add_argument('--run',default='smoke')
    parser.add_argument('--file'); parser.add_argument('--model',choices=['B0','B1','M1','M2'],default='M2')
    parser.add_argument('--seed',type=int,default=42); parser.add_argument('--kib',type=int,default=64)
    parser.add_argument('--policy',choices=['interior','start'],default='interior')
    args=parser.parse_args(argv)
    # A run is one directory name. No traversals, drive letters or absolute paths.
    if not args.run or Path(args.run).name!=args.run or args.run in ['.','..'] or ':' in args.run:
        parser.error('--run must be a simple directory name')
    root=confined(PROJECT/'runs',args.run); root.mkdir(parents=True,exist_ok=True)
    (root/'results').mkdir(exist_ok=True)
    config=json.loads(args.config.read_text(encoding='utf-8'))
    if any(v not in [64,128,256,512,1024] for v in config['segment_kib']): parser.error('Supported sizes: 64/128/256/512/1024 KiB')
    saved=root/'results/config.json'
    if saved.exists() and json.loads(saved.read_text(encoding='utf-8'))!=config:
        parser.error('Run configuration mismatch; select a new --run')
    dump_json(saved,config)
    dump_json(root/f'results/environment_{args.stage}.json',environment())
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(),logging.FileHandler(root/'results/run.log',encoding='utf-8')],force=True)
    try:
        if args.stage=='pipeline': run_pipeline(root,config)
        elif args.stage=='prepare': generate(root,config)
        elif args.stage=='derive': derive(root)
        elif args.stage=='split': split_stage(root,config)
        elif args.stage=='extract': run_extract(root,config)
        elif args.stage=='train': evaluate(root,config)
        elif args.stage=='benchmark': benchmark(root,config)
        elif args.stage=='report': report(root,config)
        elif args.stage=='demo':
            if not args.file: parser.error('--file required for demo')
            result=demo(root,config,args.file,args.model,args.seed,args.kib,args.policy)
            dump_json(root/'results/demo.json',result); print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,FileNotFoundError,FileExistsError,OSError) as exc:
        logging.error('%s: %s',type(exc).__name__,exc)
        dump_json(root/'results/last_error.json',{'stage':args.stage,'type':type(exc).__name__,'message':str(exc)})
        raise SystemExit(1) from exc

if __name__=='__main__': main()
