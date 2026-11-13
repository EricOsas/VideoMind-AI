from __future__ import annotations
import json,os,re,shutil,subprocess
from pathlib import Path
from typing import Any
VIDEO_EXTS={'.mp4','.mov','.mkv','.webm','.avi','.mpeg','.mpg','.m4v'}
def run(cmd:list[str],timeout:int=3600)->str:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-2500:])
 return p.stdout
def require_ffmpeg():
 if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): raise RuntimeError('FFmpeg and FFprobe are required on PATH.')
def probe(path:Path)->dict[str,Any]:
 d=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)])); v=next((x for x in d.get('streams',[]) if x.get('codec_type')=='video'),{})
 return {'duration':float(d.get('format',{}).get('duration',0)),'width':v.get('width'),'height':v.get('height')}
def download_youtube(url:str,target:Path)->Path:
 run(['yt-dlp','--no-playlist','--restrict-filenames','--write-subs','--write-auto-subs','--sub-langs','en.*,en','--sub-format','vtt/best','--convert-subs','vtt','-f','bv*+ba/b','--merge-output-format','mp4','-o',str(target/'source.%(ext)s'),url],7200)
 found=[p for p in target.glob('source.*') if p.suffix.lower() in VIDEO_EXTS]
 if not found: raise RuntimeError('No supported video downloaded.')
 return max(found,key=lambda p:p.stat().st_size)
def format_time(s:float)->str:
 n=max(0,int(s)); return f'{n//3600:02d}:{n%3600//60:02d}:{n%60:02d}'
def extract_frames(video:Path,out:Path,interval:int=1)->list[dict[str,Any]]:
 out.mkdir(parents=True,exist_ok=True); run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(video),'-vf',f"fps=1/{interval},scale='min(1440,iw)':-2",'-q:v','3','-vsync','0',str(out/'frame-%08d.jpg'),'-y'])
 return [{'timestamp':i*interval,'label':format_time(i*interval),'path':str(p)} for i,p in enumerate(sorted(out.glob('frame-*.jpg')))]
def select_changed_frames(frames:list[dict[str,Any]],threshold:float=1.5)->list[dict[str,Any]]:
 if len(frames)<=2:return frames
 from PIL import Image,ImageChops,ImageStat,ImageFilter
 def sig(p):
  with Image.open(p) as im:
   g=im.convert('L').resize((480,270)); return g.copy(),g.filter(ImageFilter.FIND_EDGES).copy()
 keep=[frames[0]]; pg,pe=sig(frames[0]['path'])
 for f in frames[1:-1]:
  cg,ce=sig(f['path']); px=ImageStat.Stat(ImageChops.difference(pg,cg)).mean[0]; ed=ImageStat.Stat(ImageChops.difference(pe,ce)).mean[0]; score=.65*px+.35*ed
  if score>=threshold:keep.append({**f,'difference_score':round(score,3)});pg,pe=cg,ce
 if keep[-1]['path']!=frames[-1]['path']:keep.append(frames[-1])
 return keep
def run_local_ocr(frames:list[dict[str,Any]])->list[dict[str,Any]]:
 import pytesseract
 from PIL import Image,ImageOps,ImageEnhance
 cmd=os.getenv('TESSERACT_CMD','').strip()
 if cmd:pytesseract.pytesseract.tesseract_cmd=cmd
 if not Path(pytesseract.pytesseract.tesseract_cmd).exists() and not shutil.which('tesseract'):raise RuntimeError('Install Tesseract: winget install --id UB-Mannheim.TesseractOCR -e')
 out=[]
 for f in frames:
  with Image.open(f['path']) as im:
   d=pytesseract.image_to_data(ImageEnhance.Contrast(ImageOps.grayscale(im)).enhance(1.6),config='--oem 3 --psm 6',output_type=pytesseract.Output.DICT)
  groups={};words=[]
  for i,raw in enumerate(d.get('text',[])):
   w=str(raw).strip()
   try:c=float(d['conf'][i])
   except (ValueError,TypeError,KeyError):c=-1
   if not w or c<25:continue
   k=(d['block_num'][i],d['par_num'][i],d['line_num'][i]);groups.setdefault(k,[]).append(w);words.append({'text':w,'confidence':round(c/100,3),'left':int(d['left'][i]),'top':int(d['top'][i]),'width':int(d['width'][i]),'height':int(d['height'][i])})
  out.append({'timestamp':f['timestamp'],'text':'\n'.join(' '.join(v) for v in groups.values())[:12000],'words':words[:2500]})
 return out
def parse_vtt(path:Path)->list[dict[str,Any]]:
 text=path.read_text(encoding='utf-8-sig',errors='replace');out=[]
 for block in re.split(r'\n\s*\n',text.replace('\r','\n')):
  lines=[x.strip() for x in block.splitlines() if x.strip()]; t=next((x for x in lines if '-->' in x),None)
  if not t:continue
  a,b=[x.strip().split()[0] for x in t.split('-->',1)]; parts=[float(x) for x in a.replace(',','.').split(':')]; start=parts[-1]+(parts[-2]*60 if len(parts)>1 else 0)+(parts[-3]*3600 if len(parts)>2 else 0); parts=[float(x) for x in b.replace(',','.').split(':')]; end=parts[-1]+(parts[-2]*60 if len(parts)>1 else 0)+(parts[-3]*3600 if len(parts)>2 else 0)
  body=re.sub(r'<[^>]+>',' ',' '.join(lines[lines.index(t)+1:])).strip()
  if body:out.append({'start':start,'end':end,'text':body})
 return out
