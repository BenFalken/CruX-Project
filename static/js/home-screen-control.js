// This boolean determines whether or not we are ready to read the data being sent from app.py
let graph_is_ready = false;
var direction_to_move = '';

$(document).ready(function(){
    //$("#create-network-button").css("visibility", "hidden");
    // These variables will eventually be used for the avatar being moved. It has the ID "resting"
    let displacement_x = $( window ).width()/2;
    let displacement_y = 100;

    let origin_left = $("#avatar").css("left");
    origin_left = parseInt(origin_left.slice(0, -2));

    let origin_top = $("#avatar").css("top");
    origin_top = parseInt(origin_top.slice(0, -2));

    let x = origin_left;
    let y = origin_top;


    let speed = origin_left/20;
    let div_width = 50;
    // Initialize the socket.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var data_received = [];

    // This is how we interact with the two charts in our home page

    //var ctx = document.getElementById('myChart');
    //var ctx_bar = document.getElementById('file-count');
    
    // Our EEG chart. Details on the graph:
    /*
    * No legend to annotate data
    * No animation every time to graph reloads
    * No ticks on the x or y axis
    * Y axis is clamped between +/-0.0001
    */

    //NOTE: y range used to be +/- 0.0001

    /*
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'EEG Data',
                data: [0, 0]
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            animation: {
                duration: 0
            },
            scales : {
                y : {
                    display: false
                },
                x: {
                    display: false
                }
            }
        }
    });
    */

    // Our EEG chart. Details on the graph:
    /*
    * Two bins for data (eyes open, eyes closed)
    * No legend to annotate data
    * No animation every time to graph reloads
    * No ticks on the y axis
    * Y axis fixed at 0
    */
   /*
    var fileCountChart = new Chart(ctx_bar, {
        type: 'bar',
        data: {
            labels: ["Puffy's Left-Moving Knowledge", "Puffy's Right-Moving Knowledge"],
            datasets: [{
                data: [0, 0]
        }]},
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            animation: {
                duration: 0
            },
            scales: {
            y: {
                display: false,
                beginAtZero: true
            }
            }
        }
    })
    */
    // This function makes sure our avatar does not exceed the bounds on the window, lengthwise
    function clamp(val) {
        var max = $(window).width()*(0.9 - 0.048);
        var min = $(window).width()*(0.1 - 0.016);
        return Math.min(Math.max(val, min), max);
    }
    /*
    // This function appends new data to a chart
    function addData(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        chart.update();
      }

      // This function removes old data from the chart
      function removeData(chart) {
          chart.data.labels.shift();
          chart.data.datasets.forEach((dataset) => {
              dataset.data.shift();
          });
          chart.update();
      }

      // This function updates a bar chart bin category
      function addDataToBar(chart, data) {
        chart.data.datasets.forEach((dataset) => {
            dataset.data.shift();
            dataset.data.push(data);
        });
        chart.update();
      }
      */

    // This variable tracks the total amount of data transmitted to the EEG graph. If it exceeds the size of the graph, we remove the oldest data first
    //let i = 0;

    //receive details from server
    socket.on('new_data', function(msg) {
        var position = $( "#checkerboard" ).position();
        //origin_x = position.left;
        //origin_y = position.top;

        console.log("RECIEVED DATA");

        // Ignore this. I'm not exactly sure why this is still here
        //$("#file-count").text(msg.open_file_count.toString() + " " + msg.closed_file_count.toString());

        // Update the direction of the avatar
        direction_to_move = msg.direction_to_move;
        
        // Update char chart
        //addDataToBar(fileCountChart, msg.open_file_count);
        //addDataToBar(fileCountChart, msg.closed_file_count);

        // Update the EEG graph
        /*
        if (graph_is_ready) {
            // The variable for the data's fixed size is constant but it doesn't matter if we query for it every tick (we can optimize later)
            let WINDOW_SIZE = msg.window_size;

            // Add each bit of data one by one into the graph. If the total data's size exceeds the capped size, remove oldest data
            for (var j = 0; j < msg.c3_data.length; j++) {
                addData(myChart, i, msg.c3_data[j]);
                i = i + 1;
                if (i >= WINDOW_SIZE){
                    removeData(myChart);
                }            
            }
            var total = origin_x + displacement_x
            console.log("COUNT: " + total);
            // move the avatar! This is currently not in use, since graph_frozen is always false.
            if (msg.direction_to_move == 'left') {
                //console.log("WE BEGIN")
                displacement_x -= speed;
                //count = clamp(count - speed);
            }
            else if (msg.direction_to_move == 'right') {
                //console.log("WE BEGIN")
                displacement_x += speed;
                //count = clamp(count + speed);
            }
            $("#avatar").css("left", origin_x + displacement_x);
            $("#avatar").css("top", origin_y + displacement_y);
        }
        */
        if (msg.direction_to_move == 'left') {
            //console.log("WE BEGIN")
            x = clamp(x + $(window).width()*0.032);
            //count = clamp(count - speed);
        }
        else if (msg.direction_to_move == 'right') {
            //console.log("WE BEGIN")
            x = clamp(x + $(window).width()*0.32);
            //count = clamp(count + speed);
        }
        $("#avatar").css("left", x);
        $("#avatar").css("top", y);
        //console.log("ORIGIN_X: " + origin_x)
    });
    /*
    socket.on('disconnect', function () {
        setTimeout(function () {
             //do something
        }, 10000);
    });
    */
});


function start_recording_open() {
    // The graph is ready to start collecting and displaying data
    graph_is_ready = true;
    // Change the button color to indicate it has been pressed
    var color =  $("#open-button").css("background-color");
    if (color != 'skyblue') {
        $("#open-button").css("background-color", 'skyblue');
    }
    // Call "start recording open" function
    $.getJSON('/start_recording_open',
        function(data) {
            //do nothing
    });
}

function start_recording_closed() {
    // The graph is ready to start collecting and displaying data
    graph_is_ready = true;
    // Change the button color to indicate it has been pressed
    var color =  $("#closed-button").css("background-color");
    if (color != 'skyblue') {
        $("#closed-button").css("background-color", 'skyblue');
    }
    // Call "start recording closed" function
    $.getJSON('/start_recording_closed',
        function(data) {
            //do nothing
    });
}

function create_network() {
    // Replace this with a modal later
    alert("Now processing your data!")
    console.log("CREATED NETWORK");
    // The graph is no longer ready to start collecting and displaying data
    graph_is_ready = false;
    // Call "create network" function
    $.getJSON('/create_network',
        function(data) {
            //do nothing
    });
}

function stop_recording() {
    // The graph is no longer ready to start collecting and displaying data
    graph_is_ready = false;
    // Reset both buttons
    $("#open-button").css("background-color", '#ea4c89');
    $("#closed-button").css("background-color", '#ea4c89');
    $("#stream-button").css("background-color", '#4c7bea');
    // Reset
    $.getJSON('/stop_recording',
        function(data) {
            //do nothing
    });
}

function start_streaming() {
    // The graph is no longer ready to start collecting and displaying data
    graph_is_ready = true;
    // Reset both buttons
    var color =  $("#stream-button").css("background-color");
    if (color != 'skyblue') {
        $("#stream-button").css("background-color", 'skyblue');
    }
    // Reset
    $.getJSON('/start_streaming',
        function(data) {
            //do nothing
    });
}
