import logging
from time import perf_counter
import pandas as pd
import psutil
from .common import confined, sha256, dump_json
from .features import extract, offsets, read_segment

def run_extract(root,config):
    derived=pd.read_csv(root/'data/manifests/derived.csv',keep_default_na=False)
    destination=root/'data/features'; destination.mkdir(parents=True,exist_ok=True)
    rows=[]; skips=[]; peak=0; started=perf_counter()
    for i,row in enumerate(derived.to_dict('records')):
        path=confined(root,row['path'])
        if sha256(path.read_bytes())!=row['derived_sha256']: raise ValueError('Changed/corrupt derived content')
        for kib in config['segment_kib']:
            length=kib*1024
            for policy in config['sampling_policies']:
                positions=offsets(row['size_bytes'],length,config['max_segments_per_file'],policy,config['interior_margin_bytes'])
                if not positions:
                    skips.append({**{k:row[k] for k in ['derived_id','source_id','source_group_id','source_type','transform','label','size_bytes']},
                                  'segment_kib':kib,'policy':policy,'reason':'too_small_for_complete_segment_and_margin'})
                for position in positions:
                    t=perf_counter(); raw=read_segment(root,row['path'],position,length); read_s=perf_counter()-t
                    t=perf_counter(); values=extract(raw,False); stat_s=perf_counter()-t
                    import zlib
                    t=perf_counter(); values['recompress_ratio']=len(zlib.compress(raw,config['zlib_level']))/length; recomp_s=perf_counter()-t
                    rows.append({**{k:row[k] for k in ['derived_id','source_id','source_group_id','source_type','transform','label','path']},
                                 'segment_id':f'{row["derived_id"]}:{kib}:{policy}:{position}', 'offset':position,'length':length,
                                 'segment_kib':kib,'policy':policy,'segment_sha256':sha256(raw),
                                 'read_s':read_s,'stat_feature_s':stat_s,'recompress_s':recomp_s,**values})
        peak=max(peak,psutil.Process().memory_info().rss)
        if (i+1)%100==0: logging.info('Extracted %s/%s derivatives',i+1,len(derived))
    if not rows: raise ValueError('No complete segments; inspect corpus sizes and configuration')
    frame=pd.DataFrame(rows); frame.to_csv(destination/'segments.csv',index=False)
    skip=pd.DataFrame(skips)
    skip.to_csv(destination/'excluded.csv',index=False)
    if not skip.empty:
        skip.groupby(['segment_kib','policy','source_type','transform']).size().reset_index(name='excluded_files').to_csv(destination/'excluded_summary.csv',index=False)
    dump_json(destination/'extraction_cost.json',{'wall_seconds':perf_counter()-started,'segments':len(rows),'peak_sampled_rss_bytes':peak,
              'measured_read_s':float(frame.read_s.sum()),'measured_statistics_s':float(frame.stat_feature_s.sum()),
              'measured_recompression_s':float(frame.recompress_s.sum()),'measurement':'perf_counter; each segment; hot/OS cache possible; includes originals and both policies; no warm-up here'})
    return frame
