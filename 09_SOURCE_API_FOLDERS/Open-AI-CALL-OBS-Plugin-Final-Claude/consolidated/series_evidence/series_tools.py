"""Exact duplicate quarantine and source-manifest series reader. No paid calls."""
import argparse,json,os,re
from pathlib import Path
from .ckg import scan,save,digest,uid,now,atomic,initialize,lock

def quarantine(root):
    items,_=scan(root);events=[]
    for item in items:
        keeper=Path(item['path'])
        for extra in item['locations'][1:]:
            source=Path(extra).resolve()
            allowed=[(root/'INBOX'/n).resolve() for n in ['01_PRIORITY','02_SERIES','03_GENERAL']]
            allowed += [p.resolve() for p in (root/'STATIONS').glob('*/INBOX')]
            if not any(source.is_relative_to(p) for p in allowed):raise ValueError('Duplicate outside active inbox')
            if digest(source.read_bytes())!=item['sha256'] or digest(keeper.read_bytes())!=item['sha256']:raise ValueError('Duplicate changed')
            dest=root/'INBOX/99_DUPLICATES'/item['sha256']/source.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():dest=dest.with_name(uid(str(source))+dest.suffix)
            if dest.exists():raise ValueError('Quarantine destination exists')
            event={'source':str(source),'destination':str(dest),'keeper':str(keeper),'sha256':item['sha256'],'state':'planned','time':now()}
            receipt=root/'STATE/CKG/duplicates'/(uid(str(source)+now())+'.json');save(receipt,event)
            source.rename(dest);event['state']='moved';save(receipt,event);events.append(event)
    return events

def compile_series(root):
    items,_=scan(root);groups={}
    for item in items:
        if not item['series']:continue
        raw=Path(item['path']).read_text(encoding='utf-8-sig')
        from .ckg import source_blocker
        if source_blocker(raw):continue
        groups.setdefault(item['series'],[]).append(item)
    reports=[]
    for series,members in groups.items():
        directory=root/'OUTBOX/04_BY_SERIES'/re.sub(r'[<>:"/\\|?*]',' ',series)
        manifest=[];body=['# '+series+' — Complete Series Reader','',
            'Combined individual reviews, not a new AI synthesis. Missing reviews are listed explicitly.','']
        for n,item in enumerate(members,1):
            paper=uid('paper-version:'+item['sha256'])
            candidates=list((root/'SYSTEM/RECORDS'/paper).glob('*.json'))
            record=max(candidates,key=lambda p:p.stat().st_mtime) if candidates else None
            entry={'source':item['path'],'sha256':item['sha256'],'paper_uuid':paper,'status':'MISSING_REVIEW'}
            if record:
                data=json.loads(record.read_text(encoding='utf-8'))
                source_bytes=Path(item['path']).read_bytes()
                if data['source_sha256']!=digest(source_bytes):raise ValueError('Series source changed')
                entry.update(status='INCLUDED',record=str(record),record_sha256=digest(record.read_bytes()))
                body += ['## '+str(n)+'. '+data['title'],'',data['overview']['markdown']]
                for key,section in data['sections'].items():body += ['### '+key,section['markdown'],'']
            else:body += ['## '+str(n)+'. '+Path(item['path']).name,'Review missing; synthesis must not claim full coverage.','']
            manifest.append(entry)
        save(directory/'00_SERIES_MANIFEST.json',{'series':series,'members':manifest,'order':'intake path order; editorial ordering not inferred','synthesis_status':'NOT_RUN'})
        atomic(directory/'00_COMPLETE_SERIES_READER.md','\n'.join(body).encode())
        reports.append({'series':series,'members':len(members),'included':sum(x['status']=='INCLUDED' for x in manifest)})
    return reports

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--duplicates',action='store_true');ap.add_argument('--synthesize',action='store_true');a=ap.parse_args()
    root=a.root.resolve();initialize(root)
    with lock(root):
        reports=quarantine(root) if a.duplicates else compile_series(root)
        print(json.dumps(reports,indent=2))
        if a.synthesize:
            from .ckg import read,GUARD
            from .providers import Provider
            key=os.environ.get('DEEPSEEK_API_KEY')
            if not key and (root/'CONFIG/keys.local.json').exists():key=read(root/'CONFIG/keys.local.json').get('DEEPSEEK_API_KEY')
            if not key:raise ValueError('DeepSeek credential missing')
            provider=Provider('deepseek',read(root/'CONFIG/ckg.json')['model'],key,timeout=180)
            for report in reports:
                if report['included']!=report['members']:
                    print('Synthesis blocked: missing member reviews for '+report['series']);continue
                folder=root/'OUTBOX/04_BY_SERIES'/re.sub(r'[<>:"/\\|?*]',' ',report['series'])
                manifest=read(folder/'00_SERIES_MANIFEST.json')
                fingerprint=digest(json.dumps(manifest,sort_keys=True).encode())
                receipt=folder/'SCRIPTS'/('synthesis-'+fingerprint+'.json')
                if receipt.exists():print('Already synthesized '+report['series']);continue
                abstracts=[]
                for entry in manifest['members']:
                    record=read(entry['record'])
                    abstracts.append({'paper_uuid':record['paper_uuid'],'title':record['title'],'overview':record['overview'],'objects':record['objects']})
                packet=json.dumps(abstracts,ensure_ascii=False)
                if len(packet)>90000:raise ValueError('Series exceeds synthesis budget; hierarchical synthesis required')
                result=provider.complete(GUARD+'\nFor this call return Markdown, not JSON. Write one connected series-level paper from these reviewed summaries and source-anchored objects. Cite member UUIDs. Cover every member, dependencies, competing versions, strongest argument, gaps, contradictions and next tests. Do not rank versions by date alone. This is synthesis of review records, not independent source verification.\n'+packet,8192,str(__import__('uuid').uuid4()))
                atomic(folder/'00_SERIES_SYNTHESIS.md',result.text.encode())
                save(receipt,{'manifest_sha256':fingerprint,'input_kind':'review overviews and source-anchored objects','usage':result.usage,'output_sha256':digest(result.text.encode()),'status':'AI_DRAFT_REQUIRES_REVIEW'})
if __name__=='__main__':main()
