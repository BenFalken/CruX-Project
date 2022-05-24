// Is the graph ready to display data
let graph_is_ready = false;

$(document).ready(function(){
    // Initialize the socket.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/training');

    // This is how we interact with the two charts in our home page
    var ctx = document.getElementById('myChart');
    var ctx_bar = document.getElementById('file-count');
    
    /*
    * Our EEG chart. Details on the graph:
    ** No legend to annotate data
    ** No animation every time to graph reloads
    ** No ticks on the x or y axis
    ** Y axis is clamped between +/-0.0001
    */

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

    /*
    * Our analytics chart. Details on the graph:
    ** Two bins for data (left/right motion)
    ** No legend to annotate data
    ** No animation every time to graph reloads
    ** No ticks on the y axis
    ** Y axis fixed at 0
    */

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

    // This variable tracks the total amount of data transmitted to the EEG graph. If it exceeds the size of the graph, we remove the oldest data first
    let data_pts_currently_on_graph = 0;

    // Receive details from server
    socket.on('new_data', function(msg) {   
        // Update analytics chart
        addDataToBar(fileCountChart, msg.left_motion_file_count);
        addDataToBar(fileCountChart, msg.right_motion_file_count);

        // Update the EEG graph
        if (graph_is_ready) {
            // The variable for the data's fixed size is constant but it doesn't matter if we query for it every tick (we can optimize later)
            let WINDOW_SIZE = msg.window_size;
            // Add each bit of data one by one into the graph. If the total data's size exceeds the capped size, remove oldest data
            for (var j = 0; j < msg.c3_data.length; j++) {
                addData(myChart, data_pts_currently_on_graph, msg.c3_data[j]);
                data_pts_currently_on_graph += 1;
                if (data_pts_currently_on_graph >= WINDOW_SIZE) {
                    removeData(myChart);
                }            
            }
        }
    });
});

// Resets recording button colors and triggers start_recording_left_motion function in app.py
function start_recording_left_motion() {
    graph_is_ready = true;
    var color =  $("#record-left-motion-button").css("background-color");
    if (color != 'skyblue') {
        $("#record-left-motion-button").css("background-color", 'skyblue');
    }
    $.getJSON('/start_recording_left_motion',
        function(data) {
    });
}

// Resets recording button colors and triggers start_recording_right_motion function in app.py
function start_recording_right_motion() {
    graph_is_ready = true;
    var color =  $("#record-right-motion-button").css("background-color");
    if (color != 'skyblue') {
        $("#record-right-motion-button").css("background-color", 'skyblue');
    }
    $.getJSON('/start_recording_right_motion',
        function(data) {
    });
}

// Resets recording button colors and triggers create_network function in app.py
function create_network() {
    alert("Now processing your data!")
    graph_is_ready = false;
    $.getJSON('/create_network',
        function(data) {
    });
}

// Resets recording button colors and triggers stop_recording function in app.py
function stop_recording() {
    graph_is_ready = false;
    $("#record-left-motion-button").css("background-color", '#ea4c89');
    $("#record-right-motion-button").css("background-color", '#ea4c89');
    $.getJSON('/stop_recording',
        function(data) {
    });
}
