"""Clean installation and legacy SQLite upgrades preserve editor data."""
import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class DatabaseUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for item in (patch.object(server, 'DATA', self.root),
                     patch.object(server, 'DB', self.root/'jisr.sqlite3')):
            item.start()
            self.addCleanup(item.stop)

    def test_fresh_schema_includes_language_and_can_store_all_seven(self):
        server.initialize_db()
        with server.db() as con:
            self.assertIn('target_language', [r['name'] for r in con.execute('PRAGMA table_info(projects)')])
            for code in server.LANGUAGES:
                con.execute('INSERT INTO projects (id,edit_token,share_token,title,filename,status,created,updated,target_language) VALUES (?,?,?,?,?,?,?,?,?)',
                            (code, 'private-'+code, 'viewer-'+code, code, 'original.mp4', 'uploaded', 1, 1, code))
        for code in server.LANGUAGES:
            self.assertEqual(server.project_json(server.project_row(code), True)['target_language'], code)

    def test_legacy_upgrade_preserves_edits_tokens_words_review_style_and_is_idempotent(self):
        legacy = [{'id':'cue','start':0,'end':1,'ar':'نص عربي','en':'Human edit 😀',
                   'reviewed':True,'translation_origin':'human','source_caption':'Custom source',
                   'words':[{'text':'نص','start':0,'end':.4},{'text':'عربي','start':.5,'end':1}]}]
        style = '{"size":42,"font":"amiri"}'
        with closing(sqlite3.connect(server.DB)) as con:
            con.execute('CREATE TABLE projects (id TEXT PRIMARY KEY, edit_token TEXT NOT NULL, share_token TEXT NOT NULL, title TEXT NOT NULL, filename TEXT NOT NULL, status TEXT NOT NULL, error TEXT NOT NULL DEFAULT \'\', stage TEXT NOT NULL DEFAULT \'\', duration REAL NOT NULL DEFAULT 0, segments TEXT NOT NULL DEFAULT \'[]\', style TEXT NOT NULL DEFAULT \'{}\', created REAL NOT NULL, updated REAL NOT NULL)')
            con.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        ('legacy','secret-editor','secret-viewer','Edited title','original.mp4','ready','','',1,json.dumps(legacy),style,1,2))
            con.commit()
        server.initialize_db()
        row = server.project_row('legacy')
        self.assertEqual(row['target_language'], 'en')
        self.assertEqual((row['edit_token'],row['share_token'],row['title'],row['updated'],row['style']),
                         ('secret-editor','secret-viewer','Edited title',2,style))
        cue = json.loads(row['segments'])[0]
        self.assertEqual(cue['translation'],legacy[0]['en'])
        for key in ('ar','words','reviewed','translation_origin','source_caption','start','end'):
            self.assertEqual(cue[key],legacy[0][key])
        before = copy.deepcopy(row)
        server.initialize_db()
        self.assertEqual(server.project_row('legacy'),before)

    def test_restart_recovers_interrupted_job_without_losing_saved_transcript(self):
        server.initialize_db()
        transcript = '[{"id":"cue","ar":"نص","translation":"Text","start":0,"end":1}]'
        with server.db() as con:
            con.execute('INSERT INTO projects (id,edit_token,share_token,title,filename,status,segments,created,updated,target_language) VALUES (?,?,?,?,?,?,?,?,?,?)',
                        ('interrupted','editor','viewer','Saved','original.mp4','processing',transcript,1,2,'es'))
        server.initialize_db()
        row = server.project_row('interrupted')
        self.assertEqual(row['status'],'error')
        self.assertEqual(row['target_language'],'es')
        self.assertEqual(json.loads(row['segments'])[0]['translation'],'Text')
        self.assertEqual(row['updated'],2)

