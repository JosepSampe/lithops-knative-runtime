import sys
import os
import flask
import logging
import pkgutil
import requests as req
from pywren_ibm_cloud.config import cloud_logging_config
from pywren_ibm_cloud.runtime.function_handler import function_handler

cloud_logging_config(logging.INFO)
logger = logging.getLogger('__main__')


TOTAL_REQUESTS = 0

proxy = flask.Flask(__name__)


@proxy.route('/', methods=['POST'])
def run():
    def error():
        response = flask.jsonify({'error': 'The action did not receive a dictionary as an argument.'})
        response.status_code = 404
        return complete(response)

    message = flask.request.get_json(force=True, silent=True)
    print(message, flush=True)
    if message and not isinstance(message, dict):
        return error()

    logger.info("Starting knative Function execution")
    function_handler(message)
    result = {"Execution": "Finished"}
    response = flask.jsonify(result)
    response.status_code = 202

    return complete(response)


@proxy.route('/preinstalls', methods=['POST'])
def preinstalls_task():
    logger.info("Starting Knative Function execution")
    print("Extracting preinstalled Python modules...")
    runtime_meta = dict()
    mods = list(pkgutil.iter_modules())
    runtime_meta['preinstalls'] = [entry for entry in sorted([[mod, is_pkg] for _, mod, is_pkg in mods])]
    python_version = sys.version_info
    runtime_meta['python_ver'] = str(python_version[0])+"."+str(python_version[1])
    response = flask.jsonify(runtime_meta)
    response.status_code = 202

    return complete(response)


@proxy.route('/test', methods=['GET', 'POST'])
def net_test():
    global TOTAL_REQUESTS
    TOTAL_REQUESTS = TOTAL_REQUESTS+1
    print('-- Checking Internet connection: {} Request'.format(flask.request.method))
    message = flask.request.get_json(force=True, silent=True)
    print(message, flush=True)

    url = os.environ.get('URL', 'https://httpbin.org/get')
    resp = req.get(url)
    print(resp.status_code, flush=True)
    #print('Sleeping 30 seconds', flush=True)
    #time.sleep(30)
    #print('Before sleep', flush=True)

    if resp.status_code == 200:
        return_statement = {'Internet Connection': "True", "Total Requests": TOTAL_REQUESTS}
    else:
        return_statement = {'Internet Connection': "False", "Total Requests": TOTAL_REQUESTS}

    return complete(flask.jsonify(return_statement))


def complete(response):
    # Add sentinel to stdout/stderr
    sys.stdout.flush()
    sys.stderr.write('%s\n' % 'XXX_THE_END_OF_AN_ACTIVATION_XXX')
    return response


def main():
    port = int(os.getenv('PORT', 8080))
    proxy.run(debug=True, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
