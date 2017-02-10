#!/usr/bin/python2

import uuid
import subprocess
import fnmatch
import os
#import yaml

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap

import markdown

import sys
sys.path.append('/usr/share/anki')
import anki
import anki.importing
import anki.notes
import anki.utils

def get_git_revision():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
git_revision = get_git_revision()
print 'git rev:', git_revision

class Note(object):
    def __init__(self, origin_file, uuid, include_reverse,
                 topic,
                 front, back,
                 git_revision,
                 deck):
        self.deck = deck
        self.origin_file = origin_file
        self.uuid = uuid
        self.include_reverse = include_reverse
        self.topic = topic
        self.front = front
        self.back = back
        self.git_revision = git_revision

    def to_fields(self):
        return [
            self.uuid,
            self.topic,
            self.front, self.back,
            'true' if self.include_reverse else '',
            self.origin_file,
            self.git_revision,

            #'' # TAGS  --  can add those.
        ]

collection_path = '/home/prvak/dropbox/anki/User 1/collection.anki2'
cwd = os.getcwd()
collection = anki.Collection(collection_path)
os.chdir(cwd)

uuids = set()

my_notes = []

yaml_files = []
# TODO: follow symlinks
for root, dirnames, filenames in os.walk('notes'):
    for filename in fnmatch.filter(filenames, '*.yaml'):
        yaml_files.append(os.path.join(root, filename))

for path in yaml_files:
    print(path)
    with open(path) as yf:
        data = ruamel.yaml.round_trip_load(yf)
        #data = yaml.load(yf)

    # if 'uid_tag' in data:
    #     uid_tag = data['uid_tag'] + '/'
    # else:
    #     uid_tag = ''

    if 'topic' in data:
        topic = data['topic']
    else:
        topic = ''

    deck = data['deck']

    for note_row in data['notes']:
        if not note_row:
            print(path)
            print("no note")
            sys.exit(1)
        if 'uuid' not in note_row:
            print(note_row)
            print('No UUID')
            sys.exit(1)
        if 'front' not in note_row or 'back' not in note_row:
            print(note_row)
            print('Missing front or back')
            sys.exit(1)

        note_uuid = note_row['uuid']
        try:
            uuid.UUID(note_uuid)
        except ValueError:
            print "Bad UUID", note_uuid, "in", path
            raise
        origin_file = unicode(path)
        if note_uuid in uuids:
            raise Exception("Duplicated UID:" + str(note_uuid))
        uuids.add(note_uuid)
        # print (origin_file, note_uuid)
        # (front) (back) (add-reverse) (origin-file) (note_uuid) (git-revision)
        if 'include_reverse' in note_row:
            include_reverse = note_row['include_reverse']
        else:
            include_reverse = False

        note_topic = topic
        if 'topic' in note_row:
            note_topic = note_row['topic']

        if 'front' not in note_row:
            raise Exception('No front: ' + note_uuid)

        front = unicode(note_row['front'])
        back = unicode(note_row['back'])

        if ('markdown' not in note_row) or (note_row['markdown']):
            front = markdown.markdown(unicode(note_row['front']))
            back = markdown.markdown(unicode(note_row['back']))

        note = Note(
            origin_file = origin_file,
            uuid = note_uuid,
            include_reverse = include_reverse,
            topic = note_topic,
            front = front,
            back = back,
            git_revision = git_revision,
            deck = deck
        )
        # my_notes.append()

        notes = collection.findNotes('anki-decks-uid:"' + note.uuid + '"')
        print(note.uuid, len(notes))
        assert len(notes) == 1

        anki_note = notes[0]
        print(anki_note)
        n = anki.notes.Note(collection, id=anki_note)
        print(n.guid)

        print("new:", anki.utils.guid64())

        #note_row['guid'] = str(n.guid)
        note_row.insert(1, 'guid', n.guid)

    with open(path, "w") as yf:
        ruamel.yaml.round_trip_dump(data, stream=yf,
                                    indent=8,
                                    block_seq_indent=8)
