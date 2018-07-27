# Script Bash permettant l'éxécution en ligne de commande de notre script python en lui passant les identifiants de connexion en arguments

# arrete le script si une erreur survient
set -e

# execute le script python timer.py
python2.7 timer.py --endpoint a19taqm0wo1suf.iot.eu-central-1.amazonaws.com --rootCA root-ca-cert.pem --cert timer.cert.pem --key timer.private.key --thingName fireCheck --clientId alarm
