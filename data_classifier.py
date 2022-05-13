from scipy import signal
import numpy as np

from const import *

import tensorflow as tf
from tensorflow.keras import layers, models

class DataClassifier:
    def __init__(self, firebase_comm):
        self.firebase_comm = firebase_comm
        self.data = None
        self.labels = None
        self.model = None
        self.count = 0
        self.viable_data = True

    # Fetches the number of files pertaining to eyes open, eyes closed data
    def initialize_file_counts(self):
        self.open_file_count =  self.firebase_comm.get_open_file_count()
        self.closed_file_count =  self.firebase_comm.get_closed_file_count()

    # Checks if our data is balanced enough
    def check_if_data_viable(self):
        try:
            file_count_ratio = self.open_file_count/self.closed_file_count
            if file_count_ratio < 0.8 or file_count_ratio > 1.25:
                print("It is ill advised to create a network with skewed data! Please record more data and try again.")
                self.viable_data = False
        except:
            print("It is ill advised to create a network with skewed data! Please record more data and try again.")
            self.viable_data = False

    # Create an array that will hold all of our necessary data
    def initialize_data_and_labels(self):
        self.all_data = np.zeros((self.open_file_count + self.closed_file_count, STFT_F_SIZE, STFT_T_SIZE, 1))
        self.all_labels = np.zeros((self.open_file_count + self.closed_file_count, 1))
        self.random_indices = np.arange(self.open_file_count + self.closed_file_count)
        np.random.shuffle(self.random_indices)

    # Le butterworth filter. It filters out the non-important frequencies for us
    def filter_data(self, data, fs=128):
        nyq = 0.5 * fs
        low = MIN_FREQ / nyq
        high = MAX_FREQ / nyq
        b, a = signal.butter(9, [low, high], btype="band")  # Bandpass, which means we select a "band" of frequencies
        filtered = signal.lfilter(b, a, data)
        return filtered

    # Add data from the database to our classifier
    def load_in_data(self, data, label):
        for signal in data:
            signal = signal.to_dict()['data']
            filtered_signal = self.filter_data(signal)
            if filtered_signal.size < DATA_CHUNK_SIZE:
                remaining_size = int(DATA_CHUNK_SIZE - filtered_signal.size)
                filtered_normalized_signal = np.concatenate([filtered_signal, int(filtered_signal[-1])*np.ones((remaining_size))])
            f, t, signal_stft = signal.stft(filtered_normalized_signal, nperseg=196)
            signal_stft = np.abs(signal_stft)
            for i in range(STFT_F_SIZE):
                for j in range(STFT_T_SIZE):
                    self.all_data[self.random_indices[self.count]][i][j][0] = signal_stft[i][j]
            self.all_labels[self.random_indices[self.count]] = label
            self.count += 1

    # Verifies, initializes and loads our data and labels
    def build_data(self):
        print("****************** CREATING NETWORK ******************")
        self.initialize_file_counts()
        self.check_if_data_viable()
        if not self.viable_data:
            return None, None
        self.initialize_data_and_labels()
        # Load in open eyes data
        open_data = self.firebase_comm.open_recordings.stream()
        self.load_in_data(data=open_data, label=0)
        # Load in closed eyes data
        closed_data = self.firebase_comm.closed_recordings.stream()
        self.load_in_data(data=closed_data, label=1)
        return self.all_data, self.all_labels

    # Makes our keras model
    def make_model(self, input_shape):
        self.model = models.Sequential()
        self.model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
        self.model.add(layers.MaxPooling2D((2, 2)))
        self.model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        self.model.add(layers.MaxPooling2D((2, 2)))
        self.model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(64, activation='relu'))
        self.model.add(layers.Dense(2))

    # Takes in the training data (STFT, as an image) and labels. Outputs a trained network
    def train_network(self, train_images, train_labels):
        test_images = train_images[20:]
        test_labels = train_labels[20:]

        train_images = train_images[:20]
        train_labels = train_labels[:20]

        self.make_model(input_shape=train_images.shape[1:])

        self.model.compile(optimizer='adam', loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=['accuracy'])
        self.model.fit(train_images, train_labels, epochs=10)
        
        _, accuracy = self.model.evaluate(test_images, test_labels)
        print("ACCURACY: " + str(accuracy))

        self.firebase_comm.save_model(self.model)

    # This is used to covert single signals streamed from the headset into a usuable format
    def convert_signal(self, data):
        converted_input = np.zeros((1, STFT_F_SIZE, STFT_T_SIZE, 1))
        data = self.filter_data(data)
        f, t, data_stft = signal.stft(data, nperseg=196)
        data_stft = np.abs(data_stft)
        for i in range(STFT_F_SIZE):
            for j in range(STFT_T_SIZE):
                converted_input[0][i][j][0] = data_stft[i][j]
        return converted_input

    # Classifies the signal streamed in from the headset
    def classify_input(self, data):
        self.firebase_comm.get_model_source()
        # Load TFLite model and allocate tensors.
        interpreter = tf.lite.Interpreter(model_path="arasi_model.tflite")
        interpreter.allocate_tensors()
        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        # Get input
        data = self.convert_signal(data)
        # Test model on random input data.
        input_data = np.array(data, dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        # The function 'get_tensor()' returns a copy of the tensor data.
        # Use 'tensor()' in order to get a pointer to the tensor.
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return output_data