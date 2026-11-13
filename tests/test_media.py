from PIL import Image,ImageDraw
from app.media import select_changed_frames

def test_visual_difference_retains_changed_frame(tmp_path):
    frames=[]
    for i in range(3):
        im=Image.new('RGB',(640,360),'white')
        if i==2: ImageDraw.Draw(im).rectangle((80,80,560,280),fill='black')
        p=tmp_path/f'{i}.jpg'; im.save(p); frames.append({'timestamp':i,'label':str(i),'path':str(p)})
    chosen=select_changed_frames(frames,1.5)
    assert chosen[0]['timestamp']==0 and chosen[-1]['timestamp']==2
