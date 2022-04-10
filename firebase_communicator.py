from firebase_admin import credentials, firestore, initialize_app, ml

class FirebaseCommunicator:
    def __init__(self):
        cred = credentials.Certificate('firebase_key.json')
        default_app = initialize_app(cred, options={
            'storageBucket': 'nam5',
        })

        db = firestore.client()

        self.open_recordings = db.collection('open_recordings')
        self.closed_recordings = db.collection('closed_recordings')
        self.metadata = db.collection('metadata')
    
    def get_open_file_count(self):
        return self.metadata.document("open_file_count").get().to_dict()['count']

    def get_closed_file_count(self):
        return self.metadata.document("closed_file_count").get().to_dict()['count']

    def update_open_file_count(self, file_count):
        self.metadata.document("open_file_count").update({'count': file_count})

    def update_closed_file_count(self, file_count):
        self.metadata.document("closed_file_count").update({'count': file_count})

    def add_data_to_open_recordings(self, file_count, data_chunk):
        self.open_recordings.document("recording_" + str(file_count)).set({'data': data_chunk})

    def add_data_to_closed_recordings(self, file_count, data_chunk):
        self.closed_recordings.document("recording_" + str(file_count)).set({'data': data_chunk})

    def get_data_from_open_recordings(self, file_count):
        return self.open_recordings.document("recording_" + str(file_count)).get().to_dict()['data']

    def get_data_from_closed_recordings(self, file_count):
        return self.closed_recordings.document("recording_" + str(file_count)).get().to_dict()['data']

    def save_network(self, model):
        # Load a tflite file and upload it to Cloud Storage
        source = ml.TFLiteGCSModelSource.from_keras_model(model)
        # Create the model object
        tflite_format = ml.TFLiteFormat(model_source=source)
        model = ml.Model(
            display_name="arasi_model",  # This is the name you use from your app to load the model.
            model_format=tflite_format)
        
        # Add the model to your Firebase project and publish it
        new_model = ml.create_model(model)
        ml.publish_model(new_model.model_id)
    
    def get_network(model_id):
        models = ml.list_models().iterate_all()
        for model in models:
            if model.model_id == model_id:
                return model