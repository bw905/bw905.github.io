# -*- coding: utf-8 -*-
"""
    Umbrella Helper - Quick Real-Debrid & Trakt Auth Shortcut for Umbrella
    Created for bw905
"""

import sys
import os
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

from cm_helper import run_collection, run_rescrape

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].lstrip('-').isdigit() else -1
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ART_DIR = os.path.join(ADDON_PATH, 'resources', 'art')

def get_umbrella():
    try:
        return xbmcaddon.Addon('plugin.video.umbrella')
    except Exception:
        return None

def build_menu():
    umbrella = get_umbrella()
    if not umbrella:
        item = xbmcgui.ListItem(label="[COLOR red][B]Umbrella Addon Not Found[/B][/COLOR]")
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='', listitem=item, isFolder=False)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    # Check Real-Debrid Status in Umbrella
    rd_token = umbrella.getSetting('realdebridtoken')
    rd_user = umbrella.getSetting('realdebridusername')
    if rd_token and rd_token.strip():
        if rd_user and rd_user.strip():
            rd_status = f"[COLOR lime][B]Authorized ({rd_user})[/B][/COLOR]"
        else:
            rd_status = "[COLOR lime][B]Authorized[/B][/COLOR]"
    else:
        rd_status = "[COLOR red][B]Not Authorized[/B][/COLOR]"

    # Check Trakt Status in Umbrella
    trakt_authed = umbrella.getSetting('trakt.isauthed') == 'true'
    trakt_user = umbrella.getSetting('trakt.user.name')
    if trakt_authed and trakt_user and trakt_user.strip():
        trakt_status = f"[COLOR lime][B]Authorized ({trakt_user})[/B][/COLOR]"
    elif trakt_authed:
        trakt_status = "[COLOR lime][B]Authorized[/B][/COLOR]"
    else:
        trakt_status = "[COLOR red][B]Not Authorized[/B][/COLOR]"

    FANART = ADDON.getAddonInfo('fanart')

    def add_item(title, action, art_file, plot=''):
        url = f"{sys.argv[0]}?action={action}"
        li = xbmcgui.ListItem(label=title)
        thumb_path = os.path.join(ART_DIR, art_file)
        if not os.path.exists(thumb_path):
            thumb_path = ADDON.getAddonInfo('icon')
        li.setArt({
            'icon': thumb_path,
            'thumb': thumb_path,
            'fanart': FANART,
            'poster': thumb_path,
            'landscape': thumb_path
        })
        info_tag = li.getVideoInfoTag()
        info_tag.setTitle(title)
        info_tag.setPlot(plot)
        li.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=False)

    # --- REAL-DEBRID SECTION ---
    add_item(
        f"Real-Debrid: {rd_status}",
        'rd_info',
        'rd_info.png',
        f"Real-Debrid Account: {rd_status} (Click to check account info and days remaining)"
    )
    add_item(
        "Authorize Real-Debrid",
        'rd_auth',
        'rd_auth.png',
        "Pair and authorize your Real-Debrid account with Umbrella"
    )
    add_item(
        "Revoke Real-Debrid",
        'rd_revoke',
        'rd_revoke.png',
        "Disconnect and revoke Real-Debrid credentials from Umbrella"
    )

    # --- TRAKT SECTION ---
    add_item(
        f"Trakt: {trakt_status}",
        'trakt_info',
        'trakt_info.png',
        f"Trakt.tv Account: {trakt_status} (Click to check account and scrobble info)"
    )
    add_item(
        "Authorize Trakt",
        'trakt_auth',
        'trakt_auth.png',
        "Pair and authorize your Trakt.tv account with Umbrella"
    )
    add_item(
        "Revoke Trakt",
        'trakt_revoke',
        'trakt_revoke.png',
        "Disconnect and revoke Trakt.tv credentials from Umbrella"
    )

    # --- SETTINGS & MAINTENANCE ---
    add_item(
        "Umbrella Settings",
        'umbrella_settings',
        'umbrella_settings.png',
        "Open full Umbrella addon settings and scraper configuration"
    )
    add_item(
        "Clear Scrapers Cache",
        'clear_sources',
        'clear_sources.png',
        "Wipe cached scrapers, provider domains, and torrent host resolutions"
    )
    add_item(
        "Clear All Umbrella Cache",
        'clear_all',
        'clear_all.png',
        "Clear all cached metadata, search queries, and provider caches in Umbrella"
    )
    add_item(
        "Refresh Status",
        'refresh',
        'refresh.png',
        "Refresh authorization status and reload widgets on the home screen"
    )

    xbmcplugin.setContent(ADDON_HANDLE, 'videos')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring.lstrip('?')))
    action = params.get('action') or params.get('mode')

    if not action or action == 'none':
        if ADDON_HANDLE >= 0:
            build_menu()
    elif action == 'cm_collection_add':
        xbmc.executebuiltin('Dialog.Close(contextmenu)')
        run_collection(remove=False)
    elif action == 'cm_collection_remove':
        xbmc.executebuiltin('Dialog.Close(contextmenu)')
        run_collection(remove=True)
    elif action == 'cm_rescrape':
        xbmc.executebuiltin('Dialog.Close(contextmenu)')
        run_rescrape()
    elif action == 'rd_auth':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=rd_Authorize)')
    elif action == 'rd_info':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=rd_AccountInfo)')
    elif action == 'rd_revoke':
        dialog = xbmcgui.Dialog()
        if dialog.yesno("Umbrella Helper", "Are you sure you want to revoke Real-Debrid authorization in Umbrella?"):
            xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=rd_Revoke)')
            xbmc.executebuiltin('Container.Refresh')
    elif action == 'trakt_auth':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=traktAuth)')
    elif action == 'trakt_info':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=traktAccountInfo)')
    elif action == 'trakt_revoke':
        dialog = xbmcgui.Dialog()
        if dialog.yesno("Umbrella Helper", "Are you sure you want to revoke Trakt authorization in Umbrella?"):
            xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=traktRevoke)')
            xbmc.executebuiltin('Container.Refresh')
    elif action == 'umbrella_settings':
        xbmc.executebuiltin('Addon.OpenSettings(plugin.video.umbrella)')
    elif action == 'clear_sources':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=cache_clearSources)')
        xbmcgui.Dialog().notification("Umbrella Helper", "Scrapers cache cleared!", xbmcgui.NOTIFICATION_INFO, 3000)
    elif action == 'clear_all':
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.umbrella/?action=cache_clearAll)')
        xbmcgui.Dialog().notification("Umbrella Helper", "All Umbrella cache cleared!", xbmcgui.NOTIFICATION_INFO, 3000)
    elif action == 'refresh':
        xbmc.executebuiltin('Container.Refresh')

if __name__ == '__main__':
    raw_arg = sys.argv[2] if len(sys.argv) > 2 else (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].lstrip('-').isdigit() else '')
    router(raw_arg)
