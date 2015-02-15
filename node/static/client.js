$(document).ready(function() {
    var theButton = $('#theButton');
    var objectButton = $('#objectButton');
    var theTextBox = $('#theTextBox');
    var socket = io();

    socket.on('something', function(msg){
        console.log('message: ' + msg);
    });

    theButton.click(function() {
        var text = theTextBox.val();
        if (!text) {
            console.log("Not sending a blank message, fool!");
            return;
        }
        socket.emit('string', text);
    });

    objectButton.click(function() {
        socket.emit('json', {'beans': true, 'lemons': 5});
    });
});
