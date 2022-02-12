from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event
import numpy as np
import numpy.matlib
import mne
import matplotlib.pyplot as plt
from firebase_admin import credentials, firestore, initialize_app
from scipy import signal

# Initialize Firestore DB

cred = credentials.Certificate('/Users/benfalken/Desktop/myproject/arasi-3c613-firebase-adminsdk-i534z-e88b914885.json')
default_app = initialize_app(cred)
db = firestore.client()
open_recordings = db.collection('open_recordings')
closed_recordings = db.collection('closed_recordings')
metadata = db.collection('metadata')


__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# Random number Generator Thread
thread = Thread()
thread_stop_event = Event()

WINDOW_SIZE = 100
DATA_CHUNK_SIZE = 500
DELAY = 10

recording_class = "OFF"

open_file_count = 0
closed_file_count = 0

all_data = []
t = 0

# Clamps val between zero and one
def clamp(val):
    return min(val, 0.99999)

# Applies a butterworth filter to the data
def filter_data(data):
    lowcut, highcut = 14, 71
    nyq = 0.5 * 128

    low = lowcut / nyq
    high = clamp(highcut / nyq)

    b, a = signal.butter(9, [low, high], btype="band")
    filtered = signal.lfilter(b, a, data)
    return filtered

# Since we don't yet have the openbci headset, this data comes from a file which will be attached in the repo
def collect_edf_data():
    global all_data
    raw_data = mne.io.read_raw_edf("/Users/benfalken/Desktop/BoxMove/files/S001/S001R01.edf")
    all_data = raw_data.get_data()[0].tolist()[:1000]

# Get all the data in a certain time window
def get_data():
    global t, all_data, train_data_size
    t += DELAY
    return all_data[t-DELAY: t]

# Generate fft of the data. Function unused
def process_fft_data(fft_data):
    for data in fft_data:
        plt.plot(fft_data)
        plt.show()

def eeg_processor():
    global fft_data, open_file_count, closed_file_count
    is_resting = False
    while not thread_stop_event.isSet():
        # Collect eeg data
        data = get_data()
        # If we have enough data to chunk and add to database, do so
        if t > 0 and t%DATA_CHUNK_SIZE == 0:
            if recording_class == "OPEN":
                open_recordings.document("recording_" + str(open_file_count)).set({'data': all_data[t-DATA_CHUNK_SIZE: t]})
                open_file_count += 1
            else:
                closed_recordings.document("recording_" + str(closed_file_count)).set({'data': all_data[t-DATA_CHUNK_SIZE: t]})
                closed_file_count += 1
        # Once data stops getting produced, end the program
        if not data:
            print("THE DATA STREAM HAS ENDED")
            break
        else:
            socketio.emit('newnumber', {'data': data, 'is_resting': is_resting, 'open_file_count': open_file_count, 'closed_file_count': closed_file_count, 'window_size': WINDOW_SIZE}, namespace='/test')
        socketio.sleep(0.25)
    # Update the count in the analytics chart
    if open_file_count > 0:
        metadata.document("open_file_count").update({'count': open_file_count})
    if closed_file_count > 0:
        metadata.document("closed_file_count").update({'count': closed_file_count})

@app.route('/')
def home():
    collect_edf_data()
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

# Set all variables to begin collecting eeg data for open eyes
@app.route('/start_recording_open')
def start_recording_open():
    global recording_class, open_file_count, closed_file_count
    open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    recording_class = "OPEN"

# Set all variables to begin collecting eeg data for closed eyes
@app.route('/start_recording_closed')
def start_recording_closed():
    global recording_class
    global recording_class, open_file_count, closed_file_count
    open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    recording_class = "CLOSED"

# Create a neural network with the data collected. This function is unfinished
@app.route('/create_network')
def create_network():
    print("****************** CREATING NETWORK ******************")
    open_file_count =  metadata.document("open_file_count").get().to_dict()['count']
    open_recording_data = np.zeros((open_file_count, DATA_CHUNK_SIZE))
    open_recording_labels = np.matlib.repmat([1, 0], open_file_count, 1)

    closed_file_count =  metadata.document("closed_file_count").get().to_dict()['count']
    closed_recording_data = np.zeros((closed_file_count, DATA_CHUNK_SIZE))
    closed_recording_labels = np.matlib.repmat([0, 1], closed_file_count, 1)

    for count in range(open_file_count):
        data = open_recordings.document("recording_" + str(count)).get().to_dict()['data']
        filtered_data = filter_data(data)
        fft_filtered_data = np.fft.fft(filtered_data)
        for i in range(DATA_CHUNK_SIZE):
            open_recording_data[count][i] = fft_filtered_data[i]

    for count in range(closed_file_count):
        data = closed_recordings.document("recording_" + str(count)).get().to_dict()['data']
        filtered_data = filter_data(data)
        fft_filtered_data = np.fft.fft(filtered_data)
        for i in range(DATA_CHUNK_SIZE):
            closed_recording_data[count][i] = fft_filtered_data[i]
    try:
        all_recordings = np.concatenate((open_recording_data, closed_recording_data))
        all_recording_labels = np.concatenate(open_recording_labels, closed_recording_labels)
    except:
        if open_recording_data.size == 0:
            all_recordings = closed_recording_data
            all_recording_labels = closed_recording_labels
        else:
            all_recordings = open_recording_data
            all_recording_labels = open_recording_labels
        
# Threading functions
@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread, fft_data
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.is_alive():
        print("Starting Thread")
        thread = socketio.start_background_task(eeg_processor)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)