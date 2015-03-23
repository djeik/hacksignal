$(document).ready(function(){
    var socket = io.connect(
        'http://' + document.domain + ':' + location.port + '/chat');

    socket.emit('auth', {
        username: token // a global variable provided by chat.html
    });

    socket.on('server message', function(msg) {
        $('#chatlog').append(
            '<p class="server-message">' + msg.data + '</p>');
    });

    socket.on('chat message', function(msg) {
        $('#chatlog').append(
            '<p class="message"><span class="author">' +
            msg.sender +
            '</span>: ' +
            msg.data +
            '</p>'
        );
    });

    console.log('registered socket event handler');

    $('#chatinput').submit(function(event) {
        socket.emit('chat message', {
            sender: token,
            data: $('#msg-content').val()
        });
        $("#msg-content").val("");
        return false;
    });

    console.log('registered click event handler');
});
