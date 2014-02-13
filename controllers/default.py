# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging
import re

            
def UpdatePrediction(aUserId_in, aParams_in):

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
         
        logging.info("(aMatchId: %s, aTeamIndex: %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aParams_in[aPredictReq]))
        
        db.prediction.update_or_insert((db.prediction.match_id == aMatchId) & (db.prediction.team_id == aTeamIndex) & (db.prediction.predictor_id == aUserId_in), match_id = aMatchId, team_id = aTeamIndex, predictor_id = aUserId_in, goals=int(aParams_in[aPredictReq]))

def GetPredictions(aUserId_in):
    
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
    
    aTeamTable = db().select(db.team.ALL)
    aTeamData = dict()
    for team in aTeamTable:
        aTeamData[team.team_id] = list([team.name, team.short_name, team.icon_file_name])
    
    aPredTable = db(db.prediction.predictor_id == aUserId_in).select()
    aPredData = dict()
    for pred in aPredTable:
        if pred.match_id not in aPredData:
            aPredData[pred.match_id] = dict()
        aPredData[pred.match_id][pred.team_id] = pred.goals
    
    logging.info("value of aPredData is %s", str(aPredData))
    '''
    logging.info("value of aStadiumData is %s", str(aStadiumData))
    '''
    
    
    
    aPredictions = []
    for groupName, teamData in aGroupData.items():
        aTeamIds = [item[1] for item in teamData]
 
        aMatchTable = db(db.fixture.team1.belongs(aTeamIds)).select()
                
        aMatchData = [[row.id, row.game_number, row.venue, row.referee, row.date_time,  
				row.team1, aTeamData[row.team1][0], aTeamData[row.team1][1], aTeamData[row.team1][2], aPredData[row.id][0] if row.id in aPredData and 0 in aPredData[row.id] else 0,
				row.team2, aTeamData[row.team2][0], aTeamData[row.team2][1], aTeamData[row.team2][2], aPredData[row.id][1] if row.id in aPredData and 1 in aPredData[row.id] else 0,
				row.venue, aStadiumData[row.venue][0], aStadiumData[row.venue][1]] for row in aMatchTable]
                
        aMatchData = sorted(aMatchData, key=lambda k: k[1])
        
        aPredictions.append({'group_name' : groupName,
						 'prediction' : aMatchData})
    
    return sorted(aPredictions, key=lambda k: k['group_name'])
    
#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################


def index():
    
    response.flash = T("Welcome to Fulecci!")
    nick_name = ''
    user_image = ''
    if auth.user is not None:
        nick_name = auth.user.nickname
        user_image = auth.user.image
        response.view = 'default/profile.html'
        
    logging.info("value of response.view is %s", str(response.view))
    return dict(message_header=T('Hello'), message_contents=T('Welcome to World Cup 2014 predictions'))
    

@auth.requires_login()
def get_predictions():
    
    response.view = 'default/predictions.html'
    return dict(PredictionData = GetPredictions(auth.user.id))
    
    
@auth.requires_login()  
def submit_predictions():
   
    UpdatePrediction(auth.user.id, request.vars)
    
    response.flash = T("Predictions updated...")
    
    response.view = 'default/predictions.html'
    return dict(message_header = "Predictions", PredictionData = GetPredictions(auth.user.id))
    
def get_help():
    response.view = 'default/help.html'
    return dict()
    
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())

