from time import sleep
from const import *
import mne

import argparse
import time
import numpy as np
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
from pylsl import StreamInfo, StreamOutlet

class DataStreamer:
    def __init__(self):
        self.is_recording_training_data = False
        self.is_streaming_testing_data = False

        self.recording_class = "OFF" # At the outset, we are not recording for any state of mind; the system is off
        self.open_file_count = 0
        self.closed_file_count = 0

        self.all_data = []

        BoardShim.enable_dev_board_logger()
        params = BrainFlowInputParams()
        params.serial_port = '/dev/cu.usbserial-4'
        self.board = BoardShim(BoardIds.CYTON_BOARD.value, params) # added cyton board id here
        
        self.board.prepare_session()
        self.board.start_stream()

        self.current_time = 0    # The current time, which tells us how to parse out the data into the site

    # Get all the data in a certain time window
    def get_current_data(self):
        data = self.board.get_board_data(DELAY) # this gets data continiously
        self.current_time += DELAY
        data_list = [val*SCALE_FACTOR_EEG for val in data[0]]
        self.all_data.extend(data_list)
        if len(self.all_data) > DATA_CHUNK_SIZE:
            self.all_data = self.all_data[-1*DATA_CHUNK_SIZE:]
        return data_list