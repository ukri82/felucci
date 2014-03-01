# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging
import re


#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################


def index():
    response.flash = T("Welcome to Fulecci!")
    if auth.user is not None:
        response.view = 'default/user_page.html'
        CacheData()
    
    return dict(message_header=T('Hello'), message_contents=T('Welcome to World Cup 2014 predictions'))
    

@auth.requires_login()
def get_prior_predictions():
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetPriorPredictions(auth.user.id), 
                PositionPredictionData = GetPositionPredictions(auth.user.id), 
                SubmitButtonText = "Submit Prior Predictions",
                SubmitURL = "submit_predictions"
                )
@auth.requires_login()
def get_spot_predictions():
    
    response.view = 'default/user_spot_predictions.html'
    return dict()
    
@auth.requires_login()
def get_predictions():
    
    response.view = 'default/user_predictions.html'
    return dict()
    
    
@auth.requires_login()
def get_results():
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetResults(), 
                PositionPredictionData = GetPositionPredictions(auth.user.id),
                SubmitButtonText = "Submit Results",
                SubmitURL = "submit_results"
                )
                
  

@auth.requires_login()
def get_user_stats_chunk_data():
    
    if len(request.vars.items()) > 0 and request.vars.items()[0][0] == 'NextChunk':
        session.myUserStatsOffset = session.myUserStatsOffset + 4
    else:
        session.myUserStatsOffset = 0
    
    aMoreFlag, aStatsData = RetrieveNextChunk(db.auth_user, 'last_score', session.myUserStatsOffset, 4, False)
    
    return aMoreFlag, aStatsData
    
@auth.requires_login()
def get_user_stats_chunk():
    
    aMoreFlag, aStatsData = get_user_stats_chunk_data()
    
    response.view = 'default/user_stats_chunk.html'
    return dict(UserStats = aStatsData, MoreFlag = aMoreFlag)
    
@auth.requires_login()
def get_stats():
    response.view = 'default/user_stats.html'
    return dict()

@auth.requires_login()
def get_user_details():
    response.view = 'default/user_details.html'
    return dict(UserId = request.vars.items()[0][1])    
    
@auth.requires_login()
def get_newsfeed_chunk_data():
    
    if len(request.vars.items()) > 0 and request.vars.items()[0][0] == 'NextChunk':
        session.myNewsFeedOffset = session.myNewsFeedOffset + 4
    else:
        session.myNewsFeedOffset = 0
    
    aMoreFlag, aNewsData = RetrieveNextChunk(db.news_item, 'date_time', session.myNewsFeedOffset, 4, True)
    
    return aMoreFlag, aNewsData
    
@auth.requires_login()
def get_newsfeed_chunk():
    
    aMoreFlag, aNewsData = get_newsfeed_chunk_data()
    
    response.view = 'default/user_newsfeed_chunk.html'
    return dict(NewsData = aNewsData, MoreFlag = aMoreFlag)
    
@auth.requires_login()
def get_newsfeed():
    session.myNewsFeedOffset = 0
    response.view = 'default/user_newsfeeds.html'
    return dict()
    
@auth.requires_login()  
def submit_predictions():
   
    UpdatePredictions(auth.user.id, request.vars, "prior")
    
    response.flash = T("Predictions updated...")
    
    return get_predictions()
 

@auth.requires_login()  
def get_comments():
    
    aResultsDict = ConvertURLArgs(request.vars)
    
    aComments = GetComments(aResultsDict['TargetType'], int(aResultsDict['TargetId']))
    
    response.view = 'default/user_comments.html'
    
    return dict(CommentData = aComments, TargetType = aResultsDict['TargetType'], TargetId = aResultsDict['TargetId'], ToggleState = aResultsDict['ToggleState'] if 'ToggleState' in aResultsDict else "none")
    
def submit_comment():    
    aResultsDict = ConvertURLArgs(request.vars)
    
    SubmitComment(auth.user.id, aResultsDict['TargetType'], int(aResultsDict['TargetId']), aResultsDict['UserComment'])
    return get_comments()
    
def get_help():
    response.view = 'default/help.html'
    return dict()

@auth.requires_login()
def admin_page():
    response.view = 'default/admin_page.html'
    return dict()
    
@auth.requires_login()
def submit_results():
    UpdateResults(request.vars)
    
    response.flash = T("Results updated...")
    
    return get_results()

 
@auth.requires_login() 
def profile():
    response.view = 'default/user_profile.html'
    return dict(form=auth.profile())
     
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

