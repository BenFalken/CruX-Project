# Constants for the stfts produced
STFT_T_SIZE = 99
STFT_F_SIZE = 99

## CONSTANTS AND STUFF ##
WINDOW_SIZE = 100       # How much data we are at in the graph window at once
DATA_CHUNK_SIZE = 9600  # We chunk the data and upload it to firebase. We do this in time series arrays sized to 1000 vals
DELAY = 10              # The delay is for the socket to function effectively. It chunks out how much data we get at a time. Without a good enough delay the program lags and breaks

# Cutoff frequencies
MIN_FREQ, MAX_FREQ = 3, 30

# Neural Network Training params
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 2