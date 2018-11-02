import paho.mqtt.client as mqtt
import time
import datetime
import csv
from train_SVM import *

dt = datetime.datetime.now()
brokerHost = "localhost"
#brokerHost = "telemedicine.co.id"
#brokerHost = "192.168.137.158"
#port = 49560
#portWS = 49876
port = 1883
device_id = "ECG001"
logfile = 'log_csv/ekgSignal-%s-%s-%s-%s-%s.csv' % ("edan", dt.day, dt.month, dt.year, dt.hour)
topic_decision = "rhythm/"+device_id+"/n"

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


        # check result
        if(predict_ovo[1] == 0.):
            print "Status : Normal"
            clientMQTT.publish(topic_decision , "normal")
            return 0
        elif(predict_ovo[1] == 1.):
            print "Status : PVC"
            clientMQTT.publish(topic_decision, "pvc")
            return 1
        elif(predict_ovo[1] == 2.):
            print "Status : PAC"
            clientMQTT.publish(topic_decision, "pac")
            return 2
        elif(predict_ovo[1] == 3.):
            print "Status : AFIB"
            clientMQTT.publish(topic_decision, "afib")
            return 3
        elif(predict_ovo[1] == 4.):
            print "Status : Ventricular Tachycardia"
            clientMQTT.publish(topic_decision, "vt")
            return 4


# csvwrite
def write_tocsv(topic,data) :
    with open(logfile.replace("edan",topic), "a") as output_file:
        writer = csv.writer(output_file, delimiter=',', lineterminator='\r')
        writer.writerow(data)

#define callback
temp_result = 99
count_pvc = 0
count_pvc_tot= 0
def on_message(client, userdata, message):
    print "message topic=", message.topic , " - qos=", message.qos , " - flag=", message.retain
    if ("/ecg" in message.topic):
        device_topic = message.topic.split("/")[1]
        print(device_topic)
        receivedMessage = str(message.payload.decode("utf-8"))
        print "received message = " , receivedMessage
        global count_pvc_tot
        signal = receivedMessage.split(':')
        #signal[0] = int(time.time())
        #print(signal)
        csv_result = []
        csv_result.push(int(time.time()))
        csv_result.push(signal)

        # testing features
        features = np.array([], dtype=float)
        #convert to float
        for x in range(len(signal) - 1):
            # print(float(signal[x]))
            features = np.hstack((features,float(signal[x])))

        # check if features coming with id then don't use the id
        if(len(features) == 180):
            features = features[1:181]

        result = testingData(features,'ovo','ovo_voting_exp') # testing the signal

        global temp_result,count_pvc
        # check if result is pvc and result before is pvc also then count them for tachycardiac
        if(result == 1):
            count_pvc_tot = count_pvc_tot + 1
            resPVC = countPVC(count_pvc_tot)
            temp_result = result
            csv_result.push(resPVC)
            write_tocsv(device_topic, resPVC)
        else:
            count_pvc_tot = 0
            csv_result.push(result)
            write_tocsv(device_topic, signal)  # write signal to CSV

def countPVC(total):
    """
    Count PVC to decide Double, Triple Tachycardia
    :param total:
    :return:
    """
    if(total == 2):
        # double
        print "Status : Double Tachycardia"
        clientMQTT.publish(topic_decision, "dotac")
        return 5
    elif(total == 3):
        # triple
        print "Status : Triple Tachycardia"
        clientMQTT.publish(topic_decision, "tritac")
        return 6
    elif (total == 5):
        # VT
        print "Status : Ventricular Tachycardia"
        clientMQTT.publish(topic_decision, "vt")
        return 4

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+ str(rc))
    # subscribe the topic "ekg/device1/signal"
    # subTopic = "ekg/+/signal"  # + is wildcard for all string to that level
    subTopic = "rhythm/#"
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


print(int(time.time()))




