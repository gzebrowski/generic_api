import json
import requests
from collections import OrderedDict
from generic_api import ApiBaseCaller, factory_error_classes

TestApiCallerError, TestApiWrongMethod, TestApiError = factory_error_classes('Test')
TEST_FORMAT_URL = 'https://testapi.example.com/api/v2/%(endpoint)s'


class TestApiCaller(ApiBaseCaller):
    ERROR_CLASSES = {'api_call': TestApiError, 'api_method': TestApiWrongMethod}
    METHOD_MAP = {
        'order': {'endpoint': 'order', 'subitems': {
            'add': {'method': 'post'},
            'get': {'method': 'get', 'endpoint': '%(param_1)s'},  # for example: api.order.get(10) -> /order/get/10
            'list': {'method': 'get', 'endpoint': 'list'},
            }
        }
    }

    def call_raw(self, method, endpoint, payload=None, **kwargs):
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer %s' % self.api_settings['access_token']}
        url = TEST_FORMAT_URL % {'endpoint': endpoint}
        kwargs = {}
        assert isinstance(payload, (dict, OrderedDict, list)
                          ) or payload is None
        if payload:
            kwargs['data'] = json.dumps(payload)
        result = getattr(requests, method)(url, headers=headers, **kwargs)
        return {'status_code': result.status_code, 'json': result.json()}
