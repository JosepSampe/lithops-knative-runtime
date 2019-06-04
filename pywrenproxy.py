import sys
import os
import flask
import logging
import time
import requests as req
from pywren_ibm_cloud import wrenlogging
from pywren_ibm_cloud.action.handler import ibm_cloud_function_handler

wrenlogging.ow_config(logging.INFO)
logger = logging.getLogger('__main__')

proxy = flask.Flask(__name__)


@proxy.route('/', methods=['GET', 'POST'])
def net_test():
    print('-- Checking Internet connection: {} Request'.format(flask.request.method))
    message = flask.request.get_json(force=True, silent=True)
    print(message, flush=True)

    url = os.environ.get('URL', 'https://httpbin.org/get')
    resp = req.get(url)
    print(resp.status_code, flush=True)

    time.sleep(20)

    if resp.status_code == 200:
        return_statement = {'Internet Connection': "True"}
    else:
        return_statement = {'Internet Connection': "False"}

    sys.stdout.flush()
    return flask.jsonify(return_statement)


@proxy.route('/run', methods=['POST'])
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
    ibm_cloud_function_handler(message)
    result = {"Execution": "Finished"}
    response = flask.jsonify(result)
    response.status_code = 202

    return complete(response)


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
