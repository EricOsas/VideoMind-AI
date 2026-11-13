from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from typing import Any
import json,re,zipfile
def clean_path(value:str|None)->str:
 raw=re.sub(r'^[A-Za-z]:','',(value or '').replace('\\','/')).lstrip('/');parts=[x for x in raw.split('/') if x not in {'','.','..'}];return '/'.join(parts) or 'unknown_file.txt'
def placeholder(path:str,n:int)->str:
 ext=Path(path).suffix.lower();prefix='//' if ext in {'.js','.jsx','.ts','.tsx','.java','.c','.h','.cpp','.cs','.go','.rs','.php'} else '#';return f'{prefix} MISSING LINE {n}: not legible in source video'
def reconstruct(observations:list[dict[str,Any]])->dict:
 tracks=defaultdict(dict);provenance=defaultdict(dict);valid=[]
 for obs in sorted(observations,key=lambda x:float(x.get('timestamp',0))):
  try:start=int(obs['visible_start_line'])
  except (KeyError,TypeError,ValueError):continue
  path=clean_path(obs.get('file_path'));lines={}
  for entry in obs.get('code_lines',[]):
   try:n=int(entry['line']);value=entry['text']
   except (KeyError,TypeError,ValueError):continue
   if n>0 and isinstance(value,str):lines[n]=value.rstrip('\r\n')
  if not lines:continue
  valid.append(obs)
  for n,value in lines.items():
   old=tracks[path].get(n);tracks[path][n]=value;provenance[path][n]={'timestamp':float(obs.get('timestamp',0)),'confidence':obs.get('confidence','low'),'changed_from_previous':old is not None and old!=value}
 files={}
 for path,lines in tracks.items():
  maximum=max(lines);missing=[n for n in range(1,maximum+1) if n not in lines];content='\n'.join(lines.get(n,placeholder(path,n)) for n in range(1,maximum+1))+'\n';files[path]={'content':content,'observed_lines':sorted(lines),'missing_lines':missing,'line_evidence':{str(k):v for k,v in provenance[path].items()}}
 return {'files':files,'observation_count':len(valid)}
def write_project(output:Path,reconstructed:dict,metadata:dict|None=None)->Path:
 root=output/'project';root.mkdir(parents=True,exist_ok=True)
 for relative,item in reconstructed['files'].items():
  target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item['content'],encoding='utf-8')
 manifest={'generator':'VideoMind AI','note':'Missing lines are placeholders. Review reconstructed code before running.','metadata':metadata or {},'files':{p:{'observed_lines':x['observed_lines'],'missing_lines':x['missing_lines']} for p,x in reconstructed['files'].items()}}
 (root/'VIDEOMIND_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');archive=output/'reconstructed-project.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in root.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(root))
 return archive
