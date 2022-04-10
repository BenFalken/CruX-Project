from time import sleep
from const import *
import mne

class DataStreamer:
    def __init__(self):
        self.recording_class = "OFF" # At the outset, we are not recording for any state of mind; the system is off
        self.open_file_count = 0
        self.closed_file_count = 0
        self.data = []           # All of le data
        self.t = 0               # The current time, which tells us how to parse out the data into the site

    # Since we don't yet have the openbci headset, this data comes from a file which will be attached in the repository
    def collect_edf_data(self):
        raw_data = mne.io.read_raw_edf("demo_data/S001R01.edf")
        self.data = raw_data.get_data()[0].tolist()

    # Get all the data in a certain time window
    def get_data(self):
        self.t += DELAY
        return self.data[self.t-DELAY: self.t]

    def get_time(self):
        return self.t