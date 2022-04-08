#!/usr/bin/env python3

from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from firebase_admin import credentials, firestore, initialize_app, ml
from threading import Thread, Event

from random import random
from time import sleep
from scipy import signal

import numpy as np
import pickle as pkl
import tensorflow as tf
from tensorflow.keras import layers, models

import mne

## INITIALIZE SOME SHIT ##

# Firebase

cred = credentials.Certificate('firebase_key.json')

#cred = credentials.Certificate('firebase_key.json')

default_app = initialize_app(cred, options={
      'storageBucket': 'nam5',
  })
db = firestore.client()
open_recordings = db.collection('open_recordings')
closed_recordings = db.collection('closed_recordings')
metadata = db.collection('metadata')

# Flask

__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Our threading

# Turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# Random number Generator Thread
thread = Thread()
thread_stop_event = Event()

# Constants for the stfts produced

STFT_f_size = 129
STFT_t_size = 9

## CONSTANTS AND STUFF ##

WINDOW_SIZE = 100       # How much data we are at in the graph window at once
DATA_CHUNK_SIZE = 1000  # We chunk the data and upload it to firebase. We do this in time series arrays sized to 1000 vals
DELAY = 10              # The delay is for the socket to function effectively. It chunks out how much data we get at a time. Without a good enough delay the program lags and breaks

recording_class = "OFF" # At the outset, we are not recording for any state of mind; the system is off

# This is for the user's reference; how much data in one state is there versus another?
open_file_count = 0
closed_file_count = 0

all_data = []           # All of le data
t = 0                   # The current time, which tells us how to parse out the data into the site

## CORE FUNCTIONS ##

# Clamps val between zero and one
def clamp(val):
    return min(val, 0.99999)

# Applies a butterworth filter to the data
def filter_data(data):
    lowcut, highcut = 14, 71    # 14Hz, 71Hz cutoffs
    nyq = 0.5 * 128             # Sample freq is 128

    low = lowcut / nyq
    high = clamp(highcut / nyq)

    b, a = signal.butter(9, [low, high], btype="band")  # Bandpass, which means we select a "band" of frequencies
    filtered = signal.lfilter(b, a, data)
    return filtered

# Since we don't yet have the openbci headset, this data comes from a file which will be attached in the repository
def collect_edf_data():
    global all_data
    raw_data = mne.io.read_raw_edf("demo_data/S001R01.edf")
    all_data = raw_data.get_data()[0].tolist()[:1000]

# Get all the data in a certain time window
def get_data():
    global t, all_data, train_data_size
    t += DELAY
    return all_data[t-DELAY: t]

# Our website's bread and butter
def eeg_processor():
    global fft_data, open_file_count, closed_file_count
    is_resting = False

    # Get the file counts (metadata) just because it's good to display it right off the bat
    open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']

    while not thread_stop_event.isSet():
        # Collect eeg data
        data = get_data()
        # If we have enough data to chunk and add to database, let's do so
        if t > 0 and t%DATA_CHUNK_SIZE == 0:
            # We will make and store a time series, adding it to our database
            if recording_class == "OPEN":
                open_recordings.document("recording_" + str(open_file_count)).set({'data': all_data[t-DATA_CHUNK_SIZE: t]})
                open_file_count += 1
            elif recording_class == "CLOSED":
                closed_recordings.document("recording_" + str(closed_file_count)).set({'data': all_data[t-DATA_CHUNK_SIZE: t]})
                closed_file_count += 1
        # Once data stops getting produced, end the program. Also included: code to initially display our metadata
        if not data:
            print("THE DATA STREAM HAS ENDED")
            break
        elif open_file_count != 0 or closed_file_count != 0:
            socketio.emit('new_data', {'data': data, 'is_resting': is_resting, 'open_file_count': open_file_count, 'closed_file_count': closed_file_count, 'window_size': WINDOW_SIZE}, namespace='/test')
        else:
            socketio.emit('new_data', {'data': data, 'is_resting': is_resting, 'open_file_count': open_file_count, 'closed_file_count': closed_file_count, 'window_size': WINDOW_SIZE}, namespace='/test')
        socketio.sleep(0.25)    # Necessary time delay

    # Update the count in the analytics chart
    if open_file_count > 0:
        metadata.document("open_file_count").update({'count': open_file_count})
    if closed_file_count > 0:
        metadata.document("closed_file_count").update({'count': closed_file_count})

## PAGE FUNCTIONS (don't worry about these, they just load everything) ##

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

@app.route("/networkmodal")
def networkmodal():
    return render_template("networkmodal.html")

## BUTTON FUNCTIONS ##

# Set all variables to begin collecting eeg data for open eyes
@app.route('/start_recording_open')
def start_recording_open():
    global recording_class, open_file_count, closed_file_count
    open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    recording_class = "OPEN"
    return "200"

# Set all variables to begin collecting eeg data for closed eyes
@app.route('/start_recording_closed')
def start_recording_closed():
    global recording_class
    global recording_class, open_file_count, closed_file_count
    open_file_count = metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count = metadata.document("closed_file_count").get().to_dict()['count']
    recording_class = "CLOSED"
    return "200"

## DEEP HURTING FUNCTION -- NOT AT ALL FINISHED ##

# Create a neural network with the data collected. This function is unfinished
@app.route('/create_network')
def create_network():
    print("FINISHED")
    data, labels = build_data()
    if data is not None:
        """
        arasi_file = open('arasi_file', 'ab')
        pkl.dump({"data": data, "labels": labels}, arasi_file)
        arasi_file.close()
        """
        #train_network(data, labels)
        print("Sucess")
    else:
        print("Unable to create network")
    return "200"

def build_data():
    print("****************** CREATING NETWORK ******************")
    open_file_count =  metadata.document("open_file_count").get().to_dict()['count']
    closed_file_count =  metadata.document("closed_file_count").get().to_dict()['count']

    all_data = np.zeros((open_file_count + closed_file_count, STFT_f_size, STFT_t_size))
    all_labels = np.zeros((open_file_count + closed_file_count, 2))

    for count in range(open_file_count):
        data = open_recordings.document("recording_" + str(count)).get().to_dict()['data']
        filtered_data = filter_data(data)
        f, t, data_stft = signal.stft(filtered_data, nperseg=64)
        print(data_stft.shape)
        #all_data[count] = np.abs(data_stft)
        #all_labels[count][0] = 1

    for count in range(closed_file_count):
        data = closed_recordings.document("recording_" + str(count)).get().to_dict()['data']
        filtered_data = filter_data(data)
        f, t, data_stft = signal.stft(filtered_data, nperseg=64)
        print(data_stft.shape)
        #all_data[count + open_file_count] = np.abs(data_stft)
        #all_labels[count + open_file_count][1] = 1
    return all_data, all_labels

def train_network(data, labels):

    reshaped_data = data.reshape(data.shape[0], data.shape[1], data.shape[2], 1)

    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=reshaped_data.shape[1:]))
    model.add(layers.MaxPooling2D((2, 2)))
    """model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))"""
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(2))

    model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])
              
    model.fit(reshaped_data, labels, epochs=10)

    # Convert the model to TensorFlow Lite and upload it to Cloud Storage
    source = ml.TFLiteGCSModelSource.from_keras_model(model)

    # Load a tflite file and upload it to Cloud Storage
    source = ml.TFLiteGCSModelSource.from_tflite_model_file('arasi.tflite')

    # Create the model object
    tflite_format = ml.TFLiteFormat(model_source=source)
    model = ml.Model(
        display_name="arasi_model",  # This is the name you use from your app to load the model.
        tags=["n/a"],             # Optional tags for easier management.
        model_format=tflite_format)

    # Add the model to your Firebase project and publish it
    new_model = ml.create_model(model)
    ml.publish_model(new_model.model_id)
    
    print("NETWORK BUILT")

## THREADING FUNCTIONS ##

@socketio.on('connect', namespace='/test')
def test_connect():
    # Need visibility of the global thread object
    global thread, fft_data
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
