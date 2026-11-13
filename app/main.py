from __future__ import annotations
import json,shutil,uuid
from pathlib import Path
from fastapi import FastAPI,File,Form,HTTPException,UploadFile,BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import JOBS,OUTPUTS,STATIC,MAX_UPLOAD_MB,FRAME_INTERVAL_SECONDS,FRAME_CHANGE_THRESHOLD,MAX_VIDEO_MINUTES
from . import media
from .analyzer import extract_code_observations
from .timeline import reconstruct,write_project
app=FastAPI(title='VideoMind AI',version='0.3.0');app.mount('/static',StaticFiles(directory=STATIC),name='static')
def write_job(job_id,data): (JOBS/f'{job_id}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def read_job(job_id):
 p=JOBS/f'{job_id}.json'
 if not p.exists():raise HTTPException(404,'Job not found')
 return json.loads(p.read_text(encoding='utf-8'))
def process_job(job_id,video_path,subtitle_path):
 job_dir=JOBS/job_id
 try:
  data=read_job(job_id);data.update(status='processing',stage='Inspecting video',progress=8);write_job(job_id,data);media.require_ffmpeg();meta=media.probe(video_path)
  if meta['duration']<=0:raise RuntimeError('Could not read video duration')
  if meta['duration']>MAX_VIDEO_MINUTES*60:raise RuntimeError(f'Video exceeds {MAX_VIDEO_MINUTES} minute limit')
  frames_all=media.extract_frames(video_path,job_dir/'frames',FRAME_INTERVAL_SECONDS);frames=media.select_changed_frames(frames_all,FRAME_CHANGE_THRESHOLD)
  data.update(stage='Running local Tesseract OCR',progress=25,frame_count=len(frames));write_job(job_id,data);ocr=media.run_local_ocr(frames);transcript=media.parse_vtt(subtitle_path) if subtitle_path else []
  data.update(stage=f'Sending {len(frames)} visual checkpoints to Coarena',progress=35,transcript_count=len(transcript));write_job(job_id,data);observations,model=extract_code_observations(frames,transcript,ocr)
  data.update(stage='Reconstructing source files',progress=82,observation_count=len(observations));write_job(job_id,data);result=reconstruct(observations)
  if not result['files']:raise RuntimeError('No readable numbered source code detected. Use a clearer video with visible line numbers.')
  archive=write_project(OUTPUTS/job_id,result,{'duration_seconds':meta['duration'],'source':data.get('source'),'model':model,'selected_frames':len(frames),'local_ocr_frames':len(ocr),'observations':len(observations)})
  summary={'model':model,'metadata':meta,'file_count':len(result['files']),'files':{p:{'observed_line_count':len(x['observed_lines']),'missing_line_count':len(x['missing_lines'])} for p,x in result['files'].items()},'download_url':f'/api/jobs/{job_id}/download','warning':'Review all reconstructed files. Missing lines are placeholders; generated code may not compile.'}
  (job_dir/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');data.update(status='completed',stage='Project reconstructed',progress=100,file_count=len(result['files']),download_url=summary['download_url']);write_job(job_id,data)
 except Exception as exc:
  data=read_job(job_id);data.update(status='failed',stage='Failed',error=str(exc),progress=100);write_job(job_id,data)
@app.get('/')
def home():return FileResponse(STATIC/'index.html')
@app.get('/api/health')
def health():
 from .config import AI_API_KEY
 return {'ok':True,'ai_configured':bool(AI_API_KEY)}
@app.post('/api/analyze')
async def analyze(background:BackgroundTasks,video:UploadFile|None=File(default=None),youtube_url:str=Form(default=''),subtitles:UploadFile|None=File(default=None),cloud_consent:bool=Form(default=False)):
 if not cloud_consent:raise HTTPException(400,'Confirm the Coarena data-retention notice first')
 if bool(video and video.filename)==bool(youtube_url.strip()):raise HTTPException(400,'Provide exactly one video upload or YouTube URL')
 job_id=uuid.uuid4().hex[:12];folder=JOBS/job_id;folder.mkdir(parents=True,exist_ok=True)
 try:
  if youtube_url.strip():
   if not youtube_url.startswith(('https://www.youtube.com/','https://youtube.com/','https://youtu.be/')):raise HTTPException(400,'Enter a standard YouTube URL')
   source=media.download_youtube(youtube_url.strip(),folder);captions=sorted(folder.glob('source*.vtt'));subtitle=captions[0] if captions else None
  else:
   suffix=Path(video.filename).suffix.lower()
   if suffix not in media.VIDEO_EXTS:raise HTTPException(400,'Unsupported video type')
   source=folder/f'source{suffix}';size=0
   with source.open('wb') as out:
    while chunk:=await video.read(1024*1024):
     size+=len(chunk)
     if size>MAX_UPLOAD_MB*1024*1024:raise HTTPException(413,f'Video exceeds {MAX_UPLOAD_MB} MB')
     out.write(chunk)
   subtitle=None
  if subtitles and subtitles.filename:
   if Path(subtitles.filename).suffix.lower() not in {'.vtt','.srt'}:raise HTTPException(400,'Subtitle must be VTT or SRT')
   subtitle=folder/f'captions{Path(subtitles.filename).suffix.lower()}';subtitle.write_bytes(await subtitles.read())
   if subtitle.suffix=='.srt':
    converted=folder/'captions.vtt';media.run(['ffmpeg','-y','-i',str(subtitle),str(converted)]);subtitle=converted
  write_job(job_id,{'id':job_id,'status':'queued','stage':'Queued','progress':0,'source':'youtube' if youtube_url.strip() else 'upload'});background.add_task(process_job,job_id,source,subtitle);return {'job_id':job_id,'status':'queued'}
 except HTTPException:shutil.rmtree(folder,ignore_errors=True);raise
 except Exception as exc:shutil.rmtree(folder,ignore_errors=True);raise HTTPException(400,str(exc))
@app.get('/api/jobs/{job_id}')
def status(job_id:str):return read_job(job_id)
@app.get('/api/jobs/{job_id}/download')
def download(job_id:str):
 if read_job(job_id).get('status')!='completed':raise HTTPException(409,'Project not ready')
 p=OUTPUTS/job_id/'reconstructed-project.zip'
 if not p.exists():raise HTTPException(404,'Archive not found')
 return FileResponse(p,media_type='application/zip',filename='VideoMind-Reconstructed-Project.zip')
