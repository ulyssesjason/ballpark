import csv
import random
from model import *


def calculateAverage():
    data = {}
    with open('mlb_pitcher_pivot.csv', 'rb') as f:
        dictReader = csv.DictReader(f)
        for row in dictReader:
            data = row
    global league_average_whip
    global league_average_era
    league_average_whip = (float(data['BB']) + float(data['H'])) / float(data['IP'])
    league_average_era = (float(data['ER']) / float(data['IP']))


def initializeState(state):
    current_inning = Inning()
    state.current_inning = current_inning
    state.offense = state.visit_team
    state.defense = state.home_team
    state.pitcher = state.home_team.findStartPitcher()
    state.at_bat = state.visit_team.hitter_line_up[1]
    state.visit_team.hitter_at_bat = state.at_bat


def handleRun(state, hit):
    if (state.isPlayerOnBase or hit == 4):
        state.calculateRuns(hit, game, state.at_bat)
    else:
        if (hit == 1):
            state.base1 = state.at_bat
        elif (hit == 2):
            state.base2 = state.at_bat
        else:
            state.base3 = state.at_bat

def deckPlayerAtBat(state):
    if (state.current_inning.status == 'top'):
        state.visit_team.hitter_at_bat = state.at_bat
        state.at_bat = state.visit_team.findHitterAtDeck()
    else:
        state.home_team.hitter_at_bat = state.at_bat
        state.at_bat = state.home_team.findHitterAtDeck()

def countHit(state):
    if (state.current_inning.status == 'top'):
        state.current_inning.visit_team_hits += 1
    else:
        state.current_inning.home_team_hits += 1

def pickPitcher(state, team):
    if(state.current_inning.inning_number <= 7):
        state.pitcher = team.start_pitcher
    elif(state.current_inning.inning_number == 8):
        state.pitcher = team.setup_pitcher
    else:
        state.pitcher = team.closer

def handleHit(state):
    countHit(state)
    hit_report = ("At Inning " + str(
        state.current_inning.inning_number) + " " + state.current_inning.status + " Hitter " + state.at_bat.name + " facing " + state.pitcher.name + " hit a ")
    b2 = (state.at_bat.double / state.at_bat.avg) * state.pitcher.era_minus
    b3 = (state.at_bat.triple / state.at_bat.avg) * state.pitcher.era_minus
    hr = (state.at_bat.hr / state.at_bat.avg) * state.pitcher.era_minus
    run_dice = random.random()
    if (run_dice <= hr):
        hit_report += "Home run"
        hit = 4
    elif (run_dice <= hr + b3):
        hit_report += "triple hit"
        hit = 3
    elif (run_dice <= hr + b3 + b2):
        hit_report += "double hit"
        hit = 2
    else:
        hit_report += "single hit"
        hit = 1
    game.logReport(hit_report)
    handleRun(state, hit)
    # deckPlayerAtBat(state)

def handleBB(state):
    bb_report = ("At Inning " + str(
        state.current_inning.inning_number) + " " + state.current_inning.status + " Hitter " + state.at_bat.name + " is sent by " + state.pitcher.name + " to 1B ")
    game.logReport(bb_report)
    if(state.isBaseLoaded()):
        handleRun(state,1)
    else:
        if(state.base1 is None):
            state.base1 = state.at_bat
        elif(state.base2 is None):
            state.base2 = state.base1
            state.base1 = state.at_bat
        elif(state.base3 is None):
            state.base3 = state.base2
            state.base2 = state.base1
            state.base1 = state.at_bat
    # deckPlayerAtBat(state)

def simulateInning(state):
    hitter = state.at_bat
    pitcher = state.pitcher
    hit_dice = random.random()
    avg = hitter.avg * pitcher.whip_plus
    bb = (hitter.obp - hitter.avg) * pitcher.whip_plus
    if (hit_dice <= avg):
        handleHit(state)
    elif hit_dice < bb + avg:
        handleBB(state)
    else:
        game.logReport("At Inning " + str(
            state.current_inning.inning_number) + " " + state.current_inning.status + " Pitcher " + pitcher.name + " have " + hitter.name + " " + str(hitter.lineout_number) + " out")
        state.current_inning.out_count += 1
    deckPlayerAtBat(state)


def cleanupBases(state):
    state.base1 = None
    state.base2 = None
    state.base3 = None

def playInning(state):
    if state.current_inning.out_count < 3:
        simulateInning(state)
    else:
        cleanupBases(state)
        state.current_inning.status = 'bottom'
        state.current_inning.out_count = 0
        pickPitcher(state, state.visit_team)
        if (state.current_inning.inning_number == 1):
            state.home_team.hitter_at_bat = state.home_team.hitter_line_up[1]
            state.at_bat = state.home_team.hitter_line_up[1]
        else:
            state.at_bat = state.home_team.findHitterAtDeck()
            state.home_team.hitter_at_bat = state.at_bat


def startNewInning(state):
    cleanupBases(state)
    new_inning = Inning()
    new_inning.out_count = 0
    new_inning.status = 'top'
    new_inning.inning_number = state.current_inning.inning_number + 1
    box.innings.append(state.current_inning)
    state.current_inning = new_inning
    state.at_bat = state.visit_team.findHitterAtDeck()
    state.visit_team.hitter_at_bat = state.at_bat
    pickPitcher(state, state.home_team)

    game.logReport("Inning " + str(state.current_inning.inning_number) + " start")


def playGame(state):
    if (state.current_inning.isComplete() == False):
        playInning(state)
    else:
        startNewInning(state)


def handleGame(state):
    initializeState(state)
    game.logReport("Inning 1 start")
    while (state.isGameComplete() is False):
        playGame(state)
    box.innings.append(state.current_inning)  # final inning

def simulateGame(counts, state, home_team, visit_team):
    prediction = Prediction()
    h = 0
    v = 0
    h_run = 0
    for i in range(1,counts,1):
        handleGame(state)
        h_run += (state.home_team_run - state.visit_team_run)
        if(state.home_team_run > state.visit_team_run):
            h += 1
        else:
            v += 1
        state = FieldState()
        state.home_team = home_team
        state.visit_team = visit_team
    prediction.home_team_win_percentage = float(h)/counts
    prediction.visit_team_win_percentage = float(v)/counts
    prediction.run_difference = float(h_run)/counts
    return prediction

def main():
    global game
    global box
    game = Game()
    box = Box()
    game.logReport("Game Report: ")
    game.box = box
    calculateAverage()

    home_team = Lineup()
    home_team.name = 'WSH'
    home_team.handleteamLineup('home_hitter.csv', 'home_pitcher.csv', 'home_lineup.csv', league_average_whip)

    visit_team = Lineup()
    visit_team.name = 'CHC'
    visit_team.handleteamLineup('visit_hitter.csv', 'visit_pitcher.csv', 'visit_lineup.csv', league_average_whip)

    game.home_lineup = home_team
    game.visit_lineup = visit_team
    box.home_team_name = "WSH"
    box.visit_team_name = "CHC"
    state = FieldState()
    state.home_team = home_team
    state.visit_team = visit_team
    game.report_enabled = False
    counts = 100000
    simulateGame(counts,state,home_team, visit_team).printOut()

    # handleGame(state)
    # box.printOut()
    # game.logReport("Game End.")
    # game.printReport()

if __name__ == "__main__":
    main()
