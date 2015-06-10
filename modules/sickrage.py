from flask import jsonify, render_template, request, send_file, json
import urllib2
import base64
import StringIO

from maraschino import app, logger, WEBROOT
from maraschino.tools import *
import maraschino


def sickrage_http():
    if get_setting_value('sickrage_https') == '1':
        return 'https://'
    else:
        return 'http://'


def sickrage_url():
    port = get_setting_value('sickrage_port')
    url_base = get_setting_value('sickrage_ip')
    webroot = get_setting_value('sickrage_webroot')

    if port:
        url_base = '%s:%s' % (url_base, port)

    if webroot:
        url_base = '%s/%s' % (url_base, webroot)

    url = '%s/api/%s' % (url_base, get_setting_value('sickrage_api'))

    return sickrage_http() + url


def sickrage_url_no_api():
    port = get_setting_value('sickrage_port')
    url_base = get_setting_value('sickrage_ip')
    webroot = get_setting_value('sickrage_webroot')

    if port:
        url_base = '%s:%s' % (url_base, port)

    if webroot:
        url_base = '%s/%s' % (url_base, webroot)

    return sickrage_http() + url_base


def sickrage_api(params=None, use_json=True, dev=False):
    username = get_setting_value('sickrage_user')
    password = get_setting_value('sickrage_password')

    url = sickrage_url() + params
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

@app.route('/xhr/sickrage/')
def xhr_sickrage():
    params = '/?cmd=future&sort=date'

    try:
        sickrage = sickrage_api(params)

        compact_view = get_setting_value('sickrage_compact') == '1'
        show_airdate = get_setting_value('sickrage_airdate') == '1'

        if sickrage['result'].rfind('success') >= 0:
        	
            logger.log('SICKRAGE :: Successful API call to %s' % params, 'DEBUG')
            sickrage = sickrage['data']

            for time in sickrage:
                for episode in sickrage[time]:
                    episode['image'] = get_pic(episode['indexerid'], 'banner')
                    logger.log('SICKRAGE :: Successful %s' % (episode['image']), 'DEBUG')
    except:
        return render_template('sickrage.html',
            sickrage='',
        )

    return render_template('sickrage.html',
        url=sickrage_url_no_api(),
        app_link=sickrage_url_no_api(),
        sickrage=sickrage,
        missed=sickrage['missed'],
        today=sickrage['today'],
        soon=sickrage['soon'],
        later=sickrage['later'],
        compact_view=compact_view,
        show_airdate=show_airdate,
        
    )

@app.route('/xhr/sickrage/get_all/')
def get_all():
    params = '/?cmd=shows&sort=name'

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    if sickrage['result'].rfind('success') >= 0:
        sickrage = sickrage['data']
        for show in sickrage:
            sickrage[show]['url'] = get_pic(sickrage[show]['indexerid'], 'banner')
            

    return render_template('sickrage/all.html',
        sickrage=sickrage,
    )

# returns a link with the path to the required image from SB
def get_pic(indexerid, style='banner'):
    try:
    	return '%s/xhr/sickrage/get_%s/%s' % (maraschino.WEBROOT, style, indexerid)
    except:
    	raise Exception

@app.route('/xhr/sickrage/search_ep/<indexerid>/<season>/<episode>/')
@requires_auth
def search_ep(indexerid, season, episode):
    params = '/?cmd=episode.search&indexerid=%s&season=%s&episode=%s' % (indexerid, season, episode)
    try:
        sickrage = sickrage_api(params)
        return jsonify(sickrage)
    except:
        return jsonify({'result': False})
        
 
@app.route('/xhr/sickrage/get_plot/<indexerid>/<season>/<episode>/')
def get_plot(indexerid, season, episode):
    params = '/?cmd=episode&indexerid=%s&season=%s&episode=%s' % (indexerid, season, episode)

    try:
        sickrage = sickrage_api(params)
        return sickrage['data']['description']
    except:
        return ''


@app.route('/xhr/sickrage/get_show_info/<indexerid>/')
def show_info(indexerid):
    params = '/?cmd=show&indexerid=%s' % indexerid

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    if sickrage['result'].rfind('success') >= 0:
    	
    	logger.log('SICKRAGE :: Successful API call to %s' % params, 'DEBUG')
        sickrage = sickrage['data']
        sickrage['url'] = get_pic(indexerid, 'banner')
        logger.log('SICKRAGE :: Successful %s' % (sickrage['url']), 'DEBUG')
#        sickrage['indexerid'] = indexerid

    return render_template('sickrage/show.html',
        sickrage=sickrage,
    )


@app.route('/xhr/sickrage/get_season/<indexerid>/<season>/')
def get_season(indexerid, season):
    params = '/?cmd=show.seasons&indexerid=%s&season=%s' % (indexerid, season)

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    if sickrage['result'].rfind('success') >= 0:
    	
    	logger.log('SICKRAGE :: Successful API call to %s' % params, 'DEBUG')
        sickrage = sickrage['data']
        

    return render_template('sickrage/season.html',
        sickrage=sickrage,
        id=indexerid,
        season=season,
    )


@app.route('/xhr/sickrage/history/<limit>/')
def history(limit):
    params = '/?cmd=history&limit=%s' % limit
    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    if sickrage['result'].rfind('success') >= 0:
        sickrage = sickrage['data']

        for show in sickrage:
            show['image'] = get_pic(show['indexerid'])

    return render_template('sickrage/history.html',
        sickrage=sickrage,
    )

@app.route('/xhr/sickrage/get_ep_info/<indexerid>/<season>/<ep>/')
def get_episode_info(indexerid, season, ep):
    params = '/?cmd=episode&indexerid=%s&season=%s&episode=%s&full_path=1' % (indexerid, season, ep)

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    if sickrage['result'].rfind('success') >= 0:
        sickrage = sickrage['data']

    return render_template('sickrage/episode.html',
        sickrage=sickrage,
        id=indexerid,
        season=season,
        ep=ep,
    )

@app.route('/xhr/sickrage/set_ep_status/<indexerid>/<season>/<ep>/<st>/')
def set_episode_status(indexerid, season, ep, st):
    params = '/?cmd=episode.setstatus&indexerid=%s&season=%s&episode=%s&status=%s' % (indexerid, season, ep, st)

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    status = 'error'

    if sickrage['result'] == 'success':
        status = 'success'

    return jsonify({'status': status})

@app.route('/xhr/sickrage/shutdown/')
def shutdown():
    params = '/?cmd=sb.shutdown'

    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']


@app.route('/xhr/sickrage/restart/')
def restart():
    params = '/?cmd=sb.restart'
    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']


@app.route('/xhr/sickrage/search/')
def sb_search():
    sickrage = {}
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
            sickrage = sickrage_api(params)
            sickrage = sickrage['data']['results']
        except:
            sickrage = None

    else:
        sickrage = None

    return render_template('sickrage/search.html',
        data=sickrage,
        sickrage='results',
    )


@app.route('/xhr/sickrage/add_show/<indexerid>/')
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
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']

@app.route('/xhr/sickrage/get_banner/<indexerid>/')
def get_banner(indexerid):
    logger.log('SICKRAGE :: Getting banner %s' % indexerid, 'DEBUG')
    params = '/?cmd=show.getbanner&indexerid=%s' % indexerid
    logger.log('SICKRAGE :: Getting banner params %s' % params, 'DEBUG')
    img = StringIO.StringIO(sickrage_api(params, use_json=False))
    logger.log('SICKRAGE :: Getting img params %s' % img, 'DEBUG')
    return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/sickrage/get_poster/<indexerid>/')
def get_poster(indexerid):
    params = '/?cmd=show.getposter&indexerid=%s' % indexerid
    img = StringIO.StringIO(sickrage_api(params, use_json=False))
    return send_file(img, mimetype='image/jpeg')

@app.route('/xhr/sickrage/log/<level>/')
def log(level):
    params = '/?cmd=logs&min_level=%s' % level
    try:
        sickrage = sickrage_api(params)
        if sickrage['result'].rfind('success') >= 0:
            sickrage = sickrage['data']
            if not sickrage:
                sickrage = ['The %s log is empty' % level]

    except:
        sickrage = None

    return render_template('sickrage/log.html',
        sickrage=sickrage,
        level=level,
    )


@app.route('/xhr/sickrage/delete_show/<indexerid>/')
def delete_show(indexerid):
    params = '/?cmd=show.delete&indexerid=%s' % indexerid
    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']


@app.route('/xhr/sickrage/refresh_show/<indexerid>/')
def refresh_show(indexerid):
    params = '/?cmd=show.refresh&indexerid=%s' % indexerid
    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']


@app.route('/xhr/sickrage/update_show/<indexerid>/')
def update_show(indexerid):
    params = '/?cmd=show.update&indexerid=%s' % indexerid
    try:
        sickrage = sickrage_api(params)
    except:
        raise Exception

    return sickrage['message']
<<<<<<< HEAD
=======

>>>>>>> master2
