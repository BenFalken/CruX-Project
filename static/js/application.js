let is_ready = false;

$(document).ready(function(){
    //connect to the socket server.
    let count = $("#resting").position().left;
    let speed = 5;
    let div_width = 50;
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var data_received = [];

    var ctx = document.getElementById('myChart');

    var ctx_bar = document.getElementById('file-count');
    
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
                    display: false,
                    min: -0.0001,
                    max: 0.0001,
                },
                x: {
                    display: false
                }
            }
        }
    });

    var fileCountChart = new Chart(ctx_bar, {
        type: 'bar',
        data: {
            labels: ['Eyes Open', 'Eyes Closed'],
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

    function clamp(val) {
        var max = $( window ).width() - div_width;
        var min = 0;
        return Math.min(Math.max(val, min), max);
    }

    function addData(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(data);
        });
        chart.update();
      }

      function removeData(chart) {
          chart.data.labels.shift();
          chart.data.datasets.forEach((dataset) => {
              dataset.data.shift();
          });
          chart.update();
      }

      function addDataToBar(chart, data) {
        chart.data.datasets.forEach((dataset) => {
            dataset.data.shift();
            dataset.data.push(data);
        });
        chart.update();
      }

    let i = 0;
    //receive details from server
    socket.on('new_data', function(msg) {
        console.log("RECIEVED DATA");
        $("#file-count").text(msg.open_file_count.toString() + " " + msg.closed_file_count.toString());
        addDataToBar(fileCountChart, msg.open_file_count);
        addDataToBar(fileCountChart, msg.closed_file_count);
        if (is_ready) {
            let WINDOW_SIZE = msg.window_size;
            for (var j = 0; j < msg.data.length; j++) {
                addData(myChart, i, msg.data[j]);
                i = i + 1;
                if (i >= WINDOW_SIZE){
                    removeData(myChart);
                }            
            }
            if (!msg.is_resting) {
                count = clamp(count + speed);
                $("#resting").css("margin-left", count);
            }
        }
    });
});


function start_recording_open() {
    console.log("RECORDING OPEN")
    is_ready = true;
    var color =  $("#open-button").css("background-color");
    if (color != 'skyblue') {
        $("#open-button").css("background-color", 'skyblue');
    } else { //EA4C89
        $("#open-button").css("background-color", '#EA4C89');
    }
    $.getJSON('/start_recording_open',
        function(data) {
            //do nothing
    });
}

function start_recording_closed() {
    is_ready = true;
    $.getJSON('/start_recording_closed',
        function(data) {
            //do nothing
    });
}

function create_network() {
    is_ready = false;
    $.getJSON('/create_network',
        function(data) {
            //do nothing
    });
}

function stop_recording() {
    is_ready = false;
    $("#open-button").css("background-color", '#ea4c89');
}