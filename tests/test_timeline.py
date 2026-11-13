from app.timeline import reconstruct

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
