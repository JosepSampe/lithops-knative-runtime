import sys
import os
import flask
from gevent.pywsgi import WSGIServer
import requests as req


proxy = flask.Flask(__name__)
proxy.debug = False
# disable re-initialization of the executable unless explicitly allowed via an environment
# variable PROXY_ALLOW_REINIT == "1" (this is generally useful for local testing and development)
proxy.rejectReinit = 'PROXY_ALLOW_REINIT' not in os.environ or os.environ['PROXY_ALLOW_REINIT'] != "1"
proxy.initialized = False
runner = None


def setRunner(r):
    global runner
    runner = r


@proxy.route('/', methods=['GET', 'POST'])
def net_test():
    print('------------', flask.request.method, '------------')
    #args = request.args
    #print('Args: ', args)
    req_data = flask.request.get_json()
    print('Data: ', req_data)

    #return jsonify({'Internet Connection': "True"})

    # Ensure no: k get serviceentry
    url = os.environ.get('URL', 'https://httpbin.org/get')
    resp = req.get(url)
    #print(resp.text)

    #time.sleep(10)

    if resp.status_code == 200:
        return_statement = {'Internet Connection': "True"}
    else:
        return_statement = {'Internet Connection': "False"}

    sys.stdout.flush()
    return flask.jsonify(return_statement)


@proxy.route('/init', methods=['POST'])
def init():
    if proxy.rejectReinit is True and proxy.initialized is True:
        msg = 'Cannot initialize the action more than once.'
        sys.stderr.write(msg + '\n')
        response = flask.jsonify({'error': msg})
        response.status_code = 403
        return response

    message = flask.request.get_json(force=True, silent=True)
    if message and not isinstance(message, dict):
        flask.abort(404)
    else:
        value = message.get('value', {}) if message else {}

    if not isinstance(value, dict):
        flask.abort(404)

    try:
        status = runner.init(value)
    except Exception as e:
        status = False

    if status is True:
        proxy.initialized = True
        return ('OK', 200)
    else:
        response = flask.jsonify({'error': 'The action failed to generate or locate a binary. See logs for details.'})
        response.status_code = 502
        return complete(response)


@proxy.route('/run', methods=['POST'])
def run():
    def error():
        response = flask.jsonify({'error': 'The action did not receive a dictionary as an argument.'})
        response.status_code = 404
        return complete(response)

    message = flask.request.get_json(force=True, silent=True)
    if message and not isinstance(message, dict):
        return error()
    else:
        args = message.get('value', {}) if message else {}
        if not isinstance(args, dict):
            return error()

    if runner.verify():
        try:
            code, result = runner.run(args, runner.env(message or {}))
            response = flask.jsonify(result)
            response.status_code = code
        except Exception as e:
            response = flask.jsonify({'error': 'Internal error. {}'.format(e)})
            response.status_code = 500
    else:
        response = flask.jsonify({'error': 'The action failed to locate a binary. See logs for details.'})
        response.status_code = 502
    return complete(response)


def complete(response):
    # Add sentinel to stdout/stderr
    sys.stdout.write('%s\n' % 'XXX_THE_END_OF_AN_ACTIVATION_XXX')
    sys.stdout.flush()
    sys.stderr.write('%s\n' % 'XXX_THE_END_OF_AN_ACTIVATION_XXX')
    sys.stderr.flush()
    return response


def main():
    port = int(os.getenv('PORT', 8080))
    proxy.run(debug=True, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
