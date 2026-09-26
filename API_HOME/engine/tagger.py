from __future__ import annotations
import json,re,sqlite3
from pathlib import Path
from .paths import API_HOME,external

def tags(): return json.loads((API_HOME/'config/tags.json').read_text(encoding='utf-8'))
def score_text(text:str, tag:str)->tuple[int,str,str]:
 words=[w for w in re.findall(r"[a-z0-9]+",tag.lower()) if len(w)>2]
 low=text.lower(); hits=sum(low.count(w) for w in words)
 score=min(10, round(10*hits/max(8,len(re.findall(r'\w+',text))**.5))) if hits else 0
 match=next((line.strip() for line in text.splitlines() if any(w in line.lower() for w in words)),"")
 return score,(f"Local lexical pass found {hits} relevant term occurrence(s)." if hits else "No local lexical signal."),match[:300]
def ensure_db(db:Path):
 db.parent.mkdir(parents=True,exist_ok=True)
 con=sqlite3.connect(db); con.execute('CREATE TABLE IF NOT EXISTS tag_scores (item_id TEXT, kind TEXT, tag TEXT, score INTEGER, reason TEXT, quote_or_ts TEXT, path TEXT, PRIMARY KEY(item_id,kind,tag))'); return con
def tag_item(item_id:str,kind:str,path:Path,text:str):
 values=[]
 with ensure_db(external('catalog_db',required=False)) as con:
  for tag in tags():
   score,reason,quote=score_text(text,tag); values.append({'tag':tag,'score':score,'reason':reason,'quote_or_ts':quote})
   con.execute('INSERT OR REPLACE INTO tag_scores VALUES (?,?,?,?,?,?,?)',(item_id,kind,tag,score,reason,quote,str(path)))
 return values
def find(tag:str,minimum:int=5):
 with ensure_db(external('catalog_db',required=False)) as con:
  return con.execute('SELECT item_id,kind,tag,score,reason,quote_or_ts,path FROM tag_scores WHERE lower(tag)=lower(?) AND score>=? ORDER BY score DESC,item_id',(tag,minimum)).fetchall()
