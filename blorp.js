var redis = require("redis");

function App(name, settings, io) {
    this.name = name;
    this.io = io;
    this.settings = settings;

    this.keys = {
        websockets: 'blorp:' + this.name + ':websockets',
        messages: 'blorp:' + this.name + ':messages:',
        out: 'blorp:' + this.name + ':out'
    };
    this.messages = {connection: 'connection', disconnection: 'disconnection', message: 'message'};

    this.io.on('connection', this.onClientConnection);
}

App.prototype.send = function(websocketId, type, message) {
    var queue = this.keys.messages + websocketId;
    //ensure required attributes of message
    message['type'] = type;
    message['websocketId'] = websocketId;
    this.sender.rpush(queue, JSON.stringify(message));
};

App.prototype.sendConnection = function(websocketId) {
    this.send(websocketId, this.messages.connection, {});
};

App.prototype.sendDisonnection = function(websocketId) {
    this.send(websocketId, this.messages.disconnection, {});
};

App.prototype.sendMessage = function(websocketId, message) {
    this.send(websocketId, this.messages.message, message);
};

App.prototype.onClientConnection = function(socket) {
    this.connectClient(socket.conn.id);
};

App.prototype.connectClient = function(websocketId) {
    var self = this;

    //add the websocket to the websockets zset
    this.sender.zadd(this.keys.websockets, -1, websocketId, function(err, result) {
        if (err !== null) {
            //TODO: something with errors
        }
    });

    //push a connection message to this websocket's messages queue
    this.sendConnection(websocketId);

    //listen for any messages from the websocket and forward them onto redis
    socket.on('*', function (message) {
        self.forwardMessage(websocketId, message.data[0], message.data[1]);
    });

    //disconnect the client when they disconnect
    socket.on('disconnect', function(){
        self.disconnectClient(websocketId);
    });
};

App.prototype.disconnectClient = function(websocketId) {
    var self = this;
    this.sender.zrem(this.keys.websockets, websocketId, function(err, result) {
        if (err === null && result == 1) {
            self.sendDisonnection(websocketId);
        } else {
            //TODO: something with errors
        }
    });
};

App.prototype.forwardMessage = function(websocketId, event, data) {
    self.sendMessage(websocketId, {'event': event, 'data': data});
};

App.prototype.start = function() {
    var self = this;

    self.sender = redis.createClient(self.settings.port, self.settings.host);
    self.receiver = redis.createClient(self.settings.port, self.settings.host);

    self.sender.select(self.settings.database, function (senderErr, senderRes) {
        self.receiver.select(self.settings.database, function (receiverErr, receiverRes) {
            if (senderErr === null || receiverErr === null) {
                self.listen();
            } else {
                //TODO: something with errors
            }
        });
    });
};

App.prototype.listen = function() {
    var self = this;
    this.receiver.blpop(this.keys.out, 0, function(err, data) {
        var message = JSON.parse(data[1]);
        var websocketId = message['id'];
        if (websocketId) {
            var sock = self.io.sockets.connected[websocketId];
            if (sock) {
                sock.emit(message['event'], message['data']);
            } else {
                self.disconnectClient(websocketId);
            }
        } else {
            self.io.emit(message['event'], message['data']);
        }
        process.nextTick(function() {
            self.listen();
        });
    });
};

module.exports = {App: App};
