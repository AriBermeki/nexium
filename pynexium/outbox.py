from __future__ import annotations
from . import globals
from . import background
import json
import asyncio
from collections import deque
from typing import Any, DefaultDict, Deque, Dict, Optional, Tuple
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager

ClientId = str
ElementId = int
MessageType = str
Message = Tuple[Optional[ClientId], MessageType, Any]  # Corrected to make target_id optional

# update_queue: DefaultDict[ClientId, Dict[ElementId, Optional[Element]]] = defaultdict(dict)
message_queue: Deque[Message] = deque()
message_dequeue: Deque[Tuple[MessageType, Any, Optional[str]]] = deque()  # Corrected to match message structure

def emitEvent(event: MessageType, data: Any, target_id: Optional[ClientId] = None) -> None:
    message_queue.append((target_id, event, data))

def onEvent(event: MessageType, handler, namespace: Optional[str]=None) -> None:
    async def handle_message(sid, data):


        await handler(sid, data)

    message_dequeue.append((event, handle_message, namespace))

async def _emit(event: MessageType, data: Any, target_id: Optional[ClientId] = None) -> None:
    await globals.sio.emit(event, data, room=target_id)

async def _on(event: MessageType, handler, namespace: Optional[str] = None) -> None:
    @globals.sio.on(event, namespace)
    async def wrapper(*args, **kwargs):
        await handler(*args, **kwargs)



async def loop() -> None:
    while True:
        try:
            if message_queue or message_dequeue:
                coros1 = [_emit(event, data, target_id) for target_id, event, data in message_queue]
                coros2 = [_on(event, handler, namespace) for event, handler, namespace in message_dequeue]
                message_queue.clear()
                message_dequeue.clear()  # Clear dequeue after processing

                for coro in coros1:
                    try:
                        await coro
                    except Exception as e:
                        print(e)
                
                for coro in coros2:
                    try:
                        await coro
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(0.0001)

background.background_task(loop, [])