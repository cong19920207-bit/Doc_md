"""Offline file/link audit for the approved core-document migration; no service writes."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
NEW = 'site/core-docs/prd'
EVIDENCE = ROOT / 'site/docs/design/core-docs-migration/execution/evidence'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mapped(path):
    return NEW + path[3:] if path == 'prd' or path.startswith('prd/') else path

def tracked():
    return [p.decode() for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0') if p]

def link_spans(text):
    # Inline links/images, reference definitions and HTML attributes. Keep URL text exact.
    for match in re.finditer(r'\]\(', text):
        start = match.end()
        end, depth = start, 1
        while end < len(text) and text[end] != '\n':
            if text[end] == '\\':
                end += 2
                continue
            if text[end] == '(':
                depth += 1
            elif text[end] == ')':
                depth -= 1
                if not depth:
                    break
            end += 1
        if depth:
            continue
        raw = text[start:end]
        trim = len(raw) - len(raw.lstrip())
        raw = raw.strip()
        start += trim
        if raw.startswith('<') and '>' in raw:
            yield start + 1, start + raw.index('>'), raw[1:raw.index('>')]
        else:
            title = re.search(r'\s+[\"\'].*[\"\']$', raw)
            value = raw[:title.start()] if title else raw
            yield start, start + len(value), value
    for match in re.finditer(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)', text, re.M):
        start, end = match.span(1)
        value = match.group(1)
        if value.startswith('<'):
            start, end, value = start + 1, end - 1, value[1:-1]
        yield start, end, value
    for match in re.finditer(r'\b(?:href|src)\s*=\s*([\"\'])(.*?)\1', text):
        yield match.start(2), match.end(2), match.group(2)

def resolve(source, value):
    value = unquote(value.split('#', 1)[0].split('?', 1)[0])
    if not value or value.startswith(('/', '#')) or re.match(r'[a-zA-Z][\w+.-]*:', value):
        return None
    path = Path(os.path.normpath(str((ROOT / source).parent / value)))
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return None

def verify():
    from collections import Counter
    baseline = json.loads((EVIDENCE / 'baseline.json').read_text())
    assert not (ROOT / 'prd').exists(), 'Old authority remains'
    expected_paths = {mapped(f['path']) for f in baseline['files']}
    actual_paths = {p.relative_to(ROOT).as_posix() for p in (ROOT / NEW).rglob('*') if p.is_file()}
    assert expected_paths == actual_paths, {'missing': sorted(expected_paths-actual_paths), 'extra': sorted(actual_paths-expected_paths)}
    changed = []
    for f in baseline['files']:
        p = ROOT / mapped(f['path'])
        assert not p.is_symlink(), str(p)
        assert p.stat().st_mode & 0o777 == f['mode'], f['path']
        if digest(p) != f['sha256']:
            changed.append(mapped(f['path']))
    expected_links = Counter((mapped(x['source']), mapped(x['target'])) for x in baseline['links'] if x['exists'])
    actual_links = Counter()
    for source in {key[0] for key in expected_links}:
        for _, _, value in link_spans((ROOT / source).read_text()):
            target = resolve(source, value)
            if target and (ROOT / target).exists():
                actual_links[(source, target)] += 1
    regressions = [{'source': s, 'target': t, 'missing_occurrences': n} for (s,t),n in (expected_links-actual_links).items()]
    assert not regressions, regressions
    manifest_checks = {}
    for source in ['llm-manifest.json', NEW + '/llm-manifest.json']:
        data = json.loads((ROOT / source).read_text())
        ids = [d['id'] for d in data['documents']]
        assert len(ids) == len(set(ids)), source
        paths = data['scan_roots'] + data.get('exclude_roots', []) + data.get('delegates_to', [])
        for doc in data['documents']:
            paths.append(doc['path'])
            paths.extend(doc.get('code_paths', []))
            if doc.get('delegates_to'):
                paths.append(doc['delegates_to'])
            assert set(doc.get('related_documents', []) + doc.get('depends_on', [])) <= set(ids), doc['id']
        assert all((ROOT / value).exists() for value in paths), [value for value in paths if not (ROOT / value).exists()]
        assert not any(value.startswith('prd/') for value in paths), source
        manifest_checks[source] = len(paths)
    brief_sources = 0
    for p in (ROOT / NEW / 'design').glob('*/brief/current.md'):
        source = re.search(r'^source: (.+)$', p.read_text(), re.M).group(1)
        assert source.startswith(NEW + '/') and (ROOT / source).is_file(), source
        brief_sources += 1
    # Step 4 adds one owned ignore block; the user's pre-existing rules must remain byte-identical.
    gitignore = (ROOT / '.gitignore').read_bytes()
    publication_ignore = '# 受控 Web 发布产物（从源码重新生成）\n/site/release/\n\n'.encode()
    assert gitignore.count(publication_ignore) <= 1
    assert hashlib.sha256(gitignore.replace(publication_ignore, b'')).hexdigest() == baseline['gitignore_sha256'], 'User .gitignore rules changed'
    chunks_before = json.loads((EVIDENCE / 'chunks-before.json').read_text())
    chunks_after = json.loads((EVIDENCE / 'chunks-after-ascii.json').read_text())
    assert chunks_before == chunks_after, 'Offline chunk evidence differs'
    result = {'physical_files': len(actual_paths), 'tracked_files': sum(f['tracked'] for f in baseline['files']),
              'unchanged_file_hashes': len(actual_paths)-len(changed), 'changed_files': changed,
              'valid_baseline_links': sum(expected_links.values()), 'link_regressions': regressions,
              'manifest_path_checks': manifest_checks, 'brief_source_checks': brief_sources,
              'saved_chunk_evidence_identical': True, 'user_gitignore_preserved': True,
              'runtime_verified': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    verify()
