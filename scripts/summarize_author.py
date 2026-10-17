"""Render saved CV results without retraining or changing the protocol."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
from dt083.reporting import markdown_table

ROOT=Path(__file__).resolve().parents[1]

def main():
    output=ROOT/'results/author_reference'
    frame=pd.read_csv(output/'metrics_by_seed.csv')
    summary=frame.groupby('segment_kib')[['precision','recall','f1','macro_f1','accuracy','fpr_archive']].agg(['mean','std'])
    summary.columns=['_'.join(pair) for pair in summary.columns]
    summary=summary.reset_index(); summary.to_csv(output/'metrics_summary.csv',index=False)
    paper={64:.9528,128:.9653,256:.9809,512:.9965,1024:1.0}
    table=summary[['segment_kib']].copy()
    for name in ['precision','recall','f1','accuracy','fpr_archive']:
        table[name]=[f'{m:.6f} ± {s:.6f}' for m,s in zip(summary[name+'_mean'],summary[name+'_std'])]
    table['paper_RF_All_F1']=table.segment_kib.map(paper)
    text='''# Kết quả tham khảo trên CSV tác giả

Đã chạy năm size, 10-fold stratified shuffled row CV, seed 42/123/2026; 150 lượt train/evaluate. Mỗi seed lấy trung bình metric 10 folds, sau đó báo mean ± sample SD của ba giá trị theo seed. Đây là repeated split trên cùng corpus, không phải 30 fold độc lập hay CI. Precision/recall/F1 là encrypted-positive. Không kết hợp với kết quả corpus synthetic nhóm.

KHÔNG có source_group_id hoặc raw bytes: chưa bảo đảm độc lập theo nguồn và không đo tốc độ end-to-end. Chín feature parse theo notebook, RF100/depth10/all features. Bỏ global minmax và dùng parser an toàn. Không cần scaler cho RF. Xem protocol.json và quality_audit.json; không loại duplicate feature+label nào trong năm CSV này. Các số paper chỉ là mốc, điều kiện không hoàn toàn tương đương, không tuyên bố vượt paper.

'''
    (output/'RESULTS.md').write_text(text+markdown_table(table)+'\n',encoding='utf-8')

if __name__=='__main__': main()
