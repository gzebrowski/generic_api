class ApiCallerError(Exception):
    pass


class ApiWrongMethod(ApiCallerError):
    pass


class ApiError(ApiCallerError):

    def __init__(self, msg=None, data=None, status_code=None):
        args = [msg] if msg else []
        Exception.__init__(self, *args)
        self.data = data
        self.status_code = status_code


def factory_error_classes(prefix):
    api_caller_error = type(prefix + 'ApiCallerError', (ApiCallerError,), {})
    api_wrong_method = type(prefix + 'ApiWrongMethod', (ApiWrongMethod,), {})
    api_error = type(prefix + 'ApiError', (ApiError,), {})
    return api_caller_error, api_wrong_method, api_error


class ApiBaseCaller(object):
    """
        Abstract Base Api Caller
        some values may be overloaded:
            API_SETTINGS: dictionary for maping api settings and config settings. For example:
                API_SETTINGS = {'apikey': 'SENDCLOUD_APIKEY', 'apisecret': 'SENDCLOUD_APISECRET'}
            ACTIVE_CONFIG_KEY: key from config object indicating if the API is enabled (it is by default)
            ERROR_CLASSES - can be overriden with some specific error classes for specific Api implementation
            METHOD_MAP - can be filled with some specific api endpoints. See below.
    """
    API_SETTINGS = {}
    ACTIVE_CONFIG_KEY = None
    STATUS_CODE_ERROR = 'ApiCaller: error status: %(status_code)s, error msg: %(json)s'
    ERROR_CLASSES = {'api_call': ApiError, 'api_method': ApiWrongMethod}
    METHOD_MAP = {
        # ie: 
        # 'order': {'endpoint': 'order', 'subitems': {
        #     'add': {'method': 'post'},
        #     'get': {'method': 'get', 'endpoint': '%(param_1)s'},
        #     'list': {'method': 'get', 'endpoint': 'list'},
        #     }
        # }
    }

    class MethodCaller(object):
        """
            Magic helper class
        """
        def __init__(self, parent, method=None, endpoint=None):
            self.parent = parent
            self.method = method
            if isinstance(endpoint, (list, tuple)):
                self.endpoints = list(endpoint)
            else:
                self.endpoints = [endpoint] if endpoint else []

        def __call__(self, *args, **kwargs):
            if self.method:
                return self.parent.call(self.method, *args, **kwargs)
            else:
                self.parent.call_endpoint(self.endpoints, *args, **kwargs)

        def __getattr__(self, attr):
            endpoints = list(self.endpoints) + [attr]
            return self.__class__(self.parent, method=self.method, endpoint=endpoints)

    def __init__(self, config=None, **kwargs):
        """
            for django it can be called with request object - some apis 
            can require authentication token that could be retrieved by using the request
            api = SpecificApiCaller(config=settings.SOME_CONFIG_OBJ, request=request)
        """
        self.last_status_code = None
        self.api_settings = {}
        config = config or {}
        assert isinstance(config, dict), 'config object must be either None or dictionary'
        for k, v in self.API_SETTINGS.items():
            self.api_settings[k] = cfg.get(v)
        self.api_settings.update(kwargs)
        self.active = self.ACTIVE_CONFIG_KEY is None or cfg.get(self.ACTIVE_CONFIG_KEY, True)

    def __getattr__(self, attr):
        """
            we can call api by:
                api.post('someendpoint', some_json_data)
                api.get('some-get-endpoint')
                --------------------------
                or if the overloading class provided METHOD_MAP, we can call also by:
                api.add_order(some_json_data)
                api.get_order(order_id)
        """
        if attr in ['get', 'post', 'put', 'delete', 'patch']:
            return self.__class__.MethodCaller(self, method=attr)
        elif attr in self.METHOD_MAP:
            endpoint_params = self.METHOD_MAP[attr]
            return self.__class__.MethodCaller(self, endpoint=attr)
        raise self.ERROR_CLASSES['api_method'](u'Wrong method: %s' % attr)

    def call(self, method, endpoint, *args, **kwargs):
        if not self.active:
            return {'error': 'inactive'}
        arg_formater = {'param_%s' % (x + 1):  val for x, val in enumerate(args)}
        endpoint %= arg_formater
        payload = kwargs.pop('payload', None)
        result = self.call_raw(method, endpoint, payload=payload, **kwargs)
        result = self.process_result(result, method, endpoint, payload, **kwargs)
        self.last_status_code = result['status_code']
        if result['status_code'] > 299:
            raise self.ERROR_CLASSES['api_call'](self.STATUS_CODE_ERROR % {'status_code': result['status_code'], 'json': result['json']},
                                   data=result['json'],
                                   status_code=result['status_code'])
        return result['json']

    def call_endpoint(self, endpoints, *args, **kwargs):
        api_endpoints = []
        curr_position = self.METHOD_MAP
        method = None
        result_processor = None
        try:
            for ep in endpoints:
                curr_position = curr_position[ep]
                api_endpoints.append(curr_position.get('endpoint'))
                method = curr_position.get('method')  # finally only the last one will be taken into account
                result_processor = curr_position.get('result_processor')
                curr_position = curr_position.get('subitems', {})
            api_endpoints = filter(None, api_endpoints)
            assert api_endpoints and method, ''
        except (KeyError, AssertionError):
            raise self.ERROR_CLASSES['api_method'](u'Wrong method: %s' % '.'.join(endpoints))
        result = self.call(method, '/'.join(api_endpoints), *args, **kwargs)
        result_processor = result_processor or (lambda x, *args1, **kwargs1: x)
        return result_processor(result, *args, **kwargs)

    def process_result(self, result, method, endpoint, payload, **kwargs):
        """
            method to be overloaded for proprocessing the result.
        """
        return result

    def call_raw(self, method, endpoint, payload=None, **kwargs):
        raise NotImplementedError
