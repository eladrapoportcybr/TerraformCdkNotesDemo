import json
import boto3
import datetime
import random
import string

s3 = boto3.resource("s3")
obj = s3.Object('eladr-terraform-cdk-demo-bucket', "notes.json")


# GET
def get_notes_handler(event, context):
    return {'statusCode': 200, 'body': json.dumps(read_notes())}


# POST
def add_note_handler(event: dict, context):
    new_note = update_notes(json.loads(event["body"])['content'])
    return {'statusCode': 201, 'body': json.dumps(new_note)}


# DELETE
def delete_note_handler(event, context):
    delete_note(json.loads(event["body"])['id'])
    return {'statusCode': 204}


def id_generator():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))


def read_notes():
    try:
        notes = json.loads(obj.get()['Body'].read().decode('utf-8', 'ignore'))
    except:
        notes = []
    return notes


def update_notes(note_content):
    notes = read_notes()
    new_note = {'id': id_generator(), 'content': note_content, 'date': int(datetime.datetime.now().timestamp() * 1000)}
    notes.append(new_note)
    obj.put(Body=json.dumps(notes))
    return new_note


def delete_note(id):
    notes = read_notes()
    updated = [note for note in notes if note['id'] != id]
    obj.put(Body=json.dumps(updated))
