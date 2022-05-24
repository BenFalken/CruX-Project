from time import sleep
from const import *
from random import randint

import argparse
import time
import numpy as np
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
from pylsl import StreamInfo, StreamOutlet

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
            params.serial_port = '/dev/cu.usbserial-4'
            self.board = BoardShim(BoardIds.CYTON_BOARD.value, params) # added cyton board id here
            
            self.board.prepare_session()
            self.board.start_stream()
        except:
            print("Error connecting to board. Will stream data synthetically.")

    # Get all the data in a certain time window. If board isn't connected, just return a string of ones
    def get_current_data(self):
        try:
            data = self.board.get_board_data(DELAY) # this gets data continiously
            c3_data_list = [val*SCALE_FACTOR_EEG for val in data[1]]
            c4_data_list = [val*SCALE_FACTOR_EEG for val in data[1]]
            
            if len(self.all_c3_data) > DATA_CHUNK_SIZE:
                self.all_c3_data = self.all_c3_data[-1*DATA_CHUNK_SIZE:]
            if len(self.all_c4_data) > DATA_CHUNK_SIZE:
                self.all_c4_data = self.all_c4_data[-1*DATA_CHUNK_SIZE:]
        except:
            c3_data_list = [randint(-10, 10) for _ in range(DELAY)]
            c4_data_list = [randint(-10, 10) for _ in range(DELAY)]
        self.all_c3_data.extend(c3_data_list)
        self.all_c4_data.extend(c4_data_list)
        self.current_time += DELAY
        return c3_data_list, c4_data_list