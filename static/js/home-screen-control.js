$(document).ready(function(){
    canvas = document.getElementById("game-canvas");
    ctx = canvas.getContext("2d");
    canvas.width = canvas.clientWidth;
    // For some reason this was buggy when I tried just saying canvas.height = canvas.clientHeight
    // But calculating the height from the width seems to work :)
    canvas.height = canvas.clientWidth * 1080 / 1920;

    // update game every 10 milliseconds
    timestep = 20;
    // keep track of current time (in milliseconds), current score, and highest score
    time = 0;
    score = 0;
    highest_score = 0;
    x = 100;
    // direction of movement, either "left" or "right" (or neither???)
    direction = "";

    // Initialize the socket and receive data from server
    socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    socket.on('new_test_data', function(msg) {
        direction = msg.direction_to_move;
    });

    terrain = new Image();
    terrain.src = "/static/images/terrain.png";

    puffy = [];
    for (frame = 1; frame <= 12; frame++) {
        puffy[frame - 1] = new Image();
        puffy[frame - 1].src = "/static/images/smoothbrain/frame" + frame.toString() + ".png";
    }

    sparkle = []
    for (frame = 1; frame <= 16; frame++) {
        sparkle[frame - 1] = new Image();
        sparkle[frame - 1].src = "/static/images/sparklejuice/frame" + frame.toString() + ".png";
    }

    window.requestAnimationFrame(update);
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


function update(timestamp) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    window.requestAnimationFrame(update);

    if (direction == "left") {
        x -= 1;
    } else if (direction == "right") {
        x += 1;
    }

    ctx.drawImage(terrain, 0, 0, canvas.width, canvas.height);
    // smoothbrain.gif has twelve frames that each last for 70 milliseconds
    ctx.drawImage(puffy[Math.floor(timestamp / 70) % 12], x, canvas.height - canvas.width / 10, canvas.width / 10, canvas.width / 10);
    // sparklejuice.gif has sixteen frames that each last for 70 milliseconds
    ctx.drawImage(sparkle[Math.floor(timestamp / 70) % 16], 100, 100, canvas.width / 10, canvas.width / 10);
}
