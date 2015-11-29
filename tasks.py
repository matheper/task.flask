from flask import Flask
from flask import abort
from flask import jsonify
from flask import make_response
from flask import request
from flask import url_for
from flask.ext.cors import CORS
from flask.ext.pymongo import PyMongo
from flask.ext.pymongo import DESCENDING


app = Flask(__name__)
mongo = PyMongo(app)
CORS(app)

STATUS = ['todo', 'today', 'done']


@app.route('/')
def get_title():
    return 'matheper'


@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    tasks_collection = mongo.db.get_collection('tasks')
    task = tasks_collection.find_one({'id': task_id})
    if not len(task):
        abort(404)
    return jsonify({'task': make_public_task(task)})


@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    tasks_collection = mongo.db.get_collection('tasks')
    tasks = tasks_collection.find().sort("id", DESCENDING)
    return jsonify({'tasks': [make_public_task(task) for task in tasks]})


@app.route('/todo/api/v1.0/tasks/<status>', methods=['GET'])
def get_tasks_by_status(status):
    tasks_collection = mongo.db.get_collection('tasks')
    tasks = tasks_collection.find({'status': status}).sort("id", DESCENDING)
    return jsonify({'tasks': [make_public_task(task) for task in tasks]})


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or 'title' not in request.json:
        abort(400)
    if 'status' in request.json and request.json['status'] not in STATUS:
            abort(400)
    tasks_collection = mongo.db.get_collection('tasks')
    index = 1
    for last in tasks_collection.find().sort("id", DESCENDING).limit(1):
        index = last.get('id') + 1
    task = {
        'id': index,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'status': request.json.get('status', STATUS[0]),
    }
    print task
    tasks_collection.insert_one(task)
    return jsonify({'task': make_public_task(task)}), 201


@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    tasks_collection = mongo.db.get_collection('tasks')
    task = tasks_collection.find_one({'id': task_id})
    if not len(task):
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
            abort(400)
    if 'description' in request.json and \
       type(request.json['description']) is not unicode:
            abort(400)
    if 'status' in request.json and request.json['status'] not in STATUS:
            abort(400)
    task['title'] = request.json.get('title', task['title'])
    task['description'] = request.json.get(
        'description', task['description']
    )
    task['status'] = request.json.get('status', task['status'])
    tasks_collection.replace_one({'id': task['id']}, task)
    return jsonify({'task': make_public_task(task)})


@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    tasks_collection = mongo.db.get_collection('tasks')
    task = tasks_collection.delete_one({'id': task_id})
    if not task.deleted_count:
        abort(404)
    return jsonify({'result': True})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for(
                'get_task',
                task_id=task['id'],
                _external=True
            )
        elif field == '_id':
            pass
        else:
            new_task[field] = task[field]
    return new_task


if __name__ == '__main__':
    app.run(debug=True)
