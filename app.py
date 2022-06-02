#!/usr/bin/env python3
### BEN IF YOU DELETE THE SHEBANG ONE MORE TIME I'M GONNA GET YOU (I KNOW WHERE YOU SLEEP)

## Import everything ##
from flask_socketio import SocketIO
from flask import Flask, render_template
from threading import Thread, Event

from data_streamer import DataStreamer
from firebase_communicator import FirebaseCommunicator
from data_classifier import DataClassifier
from const import *

import numpy as np

## Initialize some stuff ##

# Flask setup
__author__ = 'Ben Falkenburg'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Turn the flask app into a socketio app
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None, logger=True, engineio_logger=True)

# Create thread
thread = Thread()
thread_stop_event = Event()

# This thingy streams data from the headset. More info in data_streamer.py
streamer = DataStreamer()

# This thingy communicates with our database to fetch and deposit data. More info in firebase_communication.py
firebase_comm = FirebaseCommunicator()

# This thingy classifies our data and shit. More info in data_classifier.py
classifier = DataClassifier(firebase_comm=firebase_comm)

# Keeps track of page
namespace = '/test'

## Functions that facilitate data streaming and database interaction ##

# If we have enough data to chunk out and add to our database, let's do so
def add_data_streamed_at_current_time():
    global streamer, firebase_comm
    # If currently recording left motion, record into our left motion category
    if streamer.recording_class == "LEFT":
        firebase_comm.add_data_to_left_motion_recordings(streamer.left_motion_file_count, streamer.all_c3_data, streamer.all_c4_data)
        streamer.left_motion_file_count += 1
        firebase_comm.update_left_motion_file_count(streamer.left_motion_file_count)
    # If currently recording right motion, record into our right motion category
    elif streamer.recording_class == "RIGHT":
        firebase_comm.add_data_to_right_motion_recordings(streamer.right_motion_file_count, streamer.all_c3_data, streamer.all_c4_data)
        streamer.right_motion_file_count += 1
        firebase_comm.update_right_motion_file_count(streamer.right_motion_file_count)

def initialize_analytics_chart():
    global streamer, firebase_comm
    # Get the file counts (metadata) just because it's good to display it right off the bat
    streamer.left_motion_file_count = firebase_comm.get_left_motion_file_count()
    streamer.right_motion_file_count = firebase_comm.get_right_motion_file_count()

# Update the count in the analytics chart
def update_analytics_chart():
    global streamer, firebase_comm
    if streamer.left_motion_file_count > 0:
        firebase_comm.update_left_motion_file_count(streamer.left_motion_file_count)
    if streamer.right_motion_file_count > 0:
        firebase_comm.update_right_motion_file_count(streamer.right_motion_file_count)

# Downsample our signal for the graph so it's more efficient
def downsample_data(data):
    downsampled_data = []
    samples = 10
    step_size = int(len(data)/samples)
    try:
        for i in range(0, len(data), step_size):
            downsampled_data.append(data[i])
    except:
        return downsampled_data
    return downsampled_data

# Send all necessary info to the main page/graphs
def send_data(c3_data=[], c4_data=[], direction_to_move=''):
    global namespace
    socketio.emit('new_test_data', {
        'c3_data': c3_data,
        'c4_data': c4_data,  
        'graph_frozen': False, 
        'direction_to_move': direction_to_move,
        'left_motion_file_count': streamer.left_motion_file_count, 
        'right_motion_file_count': streamer.right_motion_file_count, 
        'window_size': WINDOW_SIZE}, namespace='/test')
    socketio.emit('new_train_data', {
        'c3_data': c3_data,
        'c4_data': c4_data,  
        'graph_frozen': False, 
        'direction_to_move': direction_to_move,
        'left_motion_file_count': streamer.left_motion_file_count, 
        'right_motion_file_count': streamer.right_motion_file_count, 
        'window_size': WINDOW_SIZE}, namespace='/training')

# Basically looks at which value is greater in magnitude. We interpret the greater value as a command to move our avatar a certain direction
def process_prediction(prediction):
    processed_prediction = int(np.argwhere(prediction[0] == np.max(prediction[0]))[0][0])
    if processed_prediction == 0:
        return "left"
    else:
        return "right"

# Decides whether to send data to be stored in our database, or to feed it into a neural network for testing. Then, we send the data to our webpage
def process_data(c3_data=[], c4_data=[]):
    global streamer, classifier, namespace
    direction_to_move = ''
    if streamer.is_recording_training_data and streamer.current_time > 0 and streamer.current_time >= DATA_CHUNK_SIZE:
        streamer.current_time = 0
        add_data_streamed_at_current_time()
    elif streamer.is_streaming_testing_data and streamer.current_time > DATA_CHUNK_SIZE:
        prediction = classifier.classify_input(streamer.all_c3_data, streamer.all_c4_data)
        print(prediction)
        direction_to_move = process_prediction(prediction)
    send_data(c3_data, c4_data, direction_to_move)

# Our website's bread and butter. Initializes the charts and webpage, then collects data until the page is closed
def eeg_processor():
    global streamer, counter_of_thing
    initialize_analytics_chart()
    send_data()

    while not thread_stop_event.isSet():
        # Collect eeg data
        if streamer.is_recording_training_data or streamer.is_streaming_testing_data:
            c3_data, c4_data = streamer.get_current_data()
            #print(len(streamer.all_c3_data))
            c3_data = downsample_data(c3_data)
            c4_data = downsample_data(c4_data)
            process_data(c3_data, c4_data)
        elif namespace == '/test':
            process_data()
        socketio.sleep(0.25)
    update_analytics_chart()
    print("The data stream has ended")

## Page rendering functions ##

@app.route('/')
def home():
    global streamer, namespace
    namespace = '/test'
    send_data()
    return render_template('home.html')

@app.route("/training")
def training():
    global streamer, namespace
    namespace = '/training'
    send_data()
    return render_template("training.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/navbar")
def navbar():
    return render_template("navbar.html")

@app.route("/footer")
def footer():
    return render_template("footer.html")

@app.route("/networkmodal")
def networkmodal():
    return render_template("networkmodal.html")

## Button-triggered functions ##

# Set all variables to begin collecting eeg data for left motion
@app.route('/start_recording_left_motion')
def start_recording_left_motion():
    global streamer, namespace
    namespace = '/training'
    streamer.is_recording_training_data = True
    streamer.is_streaming_testing_data = False
    streamer.recording_class = "LEFT"
    return "200"

# Set all variables to begin collecting eeg data for right motion
@app.route('/start_recording_right_motion')
def start_recording_right_motion():
    global streamer, namespace
    namespace = '/training'
    streamer.is_recording_training_data = True
    streamer.is_streaming_testing_data = False
    streamer.recording_class = "RIGHT"
    return "200"

# Don't record from any recording class, and don't stream any data
@app.route('/stop_recording')
def stop_recording():
    global streamer
    update_analytics_chart()
    streamer.is_recording_training_data = False
    streamer.is_streaming_testing_data = False
    streamer.recording_class = "OFF"
    return "200"

# Create a neural network with the data collected
@app.route('/create_network')
def create_network():
    global streamer
    data, labels = classifier.build_data()
    if data is not None:
        classifier.train_network(data, labels)
        print("Network created!")
    else:
        print("Unable to create network")
    return "200"

# Start streaming data from the headset, with no intention of recording it. Data will be fed into neural network
@app.route('/start_streaming')
def start_streaming():
    global streamer, namespace
    namespace = '/test'
    streamer.is_recording_training_data = False
    streamer.is_streaming_testing_data = True
    return "200"

## Threading functions ##

# Actions to take when the website loads (start thread)
@socketio.on('connect')
def test_connect():
    global thread
    print('Client connected')
    send_data()
    if not thread.is_alive():
        print("Starting Thread")
        thread = socketio.start_background_task(eeg_processor)

# Actions to take when the thread ends
@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

## Run the thing ##

if __name__ == '__main__':
    socketio.run(app)
