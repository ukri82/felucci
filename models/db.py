# -*- coding: utf-8 -*-
import logging, logging.handlers

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

migrate_flag = True

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'],migrate=True)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

auth.settings.extra_fields[auth.settings.table_user_name]= [
  Field('nickname', 'string'),
  Field('image', 'upload')
]

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'fulecci@gmail.com'
mail.settings.login = 'fulecci:icceluf123'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True



## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

db.define_table('news_item',
    Field('title','string', length=500),
    Field('body','string', length=10000),
    Field('author','string', length=100),
    Field('date_time','datetime'),
    Field('image', 'upload'),
    Field('tags','string', length=100), redefine=migrate_flag
)


db.define_table('match_result',
    Field('match_id','integer'),
    Field('team_id','integer'),
    Field('goals','integer'),
    Field('possession','double'),
    Field('total_shots','integer'),
    Field('shots_on_target','integer'),
    Field('shots_off_target','integer'),
    Field('corners','integer'),
    Field('yellow_cards','integer'),
    Field('read_cards','integer'),
    Field('goal_scorers_ids','string', length=50), redefine=migrate_flag
)

db.define_table('fixture',
    Field('fixture_id','integer'),
	Field('game_number','integer'),
    Field('team1','integer'),
    Field('team2','integer'),
    Field('date_time','datetime'),
    Field('venue','integer'),
    Field('referee','string', length=50), redefine=migrate_flag
)

db.define_table('team_group',
    Field('group_id','integer'),
    Field('name','string', length=2),
    Field('team_id','integer'), redefine=migrate_flag
)
 
db.define_table('player',
    Field('player_id','integer'),
    Field('first_name','string', length=50),
    Field('last_name','string', length=50),
    Field('player_image','string', length=50),
    Field('team_id','integer'), redefine=migrate_flag
)

db.define_table('predicter',
    Field('predicter_id','integer'),
    Field('g_id','string', length=50),
    Field('first_name','string', length=50),
    Field('last_name','string', length=50),
    Field('nick_name','string', length=50), redefine=migrate_flag
)

db.define_table('prediction',
    Field('predictor_id','integer'),
    Field('match_id','integer'),
    Field('team_id','integer'),
    Field('goals','integer'),
    Field('possession','double'),
    Field('total_shots','integer'),
    Field('shots_on_target','integer'),
    Field('shots_off_target','integer'),
    Field('corners','integer'),
    Field('yellow_cards','integer'),
    Field('red_cards','integer'),
    Field('goal_scorers_id','string', length=50), redefine=migrate_flag
)

db.define_table('stadium',
    Field('stadium_id','integer'),
    Field('name','string', length=50),
    Field('city','string', length=50),
    Field('capacity','integer'),
    Field('profile','string', length=10000),
	Field('icon_file_name','string', length=50),
    Field('location_coord','string', length=50), redefine=migrate_flag
)

db.define_table('team',
    Field('team_id','integer'),
    Field('name','string', length=30),
    Field('short_name','string', length=3),
    Field('captain','integer'),
    Field('coach','string', length=50),
    Field('icon_file_name','string', length=50),
    Field('profile','string', length=10000),
    Field('key_players','string', length=50), redefine=migrate_flag
)

'''
db.prediction.drop()
db.team.drop()
db.stadium.drop()
db.match_result.drop()
db.predicter.drop()
db.player.drop()
db.team_group.drop()
db.fixture.drop()
db.news_item.drop()
'''


## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
