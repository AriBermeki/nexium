from .outbox import onEvent,emitEvent
from typing import Awaitable





def runjavascript(name, data, callback:Awaitable, required=False):
    if required:
        onEvent('call_javascript_space', callback)
    return emitEvent('call_javascript_space', {'key':name, 'args':data, 'required':required})
    

