$(document).ready(function() {
    var theButton = $('#theButton');
    var socket = io();

    socket.on('banana', function(msg){
        console.log('message: ' + msg);
    });

    theButton.click(function() {
        socket.emit('some kind of message', 'lemonade!');
    });
});
