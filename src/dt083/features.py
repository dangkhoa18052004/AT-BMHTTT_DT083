"""Own feature definitions; not an exact implementation of the paper battery."""
import zlib
import numpy as np

STAT_FEATURES = ['entropy','chi_square','serial_correlation','bit_one_ratio','runs_z']
ALL_FEATURES = STAT_FEATURES + ['recompress_ratio']
MODEL_FEATURES = {'B0':['entropy'], 'B1':['entropy'], 'M1':STAT_FEATURES, 'M2':ALL_FEATURES}

def extract(data, recompress=True, zlib_level=6):
    if not data:
        raise ValueError('Empty segment has no defined features')
    x = np.frombuffer(data,dtype=np.uint8)
    n = len(x)
    counts = np.bincount(x,minlength=256).astype(float)
    probabilities = counts[counts>0] / n
    entropy = float(-np.sum(probabilities*np.log2(probabilities)))
    chi = float(np.sum((counts-n/256)**2/(n/256)))
    y = x.astype(float)
    if n < 2 or np.var(y[:-1]) == 0 or np.var(y[1:]) == 0:
        corr = 0.0
    else:
        a, b = y[:-1]-np.mean(y[:-1]), y[1:]-np.mean(y[1:])
        corr = float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b)))
    bits = np.unpackbits(x,bitorder='big')
    ones = int(bits.sum())
    zeros = len(bits)-ones
    run_count = 1+int(np.count_nonzero(bits[1:] != bits[:-1]))
    total = len(bits)
    expected = 1+2*ones*zeros/total
    variance = 2*ones*zeros*(2*ones*zeros-total)/(total*total*(total-1))
    runs_z = float((run_count-expected)/np.sqrt(variance)) if variance>0 else 0.0
    values = dict(entropy=entropy,chi_square=chi,serial_correlation=corr,bit_one_ratio=ones/total,runs_z=runs_z)
    if recompress: values['recompress_ratio'] = len(zlib.compress(data,level=zlib_level))/n
    return values

def matrix(frame, names):
    if not set(names).issubset(ALL_FEATURES):
        raise ValueError('Only statistical features are permitted')
    values = frame.loc[:,names].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite feature matrix; no implicit imputation')
    return values

def offsets(size, length, maximum=2, policy='interior', margin=4096):
    if length <= 0 or maximum <= 0 or margin < 0:
        raise ValueError('Invalid segment configuration')
    if policy not in ['interior','start']:
        raise ValueError('Unknown sampling policy')
    start = margin if policy == 'interior' else 0
    end = size-margin if policy == 'interior' else size
    count = min(maximum,max(0,(end-start)//length))
    if count == 0: return []
    if policy == 'start': return [i*length for i in range(count)]
    # Spread chunks within the eligible interior; distances are >= length.
    return [int(v) for v in np.linspace(start,end-length,count)] if count>1 else [(start+end-length)//2]

def read_segment(root, relative, offset, length):
    from .common import confined
    if offset < 0 or length <= 0: raise ValueError('Invalid offset/length')
    with confined(root,relative).open('rb') as handle:
        handle.seek(offset)
        data=handle.read(length)
    if len(data) != length: raise ValueError('Short or truncated segment')
    return data
