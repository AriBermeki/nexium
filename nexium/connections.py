from socketio import ASGIApp, AsyncServer
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Any
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
import json
from . import background 
from . import globals 




class ConnectionManager:
    def __init__(self):
        globals.sio=self.sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*', json=json)
        self.sio_app = ASGIApp(socketio_server=self.sio, socketio_path='/hybrid/socket.io')
        self._protocol = {}

        self.init_socket()
        
    def init_socket(self):  
        @self.sio.on('connect')  
        async def connect(sid, environ):
            print(f'Connected {sid}')

        @self.sio.on('disconnect')  
        async def disconnect(sid):
            print(f'/Disconnected {sid}')
    
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
        app.add_api_route("/nexium.js", endpoint=self.nexium_js)

    async def nexium_js(self):
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



