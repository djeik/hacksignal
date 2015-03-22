$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    console.log('connected');
    socket.on('my response', function(msg) {
        $('#chatlog').append('<p>Received: ' + msg.data + '</p>');
    });

    console.log('registered socket event handler');
    $('#submit-button').click(function(event) {
        socket.emit('my event', {data: $('#msg-content').val()});
        return false;
    });

    console.log('registered click event handler');
});
