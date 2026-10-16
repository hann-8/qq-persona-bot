import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from qqbot_gateway.cli_control import ControlExchange, model_metadata
from qqbot_gateway.errors import GatewayError


class ControlTests(unittest.TestCase):
    def reply(self, exchange, **patch):
        data = {'updated': exchange.config}
        data.update(patch)
        return {'type':'control_response','response':{'subtype':'success',
                'request_id':exchange.request_id,'response':data}}

    def test_exact_ack_and_no_duplicate(self):
        exchange = ControlExchange('set_config', {'autoCompactEnabled':False})
        exchange.accept(self.reply(exchange))
        with self.assertRaises(GatewayError): exchange.accept(self.reply(exchange))

    def test_wrong_id_error_partial_and_errors_rejected(self):
        for kind in ('id', 'subtype', 'partial', 'errors', 'wrong-type'):
            exchange = ControlExchange('set_config', {'autoCompactEnabled':False})
            event = self.reply(exchange)
            if kind == 'id': event['response']['request_id'] = 'wrong'
            if kind == 'subtype': event['response']['subtype'] = 'error'
            if kind == 'partial': event['response']['response']['updated'] = {}
            if kind == 'errors': event['response']['response']['errors'] = {'autoCompactEnabled':'bad'}
            if kind == 'wrong-type': event['response']['response']['updated']={'autoCompactEnabled':0}
            with self.subTest(kind=kind), self.assertRaises(GatewayError): exchange.accept(event)

    def test_capability_allowlist_discards_secrets(self):
        value = model_metadata({'rawModels':[{'id':'test', 'apiKey':'secret', 'url':'private',
            'reasoning':{'supportedEfforts':['high'],'secret':'x'},
            'contextWindow':{'default':123,'supportedLengths':[123],'secret':'x'}}]})
        self.assertNotIn('secret', str(value))
        self.assertNotIn('private', str(value))
        self.assertEqual(value[0]['reasoning']['supportedEfforts'], ['high'])


if __name__ == '__main__': unittest.main()
