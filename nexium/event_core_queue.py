import multiprocessing
import time
import inspect
from typing import Any, Dict, Optional,Callable
from .outbox import onEvent, emitEvent
import uvicorn
from fastapi import FastAPI

class CallbackManager:
    def __init__(self):
        self.key_callback_map = {}
        self.callback_key_map = {}
        self.ctx = multiprocessing.get_context('spawn')
        self.shared_queue = self.ctx.Queue()
        onEvent('function_space_1', self.invoke_callbacks)

    def run_in_progress(self, app: FastAPI):
        process1 = self.ctx.Process(target=self.increment, args=(self.shared_queue,))
        process2 = self.ctx.Process(target=self.decrement, args=(self.shared_queue,))
        process1.start()
        process2.start()
        uvicorn.run(app)
        process1.join()
        process2.join()

    def increment(self, queue: multiprocessing.Queue):
        while True:
            value = queue.get()
            value += 1
            print("Incremented", value)
            queue.put(value)
            time.sleep(1)

    def decrement(self, queue: multiprocessing.Queue):
        while True:
            value = queue.get()
            value -= 1
            print("Decremented", value)
            queue.put(value)
            time.sleep(3)

    def register_callback(self, callback: Callable[..., Any]) -> Optional[str]:
        cb_uuid = callback.__name__
        self.key_callback_map[cb_uuid] = callback
        self.callback_key_map[callback] = cb_uuid
        return cb_uuid

    async def invoke_callbacks(self, data: Dict[str, Any]):
        print(data)
        sid = data.get('sid')
        data_ = data.get('data')
        func = data_['func']
        args = data_['args']

        self.shared_queue.put(args[0])

        if func in self.key_callback_map:
            method = self.key_callback_map[func]
            param_length = len(inspect.signature(method).parameters)
            result = method(*args[:param_length - 1], self.shared_queue.get()) if param_length > 1 else method(self.shared_queue.get())
            print('response_space1:', result)
            emitEvent('response_space1', {'result_space1': result, 'key': func}, target_id=sid)

eventqueue = CallbackManager()

def expose_queue(callback):
    def decorator():
        if callback:
            return eventqueue.register_callback(callback)
        return callback
    return decorator

def run_queue(app: FastAPI) -> FastAPI:
    return eventqueue.run_in_progress(app)
