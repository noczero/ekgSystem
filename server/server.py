import paho.mqtt.client as mqtt
import time
import datetime
import csv
from train_SVM import *

dt = datetime.datetime.now()
brokerHost = "192.168.1.2"
brokerHost = "hantamsurga.net"
#brokerHost = "192.168.137.158"
port = 49877
#portWS = 49876
#port = 1883
logfile = 'ekgSignal-%s-%s-%s.csv' % (dt.day, dt.month, dt.year)

def featureExtraction(signal):
    num_leads = 1
    leads_flag = [1, 0]  # MLII, V1
    print("Feature Extraction : Wavelets...")

    f_wav = np.empty((0, 23 * num_leads))

    f_wav_lead = np.empty([])
    f_wav_lead = compute_wavelet_descriptor(signal, 'db1' , 3)

    print("Feature Extraction : My Extraction...")
    myExtraction = compute_my_own_descriptor(signal,90,90)
    f_wav_lead = np.hstack((f_wav_lead , myExtraction))
    print(f_wav_lead)
    return f_wav_lead

# testing
def testingData(signal,multi_mode,voting_strategy):

    # load trained SVM Model
    # model_svm_path = "svm_models\ovo_rbf_MLII_rm_bsln_wvlt_weighted_C_100.joblib.pkl" # just wvlt
    model_svm_path = "svm_models\ovo_rbf_MLII_myMorph_wvlt_weighted_C_100.joblib.pkl" # wvlt and mymorph
    svm_model = joblib.load(model_svm_path)

    feature = featureExtraction(signal)
    feature = np.vstack((feature,feature))

    if multi_mode == 'ovo':
        decision_ovo = svm_model.decision_function(feature)

        if voting_strategy == 'ovo_voting':
            predict_ovo, counter = ovo_voting(decision_ovo, 5)

        elif voting_strategy == 'ovo_voting_both':
            predict_ovo, counter = ovo_voting_both(decision_ovo, 5)

        elif voting_strategy == 'ovo_voting_exp':
            predict_ovo, counter = ovo_voting_exp(decision_ovo, 5)

        #print(predict_ovo)
        #print("Result" + str(predict_ovo))
        # svm_model.predict_log_proba  svm_model.predict_proba   svm_model.predict ...
        #perf_measures = compute_AAMI_performance_measures(predict_ovo, labels)

        if(predict_ovo[1] == 0.):
            print "Status : Normal"
            clientMQTT.publish("rhythm/ECG004/n" , "normal")
        elif(predict_ovo[1] == 1.):
            print "Status : PVC"
            clientMQTT.publish("rhythm/ECG004/n", "pvc")
        elif(predict_ovo[1] == 2.):
            print "Status : PAC"
            clientMQTT.publish("rhythm/ECG004/n", "pac")



# csvwrite
def write_tocsv(data) :
    with open(logfile, "a") as output_file:
        writer = csv.writer(output_file, delimiter=',', lineterminator='\r')
        writer.writerow(data)

#define callback
def on_message(client, userdata, message):
    print "message topic=", message.topic , " - qos=", message.qos , " - flag=", message.retain
    receivedMessage = str(message.payload.decode("utf-8"))
    print "received message = " , receivedMessage

    signal = receivedMessage.split(':')
    #print(signal)
    write_tocsv(signal) # write signal to CSV

    # testing features
    features = np.array([], dtype=float)
    #convert to float
    for x in range(len(signal) - 1):
        # print(float(signal[x]))
        features = np.hstack((features,float(signal[x])))
    #features = np.vstack((features,features)) #become 2 d array

    #print(features[0][1:181])
    if(len(features) == 180):
        features = features[1:181]

    testingData(features,'ovo','ovo_voting') # testing the signal

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+ str(rc))
    # subscribe the topic "ekg/device1/signal"
    # subTopic = "ekg/+/signal"  # + is wildcard for all string to that level
    subTopic = "rhythm/ECG004/ecg"
    print "Subscribe topic ", subTopic
    clientMQTT.subscribe(subTopic)

# create client object
clientMQTT = mqtt.Client("client-Server")

# set callback
clientMQTT.on_message = on_message
clientMQTT.on_connect = on_connect

# connection established
print "connecting to broker" , brokerHost
clientMQTT.connect(brokerHost,port) # connect to broker

clientMQTT.loop_forever() # loop forever







