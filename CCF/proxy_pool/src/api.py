import platform
from werkzeug.wrappers import Response
from flask import Flask, jsonify, request
import json

from .settings import SERVER_API, CHECK_WEBSITES
from .proxyManager import ProxyManager


__all__ = [
    'api_server'
]
HOST=SERVER_API.get('host', '127.0.0.1')
PORT=SERVER_API.get('port', 5010)

app = Flask(__name__)


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

header = '''
    'website_list': {}
    
    '# api'
    'get_random/<website>': 'get an <website> useful proxy',
    'get_all/<website>': 'get all proxy from <website> proxy pool',
    'submit_useless_proxy?proxy=<proxy>&website=<website>': 'submit a useless proxy',
    'get_status': 'proxy number'
'''.format(list(CHECK_WEBSITES.keys()))


@app.route('/')
def index():
    return header


# TODO test, 带scheme参数
@app.route('/get_random/<website>')
def get_random(website):
    random_proxy = ProxyManager().get_random(website)
    random_proxy = random_proxy or ''
    return random_proxy


# TODO test
@app.route('/get_all/<website>')
def get_all(website):
    proxies = ProxyManager().get_all(website)
    return json.dumps(proxies, indent=4, ensure_ascii=False)


# @app.route('/delete/', methods=['GET'])
# def delete():
#     proxy = request.args.get('proxy')
#     ProxyManager().delete(proxy)
#     return {"code": 0, "src": "success"}


@app.route('/submit_useless_proxy', methods=['GET'])
def submit_useless_proxy():
    proxy = request.args.get('proxy')
    website = request.args.get('website')
    result = ProxyManager().submit_useless_proxy(proxy, website)
    return {
        'state': result
    }


@app.route('/get_status/')
def get_status():
    status = ProxyManager().get_status()
    return json.dumps(status, indent=4, ensure_ascii=False)


if platform.system() != "Windows":
    import gunicorn.app.base
    from six import iteritems


    class StandaloneApplication(gunicorn.app.base.BaseApplication):

        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super(StandaloneApplication, self).__init__()

        def load_config(self):
            _config = dict([(key, value) for key, value in iteritems(self.options)
                            if key in self.cfg.settings and value is not None])
            for key, value in iteritems(_config):
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application


def runFlask():
    app.run(host=HOST, port=PORT)


def runFlaskWithGunicorn():
    _options = {
        'bind': '%s:%s' % (HOST, PORT),
        'workers': 4,
        'accesslog': '-',  # log to stdout
        'access_log_format': '%(h)s %(l)s %(t)s "%(r)s" %(s)s "%(a)s"'
    }
    StandaloneApplication(app, _options).run()

def api_server():
    if platform.system() == "Windows":
        runFlask()
    else:
        runFlaskWithGunicorn()