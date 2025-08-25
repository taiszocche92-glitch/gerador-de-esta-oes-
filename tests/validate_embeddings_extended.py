#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np

base = Path(__file__).parent / 'memoria' / 'vectors'
out = {}

try:
    cfg = json.loads((base / 'config.json').read_text(encoding='utf-8'))
    out['config_items_count'] = int(cfg.get('items_count', -1))
    out['config_model'] = cfg.get('model')
except Exception as e:
    out['config_error'] = repr(e)

try:
    emb = np.load(base / 'embeddings.npy')
    out['embeddings_count'] = int(emb.shape[0])
    out['dim'] = int(emb.shape[1]) if getattr(emb, 'ndim', 0) > 1 else 1
    # check nans
    out['has_nan'] = bool(np.isnan(emb).any())
    norms = np.linalg.norm(emb, axis=1)
    out['norm_min'] = float(np.min(norms))
    out['norm_max'] = float(np.max(norms))
    out['norm_mean'] = float(np.mean(norms))
except Exception as e:
    out['emb_error'] = repr(e)

try:
    meta_lines = [l for l in (base / 'metadata.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    out['metadata_count'] = len(meta_lines)
    # sample first/last
    if meta_lines:
        out['first_metadata_id'] = json.loads(meta_lines[0]).get('id')
        out['last_metadata_id'] = json.loads(meta_lines[-1]).get('id')
except Exception as e:
    out['meta_error'] = repr(e)

try:
    id_map = json.loads((base / 'id_map.json').read_text(encoding='utf-8'))
    if isinstance(id_map, dict):
        out['id_map_type'] = 'dict'
        out['id_map_count'] = len(id_map)
    elif isinstance(id_map, list):
        out['id_map_type'] = 'list'
        out['id_map_count'] = len(id_map)
    else:
        out['id_map_type'] = type(id_map).__name__
        out['id_map_count'] = None
except Exception as e:
    out['id_map_error'] = repr(e)

# Cross-checks
if 'embeddings_count' in out and 'metadata_count' in out:
    out['emb_meta_match'] = (out['embeddings_count'] == out['metadata_count'])
if 'embeddings_count' in out and 'id_map_count' in out:
    out['emb_idmap_match'] = (out['embeddings_count'] == out.get('id_map_count'))
if 'config_items_count' in out and 'embeddings_count' in out:
    out['config_matches_actual'] = (out['config_items_count'] == out['embeddings_count'])

print(json.dumps(out, ensure_ascii=False, indent=2))
