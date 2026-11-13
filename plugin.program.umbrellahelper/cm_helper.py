# -*- coding: utf-8 -*-
"""Shared context-menu helpers for Umbrella Helper (Trakt Collection & Re-scrape)."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xbmc
import xbmcaddon
import xbmcgui

DEFAULT_TRAKT_CLIENT_ID = '87e3f055fc4d8fcfd96e61a47463327ca877c51e8597b448e132611c5a677b13'


def _get_umbrella():
    try:
        return xbmcaddon.Addon('plugin.video.umbrella')
    except Exception:
        return None


def extract_context(item=None):
    """Extract plugin query params, metadata, and IDs from sys.listitem or infolabels."""
    raw_path = ''
    dbtype = ''
    imdb = tmdb = tvdb = season = episode = tvshowtitle = title = year = premiered = ''

    if item is not None:
        raw_path = item.getPath() or ''
        try:
            tag = item.getVideoInfoTag()
            dbtype = (tag.getMediaType() or '').lower()
            imdb = tag.getIMDBNumber() or tag.getUniqueID('imdb') or ''
            tmdb = tag.getUniqueID('tmdb') or ''
            tvdb = tag.getUniqueID('tvdb') or ''
            s_num = tag.getSeason()
            e_num = tag.getEpisode()
            season = str(s_num) if s_num >= 0 else ''
            episode = str(e_num) if e_num >= 0 else ''
            tvshowtitle = tag.getTVShowTitle() or ''
            title = tag.getTitle() or item.getLabel() or ''
            y_num = tag.getYear()
            year = str(y_num) if y_num > 0 else ''
            premiered = tag.getFirstAired() or ''
        except Exception:
            pass

    if not raw_path:
        raw_path = (
            xbmc.getInfoLabel('ListItem.FileNameAndPath')
            or xbmc.getInfoLabel('ListItem.FolderPath')
            or xbmc.getInfoLabel('ListItem.Path')
        )

    params = dict(urllib.parse.parse_qsl(raw_path.split('?', 1)[1])) if '?' in raw_path else {}
    meta = {}
    if params.get('meta'):
        try:
            meta = json.loads(params['meta'])
        except Exception:
            meta = {}

    return {
        'raw_path': raw_path,
        'meta': meta,
        'dbtype': dbtype or (xbmc.getInfoLabel('ListItem.DBTYPE') or '').lower(),
        'imdb': str(meta.get('imdb') or params.get('imdb') or imdb or xbmc.getInfoLabel('ListItem.IMDBNumber') or ''),
        'tmdb': str(meta.get('tmdb') or params.get('tmdb') or tmdb or xbmc.getInfoLabel('ListItem.UniqueID(tmdb)') or ''),
        'tvdb': str(meta.get('tvdb') or params.get('tvdb') or tvdb or xbmc.getInfoLabel('ListItem.UniqueID(tvdb)') or ''),
        'season': str(meta.get('season') or params.get('season') or season or xbmc.getInfoLabel('ListItem.Season') or ''),
        'episode': str(meta.get('episode') or params.get('episode') or episode or xbmc.getInfoLabel('ListItem.Episode') or ''),
        'tvshowtitle': meta.get('tvshowtitle') or params.get('tvshowtitle') or tvshowtitle or xbmc.getInfoLabel('ListItem.TVShowTitle') or '',
        'title': meta.get('title') or params.get('title') or title or xbmc.getInfoLabel('ListItem.Title') or '',
        'year': str(meta.get('year') or params.get('year') or year or xbmc.getInfoLabel('ListItem.Year') or ''),
        'premiered': meta.get('premiered') or params.get('premiered') or premiered or xbmc.getInfoLabel('ListItem.Premiered') or '',
    }


def _build_trakt_ids(ctx, is_show):
    ids = {}
    if ctx['imdb'] and ctx['imdb'].startswith('tt'):
        ids['imdb'] = ctx['imdb']
    if ctx['tmdb'].isdigit():
        ids['tmdb'] = int(ctx['tmdb'])
    if is_show and ctx['tvdb'].isdigit():
        ids['tvdb'] = int(ctx['tvdb'])
    return ids


def run_collection(remove=False):
    """Add or remove the focused item from the user's Trakt Collection."""
    ctx = extract_context(getattr(sys, 'listitem', None))
    umbrella = _get_umbrella()
    if not umbrella:
        xbmcgui.Dialog().notification("Umbrella Helper", "Umbrella addon not found", xbmcgui.NOTIFICATION_ERROR, 3000)
        return

    token = xbmcgui.Window(10000).getProperty('umbrella.trakt.access_token') or umbrella.getSetting('trakt.user.token')
    if not token:
        xbmcgui.Dialog().notification("Umbrella Helper", "Trakt not authorized in Umbrella", xbmcgui.NOTIFICATION_WARNING, 3000)
        return

    season_num = int(ctx['season']) if ctx['season'].isdigit() else None
    ep_num = int(ctx['episode']) if ctx['episode'].isdigit() else None
    is_show = bool(ctx['tvshowtitle'] or ctx['tvdb'] or ctx['dbtype'] in ('episode', 'season', 'tvshow') or season_num is not None)
    ids = _build_trakt_ids(ctx, is_show)
    if not ids:
        xbmcgui.Dialog().notification("Umbrella Helper", "Missing Trakt ID for selected item", xbmcgui.NOTIFICATION_WARNING, 3000)
        return

    if is_show:
        show_entry = {"ids": ids}
        name = ctx['tvshowtitle'] or ctx['title'] or 'Show'
        if season_num is not None and ep_num is not None:
            show_entry["seasons"] = [{"number": season_num, "episodes": [{"number": ep_num}]}]
            display_name = f"{name} - {season_num}x{ep_num:02d}"
            bucket = 'episodes'
        elif season_num is not None:
            show_entry["seasons"] = [{"number": season_num}]
            display_name = f"{name} - Season {season_num}"
            bucket = 'episodes'
        else:
            display_name = name
            bucket = 'shows'
        payload = {"shows": [show_entry]}
    else:
        display_name = ctx['title'] or 'Movie'
        bucket = 'movies'
        payload = {"movies": [{"ids": ids}]}

    client_id = DEFAULT_TRAKT_CLIENT_ID
    if umbrella.getSetting('traktuserkey.customenabled') == 'true' and umbrella.getSetting('trakt.clientid'):
        client_id = umbrella.getSetting('trakt.clientid')

    url = 'https://api.trakt.tv/sync/collection/remove' if remove else 'https://api.trakt.tv/sync/collection'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Kodi/21.0 (UmbrellaHelper/1.0)',
            'trakt-api-key': client_id,
            'trakt-api-version': '2',
            'Authorization': f'Bearer {token}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode('utf-8') or '{}')
        if remove:
            deleted = res.get('deleted', {}).get(bucket, 0)
            msg = "Removed from Trakt Collection" if deleted else "Item not in Trakt Collection"
        else:
            added = res.get('added', {}).get(bucket, 0)
            existing = res.get('existing', {}).get(bucket, 0)
            msg = "Added to Trakt Collection" if added else ("Already in Trakt Collection" if existing else "Updated Trakt Collection")
        xbmcgui.Dialog().notification(display_name, msg, xbmcgui.NOTIFICATION_INFO, 3000)
    except urllib.error.HTTPError as e:
        err_body = ''
        try:
            err_body = e.read().decode('utf-8', 'ignore')[:200]
        except Exception:
            pass
        xbmc.log(f"[UmbrellaHelper] Trakt HTTP {e.code} on {url}: {err_body}", xbmc.LOGWARNING)
        if e.code == 401:
            q_name = urllib.parse.quote_plus(ctx['tvshowtitle'] or ctx['title'])
            xbmc.executebuiltin(
                f"RunPlugin(plugin://plugin.video.umbrella/?action=tools_traktManager&name={q_name}&imdb={ctx['imdb']}&tmdb={ctx['tmdb']}&tvdb={ctx['tvdb']}&season={ctx['season']}&episode={ctx['episode']})"
            )
            return
        if e.code == 420:
            xbmcgui.Dialog().notification("Umbrella Helper", "Trakt Collection limit reached (account limit)", xbmcgui.NOTIFICATION_WARNING, 4000)
            return
        xbmcgui.Dialog().notification("Umbrella Helper", f"Trakt request failed ({e.code})", xbmcgui.NOTIFICATION_ERROR, 3000)
    except Exception:
        xbmcgui.Dialog().notification("Umbrella Helper", "Trakt collection update failed", xbmcgui.NOTIFICATION_ERROR, 3000)


def run_rescrape():
    """Open Umbrella's native Re-scrape Options menu for the focused item."""
    ctx = extract_context(getattr(sys, 'listitem', None))
    if not ctx['title'] and not ctx['tvshowtitle']:
        xbmcgui.Dialog().notification("Umbrella Helper", "Unable to inspect item for re-scrape", xbmcgui.NOTIFICATION_WARNING, 3000)
        return
    meta = ctx['meta'] or {
        'imdb': ctx['imdb'],
        'tmdb': ctx['tmdb'],
        'tvdb': ctx['tvdb'],
        'season': ctx['season'],
        'episode': ctx['episode'],
        'tvshowtitle': ctx['tvshowtitle'],
        'premiered': ctx['premiered'],
        'title': ctx['title'],
        'year': ctx['year'],
    }
    q = urllib.parse.quote_plus
    premiered = ctx['premiered'] if ctx['tvshowtitle'] else ''
    url = (
        f"plugin://plugin.video.umbrella/?action=rescrapeMenu"
        f"&title={q(ctx['title'])}&year={q(ctx['year'])}"
        f"&imdb={q(ctx['imdb'])}&tmdb={q(ctx['tmdb'])}&tvdb={q(ctx['tvdb'])}"
        f"&season={q(ctx['season'])}&episode={q(ctx['episode'])}"
        f"&tvshowtitle={q(ctx['tvshowtitle'])}&premiered={q(premiered)}"
        f"&meta={q(json.dumps(meta))}"
    )
    xbmc.executebuiltin(f"PlayMedia({url})")
