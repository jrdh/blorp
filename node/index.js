var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");
var io_middleware = require('socketio-wildcard')();
var blorp = require('./blorp');

io.use(io_middleware);


var redis = redis.createClient();
var namespaces = {};


app.use(express.static(path.join(__dirname, 'static')));
server.listen(3003);


redis.smembers('blorp:namespaces', function(err, members) {
    for (index in members) {
        namespace = members[index];
        namespaces[namespace] = new blorp(namespace, io);
        process.nextTick(function() {
            namespaces[namespace].listen();
        });
    }
});
