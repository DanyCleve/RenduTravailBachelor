#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import calendar
import datetime
from datetime import datetime

millis = int(round(time.time() * 1000))
print "Millisecondes   "
print millis 
print "     "

dt = datetime.now()
ms = dt.microsecond
print "Microsecondes   "
print ms
print "     "

import calendar, datetime
# heure au format UTC
d = datetime.datetime.utcnow()
# heure local
e = datetime.datetime.now()
print "POSIX   "
# conversion du format UTC au format POSIX
print calendar.timegm(e.timetuple())
print "                   "
# affichage au format UTC
print "Heure UTC utilisant la bibliothèque time"
print time.gmtime()
print "                   "
print "Heure local utilisant la bibliothèque time"
print time.localtime()
print "                   "
print "Heure UTC utilisant la bibliothèque datetime"
print e
print "                   "
print "Heure local utilisant la bibliothèque datetime"
print d


