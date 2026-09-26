"""Searchable evidence receipts. Metadata only; never modifies source documents."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

ARCHIVE = Path(r'D:\GitHub\David-OSv3\_FIS_ROOT_SIDECAR_ARCHIVE') / 'EVIDENCE'
VERSION = 'evidence.sidecar.v2'
GLOSSARY = Path(__file__).resolve().parents[1] / 'SIDECAR_CODES.json'
SIDECAR_DIR = Path(__file__).resolve().parents[1] / 'SIDECAR'

@lru_cache(maxsize=1)
def codebook():
    return json.loads(GLOSSARY.read_text(encoding='utf-8')) if GLOSSARY.exists() else {}

def compact_codes(text):
    found = []
    for code, entry in codebook().items():
        for phrase in [entry['name']] + entry.get('aliases', []):
            if re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text, re.I):
                found.append(code)
                break
    return sorted(found)

def field(text, name):
    m = re.search(r'^' + re.escape(name) + r':\s*([^\r\n]+)', text, re.M)
    return m.group(1).strip().strip('\"\'') if m else ''

def metadata(text):
    # Only read the companion, not metadata quoted inside the preserved article.
    text = text.split('<!-- ===== ORIGINAL ARTICLE BELOW')[0]
    domains = {level: field(text, 'domain_' + level) for level in ('primary', 'secondary', 'tertiary')}
    tags = re.findall(r'^\s*-\s*tag:\s*[\"\']?([^\r\n\"\']+)', text, re.M)
    for key in ('tags', 'topic_keys'):
        raw = field(text, key)
        if raw.startswith('['):
            tags.extend(t.strip().strip('\"\'') for t in raw.strip('[]').split(',') if t.strip())
    tags = sorted(set(tags))
    terms = ' '.join(list(domains.values()) + tags).lower()
    if re.search(r'\b(math\w*|algebra\w*|geometr\w*|calculus|topolog\w*)\b', terms):
        tags = sorted(set(tags + ['math', 'mathematics']))
    return {'domains': domains, 'tags': tags,
            'content_type': field(text, 'content_type'),
            'semantic_status': field(text, 'semantic_status'),
            'source_file': field(text, 'source_file'),
            'source_sha256': field(text, 'source_sha256')}

def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.sidecar-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def write_sidecar(path, *, archive=ARCHIVE, sidecar_dir=SIDECAR_DIR, classification_text=None, status='output_observed'):
    path = Path(path).resolve()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    identity = hashlib.sha256(str(path).casefold().encode()).hexdigest()
    adjacent = Path(sidecar_dir) / (identity + '.sidecar')
    existing = {}
    if adjacent.exists():
        try:
            existing = json.loads(adjacent.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    unchanged = existing.get('sha256') == digest and existing.get('schema') == VERSION
    if unchanged and classification_text is None:
        payload = existing
    else:
        text = classification_text if classification_text is not None else raw.decode('utf-8', errors='replace')
        meta = metadata(text)
        payload = {'schema': VERSION, 'path': str(path), 'name': path.name,
                   'sha256': digest, 'bytes': len(raw),
                   'recorded_at': datetime.now(timezone.utc).isoformat(),
                   'processing_status': status,
                   'classification_status': 'classified' if meta['domains']['primary'] else 'needs_classification',
                   **meta}
        payload['codes'] = compact_codes(' '.join(meta['domains'].values()) + ' ' + ' '.join(meta['tags']) + ' ' + text)
        payload['code_meanings'] = {code: codebook()[code]['name'] for code in payload['codes']}
        payload['compact_label'] = '-'.join(payload['codes']) or 'UNCL'
        atomic_json(adjacent, payload)
    # Refuse to silently create a replacement David OS root on a different machine.
    archive = Path(archive)
    if not archive.parent.is_dir():
        raise OSError(f'David OS archive unavailable; local sidecar saved: {archive.parent}')
    mirrored = archive / (identity + '.sidecar')
    mirror_current = None
    if mirrored.exists():
        try:
            mirror_current = json.loads(mirrored.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    if mirror_current != payload:
        atomic_json(mirrored, payload)
    return payload

def record_output(path, classification_text=None, status='output_written'):
    # Sidecar failures must not turn a successful article into a failed intake.
    try:
        return write_sidecar(path, classification_text=classification_text, status=status)
    except Exception as exc:
        import warnings
        warnings.warn(f'SIDECAR RETRY NEEDED for {path}: {exc}', RuntimeWarning)

def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'OUTBOX')
    parser.add_argument('--search', help='Search metadata in the David OS sidecar archive')
    parser.add_argument('--search-prompt', action='store_true', help='Ask for a search term')
    args = parser.parse_args()
    if args.search_prompt:
        args.search = input('Subject or keyword (for example math): ').strip()
        if not args.search:
            return
    if args.search:
        terms = [args.search.casefold()]
        for code, entry in codebook().items():
            if args.search.casefold() == code.casefold():
                terms = [entry['name'].casefold()] + [x.casefold() for x in entry.get('aliases', [])]
        count = 0
        for path in ARCHIVE.glob('*.sidecar'):
            data = json.loads(path.read_text(encoding='utf-8'))
            haystack = json.dumps(data, ensure_ascii=False).casefold()
            if args.search.upper() in data.get('codes', []) or any(term in haystack for term in terms):
                print(data['path'])
                count += 1
        print(f'{count} matching files')
        return
    count = review = errors = 0
    paths = [p for p in args.root.rglob('*') if p.is_file() and p.suffix.lower() not in {'.sidecar', '.tmp', '.pyc'}]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(write_sidecar, path): path for path in paths}
        for future in as_completed(futures):
            try:
                data = future.result()
                count += 1
                review += data['classification_status'] == 'needs_classification'
                if count % 250 == 0:
                    print(f'Recorded {count}/{len(paths)}', flush=True)
            except Exception as exc:
                print(f'ERROR {futures[future]}: {exc}')
                errors += 1
    print(json.dumps({'recorded': count, 'needs_classification': review, 'errors': errors}))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
