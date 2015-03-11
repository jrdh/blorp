var config = require('./config.json');
var redis = require("redis");
var io = require('socket.io').listen(config.http.port, config.http.host);
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
