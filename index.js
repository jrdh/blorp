var config = require('./config');
var _ = require('underscore');
var app = require('express')();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var io_middleware = require('socketio-wildcard')();
var blorp = require('./blorp');

io.use(io_middleware);

var apps = {};

_.each(config.blorp.apps, function(settings, appName) {
    apps[appName] = new blorp.App(appName, settings, io.of(appName));
    apps[appName].start();
    console.log("Starting listening for app " + appName);
});

server.listen(config.http.port, config.http.host);
console.log("Listening for socket.io connections on " + config.http.host + ":" + config.http.port);
