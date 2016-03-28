from urllib import urlencode
import urllib2 as urlrequest
import json

SLACK_POST_URL = "https://hooks.slack.com/services/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"


def post(payload):
    """
    Post message to Slack
    :param payload:
    """
    payload_json = json.dumps(payload)
    data = urlencode({"payload": payload_json})
    req = urlrequest.Request(SLACK_POST_URL)
    response = urlrequest.build_opener(urlrequest.HTTPHandler()).open(req, data.encode('utf-8')).read()
    return response.decode('utf-8')


def build_message(text, **kwargs):
    """
    Bulid message for posting Slack
    :param text:
    """
    post_message = {"text": text}
    post_message.update(kwargs)
    return post_message


def post_message(text):
    post(build_message(text))