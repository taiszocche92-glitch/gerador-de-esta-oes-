#!/usr/bin/env python3
"""Valida consistência de embeddings gerados.
Imprime JSON com: embeddings_count, dim, metadata_count, id_map_count, sample_metadata(id 0/last).
"""
import json
from pathlib import Path
import numpy as np

base = Path(__file__).parent / 'memoria' / 'vectors'
emb_file = base / 'embeddings.npy'
meta_file = base / 'metadata.jsonl'
id_file = base / 'id_map.json'

out = {}
try:
    emb = np.load(emb_file)
    out['embeddings_count'] = int(emb.shape[0])
    out['dim'] = int(emb.shape[1]) if getattr(emb, 'ndim', 0) > 1 else 1
except Exception as e:
    out['embeddings_error'] = repr(e)

try:
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta_lines = [line.strip() for line in f if line.strip()]
    out['metadata_count'] = len(meta_lines)
    out['first_metadata'] = json.loads(meta_lines[0]) if meta_lines else None
    out['last_metadata'] = json.loads(meta_lines[-1]) if meta_lines else None
except Exception as e:
    out['metadata_error'] = repr(e)

try:
    id_map = json.load(open(id_file, 'r', encoding='utf-8'))
    if isinstance(id_map, dict):
        out['id_map_count'] = len(id_map)
    elif isinstance(id_map, list):
        out['id_map_count'] = len(id_map)
    else:
        out['id_map_count'] = None
    out['id_map_sample'] = (id_map[0] if isinstance(id_map, list) and id_map else None)
except Exception as e:
    out['id_map_error'] = repr(e)

print(json.dumps(out, ensure_ascii=False, indent=2))
