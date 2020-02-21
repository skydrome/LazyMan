import requests
from .utils import log


class FeedBuilder:

    @staticmethod
    def fromContent(content, streamProvider):

        def idProvider(item):
            return item[mediaIdx]

        def fromItem(item):
            mediaFeedType = item["mediaFeedType"].upper()
            if mediaFeedType == "HOME":
                return Home(item["callLetters"], idProvider(item))
            if mediaFeedType == "NATIONAL":
                return National(item["callLetters"], idProvider(item))
            if mediaFeedType == "AWAY":
                return Away(item["callLetters"], idProvider(item))
            if mediaFeedType == "FRENCH":
                return French(item["callLetters"], idProvider(item))
            if mediaFeedType == "COMPOSITE":
                return Composite(item["callLetters"], idProvider(item))
            if mediaFeedType == "ISO":
                return Other(item["feedName"], item["callLetters"], idProvider(item))
            return NonViewable(item["callLetters"], idProvider(item))

        if "media" in content:
            mediaIdx = "id" if streamProvider == "MLBTV" else "mediaPlaybackId"
            try:
                return [fromItem(item)
                        for stream in content["media"]["epg"] if stream["title"] == streamProvider
                        for item in stream["items"]]
            except KeyError:
                pass

        return []

class Feed:
    _tvStation = None
    _mediaId = None

    def __init__(self, tvStation, mediaId):
        self._tvStation = tvStation
        self._mediaId = mediaId
    def viewable(self):
        return True
    @property
    def tvStation(self):
        return self._tvStation
    @property
    def mediaId(self):
        return self._mediaId

class NonViewable(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self):
        return "NonViewable"
    def viewable(self):
        return False

class Home(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self): return "%s (Home)" % (self.tvStation)

class Away(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self): return "%s (Away)" % (self.tvStation)

class National(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self): return "%s (National)" % (self.tvStation)

class French(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self): return "%s (French)" % (self.tvStation)

class Composite(Feed):
    def __init__(self, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
    def __repr__(self): return "3-Way Camera"

class Other(Feed):
    _feedName = None
    def __init__(self, feedName, tvStation, mediaId):
        Feed.__init__(self, tvStation, mediaId)
        self._feedName = feedName
    def __repr__(self): return self._feedName

class Game:
    _home = None
    _homeFull = None
    _away = None
    _awayFull = None
    _gameState = None
    _time = None
    _id = None
    _remaining = None
    _feeds = []

    def __init__(self, gid, away, home, time, gameState, awayFull, homeFull, remaining, feeds=[]):
        self._id = gid
        self._away = away
        self._home = home
        self._time = time
        self._gameState = gameState
        self._awayFull = awayFull
        self._homeFull = homeFull
        self._remaining = remaining
        if feeds is None:
            self._feeds = []
        else:
            self._feeds = feeds
    @property
    def id(self):
        return self._id
    @property
    def away(self):
        return self._away
    @property
    def home(self):
        return self._home
    @property
    def time(self):
        return self._time
    @property
    def gameState(self):
        return self._gameState
    @property
    def awayFull(self):
        return self._awayFull
    @property
    def homeFull(self):
        return self._homeFull
    @property
    def remaining(self):
        return self._remaining
    @property
    def feeds(self):
        return self._feeds

    def __repr__(self):
        return "Game(%s vs. %s, %s, feeds: %s)" % (self.away, self.home, self.remaining, ", ".join([f.tvStation for f in self.feeds]))

class GameBuilder:

    @staticmethod
    def mlbTvRemaining(state, game):
        if "In Progress" in state:
            return game["linescore"]["currentInningOrdinal"] + " " + game["linescore"]["inningHalf"]
        if state == "Final":
            return "Final"
        if state == "Postponed":
            return "PPD"
        return "N/A"

    @staticmethod
    def nhlTvRemaining(state, game):
        if "In Progress" in state:
            return game["linescore"]["currentPeriodOrdinal"] + " " + game["linescore"]["currentPeriodTimeRemaining"]
        if state == "Pre-Game":
            return "Pre Game"
        if state == "Final":
            return "Final"
        return "N/A"

    @staticmethod
    def fromDate(config, date, remaining, provider):
        u = config.get(provider, "GameScheduleUrl", raw=True) % (date, date)
        response = requests.get(u)
        data = response.json()
        #log("Server Response: %s" % data)

        if data["totalItems"] <= 0 or len(data["dates"]) == 0:
            return []
        games = data["dates"][0]["games"]

        def asGame(g):
            away = g["teams"]["away"]["team"]
            home = g["teams"]["home"]["team"]
            time = g["gameDate"][11:].replace("Z", "")
            state = g["status"]["detailedState"]
            return Game(g["gamePk"], away["abbreviation"], home["abbreviation"],
                        time, state, away["name"], home["name"], remaining(state, g),
                        FeedBuilder.fromContent(g["content"], config.get(provider, "Provider")))
        return list(map(asGame, games))
