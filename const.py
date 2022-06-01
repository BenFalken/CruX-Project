# Constants for the stfts produced
STFT_T_SIZE = 50
STFT_F_SIZE = 50

## CONSTANTS AND STUFF ##
WINDOW_SIZE = 100
DATA_CHUNK_SIZE = 2400
DELAY = 800

# Cutoff frequencies
MIN_FREQ, MAX_FREQ = 3, 30

# Neural Network Training params
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 2

# Scaling factor for conversion between raw data (counts) and voltage potentials:
SCALE_FACTOR_EEG = (4500000)/24/(2**23-1) #uV/count
SCALE_FACTOR_AUX = 0.002 / (2**4)