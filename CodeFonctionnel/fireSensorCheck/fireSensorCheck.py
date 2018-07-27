#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

'''
    Fonctionnement : Ce script nous permet de recuperer les 10 dernieres valeurs
                     délivrées par chaque capteur afin de les analyser et de detecter
                     si un incendie s'est déclenché ou pas. Pour effectuer cette analyse
                     nous recuperons une valeur au debut et à la fin afin de réaliser une
                     différence entre les deux. Si le résultat de la différence est
                     superieur strictement à cinq alors un état "alarmFire" est transmis
                     sur la rubrique .../shadow/update/reported via le device shadow fireCheck,
                     dans le cas contraire un état "normal" est transmis sur la rubrique .../shadow/update.
                     Ce script permet aussi de detecter la defaillance d'un capteur
                     dans notre infrastructure en comparant le nombre actuel de capteur
                     avec celui precedent. Si un ou plusieurs capteurs sont défaillant
                     alors nous transmettons cette liste de capteur via le device shadow sensorCheck.
'''

# importation des librairies
import couchdb
# parser les arguments passés en paramètre
import argparse
import time
import json
import AWSIoTPythonSDK
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

'''
    Partie contenant nos fonctions
'''

"""
@summary:		  Cette méthode permet de comparer deux valeurs, dans notre cas
                  il sagit des UUID des différents capteurs reliés à notre
                  passerelle.
@param points: 	  x, y : données émises par les capteurs au format JSON
@returns : 		  informations nécéssaires au tri
"""
def cmpval(x,y):
    if x.get('uuid')>y.get('uuid'):
        return 1
    elif x.get('uuid')==y.get('uuid'):
        return 0
    else:
        return -1

"""
@summary:		  Ces méthodes permettent de mettre à jour l'état reporté dans le 'fire shadow' et
                  le 'sensor shadow'

@param points: 	  payload        : document JSON retourné
                  responseStatus : status de la réponse (accepté ou refusé)
                  token          : jeton permettant de suivre une requêtemp

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

'''
# configuration du journal
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)   # set to logging.DEBUG for additional logging
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
'''
# se débarasse des anciennes requetes
AWSIoTPythonSDK.MQTTLib.DROP_OLDEST = 0
# se débarasse des nouvelles requetes
AWSIoTPythonSDK.MQTTLib.DROP_NEWEST = 1

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

fireClient = fireCheckClient.getMQTTConnection()
# nous configurons cinq éléments maximum dans notre queue
fireClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_OLDEST)

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

# creation d'un périphérique de maniere persistance (abonnement)
deviceSensorCheckHandler = sensorCheckClient.createShadowHandlerWithName("sensorCheck", True)

# format json de notre document shadow comme exemple ceci sera modifié plus bas
# pour la détection d'une alarme
fireDict = {
    "state":
        {
            "reported":
            {
                "sensorState" : 'alarmFire',
                "sensors":
                [
                    {
                        "uuid": "d8567b67-ecff-4ebd-865f-7ec4354fbb0a",
                        "location": "001 Salon"
                    }
                ]
            }
        }
}
# pour la détection d'un capteur défaillant
sensorDict = {
    "state":
        {
            "reported":
            {
                "print": "yes",
                "sensors":
                [
                    "001 Salon",
                    "001 Cuisine"
                ]
            }
        }

}

# initialisation des variables booléennes globales
firstTimeSensor = True
firstTimeFire = True

# variable contenant l'état précédent afin de déterminer si un changement d'état s'est produit
previousState = ""

# Variable contenant les valeurs des UUID constant
UUID1 = "d8567b67-ecff-4ebd-865f-7ec4354fbb0a"
UUID2 = "7aea41b6-9f2f-44c9-9fd8-a6704b0e504f"
UUID3 = "1dbb3e6f-fecd-4f98-810d-999aa638f762"
# tableau contenant nos UUID
UUID = [UUID1, UUID2, UUID3]
# boucle infinie
while True:
    # connnexion à la base de donnée
    couch = couchdb.Server('http://admin:admin@raspberrypi.local:5985')

    # selection de notre base de donnée
    dbname = "fire_data_store"
    db = couch[dbname]

    """
        Phase de recupération des données dans la base de données fire_data_store
    """
    # initialisation de la liste de données
    # liste de capteur en fonction de leur UUID
    # {'uuid': u'd8567b67-ecff-4ebd-865f-7ec4354fbb0a', 'value': [u'001 salon', 29, 1531949933]}
    # ci-dessus un exemple de listUUID dans lequel 'value' : ['location', 'temperature or smoke value', 'timestamp']
    tempList = []
    smokeList = []

    # liste de liste de valeur de capteur de temperature par UUID
    allUUID = []
    # recuperation des données de type 'temperature'
    # filtrage des données de température par UUID
    for uuid in UUID:
        for item in db.view('tempView/temp', descending=False, limit=10, key=uuid):
            tempDict = {}
            tempDict['uuid'] = item.key
            tempDict['value'] = item.value
            tempList.append(tempDict)
        allUUID.append(tempList)
        tempList = []

    # recuperation des données de fumée
    for item in db.view('smokeView/smoke', descending=False, limit=10):
        smokeDict = {}
        smokeDict['uuid'] = item.key
        smokeDict['value'] = item.value
        smokeList.append(smokeDict)

    """
        Phase de traitement des capteurs défaillants
    """
    # initialisation de la liste contenant les capteurs fonctionnels au lancement du programme
    if firstTimeSensor == True:
        functionnalSensorsList = []
        previousSensorsList = []
        for item in allUUID:
            location = str(item[0].get('value')[0])
            functionnalSensorsList.append(location)
        previousSensorsList = functionnalSensorsList
        firstTimeSensor = False

    # affectation de la liste de capteurs fonctionnels courant
    currentSensorsList = []
    for item in allUUID:
        location = str(item[0].get('value')[0])
        currentSensorsList.append(location)

    # juste pour la simulation
    # currentSensorsList.pop()

    faultySensorsList = []
    # récupération des capteurs défaillant dans la liste (faultySensorsList)
    if currentSensorsList != functionnalSensorsList:
        for item in functionnalSensorsList:
            if item not in currentSensorsList:
                faultySensorsList.append(item)
    # nous effectuons une mise à jour du document shadow si la liste de capteur courant est différente
    # de celle précédente
    if currentSensorsList != previousSensorsList:
        previousSensorsList = currentSensorsList
        # cet état print joue la transition entre timer.py et nos vues afin d'afficher
        # après une minute si pas de changement d'état la liste des capteurs défaillants
        sensorDict['state']['reported']['print'] = "no"
        sensorDict['state']['reported']['sensors'] = faultySensorsList
        jsonString = json.dumps(sensorDict)
        # mis à jour du document shadow ayant pour clientid 'sensorCheck' avec un timeout de 5 secondes
        deviceSensorCheckHandler.shadowUpdate(jsonString, fireShadowCallback_Update, 5)


    """
        Phase de traitement de nos données de température et de fumée
    """
    # recuperation des valeurs de temperatures
    # pour chaque liste nous allons effectuer un traitement sur les valeurs de
    # temperature dans l'optique de retourner un état qui sera soit 'normal' soit
    # 'alarmFire'

    # traitement et génération des états (normal et warning)
    # initialisation de notre compteur de boucle
    i = 0

    # variable contenant l'état courant délivrépar notre analyse
    currentState = "normal"
    # variable dictionnaire permettant de récupérer des informations sur les capteurs
    sensors = {}
    sensors['uuid'] = ""
    sensors['location'] = ""

    # liste contenant les capteurs ayant détectés une alarme incendie
    sensorList = []
    # boucle de traitement mettant à jour l'état courant après analyse des données de température
    # après avoir recupérer les 10 dernières valeurs par capteur, nous faisons une
    # entre la troisième et la septième valeur de la liste de valeur afin de déterminer si
    # un potentiel incendie est détecté
    while i < len(allUUID):
        x1 = allUUID[i][2].get('value')[1] # recente valeur
        x2 = allUUID[i][6].get('value')[1] # ancienne valeur
        result = x1 - x2
        if result > 3:
            uuid = str(allUUID[i][0].get('uuid'))
            currentState = "alarmFire"
            location = str(allUUID[i][0].get('value')[0])
            sensors = {}
            sensors['uuid'] = uuid
            sensors['location'] = location
            sensorList.append(sensors)
        i = i + 1

    # test pour analyse des données de fumée
    # si un écart de 10 ou superieur est detecté alors l'état est mis à jour à 'alarmFire'
    x1 = smokeList[2].get('value')[1]
    x2 = smokeList[6].get('value')[1]
    result = x1 - x2
    if  result > 10:
         uuid = str(smokeList[0].get('uuid'))
         currentState = "alarmFire"
         location = str(smokeList[0].get('value')[0])
         sensors = {}
         sensors['uuid'] = uuid
         sensors['location'] = location
         sensorList.append(sensors)

    # le test effectué nous permet de conclure s'il sagit d'une alarme simultanée dans ce cas
    # nous lançons directement l'alarme sans prévenir le poste de garde et l'état 'alarmLaunched'
    # est mis à jour dans le document shadow
    if len(sensorList) >= 2:
        currentState = "alarmLaunched"

    # si premiere execution alors on affecte l'état courant à celui précédent
    if firstTimeFire or previousState is not currentState:
        previousState = currentState
        fireDict['state']['reported']['sensorState'] = currentState
        fireDict['state']['reported']['sensors'] = sensorList
        jsonString = json.dumps(fireDict)
        # mis à jour du document shadow ayant pour clientid 'fireCheck' avec un timeout de 5 secondes
        deviceFireCheckHandler.shadowUpdate(jsonString, fireShadowCallback_Update, 5)
        firstTimeFire = False
