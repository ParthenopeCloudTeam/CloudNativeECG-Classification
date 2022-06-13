from utils import predict
from keras.models import load_model
from tensorflow import Session, get_default_graph
import numpy as np
from tensorflow.python.keras.backend import set_session
import pickle
import base64
from google.cloud import pubsub, storage
from google.oauth2 import service_account 
from flask import Flask, request


app = Flask(__name__)
    

@app.route("/", methods = ['POST'])
def index():
    
    envelope = request.get_json()
    print("envelope {}".format(envelope))
    if not envelope: 
            msg = "no Pub/Sub message received"
            print(f"error: {msg}")
            return f"Bad Request: {msg}", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            print(f"error: {msg}")
            return f"Bad Request: {msg}", 400

    pubsub_message = envelope["message"]
    print("message - envelope {}".format(pubsub_message))
    binary_package = base64.decodebytes(pubsub_message["data"].encode('utf_8'))
    package=pickle.loads(binary_package)
    tax_code = package["tax_code"]
    filename = package["filename"]
    ecg = package["ecg"]
    
    with session.as_default():
        with graph.as_default():           
            labels = predict(ecg, model)                      
    
    if "Noise" in labels:
        # Da M2 a M1
        blob = bucket.blob(tax_code)
        ecg_string = np.array2string(ecg)
        ecg_metadata = {
        "tax_code": tax_code,  # Nome file ecg col nome del file
        "filename": filename,
        "labels": "Rumore"}
        blob.metadata = ecg_metadata
        blob.upload_from_string(ecg_string, content_type="text/plain")
        blob.patch()
        
        print(f'Noise: {labels}') 
    else:
        # Da M2 a M3
        future = publisher.publish('projects/PROJECT_NAME/topics/nonNoise-ecg',  binary_package)
        future.result()
        print(f'Non noise: {labels}')
    
    return ("",204)


def initialization():
    global publisher, subscriber, bucket
    global graph, session, model
    
    print('Initializing M2.')

    credentials = service_account.Credentials.from_service_account_file("/home/src/key.json")
    publisher = pubsub.PublisherClient(credentials=credentials)
    subscriber = pubsub.SubscriberClient(credentials=credentials) 
    
    session = Session()
    set_session(session)
    graph = get_default_graph()
    model = load_model('/home/src/model.hdf5')
    with session.as_default():
        with graph.as_default():           
            dummy_ecg = np.empty([2,], dtype=np.int16)
            _ = predict(dummy_ecg, model)
    
    bucket_name = "BUCKET_NAME"
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(bucket_name)

    np.set_printoptions(threshold=np.inf)


initialization()