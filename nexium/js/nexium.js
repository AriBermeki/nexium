class NexiumManager {
  constructor() {
    this._host = window.location.origin;
    this.socket = null;
    this.connected = false;
    this.receive = new Map(); // Verbesserte Variablennamen: 'receive' statt 'resive'
    this.registeredFunctions = new Map();
    this.connect();
  }
  set_host(hostname) {
    this._host = hostname
  }
  connect() {
    if (!this.connected) {
      this.socket = io(this._host, { path: "/hybrid/socket.io", transports: ['websocket', 'polling'] });

      this.socket.on('connect', () => {
        console.log('Connected to server');
        this.connected = true;
      });


      this.socket.on('updated_shared_value', (d) => {
        console.log('updated_shared_value: ', d);
      
      });


      this.socket.on('response_space1', (data) => {
        setTimeout(() => {
          this.receive.set(data.key, data.result_space1); // Vereinfachte Logik zum Setzen des Ergebnisses
        }, 10);
      });

      this.socket.on('call_javascript_space', (data) => {
        
        setTimeout(() => {
          if (this.registeredFunctions.has(data.key)) {
            let argsArray = data.args || []; // Ensure args is defined
            let result = this.make_callback(data.key, argsArray, data.required);
            this.socket.emit('call_javascript_space', { result: result });
          } else {
            this.socket.emit('call_javascript_space', { error: 'this function is not registered on the client side' });
          }
        }, 500); // Changed from 0.5 milliseconds to 500 milliseconds
      });
      

      this.socket.on('disconnect', () => {
        console.log('Disconnected from server');
        this.connected = false;
      });

      this.socket.on('error', (error) => {
        console.error('Socket error:', error);
      });
    }
  }

  disconnect() {
    if (this.connected && this.socket) {
      this.socket.disconnect();
      this.connected = false;
      console.log('Disconnected from server');
    }
  }

  Python(func, data, callback) {
    if (this.connected && this.socket) {
      this.socket.emit('function_space_1', { func: func, args: [data] });
    } else {
      console.error('Socket is not connected');
      return; // Added return statement to exit the function if socket is not connected
    }
    setTimeout(() => {
      let responseData = this.receive.get(func); // Verbesserte Variablenbezeichnung: 'receive' statt 'resive'
      callback(responseData);
    }, 25);
  }

  PythonTimer(func, data, callback, timeout) {
    if (this.connected && this.socket) {
      this.socket.emit('function_space_1', { func: func, args: [data], protocol:'write'});
    } else {
      console.error('Socket is not connected');
      return; // Added return statement to exit the function if socket is not connected
    }
    setInterval(() => {
      this.socket.emit('function_space_1', { func: func, args: [data], protocol:'read'});
      let responseData = this.receive.get(func); 
      callback(responseData);
    }, timeout);
  }

  expose(name, func) {
    this.registeredFunctions.set(name, func);
  }

  make_callback(name, params, required) {
    const func = this.registeredFunctions.get(name);
    if (func) {
      if(required){
        return func(...params)
      } else {
        func(...params)
      }
       // Rückgabewert hinzugefügt, um das Ergebnis der Funktion zurückzugeben
    } else {
      console.error(`Function '${name}' is not registered.`);
    }
  }
}

nexium = new NexiumManager();
