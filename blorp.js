var redis = require("redis");
var io_middleware = require('socketio-wildcard')();

function App(name, settings, io) {
    this.name = name;
    this.io = io;
    this.io.use(io_middleware);
    this.settings = settings;

    this.keys = {
        control: 'blorp:' + this.name + ':control',
        messages: 'blorp:' + this.name + ':messages:',
        out: 'blorp:' + this.name + ':out'
    };
    this.messages = {disconnection: 'disconnection', message: 'message'};

    var self = this;
    this.io.on('connection', function(socket) {
        self.connectClient.apply(self, [socket]);
    });
}

App.prototype.send = function(websocketId, type, message) {
    this.sender.rpush(this.keys.messages + websocketId, JSON.stringify({'type': type, 'message': message}));
};

App.prototype.sendDisconnection = function(websocketId) {
    this.send(websocketId, this.messages.disconnection, {});
};

App.prototype.sendMessage = function(websocketId, message) {
    this.send(websocketId, this.messages.message, message);
};

App.prototype.sendControl = function(websocketId, action) {
    this.sender.rpush(this.keys.control, JSON.stringify({'action': action, 'websocketId': websocketId}));
};

App.prototype.connectClient = function(socket) {
    var websocketId = socket.conn.id;
    var self = this;

    //add a connection message to the control queue for this websocket
    this.sendControl(websocketId, 'connection');

    //listen for any messages from the websocket and forward them onto redis
    socket.on('*', function (message) {
        self.sendMessage(websocketId, {'event': message.data[0], 'data': message.data[1]});
    });

    //disconnect the client when they disconnect
    socket.on('disconnect', function(){
        self.disconnectClient(websocketId);
    });
};

App.prototype.disconnectClient = function(websocketId) {
    this.sendDisconnection(websocketId);
};

App.prototype.start = function() {
    var self = this;

    self.sender = redis.createClient(self.settings.port, self.settings.host);
    self.receiver = redis.createClient(self.settings.port, self.settings.host);

    self.sender.select(self.settings.database, function (senderErr, senderRes) {
        self.receiver.select(self.settings.database, function (receiverErr, receiverRes) {
            if (senderErr === null || receiverErr === null) {
                process.nextTick(function() {
                    self.listen();
                });
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
            var sock = self.io.connected[websocketId];
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
