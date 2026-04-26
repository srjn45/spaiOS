#!/usr/bin/env python3
"""One-time script to populate sandbox with messy test files."""
import random
import string
from pathlib import Path

sandbox = Path(__file__).parent

files = {
    # Duplicates / near-duplicates
    "report_final.pdf.txt": "Q4 revenue report. Final version.",
    "report_final_v2.pdf.txt": "Q4 revenue report. Final version. (copy)",
    "report_FINAL_actually_final.pdf.txt": "Q4 revenue report. This is really the last one.",
    "report backup.pdf.txt": "Q4 revenue report backup",
    # Temp / junk
    "temp_notes.txt": "notes from monday\ntodo: call back\nnever mind",
    "tmp_scratch.txt": "asdfasdf test 1 2 3",
    "Untitled.txt": "",
    "Untitled (1).txt": "",
    "Untitled (2).txt": "maybe something here",
    # Weirdly named
    "2024-01-15 meeting notes (version 3) REVISED.txt": "Q1 kickoff notes",
    "my resume (copy) (1) FINAL USE THIS ONE.txt": "Jane Doe | Software Engineer",
    "project   draft  with  spaces.txt": "draft content here",
    # Mixed extensions
    "data.csv.bak": "id,name,value\n1,foo,100",
    "config_old.json.bak": '{"key": "old_value"}',
    "screenshot_2024_03_12_143022.png.txt": "[screenshot placeholder]",
    # Deeply nested-ish names
    "notes/todo_list.txt": "- buy milk\n- fix bug\n- write tests",
    "notes/ideas_brainstorm.txt": "app idea: ai for groceries\napp idea: sleep tracker",
    "archive/old_project_jan2023.txt": "old project stuff from jan",
    "archive/old_project_jan2023_v2.txt": "old project stuff from jan (v2)",
    "archive/meeting_notes_archived_DO_NOT_DELETE.txt": "important meeting from 2022",
    # Random junk
    "asdf.txt": "asdf",
    "zzz_delete_me.txt": "please delete",
    "~lock.tmp": "",
    ".hidden_config": "secret=true",
}

for name, content in files.items():
    path = sandbox / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

print(f"Created {len(files)} files in {sandbox}")
