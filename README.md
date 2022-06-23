# CruX-Project

A web-based application designed to continuously record motor-based EEG signals, with the output being a small avatar that moves either left or right depending on the signal.

Users' information is stored in firebase, and is fetched as the need arises. Threading is used to continuously update the webpage. The layout is a combination of HTML/CSS, Flask, and Bootstrap. We implement a deep learning model based on a tensorflow Conv2D network, using STFTs as inputs.

## Installation steps
The following steps assume you already have `git`, `conda`, and `python3.10` installed. Note: if you already have an SSH key set up, it's better to clone via SSH than HTTPS.

```bash
cd
git clone https://github.com/BenFalken/CruX-Project.git
cd CruX-Project
conda create -n crux-project
conda activate crux-project
conda install -c conda-forge liblsl
pip install -r requirements.txt
```

Then contact someone on our team to obtain `firebase_key.json`, and put that directly inside the `CruX-Project` directory. You can now run the application by visiting `http://127.0.0.1:5000/` in your browser while running `flask run` from terminal.

Site is also accessible at: [https://arasi-site.herokuapp.com](https://arasi-site.herokuapp.com)

## Known bugs
* OpenBCI headset often buffers and fails to connect, likely a hardware issue
* "fwoop" sound effect in game cannot be played multiple times in Safari (but it does work in Chrome)
* The game assumes the update loop is called at 60Hz. If you with a 120Hz frame rate, everything moves twice as fast
* Releasing an arrow key makes puffy stop moving even if the other arrow key is being pressed
