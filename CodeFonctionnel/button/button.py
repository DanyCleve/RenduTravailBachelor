#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import Tkinter
from Tkinter import *
from tkMessageBox import *
# parser les arguments passés en paramètre
import argparse
import json
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import AWSIoTPythonSDK
from threading import Thread, RLock


# format json de notre document shadow comme exemple ceci sera modifié plus bas

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
jsonDictDes = {
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
                "print": "no"
                "sensors":
                [
                    "001 Salon",
                    "001 Cuisine"
                ]
            }
        }

}
'''
# variable contenant l'état et le numéro de version du shadow courant
sensorState = ""
printSensorList = ""
boutonState = ""
# liste contenant les capteurs reçus du document 'shadow'
sensorList = []
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
            # recuperation des documents json des devices shadow 'fireCheck' et 'sensorCheck'
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
            # recuperation des documents json des devices shadow 'fireCheck' et 'sensorCheck'
            deviceFireCheckHandler.shadowGet(sensorCallback, 5)
            time.sleep(10)

    def stop(self):
        self.running = False
"""
@summary:		  Cette méthode permet de mettre à jour l'état reporté dans le 'shadow'

@param points: 	  payload        : document JSON retourné
                  responseStatus : status de la réponse (accepté ou refusé)
                  token          : jeton permettant de suivre une requête

@returns : 		  --------
"""
def fireShadowCallback_Update(payload, responseStatus, token):

    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        # 'parsing' du payload afin de récupérer les valeurs
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~ Fire Shadow Update Accepted ~~~~~~~~~~~~~")
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
            global version
            global sensorState
            global sensorList
            jsonDict = json.loads(payload)

            if 'reported' in jsonDict['state']:
                sensorState = jsonDict['state']['reported']['sensorState']
                sensorList = jsonDict['state']['reported']['sensors']

            if 'desired' in jsonDict['state']:
                print ""

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
            global printSensorList
            global faultyVersion
            sensorDict = json.loads(payload)
            if 'print' in sensorDict['state']['reported']:
                printSensorList = sensorDict['state']['reported']['print']
                faultySensorsList = sensorDict['state']['reported']['sensors']
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Get request " + token + " rejected!")
"""
@summary:		  Cette méthode permet de modifier l'état de notre document shadow
                  (alarmFire -> alarmDeleted) si l'utilisateur appuie sur le bouton
                  "Suppress warning"

@param points: 	  --------

@returns : 		  --------
"""
def warningDelete():
    global jsonDictDes
    global sensorState
    global sensorList
    showinfo("WarningDelete", "The alarm is cancelled")
    sensorState = "alarmDeleted"
    jsonDictDes['state']['desired']['sensorState'] = sensorState
    jsonDictDes['state']['desired']['sensors'] = sensorList
    jsonString = json.dumps(jsonDictDes)
    deviceFireCheckHandler.shadowUpdate(jsonString, fireShadowCallback_Update, 5)

"""
@summary:		  Cette méthode permet de modifier l'état de notre document shadow
                  (alarmFire -> alarmLaunched) si l'utilisateur appuie sur le bouton
                  "Confirm warning"

@param points: 	  --------

@returns : 		  --------
"""
def warningConfirm():
     global jsonDictDes
     global sensorState
     global sensorList
     showinfo("WarningConfirmed", "The alarm is transmitted")
     sensorState = "alarmLaunched"
     jsonDictDes['state']['desired']['sensorState'] = sensorState
     jsonDictDes['state']['desired']['sensors'] = sensorList
     jsonString = json.dumps(jsonDictDes)
     deviceFireCheckHandler.shadowUpdate(jsonString, fireShadowCallback_Update, 5)

"""
@summary:		  Cette méthode permet d'afficher les différentes position des capteurs
                  dans une maison qui ont détectés une élévation de température dont la cause
                  peut être un incendie

@param points: 	  --------

@returns : 		  --------
"""
def showLocation():
    global sensorList
    for sensor in sensorList:
        showinfo("Location", sensor.get("location"))

"""
@summary:		  Ces méthodes ci-dessous permettent d'afficher respectivement les
                  lignes contenant nos éléments graphique pour interaction avec
                  l'utilisateur

@param points: 	  x        : position des éléments graphiques à savoir boutons et labels
                  x_       : position des espaces entre colonne
                  state    : état à afficher dans notre étiquette (label)
                  color    : couleur de l'étiquette (red -> etat alarmFire reçu, green -> autres états)

@returns : 		  --------
"""
def firstLine(x, x_, state, color, boutonState, alarmConfirm):
    y1 = 0
    y2 = 1
    y3 = 2
    y4 = 3
    y5 = 4
    y6 = 5
    y7 = 6

    columnSpace = "        "
    rowSpace = "                      "
    # espace entre chaque ligne dans la fenêtre

    lab2 = Label(frame, text=rowSpace)
    lab3 = Label(frame, text=rowSpace)
    lab4 = Label(frame, text=rowSpace)
    lab2.grid(column=x, row=y3)
    lab3.grid(column=x, row=y5)
    lab4.grid(column=x, row=y7)

    lab1 = Label(frame, text='state : ' + state, bg=color, fg="white")
    lab1.grid(column=x, row=y1)
    # nous affichons la liste de location des capteurs si l'alarme est lancée
    if alarmConfirm:
        btn0 = Button(frame, text="Location", command=showLocation, state="normal")
        btn0.grid(column=x, row=y2)
    else:
        btn0 = Button(frame, text="Location", command=showLocation, state=boutonState)
        btn0.grid(column=x, row=y2)

    btn1 = Button(frame, text="Suppress warning", command=warningDelete, state=boutonState)
    btn2 = Button(frame, text="Confirm warning", command=warningConfirm, state=boutonState)
    btn1.grid(column=x, row=y4, sticky="s")
    btn2.grid(column=x, row=y6, sticky="n")

    # espace entre chaque colonne dans la fenêtre
    lab5 = Label(frame, text=columnSpace)
    lab6 = Label(frame, text=columnSpace)
    lab5.grid(column=x_, row=y2)
    lab6.grid(column=x_, row=y3)


def secondLine(x, x_, state, color, boutonState, alarmConfirm):
    y1 = 7
    y2 = 8
    y3 = 9
    y4 = 10
    y5 = 11
    y6 = 12

    columnSpace = "        "
    rowSpace = "                      "
    # espace entre chaque ligne dans la fenêtre

    lab2 = Label(frame, text=rowSpace)
    lab3 = Label(frame, text=rowSpace)
    lab2.grid(column=x, row=y3)
    lab3.grid(column=x, row=y5)

    lab1 = Label(frame, text='state : ' + state, bg=color, fg="white")
    lab1.grid(column=x, row=y1)

    # nous affichons la liste de location des capteurs si l'alarme est lancée
    if alarmConfirm:
        btn0 = Button(frame, text="Location", command=showLocation, state="normal")
        btn0.grid(column=x, row=y2)
    else:
        btn0 = Button(frame, text="Location", command=showLocation, state=boutonState)
        btn0.grid(column=x, row=y2)

    btn1 = Button(frame, text="Suppress warning", command=warningDelete, state=boutonState)
    btn2 = Button(frame, text="Confirm warning", command=warningConfirm, state=boutonState)
    btn1.grid(column=x, row=y4, sticky="s")
    btn2.grid(column=x, row=y6, sticky="n")

    # espace entre chaque colonne dans la fenêtre
    lab5 = Label(frame, text=columnSpace)
    lab6 = Label(frame, text=columnSpace)
    lab5.grid(column=x_, row=y2)
    lab6.grid(column=x_, row=y3)


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



# Connexion à AWS IoT
fireCheckClient.connect()

# creation d'un périphérique de maniere persistance (abonnement)
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

# Connexion à AWS IoT
sensorCheckClient.connect()

fireClient = fireCheckClient.getMQTTConnection()
# nous configurons cinq éléments maximum dans notre queue
fireClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_OLDEST)

# création d'un périphérique de maniere persistance (abonnement)
deviceSensorCheckHandler = sensorCheckClient.createShadowHandlerWithName("sensorCheck", True)


"""
@summary:		  Cette méthode permet dafficher nos éléments graphique en fonction de l'état
                  reçu du 'device shadow' pour les capteurs défaillants et l'alarme incendie

@param points: 	  --------

@returns : 		  --------
"""
def printOnFrame():

    # variables globales
    global sensorList
    global sensorState
    global faultySensorsList
    # initialisation des valeurs par défaut pour le test
    houseNb = 1
    state = "normal"

    x = 0
    x_ = 2

    state = sensorState

    if sensorState == "alarmFire" and houseNb == 1:
        color = "red"
        boutonState = 'normal'
        alarmConfirm = False
    elif sensorState == "alarmLaunched" and houseNb is 1:
        color = "black"
        boutonState = 'disabled'
        alarmConfirm = True
    else:
        color = "green"
        boutonState = 'disabled'
        alarmConfirm = False

    firstLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 3
    x_ = 5
    # affichage constant des autres zones d'alarme
    color = "green"
    state = "normal"
    boutonState = 'disabled'
    alarmConfirm = False
    firstLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 6
    x_ = 8
    firstLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 9
    x_ = 11
    firstLine(x, x_, state, color, boutonState, alarmConfirm)


    x = 0
    x_ = 2
    secondLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 3
    x_ = 5
    secondLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 6
    x_ = 8
    secondLine(x, x_, state, color, boutonState, alarmConfirm)

    x = 9
    x_ = 11
    secondLine(x, x_, state, color, boutonState, alarmConfirm)

    # variable permettant de gerer l'espace entre les lignes de notre fenêtre
    rowSpace = "                      "
    x = 0
    y = 20
    # affichage de l'espace sur la fenêtre
    lab1 = Label(frame, text=rowSpace)
    lab1.grid(column=x, row=y)

    # Affichage pour les capteurs défaillants
    x = 0
    y = 22
    lab1 = Label(frame, text="List of faulty sensors")
    lab1.grid(column=x, row=y, rowspan = 8, columnspan = 15)

    x = 0
    y = 27
    lab1 = Label(frame, text=rowSpace)
    lab1.grid(column=x, row=y)

    # affichage de la liste déroulante
    scrollbar = Scrollbar(frame)
    listbox  = Listbox(frame, width = 85, height = 4, yscrollcommand = scrollbar.set)
    scrollbar.config (command = listbox.yview)
    pos = 0
    # affichage des capteurs défaillants dans la liste déroulante
    if printSensorList == "yes":
        while pos < len(faultySensorsList):
            listbox.insert (pos, faultySensorsList[pos].get('location'))
            pos += 1

    x = 0
    y = 30
    listbox.grid(column=x, row=y, rowspan = 8, columnspan = 15)
    x = 15
    y = 30
    scrollbar.grid(column=x, row=y, rowspan = 8, columnspan = 15)
    frame.update()
    frame.after(5000, printOnFrame)

# code principal (main)
# création de la fenetre racine
frame = Tk()
frame.title("alarmPanel")
frame.geometry("800x480")
fireThread = Fire()
sensorThread = Sensor()
fireThread.start()
sensorThread.start()


frame.after(0, printOnFrame)
frame.mainloop()
fireThread.stop()
fireThread.join()
sensorThread.stop()
sensorThread.join()
