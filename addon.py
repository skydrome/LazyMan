import calendar
import configparser
import os
import socket
import sys
import time
from urllib.request import urlopen
from urllib.parse import parse_qsl

import xbmcaddon
import xbmcgui
import xbmcplugin
from resources.lib import utils
from resources.lib.utils import log
from resources.lib.game import GameBuilder
from resources.lib.highlights import get_highlights

addonUrl = sys.argv[0]
addonHandle = int(sys.argv[1])
addonId = "plugin.video.lazyman.nhl.tv"
addon = xbmcaddon.Addon(id=addonId)
addonPath = addon.getAddonInfo('path')
addonName = addon.getAddonInfo('name')
sanityChecked = False
iniFilePath = os.path.join(addonPath, 'resources', 'lazyman.ini')
config = configparser.ConfigParser()
config.read(iniFilePath)

def games(date, provider):
    remaining = GameBuilder.nhlTvRemaining if provider == "NHL.tv" else GameBuilder.mlbTvRemaining
    return GameBuilder.fromDate(config, date, remaining, provider)

def listgrouphighlights(provider, group):
    items = []
    for hg in [x for x in get_highlights(config, provider) if x.title == group]:
        for h in hg.highlights:
            label = "{0} ({1})".format(h.blurb, h.duration)
            listItem = xbmcgui.ListItem(label=label)
            listItem.setInfo(type="video", infoLabels={"title": label, "mediatype": 'video'})
            url = '{0}?action=playhighlight&url={1}'.format(addonUrl, h.playbackUrl)
            items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def listhighlights(provider):
    items = []
    for hg in get_highlights(config, provider):
        listItem = xbmcgui.ListItem(label=hg.title)
        listItem.setInfo(type="video", infoLabels={"title": hg.title, "mediatype": 'video'})
        url = '{0}?action=listgrouphighlights&group={1}&provider={2}'.format(addonUrl, hg.title, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def listyears(provider):
    items = []
    for y in utils.years(provider):
        listItem = xbmcgui.ListItem(label=str(y))
        listItem.setInfo(type="video", infoLabels={"title": y, "mediatype": 'video'})
        url = '{0}?action=listmonths&year={1}&provider={2}'.format(addonUrl, y, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def highlights(provider):
    items = []

def listmonths(year, provider):
    items = []
    for (mn, m) in utils.months(year):
        listItem = xbmcgui.ListItem(label=mn)
        listItem.setInfo(type="video", infoLabels={"title": mn, "mediatype": 'video'})
        url = '{0}?action=listdays&year={1}&month={2}&provider={3}'.format(addonUrl, year, m, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def listdays(year, month, provider):
    items = []
    for d in utils.days(year, month):
        listItem = xbmcgui.ListItem(label=str(d))
        listItem.setInfo(type="video", infoLabels={"title": d, "mediatype": 'video'})
        url = '{0}?action=listgames&year={1}&month={2}&day={3}&provider={4}'.format(addonUrl, year, month, d, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def listproviders():
    items = []
    providers = config.get("LazyMan", "Providers").split(",")
    for provider in providers:
        listItem = xbmcgui.ListItem(label=provider)
        listItem.setInfo(type="video", infoLabels={"title": provider, "mediatype": 'video'})
        url = '{0}?action=listtodaysgames&provider={1}'.format(addonUrl, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def listgames(date, provider, previous=False, highlights=False):
    items = []
    dategames = games(date, provider)
    for g in dategames:
        label = "%s vs. %s [%s]" % (g.awayFull, g.homeFull, g.remaining if g.remaining != "N/A" else utils.asCurrentTz(date, g.time))
        listItem = xbmcgui.ListItem(label=label)
        listItem.setInfo(type="video", infoLabels={"title": label, "mediatype": 'video'})
        url = '{0}?action=feeds&game={1}&date={2}&provider={3}'.format(addonUrl, g.id, date, provider)
        items.append((url, listItem, True))

    if len(items) == 0:
        xbmcgui.Dialog().ok(addonName, "No games scheduled today")

    if highlights:
        listItem = xbmcgui.ListItem(label="Highlights")
        listItem.setInfo(type="video", infoLabels={"title": "Highlights", "mediatype": 'video'})
        url = '{0}?action=listhighlights&provider={1}'.format(addonUrl, provider)
        items.append((url, listItem, True))

    if previous:
        listItem = xbmcgui.ListItem(label="Previous")
        listItem.setInfo(type="video", infoLabels={"title": "Previous", "mediatype": 'video'})
        url = '{0}?action=listyears&provider={1}'.format(addonUrl, provider)
        items.append((url, listItem, True))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)
    #log("Added %d games" % len(items))

def listfeeds(game, date, provider):
    items = []
    for f in [f for f in game.feeds if f.viewable()]:
        label = str(f)
        listItem = xbmcgui.ListItem(label=label)
        listItem.setInfo(type="video", infoLabels={"title": label, "mediatype": 'video'})
        url = '{0}?action=play&date={1}&feedId={2}&provider={3}&state={4}'.format(addonUrl, date, f.mediaId, provider, game.gameState)
        items.append((url, listItem, False))

    ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items))
    xbmcplugin.endOfDirectory(addonHandle)

def playhighlight(url):
    #log("Trying to play URL: %s" % url)
    mediaAuth = utils.salt()
    if utils.head(url, dict(mediaAuth=mediaAuth)):
        completeUrl = "%s|Cookie=mediaAuth%%3D%%22%s%%22" % (url, mediaAuth)
        xbmc.Player().play(completeUrl)

def playgame(date, feedId, provider, state):
    def adjustQuality(masterUrl):
        qualityUrlDict = {
            "540p":   "2500K/2500_{0}.m3u8",
            "720p":   "3500K/3500_{0}.m3u8",
            "720p60": "5600K/5600_{0}.m3u8"
        }
        current = addon.getSetting("quality")
        if current == 'master':
            return masterUrl
        else:
            m3u8Path = qualityUrlDict.get(current, "3500K/3500_{0}.m3u8").format(
                'slide' if state in ('In Progress', 'Scheduled', 'Pre-Game')
                else 'complete-trimmed')
            #log("Quality selected: %s, adjusting to %s" % (current, m3u8Path))
            return masterUrl.rsplit('/', 1)[0] + "/" + m3u8Path

    def xbmcPlayer(url, mediaAuth):
        #log("Trying to play URL: %s" % url)
        completeUrl = "%s|Cookie=mediaAuth%%3D%%22%s%%22" % (url, mediaAuth)
        xbmc.Player().play(adjustQuality("%s|Cookie=mediaAuth%%3D%%22%s%%22" % (url, mediaAuth)))

    def getContentUrl():
        if provider == "NHL.tv":
            return "http://freegamez.ga/m3u8/%s/%s%s" % (date, feedId, cdn)
        else:
            return "http://freegamez.ga/mlb/m3u8/%s/%s%s" % (date, feedId, cdn)

    cdn = 'akc' if addon.getSetting("cdn") == "Akamai" else 'l3c'
    contentUrl = getContentUrl()

    #log("Trying to resolve from content-url: %s" % contentUrl)
    if not utils.head(contentUrl):
        log("Invalid content-url: %s" % contentUrl)
        xbmcgui.Dialog().ok(addonName, "Game not available yet")
        return

    response = urlopen(contentUrl)
    playUrl = response.read().decode('utf-8').replace('l3c', cdn)
    #log("Play URL resolved to: %s" % playUrl)
    mediaAuthSalt = utils.salt()

    if utils.get(playUrl, dict(mediaAuth=mediaAuthSalt)):
        xbmcPlayer(playUrl, mediaAuthSalt)
    else:
        otherCdn = 'akc' if cdn == 'l3c' else 'l3c'
        log("URL [%s] failed on GET, switching CDN from %s to %s" % (playUrl, cdn, otherCdn))
        xbmcPlayer(playUrl.replace(cdn, otherCdn), mediaAuthSalt)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'feeds':
            dategames = games(params['date'], params['provider'])
            gameDict = dict([(g.id, g) for g in dategames])
            listfeeds(gameDict[int(params['game'])], params['date'], params['provider'])
        elif params['action'] == 'play':
            playgame(params['date'], params['feedId'], params['provider'], params['state'])
        elif params['action'] == 'listyears':
            listyears(params['provider'])
        elif params['action'] == 'listhighlights':
            listhighlights(params['provider'])
        elif params['action'] == 'listgrouphighlights':
            listgrouphighlights(params['provider'], params['group'])
        elif params['action'] == 'playhighlight':
            playhighlight(params['url'])
        elif params['action'] == 'listmonths':
            listmonths(params['year'], params['provider'])
        elif params['action'] == 'listdays':
            listdays(params['year'], params['month'], params['provider'])
        elif params['action'] == 'listgames':
            listgames("%d-%02d-%02d" % (int(params['year']), int(params['month']), int(params['day'])), params['provider'])
        elif params['action'] == 'listtodaysgames':
            listgames(utils.today().strftime("%Y-%m-%d"), params['provider'], True, True)
    else:
        listproviders()

def sanityCheck():
    since = addon.getSetting("sanityChecked")
    if since == "" or calendar.timegm(time.gmtime()) - (3600*24) > int(since):
        providers = config.get("LazyMan", "Providers").split(",")
        icon = os.path.join(addonPath, 'resources', 'icon.png')
        for service in providers:
            xbmc.executebuiltin("Notification(LazyMan,Verifying %s,,%s)" % (service, icon))
            hostNames = config.get(service, "Host").split(",")
            lazymanServer = socket.gethostbyname('freegamez.ga')
            for h in hostNames:
                resolved = socket.gethostbyname(h)
                if resolved != lazymanServer:
                    xbmcgui.Dialog().ok(addonName, "%s doesn't resolve to the Lazyman server." % h, "Update your hosts file to point to %s" % lazymanServer)
                else:
                    addon.setSetting("sanityChecked", str(calendar.timegm(time.gmtime())))

if __name__ == '__main__':
    sanityCheck()
    router(sys.argv[2][1:])
