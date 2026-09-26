"""Readable, source-preserving projection; never a Lean verification claim."""
import hashlib,json,re
from pathlib import Path
import output_layout as layout
import lean_record_package

def render(root,row):
    root=Path(root);h=row['sha256'];uid=layout.paper_uuid(h)
    explanation=layout.explanation(root,h)
    source=layout.source_copy(root,h,Path(row.get('source',row.get('path','source.lean'))).suffix)
    if not explanation.is_file() or not source.is_file():return None
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Combined paper source hash mismatch')
    original=raw.decode('utf-8')
    text=explanation.read_text(encoding='utf-8')
    # Publisher already appends the original; render it once in its own section.
    text=text.split('<!-- SOURCE_CODE_APPENDIX -->',1)[0].rstrip()
    text=re.sub(r'\nPaper UUID: `[^`]+`\s*$','',text)
    match=re.search(r'^# (.+)$',text,re.M)
    title=match.group(1).strip() if match else Path(row.get('source','Lean paper')).stem.replace('_',' ')
    title=re.sub(r'[<>:"/\\|?*\x00-\x1f]',' ',title)
    title=re.sub(r'\s+',' ',title).strip(' .')[:100] or 'Lean explanation'
    source_name=Path(row.get('source',row.get('path',''))).stem
    aliases=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',source_name).replace('_',' ')
    # Name topics only when explicitly present in source headings/name or the explanation title.
    naming_context=source_name+' '+title+' '+ '\n'.join(x for x in original.splitlines()[:60] if x.lstrip().startswith(('--','#')))
    topics=[]
    if re.search(r'master[ _-]*equation',naming_context,re.I):topics.append('Master Equation')
    law=re.search(r'\blaw[ _-]*(\d{1,2})\b',naming_context,re.I)
    if law:topics.append('Law '+law[1])
    readable=' — '.join(topics+[title])
    target=root/'OUTBOX/00_READ_PAPERS'/f'{readable[:130]} -- {uid}.md'
    sessions=root/'OUTBOX/04_SESSION_REPORTS'/f'{uid}.jsonl'
    events=[]
    if sessions.exists():
        for line in sessions.read_text(encoding='utf-8').splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
    receipt=layout.completion(root,h,row.get('provider','deepseek'))
    receipt_text=receipt.read_text(encoding='utf-8') if receipt.exists() else 'No completion receipt available.'
    opening = re.search(r'^## What this Lean file establishes\s*\n(.*?)(?=^## |\Z)', text, re.M|re.S)
    if opening:
        overview = opening.group(1).strip()
    else:
        paragraphs = re.split(r'\n\s*\n', re.sub(r'^# [^\n]*\n', '', text, count=1).strip())
        overview = next((part for part in paragraphs if part.strip() and not part.lstrip().startswith(('#', '<!--', '---'))), 'See the explanation below for the encoded results.')
        overview = 'From the existing explanation:\n\n' + overview
    overview += '\n\n**Verification in this run:** source read and explained; Lean was not compiled.\n\n**Source version:** `' + h + '`\n\n**Assumptions:** those in the original declarations and explanation below remain required; no assumptions were removed by this summary.'
    classification, atoms = lean_record_package.build(root,row,text,original)
    sections=[('CLASSIFICATION','Proof review and classification',classification), ('OVERVIEW','What this Lean file establishes',overview), ('EXPLANATION','Explanation',text)]
    rewrites=list((root/'OUTBOX/02_REWRITTEN_PAPERS').glob('*'+uid+'*.md'))
    if rewrites:
        sections.append(('REWRITTEN','Rewritten paper',rewrites[0].read_text(encoding='utf-8')))
    fence='`'*max(3,1+max((len(m) for m in re.findall(r'`+',original)),default=0))
    sections.append(('ORIGINAL','Original Lean source',f'SHA-256: `{h}`\n\nUnchanged original file: [{source.name}]({source.as_posix()})\n\n'+fence+'lean\n'+original+('' if original.endswith('\n') else '\n')+fence))
    sections.append(('ATOMS','Atom records and remaining work',atoms))
    summary={'paper_uuid':uid,'source':row.get('source',row.get('path','')),'source_sha256':h,'title':title,'search_terms':topics+[aliases],'status':row.get('status','DRAFT_READY'),'rewritten_paper':'included' if rewrites else 'Not produced; rewriting deferred','verification':'Explanation of source; no new Lean compilation','master_list':str(root/'OUTBOX/03_MASTER_LIST/MASTER_LIST.csv')}
    sections.append(('RECORD','Paper record','```json\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n```'))
    history='\n'.join(f"- {e.get('finished_utc') or e.get('started_utc','')} | {e.get('status','')} | Session {e.get('session_id','historical')}"+((' | '+e['error']) if e.get('error') else '') for e in events)
    sections.append(('SESSIONS','Processing history',history or 'No recorded session events available.'))
    sections.append(('RECEIPT','Completion receipt','```json\n'+receipt_text+'\n```'))
    result=f'# {readable}\n\nPaper UUID: `{uid}`\n\nSearch terms: '+ '; '.join(topics+[aliases])+'\n\n'
    for key,label,body in sections:
        begin=f'<!-- PAPER_SECTION:{uid}:{key}:BEGIN -->'
        end=f'<!-- PAPER_SECTION:{uid}:{key}:END -->'
        if begin in body or end in body:raise ValueError('Section delimiter collision')
        result+='---\n\n'+begin+'\n## '+label+'\n\n'+body+'\n\n'+end+'\n\n'
    # Preserve former presentation versions if a title changes.
    target.parent.mkdir(parents=True,exist_ok=True)
    for prior in target.parent.glob('*'+uid+'.md'):
        if prior!=target:
            archive=root/'BACKUPS/previous-combined-papers'/prior.name
            archive.parent.mkdir(parents=True,exist_ok=True)
            if archive.exists() and archive.read_bytes()!=prior.read_bytes():
                archive=archive.with_name(archive.stem+'-'+hashlib.sha256(prior.read_bytes()).hexdigest()[:8]+'.md')
            if not archive.exists():layout.atomic_bytes(archive,prior.read_bytes())
            prior.unlink()
    layout.atomic_bytes(target,result.encode('utf-8'))
    return target
