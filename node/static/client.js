$(document).ready(function() {
    var theButton = $('#theButton');
    var objectButton = $('#objectButton');
    var theTextBox = $('#theTextBox');
    var socket = io();

    socket.on('banana', function(msg){
        console.log('message: ' + msg);
    });

    theButton.click(function() {
        var text = theTextBox.val();
        if (!text) {
            console.log("Not sending a blank message, fool!");
            return;
        }
        socket.emit('inputText', text);
    });

    objectButton.click(function() {
        socket.emit('randomJson', {'beans': true, 'lemons': 5});
    });
});
