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
        CreateUserPreferences()
    
    return dict(message_header=T('Hello'), message_contents=T('Welcome to World Cup 2014 predictions'))

@auth.requires_login()    
def get_settings():

    response.view = 'default/user_settings.html'
    return dict(Settings = db(db.user_preference.user_id == auth.user.id).select())

@auth.requires_login()    
def submit_user_settings():

    logger.info("[%s] : Submitting user settings (%s)", auth.user.id, str(request.vars))
    
    response.flash = T("The preferences are saved")
    SavePreferences(request.vars)
    return get_settings()
    
@auth.requires_login()
def get_prior_predictions():
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetGoalPredictions("prior"), 
                PositionPredictionData = GetPositionPredictions(), 
                SubmitButtonText = "Submit Prior Predictions",
                SubmitURL = "submit_prior_predictions",
                PredictionFormId = "PriorPredictionFormId",
                ReadOnlyFlag = "False"
                )
@auth.requires_login()
def get_spot_predictions():
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetGoalPredictions("spot"), 
                SubmitButtonText = "Submit Spot Predictions",
                SubmitURL = "submit_spot_predictions",
                PredictionFormId = "SpotPredictionFormId",
                ReadOnlyFlag = "False"
                )
    
@auth.requires_login()
def get_predictions():
    
    response.view = 'default/user_predictions.html'
    return dict()
    
    
@auth.requires_login()
def get_results():
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetResults(), 
                PositionPredictionData = GetPositionPredictions(),
                SubmitButtonText = "Submit Results",
                SubmitURL = "submit_results",
                PredictionFormId = "ResultFormId",
                ReadOnlyFlag = "False"
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
def submit_prior_predictions():
   
    logger.info("[%s] : Prior predictions are submitted: %s", auth.user.id, str(request.vars))
    
    UpdatePredictions(request.vars, "prior")
    
    response.flash = T("Predictions updated...")
    
    return get_predictions()
    
@auth.requires_login()  
def submit_spot_predictions():
   
    logger.info("[%s] : Spot predictions are submitted: %s", auth.user.id, str(request.vars))
    
    UpdatePredictions(request.vars, "spot")
    
    response.flash = T("Predictions updated...")
    
    return get_predictions()
 

@auth.requires_login()  
def get_comments():
    
    aResultsDict = ConvertURLArgs(request.vars)
    
    aComments = GetComments(aResultsDict['TargetType'], int(aResultsDict['TargetId']))
    
    response.view = 'default/user_comments.html'
    
    return dict(CommentData = aComments, TargetType = aResultsDict['TargetType'], TargetId = aResultsDict['TargetId'], ToggleState = aResultsDict['ToggleState'] if 'ToggleState' in aResultsDict else "none")
    
def submit_comment():   
    logger.info("[%s] : The following comments are submitted: %s", auth.user.id, str(request.vars))
    
    aResultsDict = ConvertURLArgs(request.vars)
    
    SubmitComment(aResultsDict['TargetType'], int(aResultsDict['TargetId']), aResultsDict['UserComment'])
    return get_comments()

@auth.requires_login()    
def submit_data_file():  
    logger.info("[%s] : The data file was imported: %s", auth.user.id, str(request.vars.csv_file.file))
    RecreateData(request.vars.csv_file.file)
    
    return "The file is successfully imported"
    
def get_help():
    response.view = 'default/help.html'
    return dict()

@auth.requires_login()    
def get_user_bets():
    response.view = 'default/user_bets.html'
    return dict()    
    
@auth.requires_login()    
def get_user_bets_active():
    response.view = 'default/user_global_bets.html'
    anActiveBets = GetActiveBets()
    return dict(ActiveBets = anActiveBets)    
    
@auth.requires_login()    
def get_user_bets_old():
    logger.info("request.vars : %s :", str(request.vars))
    response.view = 'default/user_old_bets.html'
    aUserId = request.vars.UserId if request.vars.UserId is not None else auth.user
    aUserBets = GetOldBets(aUserId)
    return dict(OldBets = aUserBets) 

    
@auth.requires_login()
def submit_bets():
    logger.info("[%s] : The following bets are submitted : %s", auth.user.id, str(request.vars))
    UpdateUserBets(request.vars)
    
    response.flash = T("Bets updated...")
    
    return get_user_bets_active()
 
@auth.requires_login() 
def profile():
    response.view = 'default/user_profile.html'
    return dict(form=auth.profile())

@auth.requires_login()    
def get_notifications():
    
    if request.vars.Direction is None:
        session.myNotificationOffset = 0
    
    if session.myNotificationOffset is None:
        session.myNotificationOffset = 0
    aMoreLeftFlag, aMoreRightFlag, session.myNotificationOffset, aNot = GetUserNotifications(session.myNotificationOffset, 20, request.vars.Direction)
    
    response.view = 'default/user_notifications.html'
    return dict(Notifications = aNot, NotificationsOffset = session.myNotificationOffset, MoreLeftFlag = aMoreLeftFlag, MoreRightFlag = aMoreRightFlag)
    
@auth.requires_login()    
def read_notification():
    logger.info("[%s] : The notification %s was read", auth.user.id, str(request.vars.Id))
    ReadNotification(request.vars.Id)
    return dict() 
    
@auth.requires_login()    
def delete_notification():
    logger.info("[%s] : The notification %s was deleted", auth.user.id, str(request.vars.Id))
    DeleteNotification(request.vars.Id)
    return dict()     

@auth.requires_login()
def get_notification_count():
    
    return response.json([GetNumUnreadNotifications()])    
    
@auth.requires_login()    
def get_leagues():
    response.view = 'default/user_leagues.html'
    return dict()   
    
@auth.requires_login()    
def get_user_leagues():
    response.view = 'default/user_user_leagues.html'
    return dict(UserLeagueData = GetUserLeagues())   

@auth.requires_login()    
def get_admin_leagues():
    response.view = 'default/user_admin_leagues.html'
    return dict(AdminLeagues = GetAdminLeagues())     
    
@auth.requires_login()    
def get_all_leagues():
    response.view = 'default/user_all_leagues.html'
    return dict(AllLeagueData = GetAllLeagues()) 


@auth.requires_login()    
def get_users_leagues():
    response.view = 'default/user_admin_leagues_all_users.html'
    return dict(LeagueDetail = GetLeagueDetails(request.vars.Id)) 
    
@auth.requires_login()    
def join_league():
    logger.info("[%s] : The person %s joined the league", auth.user.id, str(request.vars.Id))
    aMessage = JoinLeague(request.vars.Id)
    response.flash = aMessage
    return get_all_leagues()
  
@auth.requires_login()    
def leave_league():
    logger.info("[%s] : The person %s left the league", auth.user.id, str(request.vars.Id))
    LeaveLeague(request.vars.Id)
    response.flash = T("Left the league...")
    return get_user_leagues()

@auth.requires_login()    
def approve_membership():
    logger.info("[%s] : The membership %s approved", auth.user.id, str(request.vars.ItemId))
    ModifyMembership(request.vars.ItemId, 'approved', 'Your membership request is approved')
    response.flash = T("Approved the membership...")
    return get_users_leagues()
    
@auth.requires_login()    
def reject_membership():
    logger.info("[%s] : The membership %s rejected", auth.user.id, str(request.vars.ItemId))
    ModifyMembership(request.vars.ItemId, 'rejected', 'Your membership request is rejected')
    response.flash = T("Rejected the membership...")
    return get_users_leagues()

@auth.requires_login()    
def remove_membership():
    logger.info("[%s] : The membership %s removed", auth.user.id, str(request.vars.ItemId))
    ModifyMembership(request.vars.ItemId, 'removed', 'Your membership request is removed')
    response.flash = T("Removed the membership...")
    return get_users_leagues()
    
@auth.requires_login()    
def rejoin_membership():
    logger.info("[%s] : The membership %s rejoined", auth.user.id, str(request.vars.ItemId))
    ModifyMembership(request.vars.ItemId, 'approved', 'Your membership request is approved')
    response.flash = T("Rejoined the membership...")
    return get_users_leagues()

@auth.requires_login()    
def delete_league():
    logger.info("[%s] : Deleting league %s", auth.user.id, str(request.vars.Id))
    ModifyLeagueState(request.vars.Id, "deleted")
    response.flash = T("Deleted the league...")
    return get_users_leagues()
    
@auth.requires_login()    
def activate_league():
    logger.info("[%s] : Activating league %s", auth.user.id, str(request.vars.Id))
    ModifyLeagueState(request.vars.Id, "active")
    response.flash = T("Activated the league...")
    return get_users_leagues()
    
    
@auth.requires_login()    
def create_league():
    logger.info("[%s] : Creating league (%s, %s)", auth.user.id, str(request.vars.LeagueName), str(request.vars.LeagueDesc))
    aMessage = CreateLeague(request.vars.LeagueName, request.vars.LeagueDesc)
    response.flash = aMessage
    return get_leagues()

@auth.requires_login()    
def add_users_to_leage():
    logger.info("[%s] : Adding users %s to league %s", auth.user.id, str(request.vars['UserIds[]']), str(request.vars.Id))
    aMessage = AddUserToLeague(request.vars.Id, request.vars['UserIds[]'])
    response.flash = aMessage
    return get_users_leagues()

@auth.requires_login()    
def name_suggestions():
    response.view = 'default/search_user_list.html'
    selected = GetUsersStartingWith(str(request.vars.LeagueUserAddInput))
    return dict(UserList = selected, LeagueId = request.vars.LeagueId) 
    
@auth.requires_login()    
def get_league_page():
    response.view = 'default/user_league_page.html'
    return dict(LeagueDetails = GetLeagueDetails(request.vars.LeagueId))     

@auth.requires_login()    
def get_user_details_page():
    response.view = 'default/user_details_page.html'
    return dict(UserDetails = GetUserDetails(request.vars.UserId),
                UserGoalPredictions = GetGoalPredictions("prior", request.vars.UserId))

@auth.requires_login()    
def get_user_details_prior_pred():
    
    if IsAllowed("Share prior prediction with public", request.vars.UserId) == "No":
        return "<div> User doesn't want to share the prior predictions with you </div>"
    
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetGoalPredictions("prior", request.vars.UserId), 
                PositionPredictionData = GetPositionPredictions(), 
                PredictionFormId = "UserDetailsPriorPredictionFormId",
                ReadOnlyFlag = "True"
                )

@auth.requires_login()    
def get_user_details_spot_pred():

    if IsAllowed("Share spot prediction with public", request.vars.UserId) == "No":
        return "<div> User doesn't want to share the spot predictions with you </div>"
        
    response.view = 'default/user_prior_predictions.html'
    return dict(MacthPredictionData = GetGoalPredictions("spot", request.vars.UserId), 
                PredictionFormId = "UserDetailsSpotPredictionFormId",
                ReadOnlyFlag = "True"
                )       
                
@auth.requires_login()    
def get_user_details_bets():

    if IsAllowed("Share old bet details with public", request.vars.UserId) == "No":
        return "<div> User doesn't want to share the bet information with you </div>"
        
    logger.info("request.vars : %s :", str(request.vars))
    return get_user_bets_old()
                
#   Admin stuff

@auth.requires_membership('admin')
def get_bet_admin():
    response.view = 'default/admin_global_bets.html'
    anActiveBets = GetActiveBetsAdmin()
    return dict(ActiveBets = anActiveBets)  
    
@auth.requires_membership('admin')
def submit_admin_bets():

    logger.info("[%s] : The following bet offers are submitted: %s", auth.user.id, str(request.vars))
    
    UpdateAdminBets(request.vars)
    
    response.flash = T("Admin Bets updated...")
    
    return get_bet_admin()
    
    
@auth.requires_membership('admin')
def admin_page():
    response.view = 'default/admin_page.html'
    return dict()
    
@auth.requires_membership('admin')
def submit_results():

    logger.info("[%s] : The following results are submitted: %s", auth.user.id, str(request.vars))
    
    UpdateResults(request.vars)
    
    response.flash = T("Results updated...")
    
    return get_results()

#admin stuff ends.
  
  
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
    
    """
    form=auth()
    if request.args(0) == 'login':
        logger.info("request.args : %s", str(request))
        if form.accepts(request,session):
            CreateUserPreferences()           
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

