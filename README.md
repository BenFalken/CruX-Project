# CruX-Project

A web-based application designed to continuously record motor-based EEG signals, with the output being a small avatar that moves either left or right depending on the signal.

Users' information is stored in firebase, and is fetched as the need arises. Threading is used to continuously update the webpage. The layout is a combination of HTML/CSS, Flask, and Bootstrap. We implement a deep learning model based on a tensorflow Conv2D network, using STFTs as inputs.

## Installation steps

Create a python environment

`$ mkdir myproject`

`$ cd myproject`

`$ python3 -m venv venv`

Activate the python environment

`$ . venv/bin/activate`

Now, install all required packages

`$ pip install -r requirements.txt`

To run, enter the command:

`$ export FLASK_APP=application`

`$ flask run`

Email to request the firebase_key.json certificate, and it will be provided.
