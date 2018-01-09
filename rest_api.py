from flask import Flask
from flask_restplus import Resource, Api, fields
from werkzeug.contrib.fixers import ProxyFix
from flask_pymongo import PyMongo
from bson.objectid import ObjectId


app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

"""app.config['MONGO_DBNAME'] = 'resttodos'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/resttodos'"""

app.config['MONGO_DBNAME'] = 'sdc_tasks'
app.config['MONGO_URI'] = 'mongodb://admin:admin@ds247027.mlab.com:47027/sdc_tasks'

mongo = PyMongo(app)

# Api definition.
api = Api(app, version='1.0', title='Todo API',
    description='A simple Todo API',
)


ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    '_id': fields.String(readOnly=True, description='The task unique identifier'),   
    'task': fields.String(required=True, description='The task details'), 
    'status': fields.Boolean(required=True, default=False, description='The task Status')
})


class TodoDAO(object):

    @property
    def todos(self):
        todos = mongo.db.todos
        todo_items = todos.find()

        output = []
        for todo in todo_items:
            output.append(todo)
        
        return output

    def get(self, id):
        todos = mongo.db.todos
        try:
            todo = todos.find_one({"_id": ObjectId(id)})
            if todo:
                return todo
            
            raise Exception("Todo doesn't exist")            
        except Exception as e:
            api.abort(404, "Todo doesn't exist")           

    def create(self, data):
        todos = mongo.db.todos
        if '_id' in data: del data['_id']

        try:
            todo  = todos.insert(data)
            return data            
        except Exception as e:
            api.abort(400, "Error in creating Todo")

    def update(self, id, data):
        todos = mongo.db.todos
        
        todo = self.get(id)
        try:            
            # todo['task'] = data['task']
            todo['status'] = data['status']            
            todo  = todos.update({"_id": ObjectId(id)}, todo)
            data['_id'] = id
            return data
        except Exception as e:
            api.abort(400, "Error in updating Todo")
        return todo
        

    def delete(self, id):
        todos = mongo.db.todos
        try:
            todos.delete_one({"_id": ObjectId(id)})
        except Exception as e:
            api.abort(400, "Error in deleting Todo")


DAO = TodoDAO()


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo, envelope="data")
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<string:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)
        
    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)


if __name__ == '__main__':
	app.run(debug=True)
