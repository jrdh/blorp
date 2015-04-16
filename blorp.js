var config = require('./config.json');
var redis = require("redis");

function BlorpApp(namespace, io) {
    this.namespace = namespace;
    this.io = io;

    this.sender = redis.createClient(config.redis.port, config.redis.host);
    this.receiver = redis.createClient(config.redis.port, config.redis.host);

    this.queues = {
        queues: 'blorp:' + this.namespace + ':queues:',
        back: 'blorp:' + this.namespace + ':out',
        instances: 'blorp:' + this.namespace + ':instances'
    };
    this.types = {connection: 'connection', disconnection: 'disconnection', message: 'message'};
    this.instanceMap = {};

    var self = this;
    this.io.on('connection', function (socket) {
        var id = socket.conn.id;

        self.connectClient(id);

        socket.on('*', function (message) {
            self.sendMessage(id, message.data[0], message.data[1]);
        });

        socket.on('disconnect', function(){
            self.disconnectClient(id);
        });
    });
}

BlorpApp.prototype.getQueue = function(websocketId) {
    return this.queues.queues + this.instanceMap[websocketId];
};

BlorpApp.prototype.connectClient = function(websocketId) {
    var self = this;
    this.sender.srandmember(this.queues.instances, function(err, data) {
        instance_id = data;
        if (instance_id) {
            self.instanceMap[websocketId] = instance_id;
            self.sender.rpush(self.getQueue(websocketId), JSON.stringify({'type': self.types.connection, 'websocketId': websocketId}));
        } else {
            console.log("No instances are available! :(");
        }
    });
};

BlorpApp.prototype.disconnectClient = function(websocketId) {
    if (websocketId in this.instanceMap) {
        this.sender.rpush(this.getQueue(websocketId), JSON.stringify({'type': this.types.disconnection, 'websocketId': websocketId}));
        delete this.instanceMap[websocketId];
    }
};

BlorpApp.prototype.sendMessage = function(websocketId, event, data) {
    if (typeof data === 'object') {
        data = JSON.stringify(data);
    }
    this.sender.rpush(this.getQueue(websocketId), JSON.stringify({'type': this.types.message, 'event': event, 'data': data, 'websocketId': websocketId}));
};


BlorpApp.prototype.listen = function() {
    var self = this;
    this.receiver.blpop(this.queues.back, 0, function(err, data) {
        var message = JSON.parse(data[1]);
        var id = message['id'];
        if (id) {
            var sock = self.io.sockets.connected[id];
            if (sock) {
                sock.emit(message['event'], message['data']);
            } else {
                self.disconnectClient(id);
            }
        } else {
            self.io.emit(message['event'], message['data']);
        }
        process.nextTick(function() {
            self.listen();
        });
    });
};

module.exports = BlorpApp;
