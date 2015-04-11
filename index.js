var config = require('./config.json');
var redis = require("redis");
var app = require('express')();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var io_middleware = require('socketio-wildcard')();
var blorp = require('./blorp');

io.use(io_middleware);

var redis = redis.createClient(config.redis.port, config.redis.host);
var namespaces = {};

redis.smembers('blorp:namespaces', function(err, members) {
    for (index in members) {
        namespace = members[index];
        namespaces[namespace] = new blorp(namespace, io);
        process.nextTick(function() {
            namespaces[namespace].listen();
        });
    }
});

server.listen(config.http.port, config.http.host);
