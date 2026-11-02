# -*- coding: utf-8 -*-
"""
    Umbrella Helper - Quick Real-Debrid & Trakt Auth Shortcut for Umbrella
    Created for bw905
"""

import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else -1

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

    ICON = ADDON.getAddonInfo('icon')
    FANART = ADDON.getAddonInfo('fanart')

    def add_item(title, action, is_folder=False):
        url = f"{sys.argv[0]}?action={action}"
        li = xbmcgui.ListItem(label=title)
        li.setArt({'icon': ICON, 'thumb': ICON, 'fanart': FANART, 'poster': ICON})
        li.setInfo('video', {'title': title, 'plot': title})
        li.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=is_folder)

    # --- REAL-DEBRID SECTION ---
    add_item(f"[COLOR dodgerblue][B]═══ REAL-DEBRID: {rd_status} ═══[/B][/COLOR]", 'rd_info')
    add_item("  [COLOR gold]▸[/COLOR] [B]Authorize Real-Debrid[/B] [I](Umbrella)[/I]", 'rd_auth')
    add_item("  [COLOR gold]▸[/COLOR] View Real-Debrid Account Info & Days", 'rd_info')
    add_item("  [COLOR gold]▸[/COLOR] [COLOR crimson]Revoke / Log Out Real-Debrid[/COLOR]", 'rd_revoke')

    # Separator
    add_item("[COLOR dimgray]────────────────────────────────────────────[/COLOR]", 'none')

    # --- TRAKT SECTION ---
    add_item(f"[COLOR crimson][B]═══ TRAKT: {trakt_status} ═══[/B][/COLOR]", 'trakt_info')
    add_item("  [COLOR gold]▸[/COLOR] [B]Authorize Trakt[/B] [I](Umbrella)[/I]", 'trakt_auth')
    add_item("  [COLOR gold]▸[/COLOR] View Trakt Account Info", 'trakt_info')
    add_item("  [COLOR gold]▸[/COLOR] [COLOR crimson]Revoke / Log Out Trakt[/COLOR]", 'trakt_revoke')

    # Separator
    add_item("[COLOR dimgray]────────────────────────────────────────────[/COLOR]", 'none')

    # --- SHORTCUTS & MAINTENANCE ---
    add_item("  [COLOR mediumpurple]▸[/COLOR] [B]Open Full Umbrella Settings[/B]", 'umbrella_settings')
    add_item("  [COLOR mediumpurple]▸[/COLOR] Clear Scrapers & Providers Cache", 'clear_sources')
    add_item("  [COLOR mediumpurple]▸[/COLOR] Clear All Umbrella Cache", 'clear_all')
    add_item("  [COLOR deepskyblue]▸[/COLOR] [B]Refresh Status[/B]", 'refresh')

    xbmcplugin.setContent(ADDON_HANDLE, 'files')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring.lstrip('?')))
    action = params.get('action')

    if not action or action == 'none':
        build_menu()
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
    router(sys.argv[2] if len(sys.argv) > 2 else '')
