# -*- coding: utf-8 -*-
import logging
import re


#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

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

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

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

db.define_table('detailed_prediction',
    Field('detailed_prediction_id','integer'),
    Field('prediction_id','integer'),
    Field('team_id','integer'),
    Field('goals','integer'),
    Field('possession','double'),
    Field('total_shots','integer'),
    Field('shots_on_target','integer'),
    Field('shots_off_target','integer'),
    Field('corners','integer'),
    Field('yellow_cards','integer'),
    Field('red_cards','integer'),
    Field('goal_scorers_id','string', length=50), redefine=True
)

db.define_table('detailed_result',
    Field('detailed_result_id','integer'),
    Field('result_id','integer'),
    Field('team_id','integer'),
    Field('goals_scored','integer'),
    Field('possession','double'),
    Field('total_shots','integer'),
    Field('shots_on_target','integer'),
    Field('shots_off_target','integer'),
    Field('corners','integer'),
    Field('yellow_cards','integer'),
    Field('read_cards','integer'),
    Field('goal_scorers_ids','string', length=50), redefine=True
)

db.define_table('fixture',
    Field('fixture_id','integer'),
	Field('game_number','integer'),
    Field('team1','integer'),
    Field('team2','integer'),
    Field('date_time','datetime'),
    Field('venue','integer'),
    Field('referee','string', length=50), redefine=True
)

db.define_table('team_group',
    Field('group_id','integer'),
    Field('name','string', length=2),
    Field('team_id','integer'), redefine=True
)
 
db.define_table('player',
    Field('player_id','integer'),
    Field('first_name','string', length=50),
    Field('last_name','string', length=50),
    Field('player_image','string', length=50),
    Field('team_id','integer'), redefine=True
)

db.define_table('predicter',
    Field('predicter_id','integer'),
    Field('g_id','string', length=50),
    Field('first_name','string', length=50),
    Field('last_name','string', length=50),
    Field('nick_name','string', length=50), redefine=True
)

db.define_table('prediction',
    Field('prediction_id','integer'),
    Field('match_id','integer'),
    Field('team1_details_id','integer'),
    Field('team2_details_id','integer'),
    Field('predictor_id','integer'), redefine=True
)

db.define_table('match_result',
    Field('result_id','integer'),
    Field('match_id','integer'),
    Field('team1_details_id','integer'),
    Field('team2_details_id','integer'), redefine=True
)

db.define_table('stadium',
    Field('stadium_id','integer'),
    Field('name','string', length=50),
    Field('city','string', length=50),
    Field('capacity','integer'),
    Field('profile','string', length=10000),
	Field('icon_file_name','string', length=50),
    Field('location_coord','string', length=50), redefine=True
)

db.define_table('team',
    Field('team_id','integer'),
    Field('name','string', length=30),
	Field('short_name','string', length=3),
    Field('captain','integer'),
    Field('coach','string', length=50),
    Field('icon_file_name','string', length=50),
    Field('profile','string', length=10000),
    Field('key_players','string', length=50), redefine=True
)

'''
db.detailed_predictions.drop()
db.teams.drop()
db.stadiums.drop()
db.results.drop()
db.predictions.drop()
db.predicters.drop()
db.players.drop()
db.groups.drop()
db.fixture.drop()
db.detailed_results.drop()
'''
    
def GetGroups(aGroupName_in):
   rows = db(db.team_group.name==aGroupName_in).select()
   aTeamIds = [i['team_id'] for i in rows]
   rows = db(db.fixture.team1.belongs(aTeamIds) | db.fixture.team2.belongs(aTeamIds)).select()
   aMatchIds = [i['id'] for i in rows]
   message_contents = aMatchIds
   """
   for row in rows: message_contents += "(%s, %s)" % (row.id, row.date_time)
   """
   return message_contents
   
            
def UpdatePrediction(aUserId_in, aParams_in):

    '''
    Get the fixture data in a dictionary
    '''
    aFixtureTable = db().select(db.fixture.ALL)
    aFixtureData = dict()
    for match in aFixtureTable:
        aFixtureData[match.id] = list([match.team1, match.team2])
    
    '''
    See if there is an entry for the predictor in the prediction table, if not create one
    '''
    aUserRow = db(db.prediction.predictor_id==aUserId_in).select()
    predictionId = -1
    
    
    if len(aUserRow) == 0:
        predictionId = db.prediction.insert(predictor_id=aUserId_in)
    else:
        predictionId = aUserRow[0].id
        
    logging.info("value of len(aParams_in) is %s", str(len(aParams_in)))
    '''
    process each team results for each match
    '''
    for aPredictReq in aParams_in:
        aMatchIdStr = ''
        aTeamIndexStr = ''
        try:
            matchObj = re.search('(\d*)_score(\d)', aPredictReq)
            aMatchIdStr = matchObj.group(1)
            aTeamIndexStr = matchObj.group(2)
        except AttributeError:
            logging.error("value of aPredictReq is %s", str(aPredictReq))

        aMatchId = int(aMatchIdStr)
        aTeamIndex = int(aTeamIndexStr) - 1
        aTeamId = aFixtureData[aMatchId][aTeamIndex]
        
        detailedPredictionIdTeam = -1
        aDetRows = db(db.detailed_prediction.prediction_id == predictionId and db.detailed_prediction.team_id == aTeamId).select()
        if len(aDetRows) == 0:
            detailedPredictionIdTeam = db.detailed_prediction.insert(prediction_id=predictionId, team_id = aTeamId)
        else:
            detailedPredictionIdTeam = aDetRows[0].id
        
        if aTeamIndex == 0:
            db(db.prediction.id==predictionId).update(match_id=aMatchId, team1_details_id=detailedPredictionIdTeam)
        else:
            db(db.prediction.id==predictionId).update(match_id=aMatchId, team2_details_id=detailedPredictionIdTeam)
            
        db(db.detailed_prediction.id==detailedPredictionIdTeam).update(goals=int(aParams_in[aPredictReq]))
        
def GetFixture():
    
    aGroupTable = db().select(db.team_group.ALL)
    
    aGroupData = dict()
    for group in aGroupTable:
        if group.name not in aGroupData:
            aGroupData[group.name] = list()
        aGroupData[group.name].append(list([group.group_id, group.team_id]))
        
    
    aStadiumTable = db().select(db.stadium.ALL)
    aStadiumData = dict()
    for stadium in aStadiumTable:
        aStadiumData[stadium.stadium_id] = list([stadium.name, stadium.city])
     
    '''
    logging.info("value of aStadiumData is %s", str(aStadiumData))
    '''
    
    aTeamTable = db().select(db.team.ALL)
    aTeamData = dict()
    for team in aTeamTable:
        aTeamData[team.team_id] = list([team.name, team.short_name, team.icon_file_name])
    
    aFixture = []
    for groupName, teamData in aGroupData.items():
        aTeamIds = [item[1] for item in teamData]
 
        aMatchTable = db(db.fixture.team1.belongs(aTeamIds)).select()
        
        aMatchData = [[row.id, row.game_number, row.venue, row.referee, row.date_time,  
				row.team1, aTeamData[row.team1][0], aTeamData[row.team1][1], aTeamData[row.team1][2], 
				row.team2, aTeamData[row.team2][0], aTeamData[row.team2][1], aTeamData[row.team2][2], 
				row.venue, aStadiumData[row.venue][0], aStadiumData[row.venue][1]] for row in aMatchTable]
                
        aMatchData = sorted(aMatchData, key=lambda k: k[1])
        
        aFixture.append({'group_name' : groupName,
						 'fixture' : aMatchData})
    
    return sorted(aFixture, key=lambda k: k['group_name'])

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
