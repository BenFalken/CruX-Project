from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from random import randint
from itertools import repeat
from const import *

class DataStreamer:
    def __init__(self):
        # Checks for what exactly the webpage is doing -- nothing, recording, streaming?
        self.is_recording_training_data = False
        self.is_streaming_testing_data = False
        self.recording_class = "OFF" # At the outset, we are not recording for any state of mind; the system is off
        # Tracks how many files we have stored in our database for left/right motion data
        self.left_motion_file_count = 0
        self.right_motion_file_count = 0
        # The user's current brain signals
        self.all_c3_data = []
        self.all_c4_data = []
        # The current time, which tells us how to parse out the data into the site
        self.current_time = 0    
        # Simple setup of our board
        self.init_board()

    # Attempts to connect to open bci cyton board
    def init_board(self):
        try:
            BoardShim.enable_dev_board_logger()
            params = BrainFlowInputParams()
            #params.serial_port = '/dev/cu.usbserial-4'
            self.board = BoardShim(-1, params) #BoardShim(BoardIds.CYTON_BOARD.value, params)
            
            self.board.prepare_session()
            self.board.start_stream()
        except Exception as e:
            print(e)
            print("Error connecting to board. Will stream data synthetically.")
    
    def standardize_length(self, signal):
        if len(signal) > DELAY:
            signal = signal[:DELAY]
        elif len(signal) < DELAY:
            percent_of_data_chunk_size = len(signal)/DELAY
            number_of_repetitions = int((1 - percent_of_data_chunk_size)/percent_of_data_chunk_size) + 1
            signal.extend(repeat(signal, number_of_repetitions))
            signal = signal[:DELAY]
        return signal

    # Get all the data in a certain time window. If board isn't connected, just return a string of ones
    def get_current_data(self):
        data = self.board.get_board_data(DATA_CHUNK_SIZE) # this gets data continiously
        c3_data_list = [val*SCALE_FACTOR_EEG for val in data[4]]
        c4_data_list = [val*SCALE_FACTOR_EEG for val in data[6]]

        #c3_data_list = self.standardize_length(c3_data_list)
        #c4_data_list = self.standardize_length(c4_data_list)
        
        self.all_c3_data.extend(c3_data_list)
        self.all_c4_data.extend(c4_data_list)

        if len(self.all_c3_data) > DATA_CHUNK_SIZE:
            self.all_c3_data = self.all_c3_data[-1*DATA_CHUNK_SIZE:]
        if len(self.all_c4_data) > DATA_CHUNK_SIZE:
            self.all_c4_data = self.all_c4_data[-1*DATA_CHUNK_SIZE:]

        self.current_time += len(c3_data_list)
        return c3_data_list, c4_data_list