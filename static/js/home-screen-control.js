$(document).ready(function() {
    canvas = document.getElementById("game-canvas");
    ctx = canvas.getContext("2d");
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientWidth * 1080 / 1920;
    sparkle_and_brain_image_size_in_pixels = canvas.clientWidth / 8;
    canvas.addEventListener("mousemove", event => {
        var mouse_x = event.offsetX / canvas.clientWidth;
        var mouse_y = 1 - event.offsetY / canvas.clientHeight;
        particles.push(new Particle(mouse_x, mouse_y));
        particles.push(new Particle(mouse_x, mouse_y));
    });
    // Start playing when you click
    canvas.addEventListener("mousedown", event => {
        var mouse_x = event.offsetX / canvas.clientWidth;
        var mouse_y = 1 - event.offsetY / canvas.clientHeight;
        for (var i = 0; i < 50; i++) {
            particles.push(new Particle(mouse_x, mouse_y));
        }
        if (game_state == "ready" || game_state == "dead") {
            game_state = "alive";
            sustenance = 20;
            game_duration_seconds = 0;
            sparkles = [new Sparkle()];
            score = 0;
            puffy.x = .5;
            demonic_dance.play();
            console.log("Playing theme song \"Demonic_Dance.mp3\" by Paul Zhang");
        }
    });

    // game_state is sort of like an enum -- it should always be "ready" or "alive" or "dead"
    game_state = "ready";
    score = 0;
    highest_score = 0;
    sustenance = 20;
    last_timestamp = 0;
    // game_duration_seconds is only applicable if alive
    game_duration_seconds = 0;
    // direction of movement, either "left" or "right" (or neither???)
    predicted_direction = "";
    actual_direction = "";

    // Initialize the socket and receive data from server
    socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    socket.on('new_test_data', function(msg) {
        predicted_direction = msg.direction_to_move;
    });

    terrain = new Image();
    terrain.src = "/static/images/terrain.png";
    game_over_screen = new Image();
    game_over_screen.src = "/static/images/gameover.png";
    demonic_dance = new Audio();
    demonic_dance.src = "/static/audio/Demonic_Dance.mp3";
    demonic_dance.loop = true;
    fwoop = new Audio();
    fwoop.src = "/static/audio/fwoop.mp3";
    game_over_sfx = new Audio();
    game_over_sfx.src = "/static/audio/game_over.mp3";

    puffy = new SmoothBrain();
    sparkles = [new Sparkle()];
    particles = [];

    window.requestAnimationFrame(update);
});

// SMOOTHBRAIN CLASS
class SmoothBrain {
    constructor() {
        this.frames = [];
        for (var i = 1; i <= 12; i++) {
            this.frames[i - 1] = new Image();
            this.frames[i - 1].src = "/static/images/smoothbrain/frame" + i.toString() + ".png";
        }
        this.x = .5;
        this.y = 0;
        this.speed = .005;
        this.min_x =     sparkle_and_brain_image_size_in_pixels / 2 / canvas.width;
        this.max_x = 1 - sparkle_and_brain_image_size_in_pixels / 2 / canvas.width;
    }
    draw(timestamp) {
        // smoothbrain.gif has twelve frames that each last for 70 milliseconds
        var frame_number = Math.floor(timestamp / 70) % 12;
        var canvas_x_coord = canvas.width  * this.x - sparkle_and_brain_image_size_in_pixels / 2;
        // the .8 in this next line is there is a fudge factor to account for the large transparent padding in the image files
        var canvas_y_coord = canvas.height * (1 - this.y) - sparkle_and_brain_image_size_in_pixels * .8;
        ctx.drawImage(this.frames[frame_number], canvas_x_coord, canvas_y_coord, sparkle_and_brain_image_size_in_pixels, sparkle_and_brain_image_size_in_pixels);
    }
}

// SPARKLE CLASS
class Sparkle {
    constructor() {
        this.frames = [];
        for (var i = 1; i <= 16; i++) {
            this.frames[i - 1] = new Image();
            this.frames[i - 1].src = "/static/images/sparklejuice/frame" + i.toString() + ".png";
        }
        this.fall_speed = .002 + .003 * Math.random();
        this.frame_offset = Math.floor(Math.random() * 16);
        this.x = (Math.random() * (canvas.width - sparkle_and_brain_image_size_in_pixels) + sparkle_and_brain_image_size_in_pixels / 2) / canvas.width;
        this.y = 1;
    }
    fall() {
        this.y -= this.fall_speed;
    }
    touching_puffy() {
        // Fudge factors  <3 <3 <3
        var x_distance_to_puffy = this.x - puffy.x + .0005;
        var y_distance_to_puffy = (this.y - puffy.y + .03) * canvas.height / canvas.width;
        var distance_to_puffy = Math.sqrt(x_distance_to_puffy * x_distance_to_puffy + y_distance_to_puffy * y_distance_to_puffy);
        if (distance_to_puffy <= .05) {
            // sparkle is near puffy, bring it closer so that the animation is satisfying
            // (instead of just making the sparkle disappear when it gets close)
            this.x += (puffy.x - this.x) * .2;
            this.y += (puffy.y - this.y) * .2;
        }
        var is_touching_puffy = distance_to_puffy <= .03;
        if (is_touching_puffy) {
            fwoop.currentTime = 0;
            fwoop.play();
        }
        return is_touching_puffy;
    }
    draw(timestamp) {
        // smoothbrain.gif has sixteen frames that each last for 70 milliseconds
        var frame_number = (Math.floor(timestamp / 70) + this.frame_offset) % 16;
        // calculate the canvas coordinates
        var canvas_x_coord = canvas.width  * this.x - sparkle_and_brain_image_size_in_pixels / 2;
        var canvas_y_coord = canvas.height * (1 - this.y) - sparkle_and_brain_image_size_in_pixels;
        ctx.drawImage(this.frames[frame_number], canvas_x_coord, canvas_y_coord, sparkle_and_brain_image_size_in_pixels, sparkle_and_brain_image_size_in_pixels);
    }
}

// PARTICLE CLASS
class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        var random_factor = Math.random();
        if (game_state == "ready") {
            // White to light blue
            this.color = rgb([220 - random_factor * 100, 220 - random_factor * 100, 255]);
        } else if (game_state == "alive") {
            // Rainbow
            this.color = rgb(hslToRgb(random_factor, 1, .7));
        } else if (game_state == "dead") {
            // Red to brown
            this.color = rgb([150 - random_factor * 100, 30, 0]);
        }
        var angle = Math.random() * 2 * Math.PI;
        this.x_velocity = .002 * Math.cos(angle) * Math.random();
        this.y_velocity = .005 * Math.sin(angle) * Math.random();
        this.fall_speed = .0003;
        this.size = Math.random() * .003 + .002;
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x * canvas.width  - canvas.width * this.size / 2,
                     (1 - this.y) * canvas.height - canvas.width * this.size / 2,
                     this.size * canvas.width,
                     this.size * canvas.width
        );
    }
    update() {
        this.x += this.x_velocity;
        this.y += this.y_velocity;
        this.y_velocity -= this.fall_speed;
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

// Taken directly from https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
// see documentation there  :)
function hslToRgb(h, s, l){
    var r, g, b;
    if (s == 0) {
        r = g = b = l; // achromatic
    } else {
        var hue2rgb = function hue2rgb(p, q, t){
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        }
        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}


function rgb(values) {
    return 'rgb(' + values.join(', ') + ')';
}

window.addEventListener("keydown", event => {
    if (event.keyCode == 37) {
        actual_direction = "left";
    } else if (event.keyCode == 39) {
        actual_direction = "right";
    }
});
window.addEventListener("keyup", event => {
    if (event.keyCode == 37 || event.keyCode == 39) {
        // If user releases left or right arrow key, stop moving left/right
        actual_direction = "";
    }
});
window.addEventListener("resize", event => {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientWidth * 1080 / 1920;
    sparkle_and_brain_image_size_in_pixels = canvas.clientWidth / 8;
});

function update(timestamp) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    window.requestAnimationFrame(update);

    if (game_state == "alive") {
        sustenance -= (timestamp - last_timestamp) / 1000;
        game_duration_seconds += (timestamp - last_timestamp) / 1000;
    }

    if (sustenance < 0) {
        game_state = "dead";
        sustenance = 0;
        console.log("Score: " + score.toString());
        demonic_dance.pause();
        demonic_dance.currentTime = 0
        game_over_sfx.play();
    }
    if (game_state == "dead") {
        game_duration_seconds = 0;
        sparkles = [];
    }

    if (game_state == "alive") {
        if (actual_direction == "left") {
            puffy.x -= puffy.speed;
            if (puffy.x < puffy.min_x) { puffy.x = puffy.min_x; }
        } else if (actual_direction == "right") {
            puffy.x += puffy.speed;
            if (puffy.x > puffy.max_x) { puffy.x = puffy.max_x; }
        } else if (predicted_direction == "left") {
            puffy.x -= puffy.speed;
            if (puffy.x < puffy.min_x) { puffy.x = puffy.min_x; }
        } else if (predicted_direction == "right") {
            puffy.x += puffy.speed;
            if (puffy.x > puffy.max_x) { puffy.x = puffy.max_x; }
        }

        if (Math.random() < (timestamp - last_timestamp) / 1000) {
            // Spawn a new sparkle roughly once per second
            sparkles.push(new Sparkle());
        }
    }

    ctx.drawImage(terrain, 0, 0, canvas.width, canvas.height);
    if (game_state == "dead" || sustenance < 5) {
        // Gradually fade into "game over" screen and then make sparkles vanish
        var deadness = 1 - Math.ceil(sustenance) / 5;
        if (game_state == "dead") { deadness = 1; }
        ctx.globalAlpha = deadness;
        ctx.drawImage(game_over_screen, 0, 0, canvas.width, canvas.height);
    }
    ctx.globalAlpha = 1;

    if (game_state == "alive") {
        // Draw sparkles (and remove them once fallen offscreen, to avoid lag)
        var sparkle_indices_to_remove = [];
        for (var i = 0; i < sparkles.length; i++) {
            sparkles[i].fall();
            if (sparkles[i].touching_puffy()) {
                sustenance += 1 + 2 / (1 + game_duration_seconds / 10);
                score += 1;
                if (score > highest_score) { highest_score = score; }
                sparkle_indices_to_remove.push(i);
            } else if (sparkles[i].y < -1) {
                sparkle_indices_to_remove.push(i);
            }
        }
        for (const index of sparkle_indices_to_remove.reverse()) {
            sparkles.splice(index, 1);
        }
    }
    for (var i = 0; i < sparkles.length; i++) {
        sparkles[i].draw(timestamp);
    }

    if (game_state == "alive" || game_state == "ready") {
        puffy.draw(timestamp);
    } else if (game_state == "dead") {
        puffy.draw(0);
    }

    // Prepare to draw score counter at lop left
    var font_size = Math.round(canvas.height / 20);
    ctx.textAlign = "left";
    ctx.font = "bold " + font_size.toString() + "px Lato";
    ctx.fillStyle = "white";
    ctx.lineWidth = Math.floor(canvas.height / 500);
    ctx.strokeStyle = "black";
    // Draw score counter at top left of canvas
    var text = "Highest score: " + highest_score.toString();
    ctx.fillText(text, font_size, font_size);
    ctx.strokeText(text, font_size, font_size);
    text = "Score: " + score.toString();
    ctx.fillText(text, font_size, font_size * 2);
    ctx.strokeText(text, font_size, font_size * 2);
    text = "Sustenance: " + sustenance.toFixed(1);
    ctx.fillText(text, font_size, font_size * 3);
    ctx.strokeText(text, font_size, font_size * 3);

    // Draw "game over" screen
    if (game_state == "dead") {
        font_size = Math.round(canvas.height / 5);
        ctx.font = "bold " + font_size.toString() + "px Lato";
        ctx.fillStyle = "white";
        ctx.lineWidth = Math.floor(canvas.height / 100);
        ctx.strokeStyle = "black";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("GAME OVER", canvas.width / 2, (canvas.height - font_size) / 2);
        ctx.strokeText("GAME OVER", canvas.width / 2, (canvas.height - font_size) / 2);

        font_size = Math.round(canvas.height / 20);
        ctx.font = "bold italic " + font_size.toString() + "px Lato";
        ctx.fillStyle = "white";
        ctx.lineWidth = Math.floor(canvas.height / 500);
        ctx.strokeStyle = "black";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("click to play again", canvas.width / 2, canvas.height * .55);
        ctx.strokeText("click to play again", canvas.width / 2, canvas.height * .55);
    }

    // Draw start screen
    if (game_state == "ready") {
        font_size = Math.round(canvas.height / 15);
        ctx.font = "bold italic " + font_size.toString() + "px Lato";
        ctx.fillStyle = "white";
        ctx.lineWidth = Math.round(canvas.height / 400);
        ctx.strokeStyle = "black";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("click to play", canvas.width / 2, canvas.height / 2);
        ctx.strokeText("click to play", canvas.width / 2, canvas.height / 2);
    }

    // Draw particles (and remove them once fallen offscreen, to avoid lag)
    var particle_indices_to_remove = [];
    for (var i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
        if (particles[i].y < -1) {
            particle_indices_to_remove.push(i);
        }
    }
    for (const index of particle_indices_to_remove.reverse()) {
        particles.splice(index, 1);
    }

    last_timestamp = timestamp;
}
