from firebase_admin import credentials, firestore, initialize_app, ml
import requests

class FirebaseCommunicator:
    def __init__(self):
        # Firebase setup. Connects our site to the database
        cred = credentials.Certificate('firebase_key.json')
        self.bucket_name = 'arasi-3c613.appspot.com'
        self.app = initialize_app(cred, options={
            'storageBucket': self.bucket_name,
        })
        db = firestore.client()
        # All the database collections we reference
        self.open_recordings = db.collection('open_recordings')
        self.closed_recordings = db.collection('closed_recordings')
        self.metadata = db.collection('metadata')

    # Saves a keras model into firebase ml, so it can be used later
    def save_model(self, model, model_id="arasi_model"):
        # Load a tflite file and upload it to Cloud Storage
        source = ml.TFLiteGCSModelSource.from_keras_model(model)
        # Create the model object
        tflite_format = ml.TFLiteFormat(model_source=source)
        model = ml.Model(
            display_name=model_id,  # This is the name you use from your app to load the model.
            model_format=tflite_format)
        # Add the model to your Firebase project and publish it
        new_model = ml.create_model(model)
        ml.publish_model(new_model.model_id)
    
    # Downloads the model from firebase and stores it as a tflite file
    def get_model_source(self):
        URL = "https://firebasestorage.googleapis.com/v0/b/arasi-3c613.appspot.com/o/Firebase%2FML%2FModels%2Ffirebase_ml_model.tflite?alt=media&token=70bafff8-46f5-4509-b1dd-02cbef979ea0"
        response = requests.get(URL)
        arasi_file_write = open("arasi_model.tflite", "wb")
        arasi_file_write.write(response.content)
        arasi_file_write.close()
    
    # I really really really don't wanna define these fucking functions. It's just getters and setters anyway

    def update_open_file_count(self, file_count):
        self.metadata.document("open_file_count").update({'count': file_count})

    def update_closed_file_count(self, file_count):
        self.metadata.document("closed_file_count").update({'count': file_count})

    def add_data_to_open_recordings(self, file_count, c3_data_chunk, c4_data_chunk):
        self.open_recordings.document("recording_" + str(file_count) + "_c3").set({'data': c3_data_chunk})
        self.open_recordings.document("recording_" + str(file_count) + "_c4").set({'data': c4_data_chunk})

    def add_data_to_closed_recordings(self, file_count, c3_data_chunk, c4_data_chunk):
        self.closed_recordings.document("recording_" + str(file_count) + "_c3").set({'data': c3_data_chunk})
        self.closed_recordings.document("recording_" + str(file_count) + "_c4").set({'data': c4_data_chunk})

    def get_open_file_count(self):
        return self.metadata.document("open_file_count").get().to_dict()['count']

    def get_closed_file_count(self):
        return self.metadata.document("closed_file_count").get().to_dict()['count']

    def get_data_from_open_recordings(self, file_count):
        c3_data = self.open_recordings.document("recording_" + str(file_count) + "_c3").get().to_dict()['data']
        c4_data = self.open_recordings.document("recording_" + str(file_count) + "_c4").get().to_dict()['data']
        return c3_data, c4_data

    def get_data_from_closed_recordings(self, file_count):
        c3_data = self.closed_recordings.document("recording_" + str(file_count) + "_c3").get().to_dict()['data']
        c4_data = self.closed_recordings.document("recording_" + str(file_count) + "_c4").get().to_dict()['data']
        return c3_data, c4_data