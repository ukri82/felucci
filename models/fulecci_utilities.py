import logging
import re
import datetime

def ParseResultStr(aResult_in):
    
    aMatchIdStr = ''
    aTeamIndexStr = ''
    try:
        matchObj = re.search('(\d*)_score(\d)', aResult_in)
        aMatchIdStr = matchObj.group(1)
        aTeamIndexStr = matchObj.group(2)
    except AttributeError:
        logging.error("value of aResult_in is %s", str(aResult_in))

    aMatchId = int(aMatchIdStr)
    aTeamIndex = int(aTeamIndexStr) - 1

    return aMatchId, aTeamIndex
        
def UpdateResults(aParams_in):
    '''
    process each team results for each match
    '''
    for aUpdateReq in aParams_in:
        
        aMatchId, aTeamIndex = ParseResultStr(aUpdateReq)
         
        logging.info("(aMatchId: %s, aTeamIndex: %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aParams_in[aUpdateReq]))
        
        db.match_result.update_or_insert((db.match_result.match_id == aMatchId) & (db.match_result.team_id == aTeamIndex), match_id = aMatchId, team_id = aTeamIndex, goals=int(aParams_in[aUpdateReq]))

            
def UpdatePrediction(aUserId_in, aParams_in):

    '''
    process each team results for each match
    '''
    for aPredictReq in aParams_in:
        aMatchId, aTeamIndex = ParseResultStr(aPredictReq)
      
        logging.info("(aMatchId: %s, aTeamIndex: %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aParams_in[aPredictReq]))
        
        db.prediction.update_or_insert((db.prediction.match_id == aMatchId) & (db.prediction.team_id == aTeamIndex) & (db.prediction.predictor_id == aUserId_in), match_id = aMatchId, team_id = aTeamIndex, predictor_id = aUserId_in, goals=int(aParams_in[aPredictReq]))

def GetGroups():
    aGroupTable = db().select(db.team_group.ALL)
    
    aGroupData = dict()
    for group in aGroupTable:
        if group.name not in aGroupData:
            aGroupData[group.name] = list()
        aGroupData[group.name].append(list([group.group_id, group.team_id]))
        
    return aGroupData
    
def GetStadiums():
    aStadiumTable = db().select(db.stadium.ALL)
    aStadiumData = dict()
    for stadium in aStadiumTable:
        aStadiumData[stadium.stadium_id] = list([stadium.name, stadium.city])
        
    return aStadiumData
    
def GetTeams():
    aTeamTable = db().select(db.team.ALL)
    aTeamData = dict()
    for team in aTeamTable:
        aTeamData[team.team_id] = list([team.name, team.short_name, team.icon_file_name])
        
    return aTeamData
    
def GetPredictions(aUserId_in):
    
    aGroupData = GetGroups()
    aStadiumData = GetStadiums()
    aTeamData = GetTeams()
    
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
    
def GetResults():
    
    aGroupData = GetGroups()
    aStadiumData = GetStadiums()
    aTeamData = GetTeams()
    
    aResTable = db().select(db.match_result.ALL)
    aResData = dict()
    for res in aResTable:
        if res.match_id not in aResData:
            aResData[res.match_id] = dict()
        aResData[res.match_id][res.team_id] = res.goals
    
    
    
    aResults = []
    for groupName, teamData in aGroupData.items():
        aTeamIds = [item[1] for item in teamData]
 
        aMatchTable = db(db.fixture.team1.belongs(aTeamIds)).select()
                
        aMatchData = [[row.id, row.game_number, row.venue, row.referee, row.date_time,  
				row.team1, aTeamData[row.team1][0], aTeamData[row.team1][1], aTeamData[row.team1][2], aResData[row.id][0] if row.id in aResData and 0 in aResData[row.id] else 0,
				row.team2, aTeamData[row.team2][0], aTeamData[row.team2][1], aTeamData[row.team2][2], aResData[row.id][1] if row.id in aResData and 1 in aResData[row.id] else 0,
				row.venue, aStadiumData[row.venue][0], aStadiumData[row.venue][1]] for row in aMatchTable]
                
        aMatchData = sorted(aMatchData, key=lambda k: k[1])
        
        aResults.append({'group_name' : groupName,
						 'results' : aMatchData})
    logging.info("value of aResults is %s", str(aResults))
    return sorted(aResults, key=lambda k: k['group_name'])
    
def GetUsers(aUserIdList_in):
    #logger.info("value of aUserIdList_in is %s", str(aUserIdList_in))
    aUserTable = db(db.auth_user.id.belongs(aUserIdList_in)).select()
    aUserData = dict()
    for user in aUserTable:
        aUserData[user.id] = list([user.first_name, user.nickname, user.image])
        
    return aUserData

def GetComments(aTargetType_in, aTargetId_in):
    
    aCommentTable = db(db.user_comment.target_type == aTargetType_in and db.user_comment.target_id == aTargetId_in).select()
    aUserIds = [item.author_id for item in aCommentTable]
    aUserData = GetUsers(aUserIds)

    aResults = []
    for commentData in aCommentTable:
        aComment = [commentData.author_id, aUserData[commentData.author_id][0], aUserData[commentData.author_id][1], aUserData[commentData.author_id][2], commentData.body, commentData.target_type, commentData.target_id, commentData.date_time]
        aResults.append({'id' : commentData.id,
						 'comment' : aComment})

    #logger.info("value of aResults is %s", str(aResults))
    return sorted(aResults, key=lambda k: k['comment'][7])

def SubmitComment(aUserId_in, aTargetType_in, aTargetId_in, aComment_in):

    db.user_comment.insert(author_id = aUserId_in, target_id = aTargetId_in, target_type = aTargetType_in, date_time = datetime.datetime.now(), body = aComment_in)











    
    
    