import threading
from fastapi.testclient import TestClient
from app import main as app_main

def test_youtube_download_runs_off_event_loop(monkeypatch):
    seen={}
    def fake_download(url,target):
        seen['thread']=threading.current_thread().name
        (target/'source.mp4').write_bytes(b'fake')
        return target/'source.mp4'
    monkeypatch.setattr(app_main.media,'download_youtube',fake_download)
    monkeypatch.setattr(app_main,'process_job',lambda *a,**k:None)
    client=TestClient(app_main.app)
    r=client.post('/api/analyze',data={'youtube_url':'https://youtu.be/bJTnI0tWi5k','cloud_consent':'true','start_time_seconds':'0'})
    assert r.status_code==200
    body=r.json()
    assert body['status']=='queued'
    assert seen['thread']!=threading.current_thread().name
    job=app_main.read_job(body['job_id'])
    assert job['source']=='youtube'
    assert job['status']=='queued'

def test_analyze_requires_consent(monkeypatch):
    client=TestClient(app_main.app)
    r=client.post('/api/analyze',data={'youtube_url':'https://youtu.be/bJTnI0tWi5k','cloud_consent':'false'})
    assert r.status_code==400
