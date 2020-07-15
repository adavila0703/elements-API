from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from marshmallow_jsonapi.flask import Schema
from marshmallow_jsonapi import fields
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList
from marshmallow_jsonapi.flask import Relationship
from flask_rest_jsonapi import ResourceRelationship
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from datetime import datetime
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


def get_info(num):
    file = open('element-info.txt', 'r')
    out = file.readlines()
    file.close()
    return out[num]


# Create a new Flask application
app = Flask(__name__)

# Set up SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spellbreak.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, template_mode='bootstrap3')

app.config['BASIC_AUTH_USERNAME'] = get_info(0).strip()
app.config['BASIC_AUTH_PASSWORD'] = get_info(1).strip()
app.config['BASIC_AUTH_FORCE'] = True


basic_auth = BasicAuth(app)

def migration():
    manager.run()


@app.route('/secret')
@basic_auth.required
def secret_view():
    return render_template('secret.html')


# Define users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __int__(self):
        return self.discord_id


class Tourn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __repr__(self):
        return self.name


# Define record table
class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow)
    discord_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String, nullable=False)
    tourny_name = db.Column(db.String, nullable=True)
    qualy_name = db.Column(db.String, nullable=True)
    scrimy_name = db.Column(db.String, nullable=True)
    game = db.Column(db.String, nullable=True)
    place = db.Column(db.Integer, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    assists = db.Column(db.Integer, nullable=False)
    damage = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=True)


class UserModelView(ModelView):
    page_size = 50  # the number of entries to display on the list view
    can_export = True
    column_searchable_list = ['username']


class TournModelView(ModelView):
    page_size = 50
    can_export = True
    column_searchable_list = ['name']


class RecordModelView(ModelView):
    page_size = 50
    can_export = True
    column_searchable_list = ['username']


# add to admin view
admin.add_view(UserModelView(User, db.session))
admin.add_view(TournModelView(Tourn, db.session))
admin.add_view(RecordModelView(Record, db.session))

# create table
db.create_all()


# Create data abstraction
class UserSchema(Schema):
    class Meta:
        type_ = 'user'
        self_view = 'user_one'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'user_many'

    id = fields.Integer()
    username = fields.Str(required=True)
    discord_id = fields.Str()
    name = fields.Str()
    records = Relationship(self_view='user_records',
                           self_view_kwargs={'id': '<id>'},
                           related_view='user_many',
                           many=True,
                           schema='UserSchema',
                           type_='record')


class TournSchema(Schema):
    class Meta:
        type_ = 'tourn'
        self_view = 'tourn_one'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'tourn_many'

    id = fields.Integer()
    name = fields.Str()
    tourns = Relationship(
        self_view='tourn_records',
        self_view_kwargs={'id': '<id>'},
        related_view='tourn_many',
        many=True,
        schema='TournSchema',
        type_='tourn')


class RecordSchema(Schema):
    class Meta:
        type_ = 'record'
        self_view = 'record_one'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'record_many'

    id = fields.Integer()
    discord_id = fields.Integer(required=True)
    username = fields.String(required=True)
    tourny_name = fields.String()
    qualy_name = fields.String()
    scrimy_name = fields.String()
    game = fields.String()
    place = fields.Integer(required=True)
    kills = fields.Integer(required=True)
    assists = fields.Integer(required=True)
    damage = fields.Integer(required=True)


# Create resource managers and endpoints
class UserMany(ResourceList):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User}


class UserOne(ResourceDetail):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User}


class TournMany(ResourceList):
    schema = TournSchema
    data_layer = {'session': db.session,
                  'model': Tourn}


class TournOne(ResourceDetail):
    schema = TournSchema
    data_layer = {'session': db.session,
                  'model': Tourn}


class RecordMany(ResourceList):
    schema = RecordSchema
    data_layer = {'session': db.session,
                  'model': Record}


class RecordOne(ResourceDetail):
    schema = RecordSchema
    data_layer = {'session': db.session,
                  'model': Record}


class UserRecord(ResourceRelationship):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User}


class TournRecord(ResourceRelationship):
    schema = TournSchema
    data_layer = {'session': db.session,
                  'model': Tourn}


api = Api(app)

api.route(UserMany, 'user_many', '/users')
api.route(UserOne, 'user_one', '/users/<int:id>')
api.route(TournMany, 'tourn_many', '/tourns')
api.route(TournOne, 'tourn_one', '/tourns/<int:id>')
api.route(RecordOne, 'record_one', '/records/<int:id>')
api.route(RecordMany, 'record_many', '/records')
api.route(UserRecord, 'user_records', '/users/<int:id>/relationships/records')
api.route(TournRecord, 'tourn_records', '/tourns/<int:id>/relationships/records')

# main loop to run app in debug mode
if __name__ == '__main__':
    app.secret_key = 'test'
    app.run(host=str(get_info(2)), port=int(get_info(3)), debug=False)
