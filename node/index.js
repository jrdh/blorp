var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");

//for sending messages received from websockets to redis
var sender = redis.createClient();
//for receiving messages from redis so that they can then be sent to the websocket(s)
var receiver = redis.createClient();
//for sending messages about connecting and disconnecting websocket clients
var connections = redis.createClient();


app.use(express.static(path.join(__dirname, 'static')));

server.listen(3000);

io.on('connection', function (socket) {
    var id = socket.conn.id;
    var toKey = "ws:to:" + id;
    var backKey = "ws:back:" + id;

    connections.rpush('ws:connections', id);

    socket.on('some kind of message', function (data) {
        sender.publish(toKey, JSON.stringify(data))
    });

    socket.on('disconnect', function(){
        connections.rpush('ws:disconnections', id);
    });
});

receiver.on("pmessage", function (pattern, channel, message) {
    var sock = io.sockets.connected[channel.substring(8)];
    if (sock) {
        sock.emit("banana", message);
    } else {
        connections.rpush('ws:disconnections', id);
    }
});

receiver.psubscribe('ws:back:*');
