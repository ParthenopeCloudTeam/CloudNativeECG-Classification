import numpy as np

def _preprocess(x):
    # Tronco l'intero ecg in modo che sia divisibile per 256
    trunc_samp = 256 * int(len(x) / 256)
    x = x[:trunc_samp]
    
    # Standardizzo
    mean = 7.6302314
    std = 227.32915
    x = (x - mean) / std

    # Aggiungo le dimensioni richieste da keras
    x = np.expand_dims(x,0)
    x = np.expand_dims(x,-1)
    return x

def _probs_to_labels(probs):
    probs = np.squeeze(probs)
    classes = ["Atrial-Fibrillation", "Normal-Rhythm", "Other-Rhythm", "Trash"]
    labels = []
    for sequence in probs:
        labels.append(classes[int(np.argmax(sequence,axis=0))])
    return labels

def predict(ecg, model):
    x = _preprocess(ecg)
    probs = model.predict(x, verbose=1)
    labels = " ".join(map(str,_probs_to_labels(probs)))
    return labels