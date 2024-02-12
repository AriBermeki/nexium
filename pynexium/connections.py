from socketio import ASGIApp, AsyncServer
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Any
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
import json
from . import background 
from .server_event import event
from . import globals 




class ConnectionManager:
    def __init__(self):
        globals.sio=self.sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
        self.sio_app = ASGIApp(socketio_server=self.sio, socketio_path='/hybrid/socket.io')
        self._protocol = {}

        self.init_socket()
        
    def init_socket(self):  
        @self.sio.on('connect')  
        async def connect(sid, environ):
            timestamp = datetime.now().isoformat()
            await self.sio.emit('protocol', {'protocol': 'system', 'exception': None, 'Date': timestamp}, room=sid)
            print(f'Connected {sid}')

        @self.sio.on('disconnect')  
        async def disconnect(sid):
            print(f'Disconnected {sid}')

        @self.sio.on('function_call')  
        async def protocol(sid, data:dict):
            try:
                func = data.get('func')
                args = data.get('args')
                if args is not None:
                    event.make_callback(uuid=func, args=[args])
                else:
                    event.make_callback(uuid=func, args=[])

            except json.JSONDecodeError as e:
                print(f'Error decoding JSON: {e}')



        @self.sio.on('function_return')  
        async def protocol_return(sid, data:dict):
            try:
                func = data.get('func')
                args = data.get('args')
                if args is not None:
                    result = event.make_callback(uuid=func, args=args)
                    await self.sio.emit('function_return', data={'return':result}, room=sid)
                else:
                   result = event.make_callback(uuid=func, args=[])
                   await self.sio.emit('function_return', data={'return':result}, room=sid)

            except json.JSONDecodeError as e:
                print(f'Error decoding JSON: {e}')
    
    
    def get_js_file(self, js_filename: str):
        folder_path = Path(__file__).parent / 'js'
        files = list(folder_path.rglob(js_filename))

        if files:
            file_path = files[0]
            return FileResponse(path=file_path, media_type='text/javascript')
        else:
            print(f'Die Datei {js_filename} wurde nicht gefunden.')
            return {"error": f"Datei {js_filename} nicht gefunden"}
    
    def add_api_routes(self, app:FastAPI):
        app.add_api_route("/nexium.js", endpoint=self.jspy)


    async def jspy(self):
        return self.get_js_file("nexium.js")




    def add_protocol(self, protocol, func):
        self._protocol[protocol] = func





connect = ConnectionManager()

def connection(app: FastAPI):
    globals.app = app
    app.mount('/hybrid/', connect.sio_app)
    connect.add_api_routes(app=app)
    app.add_middleware(
    CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_event_handler('startup', background.startup_handler)
    app.add_event_handler('shutdown', background.shutdown_handler)  

