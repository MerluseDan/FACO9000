"""Immutable disk-backed SRDE E30 snapshot, independently reloaded before inference.

This is NOT E29's full autonomous detection/event ledger. E30 consumes explicit
revocation records, preserving them and all past claim records in an append-only
SQLite evidence snapshot. It tests persistence and selective retrieval only.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from e30_core import canonical,sha

SCHEMA='''
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS records(world TEXT NOT NULL,id TEXT NOT NULL,ordinal INTEGER NOT NULL,
    payload TEXT NOT NULL,PRIMARY KEY(world,id));
CREATE TABLE IF NOT EXISTS questions(world TEXT NOT NULL,id TEXT NOT NULL,ordinal INTEGER NOT NULL,
    payload TEXT NOT NULL,PRIMARY KEY(world,id));
CREATE TRIGGER IF NOT EXISTS no_records_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'immutable records'); END;
CREATE TRIGGER IF NOT EXISTS no_records_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'immutable records'); END;
CREATE TRIGGER IF NOT EXISTS no_questions_update BEFORE UPDATE ON questions BEGIN SELECT RAISE(ABORT,'immutable questions'); END;
CREATE TRIGGER IF NOT EXISTS no_questions_delete BEFORE DELETE ON questions BEGIN SELECT RAISE(ABORT,'immutable questions'); END;
'''

def persist_and_reload(corpus,filename):
    """Reject altered corpora and reopen from durable immutable SQLite records."""
    filename=Path(filename)
    filename.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(str(filename))
    con.executescript(SCHEMA)
    existing=dict(con.execute('SELECT key,value FROM metadata').fetchall())
    expected={'protocol':corpus['protocol'],'sha256':corpus['sha256']}
    if existing and existing!=expected:
        con.close();raise RuntimeError('Existing evidence ledger has a different frozen hash/protocol')
    if not existing:
        with con:
            con.executemany('INSERT INTO metadata(key,value) VALUES(?,?)',expected.items())
            for world in corpus['worlds']:
                for i,d in enumerate(world['docs']):
                    con.execute('INSERT INTO records(world,id,ordinal,payload) VALUES(?,?,?,?)',
                                (world['world'],d['id'],i,canonical(d)))
                for i,t in enumerate(world['tasks']):
                    con.execute('INSERT INTO questions(world,id,ordinal,payload) VALUES(?,?,?,?)',
                                (world['world'],t['id'],i,canonical(t)))
    con.close()
    con=sqlite3.connect(str(filename))
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    rows=[]
    for orig in corpus['worlds']:
        name=orig['world']
        docs=[json.loads(x[0]) for x in con.execute('SELECT payload FROM records WHERE world=? ORDER BY ordinal',(name,))]
        tasks=[json.loads(x[0]) for x in con.execute('SELECT payload FROM questions WHERE world=? ORDER BY ordinal',(name,))]
        rows.append({'seed':orig['seed'],'world':name,'docs':docs,'tasks':tasks})
    con.close()
    if sha(rows)!=corpus['sha256']:raise RuntimeError('Reopened evidence differs from frozen corpus')
    return {'protocol':corpus['protocol'],'worlds':rows,'sha256':corpus['sha256']}
