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

class DataClassifier:
    def __init__(self, firebase_comm):
        self.firebase_comm = firebase_comm
        self.data = None
        self.labels = None
        self.model = None
    def build_data(self):
        print("****************** CREATING NETWORK ******************")

        open_file_count =  self.firebase_comm.get_open_file_count()
        closed_file_count =  self.firebase_comm.get_closed_file_count()

        try:
            ratio = open_file_count/closed_file_count
            if ratio < 0.8 or ratio > 1.25:
                print("It is ill advised to create a network with skewed data! Please record more data and try again.")
                return None, None
        except:
            print("It is ill advised to create a network with skewed data! Please record more data and try again.")
            return None, None

        all_data = np.zeros((open_file_count + closed_file_count, STFT_F_SIZE, STFT_T_SIZE, 1))
        all_labels = np.zeros((open_file_count + closed_file_count, 1))

        random_indices = np.arange(open_file_count + closed_file_count)
        np.random.shuffle(random_indices)

        count = 0

        open_data = self.firebase_comm.open_recordings.stream()
        for data in open_data:
            data = data.to_dict()['data']
            filtered_data = filter_data(data)
            if filtered_data.size < DATA_CHUNK_SIZE:
                remaining_size = int(DATA_CHUNK_SIZE - filtered_data.size)
                filtered_normalized_data = np.concatenate([filtered_data, int(filtered_data[-1])*np.ones((remaining_size))])
            f, t, data_stft = signal.stft(filtered_normalized_data, nperseg=196)
            data_stft = np.abs(data_stft)
            for i in range(STFT_F_SIZE):
                for j in range(STFT_T_SIZE):
                    all_data[random_indices[count]][i][j][0] = data_stft[i][j]
            #all_data[random_indices[count]] = np.abs(data_stft)
            all_labels[random_indices[count]] = 0
            count += 1

        closed_data = self.firebase_comm.closed_recordings.stream()
        for data in closed_data:
            data = data.to_dict()['data']
            filtered_data = filter_data(data)
            if filtered_data.size < DATA_CHUNK_SIZE:
                remaining_size = int(DATA_CHUNK_SIZE - filtered_data.size)
                filtered_normalized_data = np.concatenate([filtered_data, int(filtered_data[-1])*np.ones((remaining_size))])
            f, t, data_stft = signal.stft(filtered_normalized_data, nperseg=196)
            data_stft = np.abs(data_stft)
            #all_data[random_indices[count]] = np.abs(data_stft)
            for i in range(STFT_F_SIZE):
                for j in range(STFT_T_SIZE):
                    all_data[random_indices[count]][i][j][0] = data_stft[i][j]
            all_labels[random_indices[count]] = 1
            count += 1
        
        return all_data, all_labels

    # Take in the training data (STFT, as an image) and labels. Output a trained network.
    def train_network(self, train_images, train_labels):

        test_images = train_images[20:]
        test_labels = train_labels[20:]

        train_images = train_images[:20]
        train_labels = train_labels[:20]

        self.model = models.Sequential()
        self.model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=train_images.shape[1:]))
        self.model.add(layers.MaxPooling2D((2, 2)))
        self.model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        self.model.add(layers.MaxPooling2D((2, 2)))
        self.model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(64, activation='relu'))
        self.model.add(layers.Dense(2))

        self.model.compile(optimizer='adam', loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=['accuracy'])
                
        self.model.fit(train_images, train_labels, epochs=10)
        
        _, accuracy = self.model.evaluate(test_images, test_labels)
        print("ACCURACY: " + str(accuracy))

        self.firebase_comm.save_network(self.model)