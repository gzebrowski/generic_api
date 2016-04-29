# generic_api

It is a generic class for creating a custom api interface. Pls see example in test_api.py to see how implement a simple class.

It allows to call apis by:

1.
```
api.post(payload=some_json)
api.get(...)
api.put(...)
etc.
```

2.
```
api.some.api.method.get(...)
api.another.endpoint(...)
```   
In method 2 one need to define METHOD_MAP that describes the endpoints structure. Please see the example in test_api.py

At least one method has to be implemented: call_raw(method, endpoint, payload=None, **kwargs). This method is reponsible 
for managing authentication, tokens (also for refreshing tokens if need). See example in test_api.py. The __init__ method 
takes optional config dictionary, and keword args that will be stored in self.api_settings - this can be used in call_raw() 
method (the best place for passing all required credentials, tokens, etc).

METHOD_MAP can be configured like this:

```
    METHOD_MAP = {
        'order': {'endpoint': 'order', 'subitems': {
            'add': {'method': 'post'},
            'get': {'method': 'get', 'endpoint': '%(param_1)s', 'result_processor': order_get_processor},
            'list': {'method': 'get', 'endpoint': 'list'},
            }
        }
    }
```

Then when we call:
```
api.order.add(payload={...})  # post to http://apidomain.com/api-path/order will be called
api.order.get(12)  # get to http://apidomain.com/api-path/order/12 will be called
api.order.list()  # get to http://apidomain.com/api-path/order/list will be called
```

we can implement some processing functions for some endpoinds and pass them as result_processor param. For example: 
if some api is called by /user/get/10/ and returns such json:

```
{'user': 
    '10': {
      'first_name': 'John'
      'last_name': 'Smith'
    }
}
```

then we could implement user_get_processor as:

```
def user_get_processor(json_result, user_id):
    return json_result['user'][str(user_id)]
```

and then calling api.user.get(10) would result:

```
{
  'first_name': 'John'
  'last_name': 'Smith'
}
```


* Example:
```
from test_api import TestApiCaller, TestApiCallerError

api = TestApiCaller(access_token='asd13431452a88525229682745bf8d00043a')
api.order.add(payload={'test': 12})
order = api.order
order.get(10)
list = order.list()
```
