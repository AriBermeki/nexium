let Nexium = {};
Nexium._protocol_table = new Map();
Nexium.waitingCallbacks = new Map();
Nexium.messageQueue = [];
Nexium.messageDequeue = [];
Nexium.socket_id = null;
Nexium._MAX_ID = 0xFFFFFFFF; 
Nexium._disconnect_reason = '';
Nexium._socket_events = []; // Initialisierung der _socket_events-Liste
Nexium.socket = io("ws://localhost:8000", { path: "/hybrid/socket.io", transports: ['websocket', 'polling'] });

Nexium.SocketListeners = function() {
    Nexium.socket.on('connect', () => console.log(`${Nexium.socket.id} - Connected to server`));
    
    Nexium.socket.on('disconnect', () => {
        for (let fn of Nexium._socket_events) {
            try {
                fn();
            } catch (e) {
                console.log(e);
            }
        }
        Nexium.socket_id = null;
    });
    
    Nexium.socket.on('error', (error) => console.error('Socket error:', error));
};


Nexium.add_close_event = (func) => {
    Nexium._socket_events.push(func);
};

Nexium.clear_close_event = () => {
    Nexium._socket_events.length = 0;
};

Nexium.timeoutPromise = (wake_sec) => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            reject("A timeout has occurred");
        }, Math.floor(wake_sec*1000));
    });
};

Nexium.emitEvent = (event, data, targetId = null)=>{
    Nexium.messageQueue.push([targetId, event, data]);
}

Nexium.onEvent = (event, handler, namespace = null) => {
    Nexium.messageDequeue.push({ event, handler, namespace });
};

Nexium.sendSocketIORequest=(socket, event, data)=>{
    return new Promise((resolve, reject) => {
      socket.emit(event, data, (response) => {
        if (response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response.data);
        }
      });
    });
  }
  

Nexium.callPy = (key, args)=>{
    this.emitEvent('function_call', { func: key, args: args });
},

Nexium.callPyreturn = (key, args, callback)=>{
    this.emitEvent('function_return', { func: key, args: args });
    this.onEvent('function_return', d => {
        callback(d['return']);
    });
},

Nexium._emit = async (event, messageData, targetId = null) => {
    // Implement logic to send a message
    if (Nexium.socket && Nexium.socket.connected) {
        Nexium.socket.emit(event, messageData);
    } else {
        Nexium.emitEvent(event, messageData, targetId);
    }
};

Nexium._on = async (event, messageHandler, namespace = null) => {
    // Implement logic to receive a message
    Nexium.socket.on(event, messageHandler);
};
Nexium.throttle = (callback, time, leading, trailing, id)=>{
    if (time <= 0) {
      // execute callback immediately and return
      callback();
      return;
    }
    if (Nexium.waitingCallbacks.has(id)) {
      if (trailing) {
        // update trailing callback
        Nexium.waitingCallbacks.set(id, callback);
      }
    } else {
      if (leading) {
        // execute leading callback and set timeout to block more leading callbacks
        callback();
        Nexium.waitingCallbacks.set(id, null);
      }
      else if (trailing) {
        // set trailing callback and set timeout to execute it
        Nexium.waitingCallbacks.set(id, callback);
      }
      if (leading || trailing) {
        // set timeout to remove block and to execute trailing callback
        setTimeout(() => {
          const trailingCallback = Nexium.waitingCallbacks.get(id);
          if (trailingCallback) trailingCallback();
          Nexium.waitingCallbacks.delete(id)
        }, 1000 * time);
      }
    }
}
Nexium.loop = async () => {
    while (true) {
        try {
            if (Nexium.messageQueue.length > 0) {
                const coros1 = Nexium.messageQueue.map(([targetId, event, data]) => Nexium._emit(event, data, targetId));
                Nexium.messageQueue.length = 0;

                await Promise.all(coros1);
            }

            if (Nexium.messageDequeue.length > 0) {
                for (const { event, handler, namespace } of Nexium.messageDequeue) {
                    await Nexium._on(event, handler, namespace);
                }
                Nexium.messageDequeue.length = 0;
            }
        } catch (e) {
            console.error(e);
        } finally {
            await new Promise(resolve => setTimeout(resolve, 0.0001)); // Short pause to relieve CPU
        }
    }
};

Nexium.SocketListeners();
Nexium.loop();


if(typeof require !== 'undefined'){
    // Avoid name collisions when using Electron, so jQuery etc work normally
    window.nodeRequire = require;
    delete window.require;
    delete window.exports;
    delete window.module;
}
