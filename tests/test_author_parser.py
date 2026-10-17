import importlib.util
from pathlib import Path
import pandas as pd
import pytest

def test_author_labels_and_safe_parser():
    spec=importlib.util.spec_from_file_location('author_reference',Path(__file__).parents[1]/'scripts/author_reference.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    df=pd.DataFrame({'Filetype':[0,1],'Entropy':[7.8,7.99],'jarque-bera':[2,3],'shapiro':[.8,.9],
        'Block Frequency':["[['0.2'], ['*']]","[['0.5'], ['10/10']]"],
        'Frequency':["[['0.2'], ['*']]","[['0.5'], ['*']]"],
        'Cumulative Sums':["[['0.2','0.3'], ['*','*']]","[['0.1','0.7'], ['*','*']]"],
        'Overlapping Template':["[['0.2'], ['*']]","[['0.5'], ['*']]"],
        'Chi-score':[298,299],'Monobit':['[9725,10275]','[9724]']})
    x,y=module.parse_features(df)
    assert y.tolist()==[0,1] and x.shape==(2,9)
    assert x.Monobit_.tolist()==[1,0]
    assert x.Chi_score.tolist()==[1,0]
    assert x.Cumu_sum.tolist()==pytest.approx([.5,.8])
