import logging
import re
import datetime
import collections
import math
import time
from itertools import groupby

def LogVal(aDesc_in, aVar_in):
    logger.info("Value of %s : %s", str(aDesc_in), str(aVar_in))
    
def CacheData():
    logging.info("Cache is recreated for user : %s", str(auth.user.id))
    session.StadiumTable = db().select(db.stadium.ALL).as_dict( key = 'stadium_id')
    session.TeamTable = db().select(db.team.ALL).as_dict( key = 'team_id')
    session.FixtureTable = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
    session.TeamGroupTable = db().select(db.team_group.ALL).as_dict(key = 'team_id')
    
    session.PriorPredictionTable = db((db.match_prediction.predictor_id == auth.user.id) & (db.match_prediction.pred_type == "prior")).select().as_dict(key = 'match_id')
    session.SpotPredictionTable = db((db.match_prediction.predictor_id == auth.user.id) & (db.match_prediction.pred_type == "spot")).select().as_dict(key = 'match_id')
        
def ParseResultStr(aResult_in):
    
    aMatchIdStr = ''
    aTeamIndexStr = ''
    aMatchOrPos = 'match'
    try:
        matchObj = re.search('([a-zA-Z]+)_match_(\d*)_score(\d)', aResult_in)
        aMatchIdStr = matchObj.group(2)
        aTeamIndexStr = matchObj.group(3)
    except AttributeError:
        try:
            matchObj = re.search('([a-zA-Z]+)_pos_(\d*)_team(\d)', aResult_in)
            aMatchOrPos = 'pos'
            aMatchIdStr = matchObj.group(2)
            aTeamIndexStr = matchObj.group(3)
        except AttributeError:
            logging.error("Error ins parsing the input values. value of aResult_in is %s", str(aResult_in))
    
    aMatchId = int(aMatchIdStr)
    aTeamIndex = int(aTeamIndexStr) - 1

    return aMatchId, aTeamIndex, aMatchOrPos
  
 
def StoreMatchResults(aResultData):

    for aMatchId, aData in aResultData.items():
        #logger.info("(aMatchId: %s, team1_goals: %s, team2_goals: %s)", str(aMatchId), str(aData['team1_goals']), str(aData['team2_goals']))
        db.match_result.update_or_insert((db.match_result.match_id == aMatchId), 
                                            match_id = aMatchId, 
                                            team1_goals = aData['team1_goals'], 
                                            team2_goals = aData['team2_goals'])
                                            
    if request.env.web2py_runtime_gae:
        time.sleep( 5 )             #   To workaround the eventual consistency BS of the GAE                              
    
                                          
def UpdateFixture(aFixtureData):

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
                                            
    if request.env.web2py_runtime_gae:
        time.sleep( 5 )             #   To workaround the eventual consistency BS of the GAE
    
def ExtractResultData(aParams_in):
    '''
    process each team results for each match
    '''
    logger.info("Res=============================================== %s", str(len(aParams_in)))
    aResultData = dict()
    aFixtureData = dict()
    for aUpdateReq in aParams_in:
        
        aMatchId, aTeamIndex, aMatchOrPos = ParseResultStr(aUpdateReq)
         
        logger.info("(aMatchId: %s, aTeamIndex: %s, aMatchOrPos = %s, goals: %s)", str(aMatchId), str(aTeamIndex), str(aMatchOrPos), str(aParams_in[aUpdateReq]))
        
        
        
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
                
    return aFixtureData, aResultData
                
def UpdateResults(aParams_in):

    aFixtureData, aResultData = ExtractResultData(aParams_in)
    
    UpdateFixture(aFixtureData)  
    StoreMatchResults(aResultData)   
    #   update chache
    session.FixtureTable = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
        
    CalculateGoalPredictionScores(aFixtureData, aResultData)
            
def UpdatePredictions(aParams_in, aPredictionType_in):

    '''
    process each team results for each match
    '''
    logger.info("Pred=============================================== %s", str(len(aParams_in)))
    
    aPredData = dict()
    for aPredictReq in aParams_in:
        aMatchId, aTeamIndex, aMatchOrPos = ParseResultStr(aPredictReq)
      
        logger.info("(aMatchOrPos : %s, aMatchId: %s, aTeamIndex: %s, goals: %s)", aMatchOrPos, str(aMatchId), str(aTeamIndex), str(aParams_in[aPredictReq]))
        if aMatchId not in aPredData:
            aCacheTable = session.PriorPredictionTable if aPredictionType_in == "prior" else session.SpotPredictionTable
            aPredData[aMatchId] = {'team1_goals' : aCacheTable[aMatchId]['team1_goals'] if aMatchId in aCacheTable else None,
                                        'team2_goals' : aCacheTable[aMatchId]['team2_goals'] if aMatchId in aCacheTable else None, 
                                        'team1_id' : aCacheTable[aMatchId]['team1_id'] if aMatchId in aCacheTable else None, 
                                        'team2_id' : aCacheTable[aMatchId]['team2_id'] if aMatchId in aCacheTable else None}
        
        if aMatchOrPos == "match":
            if aTeamIndex == 0:
                aPredData[aMatchId]['team1_goals'] = int(aParams_in[aPredictReq]) if aParams_in[aPredictReq] != '' else None
            else:
                aPredData[aMatchId]['team2_goals'] = int(aParams_in[aPredictReq]) if aParams_in[aPredictReq] != '' else None
        else:
            if aTeamIndex == 0:
                aPredData[aMatchId]['team1_id'] = int(aParams_in[aPredictReq]) if aParams_in[aPredictReq] != '' else None
            else:
                aPredData[aMatchId]['team2_id'] = int(aParams_in[aPredictReq]) if aParams_in[aPredictReq] != '' else None
        
    for aMatchId, aData in aPredData.items():
    
        anId = db.match_prediction.update_or_insert((db.match_prediction.match_id == aMatchId) & 
                                             (db.match_prediction.predictor_id == auth.user.id) & 
                                             (db.match_prediction.pred_type == aPredictionType_in), 
                                                match_id = aMatchId, 
                                                pred_type = aPredictionType_in,
                                                predictor_id = auth.user.id, 
                                                team1_goals = aData['team1_goals'],
                                                team2_goals = aData['team2_goals'],
                                                team1_id = aData['team1_id'],
                                                team2_id = aData['team2_id']
                                            )
        # synch back the cache without additional db query
        aCacheTable = session.PriorPredictionTable if aPredictionType_in == "prior" else session.SpotPredictionTable
        aCacheTable[aMatchId] = {'team1_goals' : aData['team1_goals'],
                                 'team2_goals' : aData['team2_goals'],
                                 'team1_id' : aData['team1_id'],
                                 'team2_id' : aData['team2_id'],
                                 'id' : anId
                                }

def CalculateGoalPredictionScores(aFixtureData_in, aResultData_in):

    aMatchIdSet = set()
        
    for aMatchId, aData in aResultData_in.items():
        CalculateGoalScore(aMatchId)
        aMatchIdSet.add(aMatchId)
    
    
    UpdateMatchScoreAndRankForAllUsers(aMatchIdSet)
    
    
    UpdateUserScores(aMatchIdSet)

    return 0


def UpdateUserRankingHistory(aUserId, aMatchId, aLeagueMemberships, aCurrentScore):

    for aLeagueMember in aLeagueMemberships:
        db.user_ranking_history.update_or_insert(((db.user_ranking_history.predictor_id == aUserId) & 
                                                  (db.user_ranking_history.match_id == aMatchId) & 
                                                  (db.user_ranking_history.member_id == aLeagueMember.id)
                                                 ), 
                                                 predictor_id = aUserId,
                                                 match_id = aMatchId,
                                                 member_id = aLeagueMember.id,
                                                 score = aCurrentScore
                                                )
    
 
def GetLastScoreForUser(aUserId_in, aMatchId_in):
    aLastScore = 0
    if aMatchId_in > 1:    #   Assumption : Match ids always start with 1
        
        aLastMatch = db(((db.user_ranking_history.predictor_id == aUserId_in) & 
                          (db.user_ranking_history.match_id == (aMatchId_in - 1))
                         )).select()   #add a validation for aMatchId_in - 1 restriction. The score will be same across all league memberships. So, ignore that in the query
        if len(aLastMatch) > 0:
            aLastScore = aLastMatch[0].score
            
    return aLastScore
                
def UpdateMatchScoreAndRankForAllUsers(aMatchSet_in):

    #   Update the scores for all users.
    for aMatchId in sorted(aMatchSet_in):
        aPredForMatch = db(db.match_prediction.match_id == aMatchId).select()   #Get all predictions for this match ### SCALE WARNING ###
        
        aUsers = list(map(lambda x:x.id, db().select(db.auth_user.ALL)))       #   Get all predictors   ### SCALE WARNING ###
        LogVal("aUsers :", aUsers)
        
        aLeagueIdSet = set()
        
        for aUserId in aUsers:
            aLeagueMemberships = db((db.league_member.member_id == aUserId) & (db.league_member.membership_state == 'approved')).select()  #   Find their league memberships
        
            aPredictionsForUser = filter(lambda x:x.predictor_id == aUserId, aPredForMatch)
            aUserScore = sum(map(lambda x:x.score, aPredictionsForUser)) if aPredictionsForUser else 0  #   Get the total score from all predictions
            aCurrentScore = GetLastScoreForUser(aUserId, aMatchId) + aUserScore
            
            #   Update the score for all league memberships
            UpdateUserRankingHistory(aUserId, aMatchId, aLeagueMemberships, aCurrentScore)
            
            LogVal("aLeagueMemberships :", aLeagueMemberships)
            aLeagueIdSet |= set(map(lambda x:x.league_id, aLeagueMemberships))
            
        
        if request.env.web2py_runtime_gae:
            time.sleep( 5 )             #   To workaround the eventual consistency BS of the GAE
            
        UpdateMatchRanking(aMatchId, aLeagueIdSet)
            
        
def UpdateMatchRanking(aMatchId_in, aLeagueIdSet_in):

    LogVal("aLeagueIdSet :", aLeagueIdSet_in)
    anAllRankMap = []
    #   Update the ranking of all users in all leagues orderby=~db.notification.date_time
    for aLeagueId in aLeagueIdSet_in:
        allMembershipsOfLeague = map(lambda x:x.id, db((db.league_member.league_id == aLeagueId) & (db.league_member.membership_state == 'approved')).select()) ### SCALE WARNING ###
        LogVal("allMembershipsOfLeague :", allMembershipsOfLeague)
        
        '''
        for aMembershipChunk in [allMembershipsOfLeague[i : i + 10] for i in range(0, len(allMembershipsOfLeague), 10)]:
            LogVal("aMembershipChunk :", aMembershipChunk)
            aUserScores = db((db.user_ranking_history.member_id.belongs(aMembershipChunk)) & (db.user_ranking_history.match_id == aMatchId_in)).select(orderby=~db.user_ranking_history.score)
            LogVal("aUserScores :", aUserScores)
            if request.env.web2py_runtime_gae:
                time.sleep( 1 )
        '''
        aUserScores = db((db.user_ranking_history.member_id.belongs(allMembershipsOfLeague)) & (db.user_ranking_history.match_id == aMatchId_in)).select(orderby=~db.user_ranking_history.score)    ### SCALE WARNING ###
        LogVal("aUserScores :", aUserScores)
        
        anAllRankMap.extend(list(zip(  map(lambda x:x.id, aUserScores), range(len(aUserScores))  )))
        
    
    LogVal("anAllRankMap :", anAllRankMap)
    for aRank in anAllRankMap:
        db(db.user_ranking_history.id == aRank[0]).update(match_rank = aRank[1] + 1)

def UpdateUserScores(aMatchSet_in):

    aUsers = list(map(lambda x:x.id, db().select(db.auth_user.ALL))) ### SCALE WARNING ###
    
    aLastMatchId = GetLastMatchId()
    if aLastMatchId == -1:
        return
        
    for aUserId in aUsers:
        aMatchHistoryRec = db((db.user_ranking_history.predictor_id == aUserId) & (db.user_ranking_history.match_id == aLastMatchId)).select().first()
        db(db.auth_user.id == aUserId).update(last_score = aMatchHistoryRec.score, last_rank = aMatchHistoryRec.match_rank )


                                           
def CalculatePositionScore():
    logger.info("==================================")
    allFixtures = db(db.fixture.stage != "Group").select()
    allNonGroupMatches = groupby(allFixtures, lambda x: x.stage)
    LogVal("allNonGroupMatches", allNonGroupMatches)
    
    
    aStageLastMatchDict = dict((aStage, max(map(lambda x:x.fixture_id, aFixtureItem))) for aStage, aFixtureItem in allNonGroupMatches)
    LogVal("aStageLastMatchDict", aStageLastMatchDict)
        
    aMatchIds = map(lambda x:x.game_number, allFixtures)
    anAllPredictions = filter(lambda x:x.team1_id is not None and x.team2_id is not None, db(db.match_prediction.match_id.belongs(aMatchIds)).select())   ### SCALE WARNING ###
    LogVal("anAllPredictions", anAllPredictions)
    
    aUserPredictionsGroups = groupby(anAllPredictions, lambda x: x.predictor_id)
    LogVal("aUserPredictionsGroups", aUserPredictionsGroups)
    
    aScoreDict = dict.fromkeys(map(lambda x:x.id, anAllPredictions), 0)
    LogVal("aScoreDict", aScoreDict)
    
    allNonGroupMatches = groupby(allFixtures, lambda x: x.stage)  # Earlier allNonGroupMatches is destroyed due to some peculiarity of groupby
    for aStage, aMatchSetDummy in allNonGroupMatches:
        LogVal("aStage", aStage)
        
        aMatchSet = list(aMatchSetDummy)
        #logger.info("aStage = %s, aMatchSet = %s", str(aStage), str(aMatchSet))
        
        
        aMatchesWithTeamsAvailable = filter(lambda x:x.team1 != -1 and x.team2 != -1, aMatchSet)
        LogVal("aMatchesWithTeamsAvailable", aMatchesWithTeamsAvailable)
        #   Check if the predictions match the positions first
        if aStage == "IP":
            
            for aMatch in aMatchesWithTeamsAvailable:
                LogVal("aMatch", aMatch)
                aPredictionsForMatch = filter(lambda x:x.match_id == aMatch.game_number, anAllPredictions)
                LogVal("aPredictionsForMatch", aPredictionsForMatch)
                if len(aPredictionsForMatch) > 0 :
                    if aPredictionsForMatch[0].team1_id == aMatch.team1:
                        LogVal("*******aPredictionsForMatch[0].team1_id********", aPredictionsForMatch[0].team1_id)
                        aScoreDict[aPredictionsForMatch[0].id] = aScoreDict[aPredictionsForMatch[0].id] + 5
                    if aPredictionsForMatch[0].team2_id == aMatch.team2:
                        LogVal("*******aPredictionsForMatch[0].team2_id*******", aPredictionsForMatch[0].team2_id)
                        aScoreDict[aPredictionsForMatch[0].id] = aScoreDict[aPredictionsForMatch[0].id] + 5
                        
        LogVal("aScoreDict after IP stage", aScoreDict)                
        #   Check if the teams falling anywhere in the stage    
        
        aTeamsInStage = set(map(lambda x:x.team1, aMatchesWithTeamsAvailable) + map(lambda x:x.team2, aMatchesWithTeamsAvailable))
        LogVal("aTeamsInStage", aTeamsInStage)
        
        #LogVal("map(lambda x:x.game_number, aMatchSet)", map(lambda x:x.game_number, aMatchSet))
        anAllPredictionsForThisStage = filter(lambda x:x.match_id in map(lambda x:x.game_number, aMatchSet), anAllPredictions)
        LogVal("anAllPredictionsForThisStage", anAllPredictionsForThisStage)
        
        aMatchesForUserInThisStage = groupby(anAllPredictionsForThisStage, lambda x: x.predictor_id)
        LogVal("aMatchesForUserInThisStage", list(aMatchesForUserInThisStage))
    
        for aPredictorId, aPredSetDummy in aMatchesForUserInThisStage:
            
            aPredSet = list(aPredSetDummy)
            
            aTeamsInPrediction = set(map(lambda x:x.team1_id, aPredSet) + map(lambda x:x.team2_id, aPredSet))
            
            LogVal("aTeamsInPrediction", aTeamsInPrediction)
            
            aCommonTeams = aTeamsInStage & aTeamsInPrediction # interesction of two sets
            
            LogVal("*******aCommonTeams*******", aCommonTeams)
            
            aNumberOfCorrectPredictions = len(aCommonTeams)
            aStageScore = 0
            if aStage == "IP":
                aStageScore = aNumberOfCorrectPredictions * 5
            elif aStage == "JQ":
                aStageScore = aNumberOfCorrectPredictions * 10
            elif aStage == "KS":
                aStageScore = aNumberOfCorrectPredictions * 15
            elif aStage == "L":
                aStageScore = aNumberOfCorrectPredictions * 15
            elif aStage == "MFN":
                aStageScore = aNumberOfCorrectPredictions * 20
            elif aStage == "NWN":
                aStageScore = aNumberOfCorrectPredictions * 20
            elif aStage == "OFN":
                aStageScore = aNumberOfCorrectPredictions * 20
               
            aLastMatchPredId = max(aPredSet, key=lambda x:x.match_id).id
            LogVal("aLastMatchPredId", aLastMatchPredId)
            aScoreDict[aLastMatchPredId] = aScoreDict[aLastMatchPredId] + aStageScore
        LogVal("aScoreDict after normal stage", aScoreDict)      
        logger.info("------------------------------------------------------")
    LogVal("aScoreDict", aScoreDict)
    

        
def CalculateGoalScore(aMatchId_in):

    anAllPredictions = db(db.match_prediction.match_id == aMatchId_in).select() ### SCALE WARNING ###
    aResult = db(db.match_result.match_id == aMatchId_in).select()[0]
    aGoalDiff = aResult.team1_goals - aResult.team2_goals
    aResultOutcome = (aGoalDiff)/abs(aGoalDiff) if aGoalDiff != 0 else 0
    LogVal("aResultOutcome :", aResultOutcome)
    
    aScoreDict = dict()
    
    for aPrediction in anAllPredictions:
        logger.info("team1_goals : %s, team2_goals : %s", str(aPrediction.team1_goals), str(aPrediction.team2_goals))
        aScore = 0
        
        if aPrediction.team1_goals is not None and aPrediction.team2_goals is not None:
            aGoalDiff = aPrediction.team1_goals - aPrediction.team2_goals
            aPredOutcome = (aGoalDiff) / abs(aGoalDiff) if aGoalDiff != 0 else 0
            LogVal("aPredOutcome :", aPredOutcome)
            
            #   Score for outcome
            aResultScore = 7 if aPrediction.pred_type == "prior" else 3
            aScore += aResultScore if aResultOutcome == aPredOutcome else 0
            LogVal("aScore1 :", aScore)
            
            #   Score for goals
            aDistance = math.sqrt((aPrediction.team1_goals - aResult.team1_goals) * (aPrediction.team1_goals - aResult.team1_goals) + 
                            (aPrediction.team2_goals - aResult.team2_goals) * (aPrediction.team2_goals - aResult.team2_goals))

            LogVal("aDistance :", aDistance)
        
        aMaxPoint = 10 if aPrediction.pred_type == "prior" else 5
        aDistance = min(aMaxPoint, aDistance)   # anything more than aMaxPoint should get 0. No negative business
        aDistanceScore = aMaxPoint - aDistance  #   more distance less score. inverse law
        LogVal("aDistanceScore :", aDistanceScore)
        
        aScore += int(aDistanceScore + 0.5) #round
        aScoreDict[aPrediction.id] = aScore
     
    #   update the score in database.
    for aPredId, aScore in aScoreDict.items():
    
        db.match_prediction.update_or_insert((db.match_prediction.id == aPredId), 
                                                score = aScore
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
                 "team1_goals" : aSourceTableData_in[fixtureId_in]['team1_goals'] if fixtureId_in in aSourceTableData_in else None,
                 "team2_goals" : aSourceTableData_in[fixtureId_in]['team2_goals'] if fixtureId_in in aSourceTableData_in else None,
                 "points_scored" : aSourceTableData_in[fixtureId_in]['score'] if fixtureId_in in aSourceTableData_in and 'score' in aSourceTableData_in[fixtureId_in] else None,
                 "venue" : aFixtureData_in['venue'], 
                 "venue_name" : session.StadiumTable[aFixtureData_in['venue']]['name'], 
                 "venue_city" : session.StadiumTable[aFixtureData_in['venue']]['city']
                 }
    return aPredData
    
def GetGoalPredictions(aPredictionType_in, aUserId_in):
    
    logging.info("aUserId_in: %s", str(aUserId_in))
    
    if aUserId_in == auth.user.id:
        aPredTableData = session.PriorPredictionTable if aPredictionType_in is "prior" else session.SpotPredictionTable
    else:
        '''if request.env.web2py_runtime_gae:
            aPredTableData = db((db.match_prediction.predictor_id == aUserId_in) & (db.match_prediction.pred_type == aPredictionType_in)).select().as_dict(key = 'match_id')
        else:'''
        aPredTableData = db((db.match_prediction.predictor_id == aUserId_in) & (db.match_prediction.pred_type == aPredictionType_in)).select().as_dict(key = 'match_id')
    
    logging.info("aPredTableData: %s", str(aPredTableData))
    return JoinFixtureWith(aPredTableData)
    
def JoinFixtureWith(aSourceData_in):
    
    aFixtureData = session.FixtureTable
    
    aResults = dict()
    for fixtureId, aFixtureData in aFixtureData.items():
        
        if aFixtureData['team1'] in session.TeamGroupTable:     #For the second round, the team id is not present in the fixture table yet.
            aPredData = CreatePredictionData(fixtureId, aFixtureData, aSourceData_in)
            
            aGroupName = session.TeamGroupTable[aFixtureData['team1']]['name'] if aFixtureData['stage'] == "Group" else aFixtureData['stage']
            
            if aGroupName not in aResults:
                aResults[aGroupName] = list()
            
            aResults[aGroupName].append(aPredData)
    
    return aResults

    
    
def GetPositionPredictions(aResults_in):
    
    if aResults_in:
        session.FixtureTable = db().select(db.fixture.ALL).as_dict(key = 'fixture_id')
        
    aPredResults = dict()
    for fixtureId, aFixtureData in session.FixtureTable.items():
    
        aTeam1Id = -1
        aTeam2Id = -1
        addFxitureId = False
        
        if not aResults_in:
            if aFixtureData['team1'] not in session.TeamGroupTable:
                addFxitureId = True
                
                if fixtureId in session.PriorPredictionTable:
                   aTeam1Id = session.PriorPredictionTable[fixtureId]['team1_id']
                   aTeam2Id = session.PriorPredictionTable[fixtureId]['team2_id']
                
        else:    
            if aFixtureData["stage"] != "Group":
                addFxitureId = True
                aTeam1Id = aFixtureData['team1']
                aTeam2Id = aFixtureData['team2']
                
            
        if addFxitureId:
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
                         "team1_id" : aTeam1Id,
                         "team2_id" : aTeam2Id
                        }
                 
            if aFixtureData["stage"] not in aPredResults:
                aPredResults[aFixtureData["stage"]] = list()
            
            aPredResults[aFixtureData["stage"]].append(aPredData)
    
    
    return aPredResults

def GetGoalPredictionResults():
    
    aResTableData = db().select(db.match_result.ALL).as_dict(key = 'match_id')
    
    return JoinFixtureWith(aResTableData)
    

    

    
def GetUsers(aUserIdList_in):
    aUserTable = db(db.auth_user.id.belongs(aUserIdList_in)).select()
    aUserData = dict()
    for user in aUserTable:
        aUserData[user.id] = {"first_name" : user.first_name, "nickname" : user.nickname, "image" : user.image}
        
    return aUserData

def GetComments(aTargetType_in, aTargetId_in):
    
    '''if request.env.web2py_runtime_gae:
        aCommentTable = db((db.user_comment.target_type == aTargetType_in) and (db.user_comment.target_id == aTargetId_in)).select()
    else:'''
    aCommentTable = db((db.user_comment.target_type == aTargetType_in) & (db.user_comment.target_id == aTargetId_in)).select()
        
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

def SubmitComment(aTargetType_in, aTargetId_in, aComment_in):
    #logger.info("value of auth.user,aTargetType_in, aTargetId_in, aComment_in  is %s, %s, %s, %s", str(auth.user), str(aTargetType_in), str(aTargetId_in), str(aComment_in))
    db.user_comment.insert(author_id = auth.user.id, target_id = aTargetId_in, target_type = aTargetType_in, date_time = datetime.datetime.now(), body = aComment_in)
    
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
    db(db.user_ranking_history.id > 0).delete()
    db(db.user_ranking_history.id > 0).delete()
    db(db.team.id > 0).delete()
    db(db.fixture.id > 0).delete()
    db(db.team_group.id > 0).delete()
    db(db.stadium.id > 0).delete()
    db.import_from_csv_file(aCSVFileName_in)
    CacheData()

def GetActiveBets():
    
    allOpenBets = db(db.bet_offer.bet_state == 'open').select()
    aUserBetTable = db(db.user_bet.predictor_id == auth.user.id).select().as_dict(key = 'bet_id')
    
    aBetData = []
    
    for aBet in allOpenBets:
        
        aBetItem = {
                    "id" : aBet["id"],
                    "match_id" : aBet["match_id"],
                    "team1" : session.TeamTable[session.FixtureTable[aBet["match_id"]]["team1"]]["name"],
                    "team2" : session.TeamTable[session.FixtureTable[aBet["match_id"]]["team2"]]["name"],
                    "offer" : aBet["offer"],
                    "odd" : aBet["odd"],
                    "points" : aUserBetTable[aBet["id"]]["points"] if aBet["id"] in aUserBetTable else 0
                   }
        aBetData.append(aBetItem)
        
    return aBetData
    
    
def GetOldBets(aUserId_in):
    
    aAllBets = db().select(db.bet_offer.ALL).as_dict(key = 'id')
    aUserBetTable = db(db.user_bet.predictor_id == aUserId_in).select()
    
    aUserBetData = []
    for aUserBet in aUserBetTable:
        if aAllBets[aUserBet["bet_id"]]["bet_state"] not in set(['unopen', 'open']):
            aMatchId = aAllBets[aUserBet["bet_id"]]["match_id"]
            aBetItem = {
                        "id" : aUserBet["id"],
                        "match_id" : aMatchId,
                        "team1" : session.TeamTable[session.FixtureTable[aMatchId]["team1"]]["name"],
                        "team2" : session.TeamTable[session.FixtureTable[aMatchId]["team2"]]["name"],
                        "offer" : aAllBets[aUserBet["bet_id"]]["offer"],
                        "odd" : aAllBets[aUserBet["bet_id"]]["odd"],
                        "points" : aUserBet["points"],
                        "scored_points" : aUserBet["scored_points"]
                        }
            aUserBetData.append(aBetItem)
        
    return aUserBetData
    
def UpdateUserBets(aParams_in):

    aAllBetReq = []
    for aBetReq, aPoint in aParams_in.items():
        aBetId = int(re.search('user_bet_(\d+)', aBetReq).group(1))
        aPoint = int(aPoint)
        aAllBetReq.append({"id" : aBetId, "points" : aPoint})

    for aReq in aAllBetReq:
        db.user_bet.update_or_insert((db.user_bet.bet_id == aReq["id"]), 
                                            bet_id = aReq["id"], 
                                            predictor_id = auth.user.id,
                                            points = aReq["points"])



def GetActiveBetsAdmin():
    
    return db(db.bet_offer.bet_state == 'open').select()

    
def UpdateAdminBets(aParams_in):

    aAllBetReq = dict()
    for aBetReq, aValue in aParams_in.items():
        matchObj = re.search('bet_([a-zA-Z]+)_(\d+)', aBetReq)
        aFieldName = matchObj.group(1)
        aBetId = int(matchObj.group(2))
        
        if aBetId not in aAllBetReq:
            aAllBetReq[aBetId] = {"result": 'unknown', "state": 'unopen'}
        
        aAllBetReq[aBetId][aFieldName] = aValue

    for aKey, aVal in aAllBetReq.items():
        db(db.bet_offer.id == aKey).update(bet_state = aVal["state"],
                                            bet_result = aVal["result"])

def GetNumUnreadNotifications():
    
    return db((db.notification.target_id == auth.user.id) & (db.notification.read_state == "unopened")).count()
    
    
def GetUserNotifications(anOffset_in, aCount_in, aDirection_in):
    
    aNumEntries = db((db.notification.target_id == auth.user.id) & (db.notification.read_state != "deleted")).count()
    
    
    if aDirection_in == 'Left':
        anOffset_in = max(0, anOffset_in - 1)
    elif aDirection_in == 'Right':
        anOffset_in = min(aNumEntries // aCount_in, anOffset_in + 1)
    elif aDirection_in == 'LeftMost':
        anOffset_in = 0
    elif aDirection_in == 'RightMost':
        anOffset_in = aNumEntries // aCount_in
        
    aLeft = anOffset_in * aCount_in
    aRight = min((anOffset_in + 1) * aCount_in, aNumEntries)
    
    aMoreLeftFlag = aLeft > 0
    aMoreRightFlag = aRight < aNumEntries
            
    allMessages = db((db.notification.target_id == auth.user.id) & (db.notification.read_state != "deleted")).select(orderby = db.notification.read_state | ~db.notification.date_time, limitby=(aLeft, aRight))
        
    aMessageData = []
    for aMessageItem in allMessages:
        #if aMessageItem.read_state != "deleted":
        aMessage = {"id" : aMessageItem.id,
                    "date_time" : aMessageItem.date_time,
                    "source_id" : aMessageItem.source_id,
                    "source_name" : db.auth_user[aMessageItem.source_id].first_name,
                    "subject" : aMessageItem.subject,
                    "notification_body" : aMessageItem.notification_body,
                    "read_state" : aMessageItem.read_state
                    }
        aMessageData.append(aMessage)
            
    return aMoreLeftFlag, aMoreRightFlag, anOffset_in, sorted(aMessageData, key=lambda k: k["date_time"], reverse = True)
    
def ReadNotification(aNotificationId_in):
    
    
    db(db.notification.id == aNotificationId_in).update(read_state = "opened")
    
def DeleteNotification(aNotificationId_in):
    
    db(db.notification.id == aNotificationId_in).update(read_state = "deleted")    


    
def GetUserLeagues():

    allUserLeagues = db((db.league_member.member_id == auth.user.id) & ~(db.league_member.membership_state == "removed")).select()
    
    aLeagueData = []
    for aLeague in allUserLeagues:
        aLeagueDetails = db(db.league.id == aLeague.league_id).select()[0]
        if aLeagueDetails.league_state != "deleted":
            aNumMembers = len(db(db.league_member.league_id == aLeague.league_id).select())
            aLeagueItem = {"league_id" : aLeagueDetails.id,
                            "league_member_id" : aLeague.id,
                            "league_name" : aLeagueDetails.name,
                            "owner_id" : aLeagueDetails.owner_id,
                            "owner_name" : db.auth_user[aLeagueDetails.owner_id].first_name if aLeagueDetails.owner_id is not None else "",
                            "membership_state" : aLeague.membership_state,
                            "num_members" : aNumMembers
                            }
            aLeagueData.append(aLeagueItem)
    
    
    return aLeagueData   
    
def GetAdminLeagues():

    allAdminLeagues = db(db.league.owner_id == auth.user.id).select()
    
    aLeagueData = []
    for aLeague in allAdminLeagues:
        aLeagueItem = {"league_id" : aLeague.id,
                        "league_name" : aLeague.name,
                        "league_desc" : aLeague.league_desc,
                        "league_state" : aLeague.league_state
                      }         
        aLeagueData.append(aLeagueItem)
    
    
    return aLeagueData 
 


def GetLeagueDetails(aLeagueId_in, anAllUserInfo_in):

    aLeague = db.league[aLeagueId_in]
    
    aMembers = db(db.league_member.league_id == aLeague.id).select()
        
    aMemberData = []
    if anAllUserInfo_in == True:
        for aMember in aMembers:
            aMemberItem = {"id" : aMember.id,
                            "member_id" : aMember.member_id,
                            "member_name" : db.auth_user[aMember.member_id].first_name,
                            "membership_state" : aMember.membership_state,
                            "last_score" : db.auth_user[aMember.member_id].last_score
                        }
            aMemberData.append(aMemberItem)
            
    aLeagueItem = {"league_id" : aLeague.id,
                    "league_name" : aLeague.name,
                    "league_desc" : aLeague.league_desc,
                    "league_state" : aLeague.league_state,
                    "all_members" : aMemberData
                    }       
                    
    return aLeagueItem 
    
def GetLastMatchId():

    aLastMatchIdRec = db(db.user_ranking_history).select(db.user_ranking_history.match_id.max())
    if aLastMatchIdRec is None:
        return -1
    
    if request.env.web2py_runtime_gae:
        aLastMatchId = aLastMatchIdRec.first().match_id
    else:
        aLastMatchId = aLastMatchIdRec.first()['_extra']['MAX(user_ranking_history.match_id)']
    return aLastMatchId
    
def GetLeagueRankNextChunk(aLeagueId_in, anOffset_in, aCount_in):

    LogVal("aLeagueId_in :", aLeagueId_in)
    aMemberDict = db(db.league_member.league_id == aLeagueId_in).select().as_dict(key = 'id')
    aMembers = aMemberDict.keys()
    aLastMatchId = GetLastMatchId()
    if aLastMatchId == -1:
        return False, []
    
    aNumEntries = db((db.user_ranking_history.member_id.belongs(aMembers)) & (db.user_ranking_history.match_id == aLastMatchId)).count()
    aMin = min(anOffset_in + aCount_in, aNumEntries)
    LogVal("aNumEntries :", aNumEntries)
    LogVal("aMin :", aMin)
    LogVal("aMembers :", aMembers)
    
    aRankingHistory = db((db.user_ranking_history.member_id.belongs(aMembers)) & (db.user_ranking_history.match_id == aLastMatchId)).select(orderby = db.user_ranking_history.match_rank, limitby=(anOffset_in, aMin))
    LogVal("aRankingHistory :", aRankingHistory)
    
    LogVal("aMemberDict :", aMemberDict)
    aMemberData = []
    for aRankingHistory in aRankingHistory:
        aMemberItem = {"id" : aRankingHistory.id,
                        "match_rank" : aRankingHistory.match_rank,
                        "member_id" : aRankingHistory.predictor_id,
                        "member_name" : db.auth_user[aRankingHistory.predictor_id].first_name,
                        "membership_state" : aMemberDict[aRankingHistory.member_id]['membership_state'],
                        "last_score" : aRankingHistory.score
                    }
        aMemberData.append(aMemberItem)
    
    LogVal("aMemberData :", aMemberData)
    return aNumEntries > aMin , aMemberData
    
    
def GetLeagueRankHistory(aLeagueId_in):

    aLeague = db.league[aLeagueId_in]
    
    aMembers = map(lambda x:x.id, db(db.league_member.league_id == aLeague.id).select())
    LogVal("aMembers :", aMembers)
    
    aLastMatchId = GetLastMatchId()
    if aLastMatchId == -1:
        return []
    
    aMaxPossibleEntries = 2
    aUserRankingHistory = db((db.user_ranking_history.member_id.belongs(aMembers)) & (db.user_ranking_history.match_id == aLastMatchId)).select(orderby = db.user_ranking_history.match_rank, limitby=(0, aMaxPossibleEntries))
    LogVal("aUserRankingHistory :", aUserRankingHistory)
    
    aUsers = set(map(lambda x:x.predictor_id, aUserRankingHistory))
    
    #   Forcibly include the current user if he is part of the league
    if auth.user.id not in aUsers:
        aUserLeagueMembership = db((db.league_member.league_id == aLeague.id) & (db.league_member.member_id == auth.user.id)).select()
        if len(aUserLeagueMembership) > 0:
            if len(aUsers) == aMaxPossibleEntries:
                aUsers.pop()
            aUsers.add(auth.user.id)
        
    LogVal("aUsers :", aUsers)
       
    aMemberData = []
    for aUserId in aUsers:
        
        aAllUserHistory = db(db.user_ranking_history.predictor_id == aUserId).select(orderby = db.user_ranking_history.match_id)
        LogVal("aAllUserHistory :", aAllUserHistory)
        
        aRankHistory = map(lambda x:{  "match_id" : x.match_id, 
                                        "match_rank" : x.match_rank, 
                                     }, aAllUserHistory)
        
        aMember = aAllUserHistory[0]                         
        aMemberItem = {"id" : aMember.id,
                        "member_id" : aMember.predictor_id,
                        "member_name" : db.auth_user[aMember.predictor_id].first_name,
                        "rank_history" : aRankHistory,
                        }
            
        aMemberData.append(aMemberItem)
            
    aLeagueItem = {"league_id" : aLeague.id,
                    "league_name" : aLeague.name,
                    "league_desc" : aLeague.league_desc,
                    "league_state" : aLeague.league_state,
                    "all_members" : aMemberData
                    }       
     
    LogVal("aLeagueItem :", aLeagueItem)
    return aLeagueItem 
    
def GetAllLeagues():

    aUserLeagues = GetUserLeagues()
    allLeagues = db(db.league.league_state != "deleted").select()   
    
    aLeagueData = []
    for aLeague in allLeagues:
        if next((item for item in aUserLeagues if item["league_id"] == aLeague["id"]), None) == None:
            aNumMembers = len(db(db.league_member.league_id == aLeague.id).select())
            aLeagueItem = {"league_id" : aLeague.id,
                            "league_name" : aLeague.name,
                            "league_desc" : aLeague.league_desc,
                            "owner_id" : aLeague.owner_id,
                            "owner_name" : db.auth_user[aLeague.owner_id].first_name,
                            "num_members" : aNumMembers
                            }
            aLeagueData.append(aLeagueItem)

    
    return aLeagueData 

def JoinLeague(aLeagueId_in):
    
    aMessage = "A request is posted to the league admin..."
    
    aMembership = db((db.league_member.member_id == auth.user.id) & (db.league_member.league_id == aLeagueId_in)).select()
    if len(aMembership) == 0:
        db.league_member.insert(league_id = aLeagueId_in, member_id = auth.user.id, membership_state = 'pending')   
        aLeagueDetails = db(db.league.id == aLeagueId_in).select()[0]
        
        aNotification = ("Dear %s, I want to join your league %s. Please approve my membership. Regards, %s") % (db.auth_user[aLeagueDetails.owner_id]['first_name'], aLeagueDetails['name'], auth.user['first_name'])
        db.notification.insert(source_id = auth.user.id, target_id = aLeagueDetails.owner_id, date_time = datetime.datetime.now(),
                                subject = 'I want to join your league', notification_body = aNotification, read_state = 'unopened')
    else:
        aMessage = "You are already member of the league"
    return aMessage

def LeaveLeague(aLeagueMemberId_in):
    
    db(db.league_member.id == aLeagueMemberId_in).update(membership_state = "removed") 


def ModifyMembership(aMembershipId_in, aNewState_in, aBody_in):
    aMembershipDetails = db.league_member[aMembershipId_in]
    aMembershipDetails.update_record(membership_state = aNewState_in)
    
    db.notification.insert(source_id = auth.user.id, target_id = aMembershipDetails.member_id, date_time = datetime.datetime.now(),
                            subject = '[%s] : %s' % (db.league[aMembershipDetails.league_id].name, aNewState_in), notification_body = aBody_in, read_state = 'unopened')


def ModifyLeagueState(aLeagueId_in, aState_in):
    
    db(db.league.id == aLeagueId_in).update(league_state = aState_in)

def CreateLeague(aLeagueName_in, aLeagueDesc_in):
    existing = db(db.league.name == aLeagueName_in).select()
    aResultMessage = "Successfully created the league"
    if len(existing) == 0:
        aLeagueId = db.league.insert(owner_id = auth.user.id, name = aLeagueName_in, league_desc = aLeagueDesc_in, league_state = 'active')
        db.league_member.insert(league_id = aLeagueId, member_id = auth.user.id, membership_state = 'approved')
    else:
        aResultMessage = "The league with the same name already exists"
    return aResultMessage
    
def AddUserToLeague(aLeagueId_in, aUserIds_in):

    aUserIds = []
    if not isinstance(aUserIds_in, list):
        aUserIds.append(aUserIds_in)
    else:
        aUserIds.extend(aUserIds_in)
    
    aMessage = "All users are added to the league"
    for aUserIdStr in aUserIds:
        
        matchObj = re.search('AdminLeageUserDivId_(\d*)_(\d*)', aUserIdStr)
        aUserId = matchObj.group(2)
        
        
        aMembership = db((db.league_member.member_id == aUserId) & (db.league_member.league_id == aLeagueId_in)).select()
        
        if len(aMembership) == 0:
            db.league_member.insert(league_id = aLeagueId_in, member_id = aUserId, membership_state = 'approved')
            db.notification.insert(source_id = auth.user.id, target_id = aUserId, date_time = datetime.datetime.now(),
                            subject = '[%s] : added to league' % db.league[aLeagueId_in].name, notification_body = "Happy to inform that you have been added to the league", read_state = 'unopened')
        else:
            aMessage = "Some users are already in the league and they are not added again"
            
    return aMessage
    
def GetUsersStartingWith(aFirstPart_in):
    
    anAllUsers = db().select(db.auth_user.ALL)
    selected = [{'id': m['id'], 'name' : str(m['first_name']) + ' ' + str(m['last_name']) + ' (' + str(m['nickname']) + ')'} 
                for m in anAllUsers 
                    if (bool(re.match(aFirstPart_in, m['first_name'] or '', re.I)) or 
                        bool(re.match(aFirstPart_in, m['last_name'] or '', re.I)) or
                        bool(re.match(aFirstPart_in, m['nickname'] or '', re.I))) and m['id'] != auth.user.id]
    
    return selected


def GetUserDetails(aUserId_in):
    
    aUserDetailsRec = db.auth_user[aUserId_in]
    aUserDetails = {"id" : aUserDetailsRec.id,
                    "last_name" : aUserDetailsRec.last_name,
                    "first_name" : aUserDetailsRec.first_name,
                    "last_score" : aUserDetailsRec.last_score,
                    "last_rank" : aUserDetailsRec.last_rank,
                    "image" : aUserDetailsRec.image,
                    }
    return aUserDetails

def CreateUserPreferences():
    
    aPrefSet = db(db.user_preference.user_id == auth.user.id).select()
    if len(aPrefSet) == 0:
        db.user_preference.insert(user_id = auth.user.id, pref_item = "Share prior prediction with public", pref_type = 'bool', pref_value = 'No')  
        db.user_preference.insert(user_id = auth.user.id, pref_item = "Share spot prediction with public", pref_type = 'bool', pref_value = 'No')
        db.user_preference.insert(user_id = auth.user.id, pref_item = "Share old bet details with public", pref_type = 'bool', pref_value = 'No') 
 
def CreateGlobalLeagueAndAddMember():
    
    aGlobalLeague = db(db.league.name == "GlobalLeague").select()
    
    aLeagueId = 0
    
    if len(aGlobalLeague) == 0:
        aLeagueId = db.league.insert(name = "GlobalLeague", league_desc = "Global League", league_state = 'active')
    else:
        aLeagueId = aGlobalLeague[0].id
        
    aLeagueMember = db(( db.league_member.league_id == aLeagueId ) & (db.league_member.member_id == auth.user.id)).select()
    if len(aLeagueMember) == 0:
        db.league_member.insert(league_id = aLeagueId, member_id = auth.user.id, membership_state = 'approved')
    

def SavePreferences(aSettings):
    for aKey, aVal in aSettings.iteritems():
        db(db.user_preference.id == aKey).update(pref_value = aVal)
    
def IsAllowed(aPref_in, aUserId_in):

    if aUserId_in == str(auth.user.id):
        return 'Yes'
        
    aPref = db((db.user_preference.user_id == aUserId_in) & (db.user_preference.pref_item == aPref_in)).select()
    if len(aPref) == 0:
        return 'No'
        
    return aPref[0]['pref_value']

def DeleteDummyUserData():

    aDummyUsers = db(db.auth_user.last_name == "Test").select()
    for aUser in aDummyUsers:
        db(db.league_member.member_id == aUser).delete()
    
    db(db.auth_user.last_name == "Test").delete()
    
def SimulateUserData():

    aGlobalLeagueId = db(db.league.name == "GlobalLeague").select().first().id
    
    aFirst = 0
    aDummyUsers = sorted(db(db.auth_user.last_name == "Test").select(), key=lambda k: int(re.search('User_(\d*)', k.first_name).group(1)))
    if len(aDummyUsers) > 0 :
        LogVal("aDummyUser : ", aDummyUsers[len(aDummyUsers) - 1])
        aRegObj = re.search('User_(\d*)', aDummyUsers[len(aDummyUsers) - 1].first_name)
        aFirst = int(aRegObj.group(1)) + 1
        
    
    for number in range(aFirst,aFirst + 100):
        aUserId = db.auth_user.insert(first_name = "User_" + str(number), last_name = "Test", email = "User_" + str(number) + "@yahoo.com")
        db.league_member.insert(league_id = aGlobalLeagueId, member_id = aUserId, membership_state = 'approved')
        time.sleep( 1 ) 
    