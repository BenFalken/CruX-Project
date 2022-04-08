# CruX-Project

A web-based application designed to continuously record motor-based EEG signals, with the output being a small avatar that moves either left or right depending on the signal.

Users' information is stored in firebase, and is fetched as the need arises. Threading is used to continuously update the webpage. The layout is a combination of HTML/CSS, Flask, and Bootstrap.

## Installation steps

CREATE AN ENVIRONMENT

`$ mkdir myproject`

`$ cd myproject`

`$ python3 -m venv venv`

ACTIVATE THE ENVIRONMENT

$ . venv/bin/activate

NOW, INSTALL FLASK AND THE SOCKET IN THE ENVIRONMENT YOU HAVE CREATED AND ACTIVATED

`$ pip install -r requirements.txt`

Ask for the firebase certificate and it will be provided.
To run, you must install all required packages using python 3. To run, enter the command:

$ export FLASK_APP=application

$ flask run
