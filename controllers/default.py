# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging
import re

def get_configured_logger(name):
    logger = logging.getLogger(name)
    if (len(logger.handlers) == 0):
        # This logger has no handlers, so we can assume it hasn't yet been configured
        # (Configure logger)

        # Create default handler
        if request.env.web2py_runtime_gae:
            # Create GAEHandler
            # handler = GAEHandler()
            logger.debug(name + ' logger created')
        else:
            # Create RotatingFileHandler
            import os
            formatter="%(asctime)s %(levelname)s %(process)s %(thread)s %(funcName)s():%(lineno)d %(message)s"
            handler = logging.handlers.RotatingFileHandler(os.path.join(request.folder,'private/app.log'),maxBytes=1024,backupCount=2)
            handler.setFormatter(logging.Formatter(formatter))

        handler.setLevel(logging.DEBUG)

        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Test entry:
        logger.debug(name + ' logger created')
    

    return logger
    
    
logger = get_configured_logger(request.application)

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
        
    
    return dict(message_header=T('Hello'), message_contents=T('Welcome to World Cup 2014 predictions'))
    

@auth.requires_login()
def get_predictions():
    
    response.view = 'default/user_predictions.html'
    return dict(PredictionData = GetPredictions(auth.user.id), match_results = 'false')
    
@auth.requires_login()
def get_results():
    
    response.view = 'default/user_predictions.html'
    return dict(PredictionData = GetResults(), match_results = 'true')
    
@auth.requires_login()
def get_stats():
    
    response.view = 'default/user_stats.html'
    return dict()
    
@auth.requires_login()
def get_newsfeed():
    aNewsData = db().select(db.news_item.ALL)
    response.view = 'default/user_newsfeeds.html'
    return dict(NewsData = aNewsData)
    
@auth.requires_login()  
def submit_predictions():
   
    UpdatePrediction(auth.user.id, request.vars)
    
    response.flash = T("Predictions updated...")
    
    return get_predictions()
 
@auth.requires_login()  
def get_comments():
   
    aComments = GetComments(request.vars['TargetType'], int(request.vars['TargetId']))
    
    response.view = 'default/user_comments.html'
    
    return dict(CommentData = aComments, TargetType = request.vars['TargetType'], TargetId = request.vars['TargetId'])
    
def submit_comment():    
    logger.info("value of request.vars.TargetId is %s", str(request.vars))
    SubmitComment(auth.user.id, request.vars.TargetType, int(request.vars.TargetId), request.vars.UserComment)
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

