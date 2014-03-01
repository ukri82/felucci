import logging
import re
import datetime
import collections

    
def CacheData():
    session.StadiumTable = db().select(db.stadium.ALL).as_dict( key = 'stadium_id')
    session.TeamTable = db().select(db.team.ALL).as_dict( key = 'team_id')
    session.FixtureTable = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    session.TeamGroupTable = db().select(db.team_group.ALL).as_dict(key = 'team_id')
    
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
    logger.info("Res=============================================== %s", str(len(aParams_in)))
    aResultData = dict()
    aFixtureData = dict()
    for aUpdateReq in aParams_in:
        
        aMatchId, aTeamIndex, aMatchOrPos = ParseResultStr(aUpdateReq)
         
        #logger.info("(aMatchId: %s, aTeamIndex: %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aParams_in[aUpdateReq]))
        
        
        
        if aMatchOrPos == "match":
            if aMatchId not in aResultData:
                aResultData[aMatchId] = {'team1_goals' : 0, 'team2_goals' : 0}
            
            if aTeamIndex == 0:
                aResultData[aMatchId]['team1_goals'] = int(aParams_in[aUpdateReq])
            else:
                aResultData[aMatchId]['team2_goals'] = int(aParams_in[aUpdateReq])
        else:
            if aMatchId not in aFixtureData:
                aFixtureData[aMatchId] = {'team1' : 0, 'team2' : 0}
                
            if aTeamIndex == 0:
                aFixtureData[aMatchId]['team1'] = int(aParams_in[aUpdateReq])
            else:
                aFixtureData[aMatchId]['team2'] = int(aParams_in[aUpdateReq])
            
    for aMatchId, aData in aResultData.items():
        #logger.info("(aMatchId: %s, team1_goals: %s, team2_goals: %s)", str(aMatchId), str(aData['team1_goals']), str(aData['team2_goals']))
        db.match_result.update_or_insert((db.match_result.match_id == aMatchId), 
                                            match_id = aMatchId, 
                                            team1_goals = aData['team1_goals'], 
                                            team2_goals = aData['team2_goals'])
                                            
    for aMatchId, aData in aFixtureData.items():
        #logger.info("(aMatchId: %s, team1: %s, team1: %s)", str(aMatchId), str(aData['team1']), str(aData['team2']))
        aTeam1 = aData['team1']
        aTeam2 = aData['team2']
        if aTeam2 == 0:
            aTeam2 = aTeam1
        
        db.fixture.update_or_insert((db.fixture.fixture_id == aMatchId), 
                                            fixture_id = aMatchId, 
                                            team1 = aTeam1,
                                            team2 = aTeam2)
            
def UpdatePredictions(aUserId_in, aParams_in, aPredictionType_in):

    '''
    process each team results for each match
    '''
    logger.info("Pred=============================================== %s", str(len(aParams_in)))
    
    aPredData = dict()
    for aPredictReq in aParams_in:
        aMatchId, aTeamIndex, aMatchOrPos = ParseResultStr(aPredictReq)
      
        #logger.info("(aMatchOrPos : %s, aMatchId: %s, aTeamIndex: %s, goals: %s)", aMatchOrPos, str(aMatchId), str(aTeamIndex), str(aParams_in[aPredictReq]))
        if aMatchId not in aPredData:
            aPredData[aMatchId] = {'team1_goals' : 0, 'team2_goals' : 0, 'team1_id' : 0, 'team2_id' : 0}
        
        if aMatchOrPos == "match":
            if aTeamIndex == 0:
                aPredData[aMatchId]['team1_goals'] = int(aParams_in[aPredictReq])
            else:
                aPredData[aMatchId]['team2_goals'] = int(aParams_in[aPredictReq])
        else:
            if aTeamIndex == 0:
                aPredData[aMatchId]['team1_id'] = int(aParams_in[aPredictReq])
            else:
                aPredData[aMatchId]['team2_id'] = int(aParams_in[aPredictReq])
        
    for aMatchId, aData in aPredData.items():
    
        db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & 
                                             (db.match_prediction.predictor_id == aUserId_in) & 
                                             (db.match_prediction.pred_type == aPredictionType_in), 
                                                match_id = aMatchId, 
                                                pred_type = aPredictionType_in,
                                                predictor_id = aUserId_in, 
                                                team1_goals = aData['team1_goals'],
                                                team2_goals = aData['team2_goals'],
                                                team1_id = aData['team1_id'],
                                                team2_id = aData['team2_id']
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
    
def GetPriorPredictions(aUserId_in):
    
    aPredTableData = db(db.match_prediction.predictor_id == aUserId_in and db.match_prediction.pred_type == "prior").select().as_dict(key = 'match_id')
    
    return JoinFixtureWith(aPredTableData)
    
def JoinFixtureWith(aSourceData_in):
    
    aFixtureData = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    
    aResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        
        if aFixtureData['team1'] in session.TeamGroupTable:     #For the second round, the team id is not present in the fixture table yet.
            aPredData = CreatePredictionData(fixtureId, aFixtureData, aSourceData_in)
            
            aGroupName = session.TeamGroupTable[aFixtureData['team1']]['name'] if aFixtureData['stage'] == "Group" else aFixtureData['stage']
            
            if aGroupName not in aResults:
                aResults[aGroupName] = list()
            
            aResults[aGroupName].append(aPredData)
    #logger.info("value of aResults is %s", str(aResults))
    return aResults

    
    
def GetPositionPredictions(aUserId_in):
    
    #aFixtureData = db(db.fixture.stage != "Group").select().as_dict(key = 'fixture_id')
    aFixtureData = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    aPredTableData = db(db.match_prediction.predictor_id == aUserId_in and db.match_prediction.pred_type == "prior").select().as_dict(key = 'match_id')
    
    aPredResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        if aFixtureData['team1'] not in session.TeamGroupTable:
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
    
    aResTableData = db().select(db.match_result.ALL).as_dict(key = 'match_id')
    
    return JoinFixtureWith(aResTableData)
    

    

    
def GetUsers(aUserIdList_in):
    aUserTable = db(db.auth_user.id.belongs(aUserIdList_in)).select()
    aUserData = dict()
    for user in aUserTable:
        aUserData[user.id] = {"first_name" : user.first_name, "nickname" : user.nickname, "image" : user.image}
        
    return aUserData

def GetComments(aTargetType_in, aTargetId_in):
    
    aCommentTable = db(db.user_comment.target_type == aTargetType_in and db.user_comment.target_id == aTargetId_in).select()
    aUserIds = [item.author_id for item in aCommentTable]
    aUserData = GetUsers(aUserIds)

    aResults = []
    for commentData in aCommentTable:
        aComment = {"author_id" : commentData.author_id, 
                    "author_first_name" : aUserData[commentData.author_id]["first_name"], 
                    "author_nickname" : aUserData[commentData.author_id]["nickname"], 
                    "author_image" : aUserData[commentData.author_id]["image"], 
                    "body" : commentData.body, 
                    "target_type" : commentData.target_type, 
                    "target_id" : commentData.target_id, 
                    "date_time" : commentData.date_time
                    }
        aResults.append({'id' : commentData.id,
						 'comment' : aComment})

    #logger.info("value of aResults is %s", str(aResults))
    return sorted(aResults, key=lambda k: k['comment']["date_time"])

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

def RetrieveNextChunk(aTable_in, aSortField_in, anOffset_in, aCount_in, anAsc_in):
    aNumEntries = db(db[aTable_in].id > 0).count()
    aMin = min(anOffset_in + aCount_in, aNumEntries)
    
    if anAsc_in == True:
        aData = db().select(db[aTable_in].ALL, orderby=db[aTable_in][aSortField_in], limitby=(anOffset_in, aMin))
    else:
        aData = db().select(db[aTable_in].ALL, orderby=~db[aTable_in][aSortField_in], limitby=(anOffset_in, aMin))
    
    return aNumEntries > aMin , sorted(aData, key=lambda k: k[aSortField_in], reverse=True)    

def RecreateData(aCSVFileName_in):
    db(db.match_result.id > 0).delete()
    db(db.match_prediction.id > 0).delete()
    db(db.team.id > 0).delete()
    db(db.fixture.id > 0).delete()
    db(db.team_group.id > 0).delete()
    db(db.stadium.id > 0).delete()
    db.import_from_csv_file(aCSVFileName_in)
    CacheData()


    
    
    