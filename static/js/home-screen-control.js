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
    sparkles = [new Sparkle()];

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
        this.width_in_pixels = canvas.width / 8;
        this.height_in_pixels = canvas.width / 8;
        this.min_x =     this.width_in_pixels / 2 / canvas.width;
        this.max_x = 1 - this.width_in_pixels / 2 / canvas.width;
    }
    draw(timestamp) {
        // smoothbrain.gif has twelve frames that each last for 70 milliseconds
        var frame_number = Math.floor(timestamp / 70) % 12;
        // calculate the canvas coordinates
        var canvas_x_coord = canvas.width  * this.x - this.width_in_pixels / 2;
        // the .8 in this next line is there is a fudge factor to account for the large transparent padding in the image files
        var canvas_y_coord = canvas.height * (1 - this.y) - this.height_in_pixels * .8;
        ctx.drawImage(this.frames[frame_number], canvas_x_coord, canvas_y_coord, this.width_in_pixels, this.height_in_pixels);
    }
}

class Sparkle {
    constructor() {
        this.frames = [];
        for (var i = 1; i <= 16; i++) {
            this.frames[i - 1] = new Image();
            this.frames[i - 1].src = "/static/images/sparklejuice/frame" + i.toString() + ".png";
        }
        this.width_in_pixels = canvas.width / 8;
        this.height_in_pixels = canvas.width / 8;
        this.fall_speed = .002 + .002 * Math.random();
        this.frame_offset = Math.floor(Math.random() * 16);
        this.x = (Math.random() * (canvas.width - this.width_in_pixels) + this.width_in_pixels / 2) / canvas.width;
        this.y = 1;
    }
    fall() {
        this.y -= this.fall_speed;
    }
    touching_puffy() {
        var x_distance_to_puffy = this.x - puffy.x + .0005;
        var y_distance_to_puffy = (this.y - puffy.y + .03) * canvas.height / canvas.width;
        var distance_to_puffy = Math.sqrt(x_distance_to_puffy * x_distance_to_puffy + y_distance_to_puffy * y_distance_to_puffy);
        if (distance_to_puffy <= .05) {
            // sparkle is near puffy, bring it closer so that the animation is satisfying
            // (instead of just making the sparkle disappear when it gets close)
            this.x += (puffy.x - this.x) * .1;
            this.y += (puffy.y - this.y) * .1;
        }
        return distance_to_puffy <= .03;
    }
    draw(timestamp) {
        // smoothbrain.gif has sixteen frames that each last for 70 milliseconds
        var frame_number = (Math.floor(timestamp / 70) + this.frame_offset) % 16;
        // calculate the canvas coordinates
        var canvas_x_coord = canvas.width  * this.x - this.width_in_pixels / 2;
        var canvas_y_coord = canvas.height * (1 - this.y) - this.height_in_pixels;
        ctx.drawImage(this.frames[frame_number], canvas_x_coord, canvas_y_coord, this.width_in_pixels, this.height_in_pixels);
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
        if (puffy.x < puffy.min_x) { puffy.x = puffy.min_x; }
    } else if (actual_direction == "right") {
        puffy.x += .005;
        if (puffy.x > puffy.max_x) { puffy.x = puffy.max_x; }
    } else if (predicted_direction == "left") {
        puffy.x -= .005;
        if (puffy.x < puffy.min_x) { puffy.x = puffy.min_x; }
    } else if (predicted_direction == "right") {
        puffy.x += .005;
        if (puffy.x > puffy.max_x) { puffy.x = puffy.max_x; }
    }

    if (Math.random() < .01) {
        sparkles.push(new Sparkle());
    }

    ctx.drawImage(terrain, 0, 0, canvas.width, canvas.height);

    var indices_to_remove = [];
    for (var i = 0; i < sparkles.length; i++) {
        sparkles[i].fall();
        if (sparkles[i].touching_puffy()) {
            score += 1;
        }
        if (sparkles[i].touching_puffy() || sparkles[i].y < -1) {
            indices_to_remove.push(i);
        }
    }
    for (const index of indices_to_remove.reverse()) {
        sparkles.splice(index, 1);
    }
    for (var i = 0; i < sparkles.length; i++) {
        sparkles[i].draw(timestamp);
    }

    puffy.draw(timestamp);
}
