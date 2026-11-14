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
def build_analysis_report(reconstructed:dict,metadata:dict)->dict:
 files={}
 for path,item in reconstructed['files'].items():
  evidence=list(item.get('line_evidence',{}).values())
  files[path]={'observed_line_count':len(item['observed_lines']),'missing_line_count':len(item['missing_lines']),'observed_lines':item['observed_lines'],'missing_lines':item['missing_lines'],'confidence_counts':{level:sum(1 for x in evidence if str(x.get('confidence','low')).lower()==level) for level in ('high','medium','low')}}
 return {'report_version':1,'generator':'VideoMind AI','created_for':'Coding tutorial source reconstruction','source':metadata.get('source'),'video_duration_seconds':metadata.get('duration_seconds'),'analysis_range_seconds':metadata.get('analysis_range_seconds'),'analysis_range':metadata.get('analysis_range'),'model':metadata.get('model'),'frame_interval_seconds':metadata.get('frame_interval_seconds'),'scene_change_threshold':metadata.get('scene_change_threshold'),'uniform_frames':metadata.get('uniform_frames',0),'scene_change_frames':metadata.get('scene_change_frames',0),'selected_frames':metadata.get('selected_frames',0),'observations':metadata.get('observations',0),'detected_scene_timestamps':metadata.get('detected_scene_timestamps',[]),'reconstructed_file_count':len(files),'files':files,'warnings':['Missing lines are placeholders, not inferred code.','Review OCR and model-derived code before running or deploying.']}
def render_report_markdown(report:dict)->str:
 lines=['# VideoMind AI — Analysis Report','',f"- Source: {report.get('source') or 'unknown'}",f"- Video duration: {report.get('video_duration_seconds')} seconds",f"- Analysis range: {report.get('analysis_range') or 'Full video'}",f"- Model: {report.get('model') or 'unknown'}",f"- Uniform frames: {report.get('uniform_frames',0)}",f"- Scene-change frames: {report.get('scene_change_frames',0)}",f"- Frames sent for analysis: {report.get('selected_frames',0)}",f"- Valid code observations: {report.get('observations',0)}",f"- Reconstructed files: {report.get('reconstructed_file_count',0)}",'','## Detected scene changes']
 lines += [f"- {x}" for x in report.get('detected_scene_timestamps',[])] or ['- No scene changes detected above threshold']
 lines += ['','## Reconstructed files']
 for path,item in report.get('files',{}).items():
  lines += [f"### {path}",f"- Observed lines: {item['observed_line_count']}",f"- Missing lines: {item['missing_line_count']}",f"- Confidence labels: {item['confidence_counts']}"]
  if item['missing_lines']:lines.append(f"- Missing line numbers: {', '.join(map(str,item['missing_lines'][:100]))}")
 lines += ['','## Warnings']+[f"- {x}" for x in report.get('warnings',[])]
 return '\n'.join(lines)+'\n'
def write_project(output:Path,reconstructed:dict,metadata:dict|None=None)->Path:
 root=output/'project';root.mkdir(parents=True,exist_ok=True)
 for relative,item in reconstructed['files'].items():
  target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item['content'],encoding='utf-8')
 report=build_analysis_report(reconstructed,metadata or {})
 (root/'VIDEOMIND_ANALYSIS_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 (root/'VIDEOMIND_ANALYSIS_REPORT.md').write_text(render_report_markdown(report),encoding='utf-8')
 manifest={'generator':'VideoMind AI','note':'Missing lines are placeholders. Review reconstructed code before running.','metadata':metadata or {},'analysis_report':'VIDEOMIND_ANALYSIS_REPORT.json','files':{p:{'observed_lines':x['observed_lines'],'missing_lines':x['missing_lines']} for p,x in reconstructed['files'].items()}}
 (root/'VIDEOMIND_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');archive=output/'reconstructed-project.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in root.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(root))
 return archive
