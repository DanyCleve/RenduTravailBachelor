#!/usr/bin/env python
# -*- coding: utf-8 -*-

# parser les arguments passés en paramètre
import argparse
import json
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from threading import Thread
import threading
import AWSIoTPythonSDK

# format json de notre document shadow comme exemple ceci sera modifié plus bas
# json reçu
fireDict = {
    "state":
        {
            "reported":
            {
                "sensorState": 'state',
                "sensors":
                [
                    {
                        "uuid": "u1",
                        "location": "Salon"
                    }
                ]
            }
        }
}
# json désiré par l'utilisateur
'''
fireDict = {
    "state":
        {
            "desired":
            {
                "sensorState": 'state',
                "sensors":
                [
                    {
                        "uuid": "u1",
                        "location": "Salon"
                    }
                ]
            }
        }
}
'''
# json utilisé pour les capteurs défaillants
sensorDict = {
    "state":
        {
            "reported":
            {
                "print": "no",
                "sensors":
                [
                    "001 Salon",
                    "001 Cuisine"
                ]
            }
        }

}
# variable contenant l'état et le numéro de version du shadow courant
sensorState = ""
version = 0
faultyVersion = 0
sensorStateDesired = ""
payloadString = ""
printState = ""

# liste contenant les capteurs reçus du document 'shadow'
sensorList = []
sensorListDesired = []
faultySensorsList = []

# threads permettant d'éffectuer des GET sur la rubrique continuellement
class Fire(Thread):

    # constructeur
    def __init__(self):
        Thread.__init__(self)
        self.running = True


    # fonction exécutée par tous les threads dès leur Lancement
    def run(self):
        while self.running:
            # récuperation du document json 'fireCheck' si changement d'état
            # ce thread permet de récuperer l'état mis à jour par le controlleur (fireSensorCheck)
            # soit par la vue (interface graphique) avec un timeout de 5 secondes
            deviceFireCheckHandler.shadowGet(fireCallback, 5)
            time.sleep(10)

    def stop(self):
        self.running = False


class Sensor(Thread):

    # constructeur
    def __init__(self):
        Thread.__init__(self)
        self.running = True


    # fonction exécutée par tous les threads dès leur Lancement
    def run(self):
        while self.running:
            # récupération du document json 'sensorCheck' si changement d'état
            # ce thread permet de récupérer la liste des capteurs défaiilants
            deviceFireCheckHandler.shadowGet(sensorCallback, 5)
            time.sleep(10)
    def stop(self):
        self.running = False

# creation de notre classe Thread pour l'alarme incendie
"""
@summary:		  Cette classe permet de changer d'état (alarmFire -> alarmLaunched) après 30 secondes
                  et aussi de changer l'état reçu du bouton (alarmDeleted -> normal) après 30 secondes
                  afin que l'action de l'utilisateur soit visible et prise en compte si cet état (normal -> alarmFire)
                  venait à être changer au même moment.

"""

class FireTimer(Thread):

    # constructeur
    def __init__(self, sensorState, version):
        Thread.__init__(self)
        self.sensorState = sensorState
        self.version = version


    # fonction exécutée par tous les threads dès leur Lancement
    def run(self):
        # attente pendant 30 secondes avant de tester si la version du document shadow
        # a été mis à jour
        time.sleep(30)
        # si la version est inchangé alors on passe à l'état alarmLaunched
        if self.version == version:
            fireDict['state']['reported']['sensorState'] = "alarmLaunched"
            fireDict['state']['reported']['sensors'] = sensorList
            jsonString = json.dumps(fireDict)
            deviceFireCheckHandler.shadowUpdate(jsonString, fireShadowCallback_Update, 5)

"""
@summary:		  Cette classe permet de changer l'état reçu du bouton (alarmDeleted -> normal) après 30 secondes
                  afin que l'action de l'utilisateur soit visible et prise en compte si cet état (normal -> alarmFire)
                  venait à être changer au même moment.

"""
class FireDeltaTimer(Thread):

    # constructeur
    def __init__(self, payloadString):
        Thread.__init__(self)
        self.payloadString = payloadString


    # fonction exécutée par tous les threads dès leur Lancement
    def run(self):
        # attente pendant 30 secondes avant de tester si la version du document shadow
        # a été mis à jour
        time.sleep(30)
        fireDict['state']['reported']['sensorState'] = "normal"
        self.payloadString = json.dumps(payloadDict)
        deviceFireCheckHandler.shadowUpdate(self.payloadString, fireShadowCallback_Update, 5)



class SensorTimer(Thread):

    # constructeur
    def __init__(self, version):
        Thread.__init__(self)
        self.version = version


    # fonction exécutée par tous les threads dès leur Lancement
    def run(self):
        # attente avant de tester si la version est resté inchangé dans ce cas
        # on affiche la liste des capteurs défaillants dans l'interface graphique
        time.sleep(30)

        if self.version == faultyVersion:
            sensorDict['state']['reported']['print'] = "yes"
            sensorDict['state']['reported']['sensors'] = faultySensorsList
            jsonString = json.dumps(sensorDict)
            deviceSensorCheckHandler.shadowUpdate(jsonString, sensorShadowCallback_Update, 5)

"""
@summary:		  Cette méthode permet de mettre à jour l'état reporté dans le 'shadow'
                  à partir de l'état désiré contenu dans le message 'delta'

@param points: 	  payload        : document JSON retourné
                  responseStatus : status de la réponse (accepté ou refusé)
                  token          : jeton permettant de suivre une requêtemp

@returns : 		  --------
"""

def fireShadowCallback_Delta(payload, responseStatus, token):
    # conversion de la chaine de caractere json en dictionnaire python

    payloadDict = json.loads(payload)
    print("++++++++ Received Fire Shadow Delta ++++++++++")
    print(payload)
    print("+++++++++++++++++++++++\n\n")
    global sensorStateDesired
    global fireDict

    if 'reported' in payloadDict['state'] :
        print ""

    if 'desired' in payloadDict['state']:
        sensorStateDesired = payloadDict['state']['desired']['sensorState']
        if sensorStateDesired == "alarmLaunched":
            fireDict['state']['reported']['sensorState'] = "alarmLaunched"
            fireDict['state']['reported']['sensors'] = sensorList
            fireString = json.dumps(fireDict)
            deviceFireCheckHandler.shadowUpdate(fireString, fireShadowCallback_Update, 5)

"""
@summary:		  Ces méthodes permettent de mettre à jour l'état reporté dans le 'fire shadow'
                  et le 'sensor shadow'

@param points: 	  payload        : document JSON retourné
                  responseStatus : status de la réponse (accepté ou refusé)
                  token          : jeton permettant de suivre une requête

@returns : 		  --------
"""
def fireShadowCallback_Update(payload, responseStatus, token):

    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~ Fire Shadow Update Accepted ~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def sensorShadowCallback_Update(payload, responseStatus, token):

    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~ Sensor Shadow Update Accepted ~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

"""
@summary:		  Ces méthodes permettent de recupérer le document json du 'fire shadow' et
                  du 'sensor shadow'

@param points: 	  payload        : document JSON retourné
                  responseStatus : status de la réponse (accepté ou refusé)
                  token          : jeton permettant de suivre une requête

@returns : 		  --------
"""
def fireCallback(payload, responseStatus, token):
        if responseStatus == "timeout":
            print("Get request " + token + " time out!")
        if responseStatus == "accepted":
            print("~~~~~~~~~~ Fire Shadow get Accepted~~~~~~~~~~~~~")
            print("Get request with token: " + token + " accepted!")
            print(payload)
            # définition de nos variables globales utilisées par le FireTimer
            # correspondant à notre classe de Thread
            global version
            global sensorState
            global sensorList
            global fireDict

            fireDict = json.loads(payload)

            if 'reported' in fireDict['state'] :
                sensorState = fireDict['state']['reported']['sensorState']
                sensorList = fireDict['state']['reported']['sensors']

            if 'desired' in fireDict['state']:
                print ""
            version = fireDict['version']
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Get request " + token + " rejected!")

def sensorCallback(payload, responseStatus, token):
        if responseStatus == "timeout":
            print("Get request " + token + " time out!")
        if responseStatus == "accepted":
            print("~~~~~~~~~~ Sensor Shadow get Accepted~~~~~~~~~~~~~")
            print("Get request with token: " + token + " accepted!")
            print(payload)
            global faultySensorsList
            global faultyVersion
            global printState
            sensorDict = json.loads(payload)
            if 'print' in sensorDict['state']['reported']:
                printSensorList = sensorDict['state']['reported']['print']
                faultySensorsList = sensorDict['state']['reported']['sensors']
            faultyVersion = sensorDict['version']
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Get request " + token + " rejected!")


# se débarasse des anciennes requetes
AWSIoTPythonSDK.MQTTLib.DROP_OLDEST = 0
# se débarasse des nouvelles requetes
AWSIoTPythonSDK.MQTTLib.DROP_NEWEST = 1

# lecture des paramètres passés en ligne de commande
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="lightController",
                    help="Targeted client id")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
thingName = args.thingName
clientId = args.clientId

# Connexion du device shadow (firecheck) pour l'alarme incendie
# Initialisation du client shadow
fireCheckClient = AWSIoTMQTTShadowClient(clientId)
fireCheckClient.configureEndpoint(host, 8883)
fireCheckClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# configuration du client shadow
fireCheckClient.configureAutoReconnectBackoffTime(1, 32, 20)
fireCheckClient.configureConnectDisconnectTimeout(10)  # 10 sec
fireCheckClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connexion à AWS IoT du client fireCheck (device shadow)
fireCheckClient.connect()

fireClient = fireCheckClient.getMQTTConnection()
# nous configurons cinq éléments maximum dans notre queue
fireClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_OLDEST)

# connexion persistante (abonnement) du device shadow fireCheck
deviceFireCheckHandler = fireCheckClient.createShadowHandlerWithName(thingName, True)

# Connexion du device shadow (sensorCheck) pour les capteurs défaillants
# Initialisation du client shadow
sensorCheckClient = AWSIoTMQTTShadowClient("sensorCheck")
sensorCheckClient.configureEndpoint(host, 8883)
sensorCheckClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# configuration du client shadow
sensorCheckClient.configureAutoReconnectBackoffTime(1, 32, 20)
sensorCheckClient.configureConnectDisconnectTimeout(10)  # 10 sec
sensorCheckClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connexion à AWS IoT du client sensorCheck (device shadow)
sensorCheckClient.connect()

# connexion persistante (abonnement) du device shadow sensorCheck
deviceSensorCheckHandler = sensorCheckClient.createShadowHandlerWithName("sensorCheck", True)

# cette ligne permet la suppression du document JSON dans le device shadow
# deviceFireCheckHandler.shadowDelete(fireCallback, 5)
#
# écoute sur le delta si un écart survient entre l'état 'reported' et 'desired'
deviceFireCheckHandler.shadowRegisterDeltaCallback(fireShadowCallback_Delta)

fireThread = Fire()
sensorThread = Sensor()
fireThread.start()
sensorThread.start()

# boucle infinie
while True:

    # cette ligne permet la suppression du document JSON dans le device shadow
    # deviceFireCheckHandler.shadowDelete(fireCallback, 5)


    if sensorState == "alarmFire":
        thread = FireTimer(sensorState, version)
        thread.start()
        thread.join()

    if len(faultySensorsList) != 0 and printState == "no":
        thread = SensorTimer(faultyVersion)
        thread.start()
        thread.join()

    if sensorStateDesired == "alarmDeleted":
        thread = FireDeltaTimer()
        thread.start()
        thread.join()

fireThread.stop()
fireThread.join()

sensorThread.stop()
sensorThread.join()
