var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");
var sender = redis.createClient();
var receiver = redis.createClient();


app.use(express.static(path.join(__dirname, 'static')));

server.listen(3000);


io.on('connection', function (socket) {
    var id = socket.conn.id;
    var key = "ws." + id;
    console.log("connection from:", id, "key: ", key);
    receiver.subscribe(key);

    socket.on('some kind of message', function (data) {
        console.log("Message from websocket:", data);
        sender.publish(key, data)
    });

    socket.on('disconnect', function(){
        console.log('user disconnected');
        receiver.unsubscribe(channel);
    });
});


receiver.on("message", function (channel, message) {
    console.log("channel:", channel, "message:", message);
    var sock = io.sockets.connected[channel.substring(3)];
    if (sock) {
        sock.emit("banana", "woop!");
    } else {
        console.log('user is disconnected?');
        //shouldn't really be able to get here, but hey ho may as well make sure we clean up completely
        receiver.unsubscribe(channel);
    }
});
