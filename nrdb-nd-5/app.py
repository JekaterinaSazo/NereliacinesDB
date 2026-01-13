import json
from random import randrange

from flask import Flask, request
from pymongo import MongoClient
from bson import json_util
import datetime
app = Flask(__name__)
mongodb_uri = 'mongodb://127.0.0.1:27017,127.0.0.1:27018/'
client = MongoClient(mongodb_uri)
db = client['uni']


def parse_json(data):
    return json.loads(json_util.dumps(data))

def gen_student_id(year):
    year = str(year)[len(str(year)) - 2:]
    student_id = "S"+ year + str(randrange(0,99999)).zfill(5)
    while db['students'].find_one({'_id': student_id}):
        student_id = "S" + year + str(randrange(0, 99999)).zfill(5)
    return student_id

def gen_specialty_id():
    specialty_id = "SP"+ str(randrange(0,99999999)).zfill(8)
    while db['specialties'].find_one({'_id': specialty_id}):
        specialty_id = "SP" + str(randrange(0,99999999)).zfill(8)
    return specialty_id

def gen_group_id(specialty_id):
    res = db['specialties'].find_one({'_id': specialty_id})
    res_name = res.get('name')[:3]
    group_id = res_name + str(randrange(0, 999)).zfill(3)
    while db['groups'].find_one({'_id': group_id}):
        group_id = res_name + str(randrange(0,999)).zfill(3)
    return group_id

def gen_subject_id():
    subject_id = "SB"+ str(randrange(0,99999999)).zfill(8)
    while db['subjects'].find_one({'_id': subject_id}):
        subject_id = "SB" + str(randrange(0,99999999)).zfill(8)
    return subject_id

@app.route('/students', methods=['PUT'])
def add_student():  
    required = ['name','surname','date_of_birth','join_year']
    req_body = request.get_json()
    if not all(key in req_body for key in required):
        return 'Not enough information', 400
    req_body['date_of_birth'] = datetime.datetime.strptime(req_body['date_of_birth'], "%Y-%m-%d")
    student_id = gen_student_id(req_body['join_year'])
    req_body['_id'] = student_id
    db['students'].insert_one(req_body)
    return {'id':req_body['_id']},201

@app.route('/students/<student_id>', methods=['GET'])
def get_student(student_id):  
    student = db['students'].find_one({'_id': student_id})
    if student is None:
        return "not found", 404
    parsed_student = parse_json(student)
    parsed_student['id'] = parsed_student.pop('_id')
    parsed_student['date_of_birth'] = parsed_student['date_of_birth'].strftime("%Y-%m-%d")
    parsed_student['join_date'] = parsed_student['join_date'].strftime("%Y-%m-%d")
    return parsed_student,201

@app.route('/specialties', methods=['PUT'])
def add_specialty():
    required = ['name']
    req_body = request.get_json()
    if not all(key in req_body for key in required):
        return 'Not enough information', 400
    if "id" not in req_body:
        req_body['id'] = gen_specialty_id()
    req_body['_id'] = req_body.pop("id")
    db['specialties'].insert_one(req_body)
    return {'id':req_body['_id']},201

@app.route('/specialties/<specialty_id>/groups', methods=['PUT'])
@app.route('/specialties/<specialty_id>/groups/<group_id>', methods=['PUT'])
def add_group(specialty_id, group_id=None):
    if group_id is None:
        group_id = gen_group_id(specialty_id)
    req_body = {"specialty_id": specialty_id, "_id": group_id}
    db['groups'].insert_one(req_body)
    return {'id':req_body['_id']},201

@app.route('/specialties/<specialty_id>/groups', methods=['GET'])
def get_groups(specialty_id):
    res = db['groups'].find({"specialty_id": specialty_id}).to_list()
    for group in res:
        group['id'] = group.pop('_id')
    return res, 200

@app.route('/subjects', methods=['PUT'])
def add_subject():
    required = ['title','lecturer_name', 'lecturer_surname', 'semester']
    req_body = request.get_json()
    if not all(key in req_body for key in required):
        return 'Not enough information', 400
    if "id" not in req_body:
        req_body['_id'] = gen_subject_id()
    else:
        req_body['_id'] = req_body.pop('id')
    db['subjects'].insert_one(req_body)
    return {'id':req_body['_id']},201



@app.route('/groups/<group_id>/students/<student_id>', methods=['PUT'])
def add_student_to_group(group_id, student_id):
    req_body = {"relation_id": group_id, "student_id": student_id}
    if db['students'].find_one({'_id': req_body['student_id']}) is None:
        return "Student not found", 404
    if db['groups'].find_one({'_id': req_body['relation_id']}) is None:
        return "Group not found", 404
    req_body['type'] = "groups"
    db['relations'].insert_one(req_body)
    return "Student added to group", 201
@app.route('/subjects/<subject_id>/students/<student_id>', methods=['PUT'])
def add_student_to_subject(subject_id, student_id):
    req_body = {"relation_id": subject_id, "student_id": student_id}
    if db['students'].find_one({'_id': req_body['student_id']}) is None:
        return "Student not found", 404
    if db['subjects'].find_one({'_id': req_body['relation_id']}) is None:
        return "subject not found", 404
    req_body['type'] = "subjects"
    db['relations'].insert_one(req_body)
    return "Student added to subject", 201


@app.route('/subjects/<relation_id>/students', methods=['GET'])
@app.route('/groups/<relation_id>/students', methods=['GET'])
def get_students_by_relation(relation_id):
    type = request.path.split('/')[1]
    pipeline = [
        {"$match": {"type": type, "relation_id": relation_id}},  
        {
            "$lookup": {
                "from": "students",  
                "localField": "student_id",  
                "foreignField": "_id",  
                "as": "student",  
            }
        },
        {"$project": {"_id":0, "student": 1}}  
    ]
    res = db['relations'].aggregate(pipeline).to_list()
    if not res:
        return "Data not found", 404
    for i in range(len(res)):
        temp = res[i]['student'][0]
        temp['id'] = temp.pop('_id')
        temp['date_of_birth'] = temp['date_of_birth'].strftime("%Y-%m-%d")
        temp['join_date'] = temp['join_date'].strftime("%Y-%m-%d")
        res[i] = temp
    return res, 200

@app.route('/specialties/<specialty_id>/students', methods=['GET'])
def get_students_by_specialty(specialty_id):
    pipeline = [
        {
            "$match": {
                "_id": specialty_id  
            }
        },
        {
            "$lookup": {
                "from": "groups",  
                "localField": "_id",  
                "foreignField": "specialty_id",  
                "as": "groups"
            }
        },
        {
            "$unwind": "$groups"
        },

        {
            "$lookup": {
                "from": "relations",  
                "localField": "groups._id",  
                "foreignField": "relation_id",  
                "as": "students_relations"
            }
        },

        {
            "$unwind": "$students_relations"
        },

        {
            "$lookup": {
                "from": "students",  
                "localField": "students_relations.student_id",  
                "foreignField": "_id",  
                "as": "students"
            }
        },

        {
            "$unwind": "$students"
        },

        {
            "$project": {
                "_id": 0, "students": 1
            }
        }
    ]
    res = db['specialties'].aggregate(pipeline).to_list()
    if not res:
        return "Data not found", 404
    for i in range(len(res)):
        temp = res[i]['students']
        temp['id'] = temp.pop('_id')
        temp['date_of_birth'] = temp['date_of_birth'].strftime("%Y-%m-%d")
        temp['join_date'] = temp['join_date'].strftime("%Y-%m-%d")
        res[i] = temp
    return res, 200

@app.route('/specialties', methods=['GET'])
def get_specialties():
    res = db['specialties'].find().to_list()
    for i in range(len(res)):
        temp = res[i]
        temp['id'] = temp.pop('_id')
        res[i] = temp
    return res, 200

@app.route('/subjects', methods=['GET'])
def get_subjects():
    res = db['subjects'].find().to_list()
    for i in range(len(res)):
        temp = res[i]
        temp['id'] = temp.pop('_id')
        res[i] = temp
    return res, 200

@app.route('/cleanup', methods=['PUT'])
def cleanup():
    db['groups'].drop()
    db['subjects'].drop()
    db['relations'].drop()
    db['specialties'].drop()
    db['students'].drop()
    db.create_collection('groups')
    db.create_collection('subjects')
    db.create_collection('relations')
    db.create_collection('specialties')
    db.create_collection('students')
    return "db cleaned", 204
if __name__ == '__main__':
    app.run()
