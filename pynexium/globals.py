import asyncio
from typing import TYPE_CHECKING, Optional
from fastapi import  FastAPI
from socketio import AsyncServer
from uvicorn import Server



app: FastAPI
sio: AsyncServer
loop: Optional[asyncio.AbstractEventLoop] = None
server: Server