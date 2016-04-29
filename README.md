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

```
from test_api import TestApiCaller, TestApiCallerError

api = TestApiCaller(access_token='asd13431452a88525229682745bf8d00043a')
api.order.add(payload={'test': 12})
order = api.order
order.get(10)
list = order.list()
```
