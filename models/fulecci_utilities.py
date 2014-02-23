import logging
import re
import datetime
import collections

def ParseResultStr(aResult_in):
    
    aMatchIdStr = ''
    aTeamIndexStr = ''
    aMatchOrPos = 'match'
    try:
        matchObj = re.search('match_(\d*)_score(\d)', aResult_in)
        aMatchIdStr = matchObj.group(1)
        aTeamIndexStr = matchObj.group(2)
    except AttributeError:
        try:
            matchObj = re.search('pos_(\d*)_team(\d)', aResult_in)
            aMatchOrPos = 'pos'
            aMatchIdStr = matchObj.group(1)
            aTeamIndexStr = matchObj.group(2)
        except AttributeError:
            logging.error("Error ins parsing the input values. value of aResult_in is %s", str(aResult_in))
    
    aMatchId = int(aMatchIdStr)
    aTeamIndex = int(aTeamIndexStr) - 1

    return aMatchId, aTeamIndex, aMatchOrPos
        
def UpdateResults(aParams_in):
    '''
    process each team results for each match
    '''
    for aUpdateReq in aParams_in:
        
        aMatchId, aTeamIndex = ParseResultStr(aUpdateReq)
         
        logging.info("(aMatchId: %s, aTeamIndex: %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aParams_in[aUpdateReq]))
        
        if aTeamIndex == 0:
            db.match_result.update_or_insert((db.match_result.match_id == aMatchId), match_id = aMatchId, team1_goals=int(aParams_in[aUpdateReq]))
        else:
            db.match_result.update_or_insert((db.match_result.match_id == aMatchId), match_id = aMatchId, team2_goals=int(aParams_in[aUpdateReq]))

            
def UpdatePrediction(aUserId_in, aParams_in):

    '''
    process each team results for each match
    '''
    for aPredictReq in aParams_in:
        aMatchId, aTeamIndex, aMatchOrPos = ParseResultStr(aPredictReq)
      
        logger.info("(aMatchOrPos : %s, aMatchId: %s, aTeamIndex: %s, goals: %s)", aMatchOrPos, str(aMatchId), str(aTeamIndex), str(aParams_in[aPredictReq]))
        if aMatchOrPos == "match":
            if aTeamIndex == 0:
                db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & (db.match_prediction.predictor_id == aUserId_in), 
                                                        match_id = aMatchId, 
                                                        predictor_id = aUserId_in, 
                                                        team1_goals = int(aParams_in[aPredictReq])
                                                    )
            else:
                db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & (db.match_prediction.predictor_id == aUserId_in), 
                                                        match_id = aMatchId, 
                                                        predictor_id = aUserId_in, 
                                                        team2_goals = int(aParams_in[aPredictReq])
                                                    )
        else:
            if aTeamIndex == 0:
                db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & (db.match_prediction.predictor_id == aUserId_in), 
                                                        match_id = aMatchId, 
                                                        predictor_id = aUserId_in, 
                                                        team1_id = int(aParams_in[aPredictReq])
                                                    )
            else:
                db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & (db.match_prediction.predictor_id == aUserId_in), 
                                                        match_id = aMatchId, 
                                                        predictor_id = aUserId_in, 
                                                        team2_id = int(aParams_in[aPredictReq])
                                                    )
     

def GetAllPossibleTeams(aMatchId_in, aTeamPos_in):
    
    aFieldTag = "team" + str(aTeamPos_in) + "_gen_matches"
    
    aResult = set()
    if session.FixtureTable[aMatchId_in][aFieldTag] == []:
        return [session.FixtureTable[aMatchId_in]["team1"], session.FixtureTable[aMatchId_in]["team2"]]
    else :
        for aMatchId in session.FixtureTable[aMatchId_in][aFieldTag]:
            aResult = aResult.union(GetAllPossibleTeams(aMatchId, 1))
            aResult = aResult.union(GetAllPossibleTeams(aMatchId, 2))
    
    return aResult
    
def CacheData():
    session.StadiumTable = db().select(db.stadium.ALL).as_dict( key = 'stadium_id')
    session.TeamTable = db().select(db.team.ALL).as_dict( key = 'team_id')
    session.FixtureTable = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    session.TeamGroupTable = db().select(db.team_group.ALL).as_dict(key = 'team_id')

def CreatePredictionData(fixtureId_in, aFixtureData_in, aSourceTableData_in):
    aPredData = {"fixture_id":fixtureId_in,
                 "game_number" : aFixtureData_in['game_number'], 
                 "date_time" : aFixtureData_in['date_time'], 
                 "referee" : aFixtureData_in['referee'], 
                 "team1_id" : aFixtureData_in['team1'], 
                 "team2_id" : aFixtureData_in['team2'], 
                 "team1_name" : session.TeamTable[aFixtureData_in['team1']]["name"], 
                 "team2_name" : session.TeamTable[aFixtureData_in['team2']]["name"],
                 "team1_short_name" : session.TeamTable[aFixtureData_in['team1']]["short_name"], 
                 "team2_short_name" : session.TeamTable[aFixtureData_in['team2']]["short_name"],
                 "team1_icon" : session.TeamTable[aFixtureData_in['team1']]["icon_file_name"],
                 "team2_icon" : session.TeamTable[aFixtureData_in['team2']]["icon_file_name"],
                 "team1_goals" : aSourceTableData_in[fixtureId_in]['team1_goals'] if fixtureId_in in aSourceTableData_in else 0,
                 "team2_goals" : aSourceTableData_in[fixtureId_in]['team2_goals'] if fixtureId_in in aSourceTableData_in else 0,
                 "venue" : aFixtureData_in['venue'], 
                 "venue_name" : session.StadiumTable[aFixtureData_in['venue']]['name'], 
                 "venue_city" : session.StadiumTable[aFixtureData_in['venue']]['city']
                 }
    return aPredData
    
def GetMatchPredictions(aUserId_in):
    
    aFixtureData = db(db.fixture.stage == "Group").select().as_dict(key = 'fixture_id')
    aPredTableData = db(db.match_prediction.predictor_id == aUserId_in).select().as_dict(key = 'match_id')
    
    aPredResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        
        aPredData = CreatePredictionData(fixtureId, aFixtureData, aPredTableData)
        aGroupName = session.TeamGroupTable[aFixtureData['team1']]['name']
        if aGroupName not in aPredResults:
            aPredResults[aGroupName] = list()
        
        aPredResults[aGroupName].append(aPredData)
    
    return aPredResults
    
def GetPositionPredictions(aUserId_in):
    
    aFixtureData = db(db.fixture.stage != "Group").select().as_dict(key = 'fixture_id')
    aPredTableData = db(db.match_prediction.predictor_id == aUserId_in).select().as_dict(key = 'match_id')
    
    aPredResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        aPossibleTeam1 = GetAllPossibleTeams(fixtureId, 1)
        aPossibleTeam2 = GetAllPossibleTeams(fixtureId, 2)
        
        aPossibleTeam1Data = [{"id" : row, "name" : session.TeamTable[row]['name']} for row in aPossibleTeam1]
        aPossibleTeam2Data = [{"id" : row, "name" : session.TeamTable[row]['name']} for row in aPossibleTeam2]
        
        aPredData = {"fixture_id":fixtureId, 
                     "game_number" : aFixtureData['game_number'], 
                     "team1_desc" : aFixtureData['team1_definition'], 
                     "team2_desc" : aFixtureData['team2_definition'], 
                     "possible_team1" : aPossibleTeam1Data, 
                     "possible_team2" : aPossibleTeam2Data,
                     "team1_id" : aPredTableData[fixtureId]['team1_id'] if fixtureId in aPredTableData else 0,
                     "team2_id" : aPredTableData[fixtureId]['team2_id'] if fixtureId in aPredTableData else 0
                    }
         
        if aFixtureData["stage"] not in aPredResults:
            aPredResults[aFixtureData["stage"]] = list()
        
        aPredResults[aFixtureData["stage"]].append(aPredData)
    
    return aPredResults

def GetResults():
    
    aFixtureData = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    aResTableData = db().select(db.match_result.ALL).as_dict(key = 'match_id')
    
    aPredResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        
        aPredData = CreatePredictionData(fixtureId, aFixtureData, aResTableData)
        
        aGroupName = session.TeamGroupTable[aFixtureData['team1']]['name']
        if aGroupName not in aPredResults:
            aPredResults[aGroupName] = list()
        
        aPredResults[aGroupName].append(aPredData)
    #logger.info("value of aPredResults is %s", str(aPredResults))
    return aPredResults

    
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

def ConvertURLArgs(anArgs_in):
    
    aResDict = dict()
    
    for key, value in request.vars.iteritems():
        if key.startswith('TargetType'):
            aResDict['TargetType'] = value
        if key.startswith('TargetId'):
            aResDict['TargetId'] = value
        if key.startswith('UserComment'):
            aResDict['UserComment'] = value
        if key.startswith('ToggleState'):
            aResDict['ToggleState'] = value
    return aResDict

def GetPosts():
    aNumPosts = db(db.news_item.id > 0).count()
    #ignore the count for the timebeing. Do it later.
    aNewsData = db().select(db.news_item.ALL, orderby=db.news_item.date_time, limitby=(0, aNumPosts)) 
    
    return sorted(aNewsData, key=lambda k: k['date_time'], reverse=True)
    








    
    
    