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
//for sending messages about connecting and disconnecting websocket clients
var connections = redis.createClient();
//for receiving messages that are meant to go to all clients
var all_receiver = redis.createClient();


app.use(express.static(path.join(__dirname, 'static')));

server.listen(3002);

io.on('connection', function (socket) {
    var id = socket.conn.id;
    var toKey = "ws:to:" + id;
    var backKey = "ws:back:" + id;

    connections.rpush('ws:connections', id);

    socket.on('*', function (message) {
        var event = message.data[0];
        var data = message.data[1];
        var key = toKey + ':' + event;
        if (typeof data === 'object') {
            data = JSON.stringify(data);
        }
        sender.publish(key, data);
    });

    socket.on('disconnect', function(){
        connections.rpush('ws:disconnections', id);
    });
});

receiver.on("pmessage", function (pattern, channel, message) {
    var sock = io.sockets.connected[channel.substring(8)];
    message = JSON.parse(message);
    if (sock) {
        sock.emit(message['event'], message['data']);
    } else {
        connections.rpush('ws:disconnections', id);
    }
});

all_receiver.on("message", function (channel, message) {
    message = JSON.parse(message);
    io.emit(message['event'], message['data']);
});

receiver.psubscribe('ws:back:*');
all_receiver.subscribe('ws:all');
