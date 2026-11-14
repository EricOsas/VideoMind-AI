from pathlib import Path
import os
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
DATA=ROOT/'data'; JOBS=DATA/'jobs'; OUTPUTS=DATA/'outputs'; STATIC=ROOT/'static'
for p in (JOBS,OUTPUTS): p.mkdir(parents=True,exist_ok=True)
AI_BASE_URL=os.getenv('AI_BASE_URL','https://coarena.ai/api/v1').rstrip('/')
AI_API_KEY=os.getenv('AI_API_KEY','').strip()
AI_MODEL=os.getenv('AI_MODEL','gemini-3-8-flash')
MAX_UPLOAD_MB=int(os.getenv('MAX_UPLOAD_MB','1024'))
FRAME_INTERVAL_SECONDS=max(1,int(os.getenv('FRAME_INTERVAL_SECONDS','1')))
FRAME_CHANGE_THRESHOLD=float(os.getenv('FRAME_CHANGE_THRESHOLD','1.5'))
SCENE_CHANGE_THRESHOLD=min(1.0,max(0.01,float(os.getenv('SCENE_CHANGE_THRESHOLD','0.25'))))
MAX_VIDEO_MINUTES=int(os.getenv('MAX_VIDEO_MINUTES','120'))
