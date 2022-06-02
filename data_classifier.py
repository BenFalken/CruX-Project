from scipy import signal
from scipy.ndimage import gaussian_filter
from tensorflow.keras import layers, models
from const import *
import numpy as np
import tensorflow as tf

class DataClassifier:
    def __init__(self, firebase_comm):
        self.firebase_comm = firebase_comm
        self.data = None
        self.labels = None
        self.model = None
        self.count = 0
        self.viable_data = True
        self.model_fetched = False

    # Fetches the number of files pertaining to left/right motion data
    def initialize_file_counts(self):
        self.left_motion_file_count =  self.firebase_comm.get_left_motion_file_count()
        self.right_motion_file_count =  self.firebase_comm.get_right_motion_file_count()

    # Checks if our data is balanced enough
    def check_if_data_viable(self):
        file_count_ratio = self.left_motion_file_count / self.right_motion_file_count
        """
        if file_count_ratio < 0.8 or file_count_ratio > 1.25:
            print("It is ill-advised to create a network with skewed data! Please record more data and try again.")
            self.viable_data = False
        """

    # Create an array that will hold all of our necessary data
    def initialize_data_and_labels(self):
        num_images = self.left_motion_file_count + self.right_motion_file_count
        rows_per_img = STFT_F_SIZE
        columns_per_img = STFT_T_SIZE
        self.all_data = np.zeros((num_images, rows_per_img, columns_per_img, 1))
        self.all_labels = np.zeros((num_images, 1))
        # Hmmm maybe shuffle data later on? this isn't well encapsulated since random_indices is defined here but only used in another function
        self.random_indices = np.arange(num_images)
        np.random.shuffle(self.random_indices)

    # Le butterworth filter. It filters out the non-important frequencies for us
    def filter_data(self, data, fs=128):
        nyq = 0.5 * fs
        low = MIN_FREQ / nyq
        high = MAX_FREQ / nyq
        b, a = signal.butter(9, [low, high], btype="band")  # Bandpass, which means we select a "band" of frequencies
        # What are a and b? what do signal.butter and signal.lfilter do?
        b_notch, a_notch = signal.iirnotch(30, 5, 128)
        filtered = signal.filtfilt(b_notch, a_notch, data)
        b_notch, a_notch = signal.iirnotch(31, 5, 128)
        filtered = signal.filtfilt(b_notch, a_notch, data)
        b_notch, a_notch = signal.iirnotch(32, 5, 128)
        filtered = signal.filtfilt(b_notch, a_notch, filtered)
        filtered = signal.lfilter(b, a, filtered)
        return filtered

    def preprocess_signal(self, data):
        data = (data - np.min(data)) / (np.max(data) - np.min(data))
        filtered_signal = self.filter_data(data)
        f, t, signal_stft = signal.stft(filtered_signal, nperseg=196)
        signal_stft = np.abs(signal_stft)
        mean = np.mean(signal_stft)
        var = np.std(signal_stft)
        outlier = mean + 2*var
        signal_stft[signal_stft > outlier] = mean
        signal_stft = gaussian_filter(signal_stft, sigma=1)
        return signal_stft

    # Add data from the database to our classifier
    def load_in_data(self, data, label):
        self.count = 0
        for signal in data:
            signal_dict = signal.to_dict()
            c3_signal = signal_dict['c3_data']
            c4_signal = signal_dict['c4_data']
            
            c3_signal_stft = self.preprocess_signal(c3_signal)
            c4_signal_stft = self.preprocess_signal(c4_signal)

            for i in range(STFT_F_SIZE):
                for j in range(STFT_T_SIZE):
                    self.all_data[self.random_indices[self.count]][i][j][0] = (c3_signal_stft[i][j]/c4_signal_stft[i][j])
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
        # Load in left motion data
        left_motion_data = self.firebase_comm.left_motion_recordings.stream()
        self.load_in_data(data=left_motion_data, label=0)
        # Load in right motion data
        right_motion_data = self.firebase_comm.right_motion_recordings.stream()
        self.load_in_data(data=right_motion_data, label=1)
        return self.all_data, self.all_labels

    # Makes our keras model
    def make_model(self, input_shape):
        # What are all these settings??
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
    def train_network(self, images, labels):
        num_images = len(images)
        assert num_images == len(labels)

        num_of_train_images = int(num_images * .2)

        # Split 20% of the data into the test set and the rest into the training set
        test_images = images[num_of_train_images:]
        test_labels = labels[num_of_train_images:]
        train_images = images[:num_of_train_images]
        train_labels = labels[:num_of_train_images]

        self.make_model(input_shape=train_images.shape[1:])

        self.model.compile(optimizer='adam', loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=['accuracy'])
        self.model.fit(train_images, train_labels, epochs=10)
        
        _, accuracy = self.model.evaluate(test_images, test_labels)
        print(f'ACCURACY: {accuracy}')

        self.firebase_comm.save_model(self.model)

    # This is used to covert single signals streamed from the headset into a usuable format
    def convert_signal(self, c3_data, c4_data):
        converted_input = np.ones((1, STFT_F_SIZE, STFT_T_SIZE, 1))
        c3_data = self.filter_data(c3_data)
        c4_data = self.filter_data(c4_data)
        f, t, c3_data_stft = signal.stft(c3_data, nperseg=196)
        f, t, c4_data_stft = signal.stft(c4_data, nperseg=196)
        c3_data_stft = np.abs(c3_data_stft)
        c4_data_stft = np.abs(c4_data_stft)
        for i in range(STFT_F_SIZE):
            for j in range(STFT_T_SIZE):
                converted_input[0][i][j][0] *= c3_data_stft[i][j]
                converted_input[0][i][j][0] /= c4_data_stft[i][j]
        return converted_input

    # Classifies the signal streamed in from the headset
    def classify_input(self, c3_data, c4_data):
        if not self.model_fetched:
            self.firebase_comm.get_model_source()
            self.model_fetched = True
        # Load TFLite model and allocate tensors.
        interpreter = tf.lite.Interpreter(model_path = 'arasi_model.tflite')
        interpreter.allocate_tensors()
        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        # Get input
        data = self.convert_signal(c3_data, c4_data)
        # Test model on random input data.
        input_data = np.array(data, dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        # The function 'get_tensor()' returns a copy of the tensor data.
        # Use 'tensor()' in order to get a pointer to the tensor.
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return output_data
