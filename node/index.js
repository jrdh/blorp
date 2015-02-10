var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");
var sender = redis.createClient();
var receiver = redis.createClient();


app.use(express.static(path.join(__dirname, 'static')));

server.listen(4005);


io.on('connection', function (socket) {
    var id = socket.conn.id;
    var toKey = "ws.to." + id;
    var backKey = "ws.back." + id;
    console.log("connection from:", id, "toKey: ", toKey, "backKey: ", backKey);
    receiver.subscribe(backKey);

    socket.on('some kind of message', function (data) {
        console.log("Message from websocket:", data);
        sender.publish(toKey, data)
    });

    socket.on('disconnect', function(){
        console.log('user disconnected');
        receiver.unsubscribe(channel);
    });
});


receiver.on("message", function (channel, message) {
    console.log("channel:", channel, "message:", message);
    var sock = io.sockets.connected[channel.substring(8)];
    if (sock) {
        sock.emit("banana", "woop!");
    } else {
        console.log('user is disconnected?');
        //shouldn't really be able to get here, but hey ho may as well make sure we clean up completely
        receiver.unsubscribe(channel);
    }
});
