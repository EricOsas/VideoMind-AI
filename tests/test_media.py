from types import SimpleNamespace
from pathlib import Path
import shutil,subprocess
import pytest
from PIL import Image,ImageDraw
from app import media
from app.media import select_changed_frames

def test_visual_difference_retains_changed_frame(tmp_path):
    frames=[]
    for i in range(3):
        im=Image.new('RGB',(640,360),'white')
        if i==2: ImageDraw.Draw(im).rectangle((80,80,560,280),fill='black')
        p=tmp_path/f'{i}.jpg'; im.save(p); frames.append({'timestamp':i,'label':str(i),'path':str(p)})
    chosen=select_changed_frames(frames,1.5)
    assert chosen[0]['timestamp']==0 and chosen[-1]['timestamp']==2

def test_download_youtube_enables_available_js_runtime(tmp_path,monkeypatch):
    captured={}
    def fake_run(cmd,timeout=0):
        captured['cmd']=cmd
        (tmp_path/'source.mp4').write_bytes(b'x')
        return ''
    monkeypatch.setattr(media,'run',fake_run)
    monkeypatch.setattr(media.shutil,'which',lambda name: 'C:/node/node.exe' if name=='node' else None)
    media.download_youtube('https://youtu.be/bJTnI0tWi5k',tmp_path)
    cmd=captured['cmd']
    assert '--js-runtimes' in cmd
    assert cmd[cmd.index('--js-runtimes')+1]=='node'
    assert '--remote-components' in cmd
    assert cmd[cmd.index('--remote-components')+1]=='ejs:github'
    assert '--socket-timeout' in cmd
    assert '--retries' in cmd
    has_curl_cffi=True
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        has_curl_cffi=False
    assert ('--impersonate' in cmd)==has_curl_cffi

def test_download_youtube_omits_js_runtime_when_none_available(tmp_path,monkeypatch):
    captured={}
    def fake_run(cmd,timeout=0):
        captured['cmd']=cmd
        (tmp_path/'source.mp4').write_bytes(b'x')
        return ''
    monkeypatch.setattr(media,'run',fake_run)
    monkeypatch.setattr(media.shutil,'which',lambda name: None)
    media.download_youtube('https://youtu.be/bJTnI0tWi5k',tmp_path)
    assert '--js-runtimes' not in captured['cmd']

def test_focused_range_args_use_start_and_duration():
    assert media._range_args(30,43)==['-ss','30.000','-t','13.000']
    assert media._range_args(0,None)==['-ss','0.000']

def test_scene_detection_returns_video_timestamps(tmp_path,monkeypatch):
    captured={}
    def fake_run(cmd,**kwargs):
        captured['cmd']=cmd
        for i in range(2):
            Image.new('RGB',(32,32),'white').save(tmp_path/f'scene-{i+1:08d}.jpg')
        return SimpleNamespace(returncode=0,stdout='',stderr='pts_time:2.500\\npts_time:7.250\\n')
    monkeypatch.setattr(media.subprocess,'run',fake_run)
    scenes=media.extract_scene_frames(tmp_path/'video.mp4',tmp_path,0.25,start=30,end=45)
    assert [x['timestamp'] for x in scenes]==[32.5,37.25]
    assert all(x['kind']=='scene_change' for x in scenes)
    vf=captured['cmd'][captured['cmd'].index('-vf')+1]
    assert 'format=yuvj420p' in vf

@pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='ffmpeg not installed')
def test_scene_detection_encodes_limited_range_av1_video(tmp_path):
    video=tmp_path/'limited.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc=size=320x240:rate=10:duration=2','-f','lavfi','-i','color=black:size=320x240:rate=10:duration=2','-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p','-color_range','tv','-c:v','libx264','-pix_fmt','yuv420p',str(video),'-y'],check=True)
    scenes=media.extract_scene_frames(video,tmp_path/'scene',0.25,0,None)
    assert len(scenes)>=1
    assert all(Path(x['path']).exists() for x in scenes)

def test_focused_range_filters_transcript_cues_without_rewriting_them():
    cues=[
        {'start':1.0,'end':4.0,'text':'before'},
        {'start':29.0,'end':32.0,'text':'overlap start'},
        {'start':35.0,'end':38.0,'text':'inside'},
        {'start':44.0,'end':46.0,'text':'after'},
    ]
    assert media.filter_transcript_range(cues,30,43)==cues[1:3]
