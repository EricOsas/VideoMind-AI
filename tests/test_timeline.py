from app.timeline import reconstruct,build_analysis_report,write_project
import json,zipfile

def test_progressive_line_merge_and_edit():
    result = reconstruct([
        {'timestamp':1,'file_path':'src/app.py','visible_start_line':390,'visible_end_line':400,'code_lines':[{'line':395,'text':'old'}]},
        {'timestamp':2,'file_path':'src/app.py','visible_start_line':1,'visible_end_line':3,'code_lines':[{'line':1,'text':'start'},{'line':2,'text':'middle'}]},
        {'timestamp':3,'file_path':'src/app.py','visible_start_line':395,'visible_end_line':398,'code_lines':[{'line':395,'text':'new'}]},
    ])
    item=result['files']['src/app.py']
    assert 'new' in item['content'] and 'old' not in item['content']
    assert 3 in item['missing_lines']

def test_files_are_not_merged():
    result=reconstruct([
        {'timestamp':1,'file_path':'a.py','visible_start_line':1,'visible_end_line':1,'code_lines':[{'line':1,'text':'a'}]},
        {'timestamp':2,'file_path':'b.py','visible_start_line':1,'visible_end_line':1,'code_lines':[{'line':1,'text':'b'}]},
    ])
    assert set(result['files'])=={'a.py','b.py'}

def test_structured_report_and_project_archive(tmp_path):
    result=reconstruct([{'timestamp':4,'file_path':'main.py','visible_start_line':1,'code_lines':[{'line':1,'text':'print(1)'}],'confidence':'high'}])
    metadata={'source':'upload','analysis_range':'00:00:02 – 00:00:08','analysis_range_seconds':{'start':2,'end':8},'scene_change_frames':2,'detected_scene_timestamps':['00:00:04','00:00:06']}
    report=build_analysis_report(result,metadata)
    assert report['analysis_range_seconds']=={'start':2,'end':8}
    assert report['scene_change_frames']==2
    assert report['files']['main.py']['confidence_counts']['high']==1
    archive=write_project(tmp_path,result,metadata)
    with zipfile.ZipFile(archive) as z:
        assert 'VIDEOMIND_ANALYSIS_REPORT.json' in z.namelist()
        assert 'VIDEOMIND_ANALYSIS_REPORT.md' in z.namelist()
        parsed=json.loads(z.read('VIDEOMIND_ANALYSIS_REPORT.json'))
        assert parsed['reconstructed_file_count']==1
