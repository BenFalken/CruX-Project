from scipy import signal
import numpy as np

from const import *

import tensorflow as tf
from tensorflow.keras import layers, models

# Le butterworth filter. It filters out the non-important frequencies for us
def filter_data(data, fs=128):
    nyq = 0.5 * fs             # Sample freq is 128
    low = MIN_FREQ / nyq
    high = MAX_FREQ / nyq
    b, a = signal.butter(9, [low, high], btype="band")  # Bandpass, which means we select a "band" of frequencies
    filtered = signal.lfilter(b, a, data)
    return filtered

def build_data(firebase_comm):
    print("****************** CREATING NETWORK ******************")
    open_file_count =  firebase_comm.get_open_file_count()
    closed_file_count =  firebase_comm.get_closed_file_count()

    ratio = open_file_count/closed_file_count

    if ratio < 0.8 or ratio > 1.25:
        print("It is ill advised to create a network with skewed data! Please record more data and try again.")
        return None, None

    all_data = np.zeros((open_file_count + closed_file_count, STFT_F_SIZE, STFT_T_SIZE))
    all_labels = np.zeros((open_file_count + closed_file_count, 1))

    random_indices = np.arange(open_file_count + closed_file_count)
    np.random.shuffle(random_indices)

    for count in range(open_file_count):
        data = firebase_comm.get_data_from_open_recordings(count)
        filtered_data = filter_data(data)
        f, t, data_stft = signal.stft(filtered_data, nperseg=196)
        #print(data_stft.shape)
        all_data[random_indices[count]] = np.abs(data_stft)
        all_labels[random_indices[count]] = 0

    for count in range(closed_file_count):
        data = firebase_comm.get_data_from_closed_recordings(count)
        filtered_data = filter_data(data)
        f, t, data_stft = signal.stft(filtered_data, nperseg=196)
        #print(data_stft.shape)
        all_data[random_indices[count + open_file_count]] = np.abs(data_stft)
        all_labels[random_indices[count + open_file_count]] = 1
    return all_data, all_labels


# Take in the training data (STFT, as an image) and labels. Output a trained network.
def train_network(train_images, train_labels, firebase_comm):

    test_images = train_images[90:]
    test_labels = train_labels[90:]

    train_images = train_images[:90]
    train_labels = train_labels[:90]

    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=train_images.shape[1:]))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(2))

    model.compile(optimizer='adam', loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=['accuracy'])
              
    model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))
    
    _, accuracy = model.evaluate(test_images, test_labels)
    print("ACCURACY: " + str(accuracy))

    firebase_comm.save_network(model)