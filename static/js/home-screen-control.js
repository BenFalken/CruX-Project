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
    // direction of movement, either "left" or "right" (or neither???)
    predicted_direction = "";
    actual_direction = "";

    // Initialize the socket and receive data from server
    socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    socket.on('new_test_data', function(msg) {
        direction = msg.direction_to_move;
    });

    terrain = new Image();
    terrain.src = "/static/images/terrain.png";

    puffy = new SmoothBrain();

    sparkle = []
    for (frame = 1; frame <= 16; frame++) {
        sparkle[frame - 1] = new Image();
        sparkle[frame - 1].src = "/static/images/sparklejuice/frame" + frame.toString() + ".png";
    }

    window.requestAnimationFrame(update);
});

class SmoothBrain {
    constructor() {
        this.frames = [];
        for (var i = 1; i <= 12; i++) {
            this.frames[i - 1] = new Image();
            this.frames[i - 1].src = "/static/images/smoothbrain/frame" + i.toString() + ".png";
        }
        this.x = .5;
        this.y = 0;
    }
    draw(timestamp) {
        // time should be given in milliseconds
        var frame_number = Math.floor(timestamp / 70) % 12;
        // calculate the canvas coordinates
        var image_width = canvas.width / 8;
        var image_height = image_width;
        var canvas_x_coord = canvas.width  * this.x - image_width / 2;
        var canvas_y_coord = canvas.height * (1 - this.y) - image_height;
        // smoothbrain.gif has twelve frames that each last for 70 milliseconds
        ctx.drawImage(this.frames[frame_number], canvas_x_coord, canvas_y_coord, image_width, image_height);
    }
}

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

window.addEventListener("keydown", event => {
    if (event.keyCode == 37) {
        actual_direction = "left";
    } else if (event.keyCode == 39) {
        actual_direction = "right";
    }
});
window.addEventListener("keyup", event => {
    actual_direction = "";
});


function update(timestamp) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    window.requestAnimationFrame(update);

    if (actual_direction == "left") {
        puffy.x -= .005;
        if (puffy.x < 0) { puffy.x = 0; }
    } else if (actual_direction == "right") {
        puffy.x += .005;
        if (puffy.x > 1) { puffy.x = 1; }
    } else if (predicted_direction == "left") {
        puffy.x -= .005;
        if (puffy.x < 0) { puffy.x = 0; }
    } else if (predicted_direction == "right") {
        puffy.x += .005;
        if (puffy.x > 1) { puffy.x = 1; }
    }

    ctx.drawImage(terrain, 0, 0, canvas.width, canvas.height);
    puffy.draw(timestamp);
    // sparklejuice.gif has sixteen frames that each last for 70 milliseconds
    ctx.drawImage(sparkle[Math.floor(timestamp / 70) % 16], 100, 100, canvas.width / 10, canvas.width / 10);
}
