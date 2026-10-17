import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def markdown_table(frame):
    headers=list(frame.columns)
    lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
    for row in frame.itertuples(index=False,name=None): lines.append('| '+' | '.join(str(x) for x in row)+' |')
    return '\n'.join(lines)

def report(root,config):
    output=root/'results'
    subgroups=pd.read_csv(output/'metrics_subgroups.csv')
    subgroup_columns=['precision','recall','f1','macro_f1','accuracy','fpr_archive','n_samples','n_source_groups','n_compressed','n_encrypted','flagged_encrypted_fraction']
    subgroup_summary=subgroups.groupby(['segment_kib','policy','model','grouping','value'])[subgroup_columns].agg(['mean','std'])
    subgroup_summary.columns=['_'.join(pair) for pair in subgroup_summary.columns]
    subgroup_summary=subgroup_summary.reset_index()
    subgroup_counts=subgroups.groupby(['segment_kib','policy','model','grouping','value']).seed.nunique().reset_index(name='n_seeds')
    subgroup_summary.merge(subgroup_counts).to_csv(output/'metrics_subgroups_summary.csv',index=False)
    metrics=pd.read_csv(output/'metrics_raw.csv')
    summary=pd.read_csv(output/'metrics_summary.csv')
    benchmarks=pd.read_csv(output/'benchmark_by_seed.csv')
    selected=['read_ms_per_segment','features_ms_per_segment','predict_ms_per_segment','end_to_end_ms_per_segment','end_to_end_mib_per_s']
    merged=metrics.merge(benchmarks[['seed','segment_kib','policy','model']+selected],on=['seed','segment_kib','policy','model'],validate='one_to_one')
    trade=merged.groupby(['segment_kib','policy','model'])[['f1','fpr_archive']+selected].agg(['mean','std'])
    trade.columns=['_'.join(pair) for pair in trade.columns]; trade=trade.reset_index()
    trade.to_csv(output/'tradeoff.csv',index=False)
    paired=merged.pivot(index=['seed','segment_kib','policy'],columns='model',values=['f1','fpr_archive','features_ms_per_segment','end_to_end_ms_per_segment'])
    ablation=pd.DataFrame({metric+'_M2_minus_M1':paired[metric]['M2']-paired[metric]['M1'] for metric in ['f1','fpr_archive','features_ms_per_segment','end_to_end_ms_per_segment']}).reset_index()
    ablation.to_csv(output/'ablation_M2_minus_M1.csv',index=False)
    headers=metrics.pivot(index=['seed','segment_kib','model'],columns='policy',values=['f1','fpr_archive'])
    if all(policy in headers['f1'] for policy in ['start','interior']):
        pd.DataFrame({name+'_start_minus_interior':headers[name]['start']-headers[name]['interior'] for name in ['f1','fpr_archive']}).reset_index().to_csv(output/'header_sensitivity.csv',index=False)
    for (kib,policy),part in metrics.groupby(['segment_kib','policy']):
        fig,axes=plt.subplots(1,4,figsize=(14,3.5))
        for axis,(name,values) in zip(axes,part.groupby('model',sort=True)):
            total=values[['tn','fp','fn','tp']].sum().to_numpy().reshape(2,2)
            axis.imshow(total,cmap='Blues'); axis.set_title(name)
            for i in range(2):
                for j in range(2): axis.text(j,i,str(total[i,j]),ha='center',va='center')
            axis.set_xticks([0,1],['compressed','encrypted']); axis.set_yticks([0,1],['compressed','encrypted'])
            axis.set_xlabel('Prediction'); axis.set_ylabel('True label')
        fig.suptitle(f'{kib} KiB, {policy}: sum of 3 seed runs (overlapping source observations)')
        fig.tight_layout(); fig.savefig(output/f'confusion_{kib}_{policy}.png',dpi=180); plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for policy in config['sampling_policies']:
        for name in ['B0','B1','M1','M2']:
            subset=trade[(trade.policy==policy)&(trade.model==name)]
            for axis,metric in zip(axes,['f1','fpr_archive','end_to_end_ms_per_segment']):
                axis.errorbar(subset.segment_kib,subset[metric+'_mean'],yerr=subset[metric+'_std'].fillna(0),marker='o',label=f'{name}/{policy}')
                axis.set_xlabel('Segment size (KiB)'); axis.set_ylabel(metric)
    axes[-1].legend(fontsize=7); fig.tight_layout(); fig.savefig(output/'tradeoff.png',dpi=180); plt.close(fig)
    table=summary[['segment_kib','policy','model','n_seeds']].copy()
    for name in ['precision','recall','f1','macro_f1','accuracy','fpr_archive']:
        table[name]=[f'{m:.4f} ± {s:.4f}' for m,s in zip(summary[name+'_mean'],summary[name+'_std'])]
    corpus=json.loads((root/'data/manifests/corpus_summary.json').read_text(encoding='utf-8'))
    intro=f'''# Kết quả đo thực tế: {config['mode']}

Corpus **tổng hợp**: {corpus['source_files']} tệp, **{corpus['source_groups']} nhóm template**. Số tệp không phải số nguồn độc lập. Nhãn chính: compressed=0, encrypted=1; original không tham gia huấn luyện hay metrics chính. Kết quả dưới đây là cấp đoạn, không phải khả năng phát hiện ransomware ngoài thực tế.

Ba seed chia theo nhóm; mean ± sample standard deviation (ddof=1). Các split giữa seed có thể dùng lại cùng nguồn, nên đây không phải ba corpus độc lập và không phải confidence interval. Confusion matrix cộng các run chỉ là minh họa; không coi tổng đó là số quan sát độc lập.

'''
    (output/'RESULTS.md').write_text(intro+markdown_table(table)+'\n\nChi phí đọc/trích/predict thực sự từ byte: `benchmark_raw.csv`, protocol trong `benchmark_protocol.json`. Ablation từng seed: `ablation_M2_minus_M1.csv`. Ảnh hưởng đoạn đầu: `header_sensitivity.csv`. Các file bị loại theo split: `excluded_by_split.csv`.\n',encoding='utf-8')
    pred=pd.read_csv(output/'test_predictions.csv'); wrong=pred[pred.label!=pred.prediction]
    wrong.to_csv(output/'errors.csv',index=False)
    error_counts=wrong.groupby(['seed','segment_kib','policy','model','source_type','transform']).size().reset_index(name='errors')
    error_counts.to_csv(output/'error_counts.csv',index=False)
    details=wrong.groupby(['model','source_type','transform']).size().reset_index(name='wrong_segment_predictions')
    error_text=f'''# Phân tích lỗi: {config['mode']}

Đã đo {len(wrong)} dự đoán sai trên {len(pred)} lượt dự đoán đoạn (gồm seed, kích thước và policy; có lặp nguồn). Không dùng tổng này làm kiểm định độc lập.

{markdown_table(details)}

`metrics_subgroups.csv` chứa cả mẫu số, số nhóm và FPR riêng ZIP/GZIP/BZIP2. `errors.csv` có offset và feature để kiểm tra thủ công; không sửa threshold từ các lỗi test này.

Các phép nén có thể cho byte gần ngẫu nhiên; AES-GCM giữ độ dài source, còn nén có thể giảm xuống dưới một đoạn. Vì thế thành phần định dạng/lớp thay đổi theo kích thước. Xem `excluded_by_split.csv` trước khi diễn giải F1. Nếu nhóm TXT nén nhỏ bị loại, tập được chọn thiên về ảnh/PDF hoặc dữ liệu khó nén. Chênh lệch M1/M2 có thể nhỏ vì ciphertext và ảnh đã nén đều khó nén lại; chỉ đánh giá chênh lệch đo trong `ablation_M2_minus_M1.csv`.

So sánh start/interior kiểm tra ảnh hưởng sampling và header chung; offset còn khác nhau nên không chứng minh tác động nhân quả riêng của header. Margin cố định 4096 byte không bảo đảm bỏ hết mọi metadata định dạng. Các họ mẫu ít và tổng hợp, vì thế một split giữ lại họ có tính thống kê khác có thể thay đổi FPR đáng kể. Original supplementary là tỷ lệ bị gán encrypted, không phải metric chính. Không đánh giá malware, partial encryption, process events hay deployment.
'''
    (output/'error_analysis.md').write_text(error_text,encoding='utf-8')
