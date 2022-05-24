$(document).ready(function(){
    // Get current x position
    let x = $("#avatar").css("left");
    x = parseInt(x.slice(0, -2));

    // Initialize the socket.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    // This function makes sure our avatar does not exceed the bounds on the window, lengthwise
    function clamp(val) {
        var max = $(window).width()*(0.9 - 0.048);
        var min = $(window).width()*(0.1 - 0.016);
        return Math.min(Math.max(val, min), max);
    }

    // Receive details from server
    socket.on('new_data', function(msg) {
        // Update the direction of the avatar
        if (msg.direction_to_move == 'left') {
            x = clamp(x - $(window).width()*0.032);
        }
        else if (msg.direction_to_move == 'right') {
            x = clamp(x + $(window).width()*0.32);
        }
        $("#avatar").css("left", x);
    });
});

// Sets the play button to on and triggers the start_streaming function in app.py
function start_playing() {
    var color =  $("#stream-button").css("background-color");
    if (color != 'skyblue') {
        $("#stream-button").css("background-color", 'skyblue');
    }
    $.getJSON('/start_streaming',
        function(data) {
    });
}

// Resets the play button to on and triggers the stop_streaming function in app.py
function stop_playing() {
    $("#stream-button").css("background-color", '#4c7bea');
    $.getJSON('/stop_recording',
        function(data) {
    });
}
