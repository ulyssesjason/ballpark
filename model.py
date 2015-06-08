import copy
import csv


class Inning(object):
    home_team_run = 0
    visit_team_run = 0
    home_team_hits = 0
    visit_team_hits = 0
    home_team_error = 0
    visit_team_error = 0
    inning_number = 1
    out_count = 0
    status = 'top'

    def isComplete(self):
        return (self.out_count == 3 and self.status == 'bottom')

    def isTopInningComplete(self):
        return self.status == "top" and self.out_count == 3


class Box(object):
    home_team_name = ''
    visit_team_name = ''
    innings = []

    def printOut(self):
        print "box"
        home = self.home_team_name + "\t| "
        visit = self.visit_team_name + "\t| "
        home_hit = 0
        visit_hit = 0
        home_error = 0
        visit_error = 0
        home_runs = 0
        visit_runs = 0
        for i in self.innings:
            home = home + str(i.home_team_run) + " | "
            visit = visit + str(i.visit_team_run) + " | "
            home_hit = i.home_team_hits + home_hit
            visit_hit = i.visit_team_hits + visit_hit
            home_error = i.home_team_error + home_error
            visit_error = i.visit_team_error + visit_error
            home_runs = i.home_team_run + home_runs
            visit_runs = i.visit_team_run + visit_runs
        home = home + 'runs: ' + str(home_runs) + " | " + 'hits: ' + str(home_hit) + " | " + 'errors: ' + str(
            home_error) + " | "
        visit = visit + 'runs: ' + str(visit_runs) + " | " + 'hits: ' + str(visit_hit) + " | " + 'errors: ' + str(
            visit_error) + " | "
        print home
        print visit


class Player(object):
    team = ''
    name = ''
    position = ''

    def notExist(self):
        return len(self.name) == 0


class Hitter(Player):
    lineout_number = None
    avg = 0.3
    obp = 0.4
    single = 0.1
    double = 0.2
    triple = 0.3
    hr = 0

    atBatting = 0
    hits = 0
    runs = 0
    steal_base = 0
    hr_counts = 0
    rbi = 0

class Pitcher(Player):
    era_minus = 100
    whip_plus = 1

    pitch_counts = 0
    strike = 0
    er = 0
    hit_by = 0
    inning_count = 0

class Lineup(object):
    start_pitcher = Pitcher()
    setup_pitcher = Pitcher()
    closer = Pitcher()
    hitters = []
    pitchers = []
    hitter_line_up = {}
    pitcher_line_up = []
    hitter_at_bat = Hitter()
    name = ''
    bullpen = []
    pitcher_on_mound = Pitcher()

    def handleHitter(self, row):
        hitter = Hitter()
        hitter.name = row['Name']
        hitter.avg = float(row['AVG'])
        if(int(row['AB']) != 0):
            hitter.obp = (float(row['HBP']) + float(row['IBB']) + float(row['BB']) + float(row['H'])) / float(row['AB'])
            hitter.single = float(row['1B']) / float(row['AB'])
            hitter.double = float(row['2B']) / float(row['AB'])
            hitter.triple = float(row['3B']) / float(row['AB'])
            hitter.hr = float(row['HR']) / float(row['AB'])


        return hitter

    def handlePitcher(self, row, averageWhip):
        pitcher = Pitcher()
        pitcher.name = row['Name']
        pitcher.era_minus = float(row['ERA-']) / 100
        pitcher.whip_plus = float(row['WHIP']) / averageWhip
        return pitcher

    def handleHitterLine(self, line):
        lineup = {}
        j = 1
        for i in line:
            h = self.findHitterByName(i)
            h.lineout_number = j
            lineup[j] = h
            j += 1
        self.hitter_line_up = lineup

    def handlePitcherLine(self, line):
        self.start_pitcher = self.findPitcherByName(line[0])
        self.setup_pitcher = self.findPitcherByName(line[1])
        self.closer = self.findPitcherByName(line[2])

    def handleteamLineup(self, hitterFileName, pitcherFileName, lineupFileName, averageWhip):
        with open(hitterFileName, 'rb') as f:
            temp = []
            dictReader = csv.DictReader(f)
            for row in dictReader:
                h = self.handleHitter(row)
                if (h is not None):
                    temp.append(h)
            self.hitters = temp
        with open(pitcherFileName, 'rb') as f:
            temp = []
            dictReader = csv.DictReader(f)
            for row in dictReader:
                p = self.handlePitcher(row, averageWhip)
                if (p is not None):
                    temp.append(p)
            self.pitchers = temp
        with open(lineupFileName, 'rb') as f:
            reader = csv.reader(f)
            line = list(reader)
            if (line is not None):
                self.handleHitterLine(line[0])
                self.handlePitcherLine(line[1])
                # self.handleBullpen(line[2])

    def findHitterByName(self, name):
        if (len(self.hitters) > 0 and name is not None):
            for h in self.hitters:
                if (h.name == name):
                    return h

    def findPitcherByName(self, name):
        if (len(self.pitchers) > 0 and name is not None):
            for p in self.pitchers:
                if (p.name == name):
                    return p

    def findStartPitcher(self):
        return self.start_pitcher

    def findHitterAtBat(self):
        return self.hitter_at_bat

    def findHitterAtDeck(self):
        if (self.hitter_at_bat.lineout_number != 9):
            return self.hitter_line_up[self.hitter_at_bat.lineout_number + 1]
        else:
            return self.hitter_line_up[1]


class FieldState(object):
    home_team = Lineup()
    visit_team = Lineup()
    offense = Lineup()
    defense = Lineup()
    pitcher = Pitcher()
    at_bat = Hitter()
    base1 = None
    base2 = None
    base3 = None
    current_inning = Inning()
    home_team_run = 0
    visit_team_run = 0

    def isBaseLoaded(self):
        return self.base1 is not None and self.base2 is not None and self.base3 is not None

    def isGameComplete(self):
        if (self.current_inning.inning_number >= 9 and (self.current_inning.isComplete() or (
            self.current_inning.isTopInningComplete() and self.home_team_run > self.visit_team_run)) and self.home_team_run != self.visit_team_run):
            return True
        else:
            return False

    def reverseOffDef(self):
        temp = copy.deepcopy(self.offense)
        self.offense = copy.deepcopy(self.defense)
        self.defense = temp

    @property
    def isPlayerOnBase(self):
        return self.base1 is not None or self.base2 is not None or self.base3 is not None

    def score(self):
        if (self.current_inning.status == 'top'):
            self.current_inning.visit_team_run += 1
            self.visit_team_run += 1
        else:
            self.current_inning.home_team_run += 1
            self.home_team_run += 1

    def base3Score(self, game):
        if (self.base3 is not None):
            game.logReport("3B " + self.base3.name + " run back home")
            self.base3 = None
            self.score()

    def base2Score(self, game):
        if (self.base2 is not None):
            game.logReport("2B " + self.base2.name + " run back home")
            self.base2 = None
            self.score()

    def base1Score(self, game):
        if (self.base1 is not None):
            game.logReport("1B " + self.base1.name + " run back home")
            self.base1 = None
            self.score()

    def calculateRuns(self, hits, game, hitter):
        if (hits == 1):
            self.base3Score(game)
            self.base3 = self.base2
            self.base2 = None
            self.base2 = self.base1
            self.base1 = hitter
        elif (hits == 2):
            self.base3Score(game)
            self.base2Score(game)
            self.base3 = self.base1
            self.base1 = None
            self.base2 = hitter
        elif (hits == 3 or hits == 4):
            self.base3Score(game)
            self.base2Score(game)
            self.base1Score(game)
            if (hits == 4):
                self.score()
            else:
                self.base3 = hitter


class Game(object):
    box = Box()
    home_lineup = Lineup()
    visit_lineup = Lineup()
    report = []
    report_enabled = True

    def logReport(self, text):
        if(self.report_enabled == True):
            self.report.append(text)

    def printReport(self):
        for r in self.report:
            print r


class Prediction(object):
    home_team_win_percentage = 0.5
    visit_team_win_percentage = 0.5
    run_difference = 0

    def printOut(self):
        print "home team winning percentage: " + str(self.home_team_win_percentage)
        print "visit team winning percentage: " + str(self.visit_team_win_percentage)
        print "run difference, home to visit: " + str(self.run_difference)