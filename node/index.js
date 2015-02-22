var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");
var io_middleware = require('socketio-wildcard')();


io.use(io_middleware);

//for sending messages received from websockets to redis
var sender = redis.createClient();
//for receiving messages from redis so that they can then be sent to the websocket(s)
var receiver = redis.createClient();


//queue names
var queues = {
    to: 'blorp:to',
    back: 'blorp:back',
};

//message types
var types = {
    connection: 'connection',
    disconnection: 'disconnection',
    message: 'message'
};


app.use(express.static(path.join(__dirname, 'static')));
server.listen(3003);


function connectClient(websocketId) {
    sender.rpush(queues.to, JSON.stringify({'type': types.connection, 'websocketId': websocketId}));
};

function disconnectClient(websocketId) {
    sender.rpush(queues.to, JSON.stringify({'type': types.disconnection, 'websocketId': websocketId}));
};

function sendMessage(websocketId, event, data) {
    if (typeof data === 'object') {
        data = JSON.stringify(data);
    }
    sender.rpush(queues.to, JSON.stringify({'type': types.message, 'event': event, 'data': data, 'websocketId': websocketId}));
};

io.on('connection', function (socket) {
    var id = socket.conn.id;

    connectClient(id);

    socket.on('*', function (message) {
        sendMessage(id, message.data[0], message.data[1]);
    });

    socket.on('disconnect', function(){
        disconnectClient(id);
    });
});

function listen() {
    receiver.blpop(queues.back, 0, function(err, data) {
        var message = JSON.parse(data[1]);
        var id = message['id'];
        if (id) {
            var sock = io.sockets.connected[id];
            if (sock) {
                sock.emit(message['event'], message['data']);
            } else {
                disconnectClient(id);
            }
        } else {
            io.emit(message['event'], message['data']);
        }
        process.nextTick(function() {
            listen();
        });
    });
};


listen();