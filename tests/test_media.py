from types import SimpleNamespace
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

def test_focused_range_args_use_start_and_duration():
    assert media._range_args(30,43)==['-ss','30.000','-t','13.000']
    assert media._range_args(0,None)==['-ss','0.000']

def test_scene_detection_returns_video_timestamps(tmp_path,monkeypatch):
    def fake_run(cmd,**kwargs):
        for i in range(2):
            Image.new('RGB',(32,32),'white').save(tmp_path/f'scene-{i+1:08d}.jpg')
        return SimpleNamespace(returncode=0,stdout='',stderr='pts_time:2.500\\npts_time:7.250\\n')
    monkeypatch.setattr(media.subprocess,'run',fake_run)
    scenes=media.extract_scene_frames(tmp_path/'video.mp4',tmp_path,0.25,start=30,end=45)
    assert [x['timestamp'] for x in scenes]==[32.5,37.25]
    assert all(x['kind']=='scene_change' for x in scenes)
