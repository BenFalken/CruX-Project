# IMPORT SOME SHIT

from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context

from threading import Thread, Event

import classifier
from data_streamer import DataStreamer
from firebase_communicator import FirebaseCommunicator
from const import *

## INITIALIZE SOME STUFF ##

# Flask

__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Our threading

# Turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# Thread
thread = Thread()
thread_stop_event = Event()
# Streamer
streamer = DataStreamer()
# Firebase
firebase_comm = FirebaseCommunicator()


# Our website's bread and butter
def eeg_processor():
    global streamer, firebase_comm
    # Ignore this boolea for rn. It's unecessary
    is_resting = False

    # Get the file counts (metadata) just because it's good to display it right off the bat
    streamer.open_file_count = firebase_comm.get_open_file_count()
    streamer.closed_file_count = firebase_comm.get_closed_file_count()

    while not thread_stop_event.isSet():
        # Collect eeg data
        data_streamed_at_current_time = streamer.get_data()
        t = streamer.get_time()

        # If we have enough data to chunk and add to database, let's do so
        if t > 0 and t%DATA_CHUNK_SIZE == 0:
            # We will make and store a time series, adding it to our database
            if streamer.recording_class == "OPEN":
                firebase_comm.add_data_to_open_recordings(streamer.open_file_count, streamer.data[t-DATA_CHUNK_SIZE: t])
                streamer.open_file_count += 1
            elif streamer.recording_class == "CLOSED":
                firebase_comm.add_data_to_closed_recordings(streamer.closed_file_count, streamer.data[t-DATA_CHUNK_SIZE: t])
                streamer.closed_file_count += 1
        # Once data stops getting produced, end the program. Also included: code to initially display our metadata
        if not data_streamed_at_current_time:
            print("THE DATA STREAM HAS ENDED")
            break
        elif streamer.open_file_count != 0 or streamer.closed_file_count != 0:
            socketio.emit('new_data', {'data': data_streamed_at_current_time, 'is_resting': is_resting, 'open_file_count': streamer.open_file_count, 'closed_file_count': streamer.closed_file_count, 'window_size': WINDOW_SIZE}, namespace='/test')
        else:
            socketio.emit('new_data', {'data': data_streamed_at_current_time, 'is_resting': is_resting, 'open_file_count': streamer.open_file_count, 'closed_file_count': streamer.closed_file_count, 'window_size': WINDOW_SIZE}, namespace='/test')
        socketio.sleep(0.25)    # Necessary time delay

    # Update the count in the analytics chart
    if streamer.open_file_count > 0:
        firebase_comm.update_open_file_count(streamer.open_file_count)
    if streamer.closed_file_count > 0:
        firebase_comm.update_closed_file_count(streamer.closed_file_count)

## PAGE FUNCTIONS (don't worry about these, they just load everything) ##

@app.route('/')
def home():
    global streamer
    streamer.collect_edf_data()
    return render_template('home.html')

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

## BUTTON FUNCTIONS ##

# Set all variables to begin collecting eeg data for open eyes
@app.route('/start_recording_open')
def start_recording_open():
    global streamer
    #streamer.open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    #streamer.closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    streamer.recording_class = "OPEN"
    return "200"

# Set all variables to begin collecting eeg data for closed eyes
@app.route('/start_recording_closed')
def start_recording_closed():
    global streamer
    #streamer.open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    #streamer.closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    streamer.recording_class = "CLOSED"
    return "200"

# Create a neural network with the data collected. This function is unfinished
@app.route('/create_network')
def create_network():
    global streamer
    data, labels = classifier.build_data(firebase_comm=firebase_comm)
    if data is not None:
        #train_network(data, labels)
        print("Success")
    else:
        print("Unable to create network")
    return "200"

## THREADING FUNCTIONS ##

@socketio.on('connect', namespace='/test')
def test_connect():
    # Need visibility of the global thread object
    global thread
    print('Client connected')

    # Start the thread only if the thread has not been started before.
    if not thread.is_alive():
        print("Starting Thread")
        thread = socketio.start_background_task(eeg_processor)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

## RUN THE THING ##

if __name__ == '__main__':
    socketio.run(app)