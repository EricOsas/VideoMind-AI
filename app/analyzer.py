from __future__ import annotations
import base64,json,time
from pathlib import Path
from typing import Any
from .config import AI_API_KEY,AI_BASE_URL,AI_MODEL
PROMPT='''Read source code from each screenshot independently. Never invent unreadable code. Preserve spelling, punctuation and indentation. Identify visible file/tab and numbered lines. Return JSON only: {"observations":[{"image_index":0,"file_path":"src/main.py","visible_start_line":1,"visible_end_line":10,"code_lines":[{"line":1,"text":"exact code"}],"confidence":"high|medium|low","evidence":"visible tab and line-number cues"}]}. Empty code_lines if unreadable. OCR/transcript are supporting evidence only; verify against image.'''
def _url(p:Path):return 'data:image/jpeg;base64,'+base64.b64encode(p.read_bytes()).decode()
def _text(r:Any):
 c=r.choices[0].message.content
 return c if isinstance(c,str) else '\n'.join(x.get('text','') for x in c if isinstance(x,dict)) if isinstance(c,list) else str(c or '')
def _json(s:str):
 s=s.strip()
 if s.startswith('```'):s=s.split('\n',1)[-1].rsplit('```',1)[0]
 try:return json.loads(s)
 except json.JSONDecodeError:
  a,b=s.find('{'),s.rfind('}')
  if a>=0 and b>a:return json.loads(s[a:b+1])
  raise RuntimeError('Vision model returned invalid JSON: '+s[:500])
def extract_code_observations(frames:list[dict],transcript:list[dict],ocr_results:list[dict]|None=None):
 if not AI_API_KEY:raise RuntimeError('AI_API_KEY missing in .env')
 from openai import OpenAI
 client=OpenAI(base_url=AI_BASE_URL,api_key=AI_API_KEY,timeout=180);ocr={round(x['timestamp'],3):x.get('text','') for x in (ocr_results or [])};captions='\n'.join(f"[{x['start']:.1f}s] {x['text']}" for x in transcript)[:18000];out=[]
 for offset in range(0,len(frames),6):
  batch=frames[offset:offset+6]; content=[{'type':'text','text':PROMPT+'\nTranscript context only:\n'+(captions or 'None')}]
  for i,f in enumerate(batch):
   content.append({'type':'text','text':f"IMAGE_INDEX={i}; VIDEO_TIMESTAMP_SECONDS={f['timestamp']:.3f}; LOCAL OCR (noisy; verify):\n{ocr.get(round(f['timestamp'],3),'')[:10000]}"});content.append({'type':'image_url','image_url':{'url':_url(Path(f['path']))}})
  response=client.chat.completions.create(model=AI_MODEL,messages=[{'role':'user','content':content}],temperature=0,max_tokens=12000)
  for obs in _json(_text(response)).get('observations',[]):
   i=int(obs.get('image_index',-1))
   if 0<=i<len(batch):obs['timestamp']=batch[i]['timestamp'];obs['evidence']=batch[i]['label']+' — '+str(obs.get('evidence',''));out.append(obs)
  if offset+6<len(frames):time.sleep(2.05)
 return out,AI_MODEL
