import uuid
from inspect import signature
import threading



class CallbackRegistryType:
    uuid_callback_map = {}
    callback_uuid_map = {}

    def register_event(self, callback):
        if callback is None:
            return None
        if callback in self.callback_uuid_map:
            return self.callback_uuid_map[callback]
        else:
            cb_uuid = callback.__name__
            self.uuid_callback_map[cb_uuid] = callback
            self.callback_uuid_map[callback] = cb_uuid
            return cb_uuid
        
    def make_callback(self, uuid, args):
        if uuid in self.uuid_callback_map:
            method = self.uuid_callback_map[uuid]
            param_length = len(signature(method).parameters)
            return method(*args[:param_length])
        else:
            # TODO: Return an error to the frontend
            return None

event = CallbackRegistryType()

