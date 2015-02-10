var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var path = require('path');
var redis = require("redis");


app.use(express.static(path.join(__dirname, 'static')));

server.listen(3004);


function addWorker(theKey, theReceiver) {
    console.log("starting listening on key", theKey);
    theReceiver.blpop(theKey, 0, function(err, data) {
      console.log('processing data on', theKey, data[1]);
      process.nextTick(function() {
          addWorker(theKey, theReceiver);
      });
    });
}


io.on('connection', function (socket) {
  var sender = redis.createClient();
  var id = socket.conn.id;
  var key = "ws." + id;
  console.log("connection from", id, key);

  addWorker(key, redis.createClient());

  socket.on('some kind of message', function (data) {
    console.log("Message from websocket: '" + data + "'");
    sender.rpush(key, data);
    //receiver.subscribe('ws.' + id);
    //sender.publish('ws.' + id, data)
  });

  socket.on('disconnect', function(){
    console.log('user disconnected');
  });
});

//receiver.on("message", function (channel, message) {
//    console.log("channel " + channel + ": " + message);
//    var sock = io.sockets.connected[channel.substring(3)];
//    if (sock) {
//        sock.emit("banana", "woop!");
//    } else {
//        console.log('user is disconnected?');
//        //shouldn't really be able to get here, but hey ho may as well make sure we clean up completely
//        receiver.unsubscribe(channel);
//    }
//});
