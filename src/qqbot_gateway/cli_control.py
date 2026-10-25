"""Bounded, correlated CLI controls; no user messages or authentication data."""
import uuid
import json
from .errors import GatewayError


class ControlExchange:
    def __init__(self, subtype, config=None):
        self.request_id = 'cfg-' + uuid.uuid4().hex
        self.subtype = subtype
        self.config = config
        self.response = None

    def request(self):
        request = {'subtype': self.subtype}
        if self.config is not None:
            request['config'] = self.config
        return {'type': 'control_request', 'request_id': self.request_id, 'request': request}

    def accept(self, event):
        if self.response is not None or not isinstance(event, dict) or event.get('type') != 'control_response':
            raise GatewayError('PROTOCOL_ERROR')
        envelope = event.get('response')
        if (not isinstance(envelope, dict) or envelope.get('request_id') != self.request_id or
                envelope.get('subtype') != 'success' or envelope.get('error')):
            raise GatewayError('PROTOCOL_ERROR')
        response = envelope.get('response')
        if not isinstance(response, dict) or response.get('errors'):
            raise GatewayError('PROTOCOL_ERROR')
        if self.config is not None and json.dumps(response.get('updated'),sort_keys=True) != json.dumps(self.config,sort_keys=True):
            raise GatewayError('PROTOCOL_ERROR')
        self.response = response
        return response


def model_metadata(response):
    """Keep only non-sensitive capability fields, never raw provider settings."""
    values = response.get('rawModels')
    if not isinstance(values, list):
        raise GatewayError('PROTOCOL_ERROR')
    models = []
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get('id'), str):
            continue
        result = {'id': value['id']}
        for key in ('maxInputTokens', 'maxOutputTokens'):
            if type(value.get(key)) is int and value[key] > 0:
                result[key] = value[key]
        for key in ('supportsReasoning','onlyReasoning','supportsImages'):
            if type(value.get(key)) is bool:result[key]=value[key]
        window = value.get('contextWindow')
        if isinstance(window, dict):
            result['contextWindow'] = {}
            for field in ('default','defaultLength'):
                if type(window.get(field)) is int and window[field]>0:
                    result['contextWindow'][field]=window[field]
            if isinstance(window.get('supportedLengths'),list):
                result['contextWindow']['supportedLengths']=[v for v in window['supportedLengths'] if type(v) is int and v>0]
        reasoning = value.get('reasoning')
        if isinstance(reasoning, dict):
            allowed=('minimal','low','medium','high','xhigh','max')
            result['reasoning'] = {k: reasoning[k] for k in ('defaultEffort', 'effort') if reasoning.get(k) in allowed}
            if isinstance(reasoning.get('supportedEfforts'),list):
                result['reasoning']['supportedEfforts']=[v for v in reasoning['supportedEfforts'] if v in allowed]
        models.append(result)
    return models
