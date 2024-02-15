import multiprocessing
import ctypes
import time
import asyncio
from typing import Any, Dict
from .outbox import onEvent, emitEvent
import uvicorn
from fastapi import FastAPI
from . import background
import inspect
from inspect import signature
import random





class CallbackManager:
    def __init__(self):
        
        self.key_callback_map = {}
        self.callback_key_map = {}
        self.initial_value = 0
        self.shared_cmd = multiprocessing.Value(ctypes.c_int, self.initial_value)  # Erstellung eines gemeinsam genutzten Werts
        self.shared_x = multiprocessing.Value(ctypes.c_double, self.initial_value)
        self.shared_y = multiprocessing.Value(ctypes.c_double, self.initial_value)
        self.strQueue = multiprocessing.Queue(10)
        self.lock = multiprocessing.Lock()  # Lock erstellen
        onEvent('function_space_1', self.invoke_callbacks)





    def run_in_progress(self, app):
        processes = [
            multiprocessing.Process(target=self.increment, args= (self.shared_cmd, self.shared_x,self.shared_y, self.strQueue, self.lock)),
            multiprocessing.Process(target=self.decrement, args=(self.shared_cmd,self.shared_x,self.shared_y, self.strQueue, self.lock))
        ]
        for process in processes:
            process.start()
        uvicorn.run(app)
        for process in processes:
            process.join()







    def increment(self, cmd, x, y, cQueue, lock):
        while True:
            with lock:
                x.value += 1  # Inkrementieren des Wertes
                y.value = random.randint(a=0,b=100)
                print("P1: ", x.value)
            time.sleep(1)






    def decrement(self, cmd, x, y, cQueue,  lock):
        msg = ["msg_1", "msg_2"]
        while True:
            with lock:
                if (cmd.value == 0):
                    #cQueue.put(msg[0])
                    print("Decremented", msg[0])
                else:
                    #cQueue.put(msg[1])
                    print("Decremented", msg[1])
            time.sleep(3)








    def register_callback(self, callback):
        if callback in self.callback_key_map:
            return self.callback_key_map[callback]
        else:
            cb_uuid = callback.__name__
            self.key_callback_map[cb_uuid] = callback
            self.callback_key_map[callback] = cb_uuid
            return cb_uuid
        









    async def invoke_callbacks(self, data: Dict[str, Any]):
        sid = data.get('sid')
        data_ = data.get('data')
        func = data_['func']
        args = data_['args']
        protocol = data_['protocol']

        
        if protocol == 'write':
            with self.lock:
                self.shared_cmd.value = args[0]  # Setzen des Wertes

            if func in self.key_callback_map:
                method = self.key_callback_map[func]
                param_length = len(inspect.signature(method).parameters)
                with self.lock:
                    shared_cmd_copy = self.shared_cmd.value
                if param_length > 1:
                    result = method(*args[:param_length - 1], shared_cmd_copy)
                    self.updated_shared_cmd = self.shared_cmd.value 
                    emitEvent('response_space1', {'result_space1': result, 'key': func}, target_id=sid)
                else:
                    result = method(shared_cmd_copy)
                    self.updated_shared_cmd = self.shared_cmd.value 
                    emitEvent('response_space1', {'result_space1': result, 'key': func}, target_id=sid)
                
        elif protocol == 'read':

            data = {
                'data':[
                { 'x': '1991', 'y': 3 },
                { 'x': '1992', 'y': 4 },
                { 'x': '1993', 'y': 3.5 },
                { 'x': '1994', 'y': 5 },
                { 'x': '1995', 'y': 4.9 },
                { 'x': '1996', 'y': 6 },
                { 'x': '1997', 'y': 7 },
                { 'x': '1998', 'y': 9 },
                { 'x': '1999', 'y': 13 },
            ],
            'message':{'output_protocol':'hallo'}
            }
            kommando_dict = {'x':self.shared_x.value, 'y':self.shared_y.value}
            kommando_list = [self.shared_x.value, self.shared_y.value]
            emitEvent('response_space1', {'result_space1': data, 'key': func}, target_id=sid)
            #kommando.update()



eventvalue = CallbackManager()
#background.background_task(eventvalue.uberwachung, [])


def expose_value(callback):
    def decorator():
        if callback:
            return eventvalue.register_callback(callback)
        return callback
    return decorator


def run_value(app: FastAPI) -> FastAPI:
    return eventvalue.run_in_progress(app)
