var configJson = require('./config.json');
var _ = require('underscore');

var apps = {};
_.each(configJson.blorp.apps, function(settings, appName) {
    apps[appName] = _.extend({}, configJson.blorp.defaultRedis, settings);
});

var config = {
    http: {
        port: configJson.http.port || 3003,
        host: configJson.http.host || "localhost"
    },
    blorp: {
        apps: apps
    }
};

module.exports = config;
