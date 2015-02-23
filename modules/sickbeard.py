from flask import jsonify, render_template, request, send_file, json
import urllib2
import base64
import StringIO

from maraschino import app, logger, WEBROOT
from maraschino.tools import *
import maraschino


def sickbeard_http():
    if get_setting_value('sickbeard_https') == '1':
        return 'https://'
    else:
        return 'http://'


def sickbeard_url():
    port = get_setting_value('sickbeard_port')
    url_base = get_setting_value('sickbeard_ip')
    webroot = get_setting_value('sickbeard_webroot')

    if port:
        url_base = '%s:%s' % (url_base, port)

    if webroot:
        url_base = '%s/%s' % (url_base, webroot)

    url = '%s/api/%s' % (url_base, get_setting_value('sickbeard_api'))

    return sickbeard_http() + url


def sickbeard_url_no_api():
    port = get_setting_value('sickbeard_port')
    url_base = get_setting_value('sickbeard_ip')
    webroot = get_setting_value('sickbeard_webroot')

    if port:
        url_base = '%s:%s' % (url_base, port)

    if webroot:
        url_base = '%s/%s' % (url_base, webroot)

    return sickbeard_http() + url_base


def sickbeard_api(params=None, use_json=True, dev=False):
    username = get_setting_value('sickbeard_user')
    password = get_setting_value('sickbeard_password')

    url = sickbeard_url() + params
    r = urllib2.Request(url)

    if username and password:
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        r.add_header("Authorization", "Basic %s" % base64string)

    data = urllib2.urlopen(r).read()
    if dev:
        print url
        print data
    if use_json:
        data = json.JSONDecoder().decode(data)
    return data


@app.route('/xhr/sickbeard/')
def xhr_sickbeard():
    params = '/?cmd=future&sort=date'

    try:
        sickbeard = sickbeard_api(params)

        compact_view = get_setting_value('sickbeard_compact') == '1'
        show_airdate = get_setting_value('sickbeard_airdate') == '1'

        if sickbeard['result'].rfind('success') >= 0:
            logger.log('SICKRAGE :: Successful API call to %s' % params, 'DEBUG')
            sickbeard = sickbeard['data']
            for time in sickbeard:
                for episode in sickbeard[time]:
                    episode['image'] = get_pic(episode['indexerid'], 'banner')
                    logger.log('SICKRAGE :: Successful API call to %s' % params, 'DEBUG')
    except:
        return render_template('sickbeard.html',
            sickbeard='',
        )

    return render_template('sickbeard.html',
        url=sickbeard_url_no_api(),
        app_link=sickbeard_url_no_api(),
        sickbeard=sickbeard,
        missed=sickbeard['missed'],
        today=sickbeard['today'],
        soon=sickbeard['soon'],
        later=sickbeard['later'],
        compact_view=compact_view,
        show_airdate=show_airdate,
    )


@app.route('/xhr/sickbeard/search_ep/<indexerid>/<season>/<episode>/')
@requires_auth
def search_ep(indexerid, season, episode):
    params = '/?cmd=episode.search&indexerid=%s&season=%s&episode=%s' % (indexerid, season, episode)

    try:
        sickbeard = sickbeard_api(params)
        return jsonify(sickbeard)
    except:
        return jsonify({'result': False})


@app.route('/xhr/sickbeard/get_plot/<indexerid>/<season>/<episode>/')
def get_plot(indexerid, season, episode):
    params = '/?cmd=episode&indexerid=%s&season=%s&episode=%s' % (indexerid, season, episode)

    try:
        sickbeard = sickbeard_api(params)
        return sickbeard['data']['description']
    except:
        return ''


@app.route('/xhr/sickbeard/get_all/')
def get_all():
    params = '/?cmd=shows&sort=name'

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    if sickbeard['result'].rfind('success') >= 0:
        sickbeard = sickbeard['data']

        for show in sickbeard:
            sickbeard[show]['url'] = get_pic(sickbeard[show]['indexerid'], 'banner')

    return render_template('sickbeard/all.html',
        sickbeard=sickbeard,
    )


@app.route('/xhr/sickbeard/get_show_info/<indexerid>/')
def show_info(indexerid):
    params = '/?cmd=show&indexerid=%s' % indexerid

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    if sickbeard['result'].rfind('success') >= 0:
        sickbeard = sickbeard['data']
        sickbeard['url'] = get_pic(indexerid, 'banner')
        sickbeard['indexerid'] = indexerid

    return render_template('sickbeard/show.html',
        sickbeard=sickbeard,
    )


@app.route('/xhr/sickbeard/get_season/<indexerid>/<season>/')
def get_season(indexerid, season):
    params = '/?cmd=show.seasons&indexerid=%s&season=%s' % (indexerid, season)

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    if sickbeard['result'].rfind('success') >= 0:
        sickbeard = sickbeard['data']

    return render_template('sickbeard/season.html',
        sickbeard=sickbeard,
        id=indexerid,
        season=season,
    )


@app.route('/xhr/sickbeard/history/<limit>/')
def history(limit):
    params = '/?cmd=history&limit=%s' % limit
    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    if sickbeard['result'].rfind('success') >= 0:
        sickbeard = sickbeard['data']

        for show in sickbeard:
            show['image'] = get_pic(show['indexerid'])

    return render_template('sickbeard/history.html',
        sickbeard=sickbeard,
    )


# returns a link with the path to the required image from SB
def get_pic(indexerid, style='banner'):
    return '%s/xhr/sickbeard/get_%s/%s' % (maraschino.WEBROOT, style, indexerid)


@app.route('/xhr/sickbeard/get_ep_info/<indexerid>/<season>/<ep>/')
def get_episode_info(indexerid, season, ep):
    params = '/?cmd=episode&indexerid=%s&season=%s&episode=%s&full_path=1' % (indexerid, season, ep)

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    if sickbeard['result'].rfind('success') >= 0:
        sickbeard = sickbeard['data']

    return render_template('sickbeard/episode.html',
        sickbeard=sickbeard,
        id=indexerid,
        season=season,
        ep=ep,
    )


@app.route('/xhr/sickbeard/set_ep_status/<indexerid>/<season>/<ep>/<st>/')
def set_episode_status(indexerid, season, ep, st):
    params = '/?cmd=episode.setstatus&indexerid=%s&season=%s&episode=%s&status=%s' % (indexerid, season, ep, st)

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    status = 'error'

    if sickbeard['result'] == 'success':
        status = 'success'

    return jsonify({'status': status})


@app.route('/xhr/sickbeard/shutdown/')
def shutdown():
    params = '/?cmd=sb.shutdown'

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']


@app.route('/xhr/sickbeard/restart/')
def restart():
    params = '/?cmd=sb.restart'
    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']


@app.route('/xhr/sickbeard/search/')
def sb_search():
    sickbeard = {}
    params = ''

    try:
        params = '&name=%s' % (urllib2.quote(request.args['name']))
    except:
        pass

    try:
        params = '&indexerid=%s' % (urllib2.quote(request.args['indexerid']))
    except:
        pass

    try:
        params = '&lang=%s' % (urllib2.quote(request.args['lang']))
    except:
        pass

    if params is not '':
        params = '/?cmd=sb.searchtvdb%s' % params

        try:
            sickbeard = sickbeard_api(params)
            sickbeard = sickbeard['data']['results']
        except:
            sickbeard = None

    else:
        sickbeard = None

    return render_template('sickbeard/search.html',
        data=sickbeard,
        sickbeard='results',
    )


@app.route('/xhr/sickbeard/add_show/<indexerid>/')
def add_show(indexerid):
    params = '/?cmd=show.addnew&indexerid=%s' % indexerid
    try:
        status = urllib2.quote(request.args['status'])
        lang = urllib2.quote(request.args['lang'])
        initial = urllib2.quote(request.args['initial'])
        if status:
            params += '&status=%s' % status

        if lang:
            params += '&lang=%s' % lang

        if initial:
            params += '&initial=%s' % initial
    except:
        pass

    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']


@app.route('/xhr/sickbeard/get_banner/<indexerid>/')
def get_banner(indexerid):
    params = '/?cmd=show.getbanner&indexerid=%s' % indexerid
    img = StringIO.StringIO(sickbeard_api(params, use_json=False))
    return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/sickbeard/get_poster/<indexerid>/')
def get_poster(indexerid):
    params = '/?cmd=show.getposter&indexerid=%s' % indexerid
    img = StringIO.StringIO(sickbeard_api(params, use_json=False))
    return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/sickbeard/log/<level>/')
def log(level):
    params = '/?cmd=logs&min_level=%s' % level
    try:
        sickbeard = sickbeard_api(params)
        if sickbeard['result'].rfind('success') >= 0:
            sickbeard = sickbeard['data']
            if not sickbeard:
                sickbeard = ['The %s log is empty' % level]

    except:
        sickbeard = None

    return render_template('sickbeard/log.html',
        sickbeard=sickbeard,
        level=level,
    )


@app.route('/xhr/sickbeard/delete_show/<indexerid>/')
def delete_show(indexerid):
    params = '/?cmd=show.delete&indexerid=%s' % indexerid
    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']


@app.route('/xhr/sickbeard/refresh_show/<indexerid>/')
def refresh_show(indexerid):
    params = '/?cmd=show.refresh&indexerid=%s' % indexerid
    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']


@app.route('/xhr/sickbeard/update_show/<indexerid>/')
def update_show(indexerid):
    params = '/?cmd=show.update&indexerid=%s' % indexerid
    try:
        sickbeard = sickbeard_api(params)
    except:
        raise Exception

    return sickbeard['message']
