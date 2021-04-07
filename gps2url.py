#!//usr/bin/python3
# This app reports the gps location to an URL every xx seconds,
# replacing variables in the url string.
# It works for the Sixfab Raspberry Pi Cellular IoT HAT 
# [https://sixfab.com/product/raspberry-pi-lte-m-nb-iot-egprs-cellular-hat/]a
# The endpoint URL string can contain the following variables that will be
# replaced with the values obtained from the GPS
# %LAT% = latitude in decimal format with a N/S as last byte (N=North, S=South)
# %LONG% = longitude in decimal format with a E/W as last byte (E=East, W=West)
# %HOSTNAME% = hostname set in the operating system, it can be used as Unique Id
# %SPEED% = Speed in Knots
# %TRUECOURSE% = direction of movement on the compass a value between 0 and 360
# %DATE% = Date from GPS network in format YYYY-MM-DD
# %TIME = Time received from GPS network in the format HH:MM:SS
# %SIGNATURE% = Strong authentication singature calculated as SHA3-256( %LAT% + %LONG% + %HOSTNAME% + secretseed)
# The signature blocks spoofing attacks, the scenario where an attacker could inject wrong locations.
# It's important to change the "secretseed" with your own string in production environment.
# The endpoit should verifiy the signature before storing the locations received.

# modules importation
import serial
import urllib.request
import socket
import time 
import hashlib
import sys, getopt
import ssl

############################ CUSTOM DEFAULT PARAMETERS #########################
endpoint="https://yourdomainname.org?lat=%LAT%&long=%LONG%&uid=%HOSTNAME%";
portwrite = "/dev/ttyUSB2"  # used to enabled the gps module
portread = "/dev/ttyUSB1"	    # for reading the gps coordinates
interval = 6.0	    # report the position every xx seconds
intervalsameposition= 300.0  # report the same position every xxx seconds
secretseed= "478c60b2f1e806f41f4b81d882594e8a54b9d2554dd1df30b9607024a7bb39ac"
################## END CUSTOM PARAMETERS #######################################
# functiont to decode coordinates
def decode(coord):
    #Converts DDDMM.MMMMM -> DD deg MM.MMMMM min
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    return deg + " deg " + min + "." + tail + " min"
    
# get command line parameters if any
try:
   opts, args = getopt.getopt(sys.argv[1:],"he:w:r:i:s:x:",["endpoint=","portwrite=","portread","interval","intervalsamepos","secretseed"])
except getopt.GetoptError:
   print("usage: gps2url.py --endpoint=<urlendpoint> --portwrite=</dev/ttyXXX> --portread=</dev/ttyXXX> --interval=<x> --intervalsamepos=<x> -- secretseed=<xxxxxxxxxxxxxxx>")
   sys.exit(2)
for opt, arg in opts:
   if opt == '-h':
      print("usage: gps2url.py --endpoint=<urlendpoint> --portwrite=</dev/ttyXXX> --portread=</dev/ttyXXX> --interval=<x> --intervalsamepos=<x> -- secretseed=<xxxxxxxxxxxxxxx>")
      sys.exit()
   elif opt in ("-e", "--endpoint"):
      endpoint = arg
   elif opt in ("-w", "--portwrite"):
      portwrite = arg
   elif opt in ("-r", "--portread"):
      portread = arg
   elif opt in ("-i", "--interval"):
      interval = arg    
   elif opt in ("-s", "--intervalsamepos"):
      intervalsameposition = arg        
   elif opt in ("-x", "--secretseed"):
      secretseed = arg        

# Enable the GPS module by sending the required AT commmand
print("[Info] Connecting Serial Port..")
try:
    serw = serial.Serial(portwrite, baudrate = 115200, timeout = 1,rtscts=True, dsrdtr=True)
    # for https://sixfab.com/product/raspberry-pi-lte-m-nb-iot-egprs-cellular-hat/
    print("Configuration: (1/5)")
    serw.write('AT+QGPS=1\r'.encode())
    time.sleep(1)
    # for https://docs.sixfab.com/docs/raspberry-pi-3g-4g-lte-base-hat-introduction
    print("Configuration: (2/5)")
    #serw.write('AT$GPSRST\r'.encode())
    #time.sleep(1)
    print("Configuration: (3/5)")
    #serw.write('AT$GPSNVRAM=15,0\r'.encode())
    #time.sleep(1)
    print("Configuration: (4/5)")
    serw.write('AT$GPSNMUN=2,1,1,1,1,1,1\r'.encode())
    time.sleep(1)
    serw.write('AT$GPSP=1\r'.encode())
    serw.close()
    time.sleep(1)
    print("Configuration: (5/5) completed")
except Exception as e: 
    print("[Error] Serial port connection failed. Please check the custom parameters")
    print(e)
    quit()

# initialize some variables
newread = 0.0
lastspeed="-1"
lasttimeurl=0.0
# set serial port parameters for receiving
print("[Info] Receiving GPS data\n")
ser = serial.Serial(portread, baudrate = 115200, timeout = 0.5,rtscts=True, dsrdtr=True)

# Start the loop to receive NMEA0183 messages
while True:
   data = ser.readline().decode('utf-8')
   # shows NMEA00183 message
   print(data, end='') 
   currenttm=time.time()
   # check $GPRMC message for position coordinates
   if data[0:6] == "$GPRMC" and currenttm >= newread :
        sdata = data.split(",")
        if sdata[2] == 'V':
            print("[Warning] GPS location not yet available\n")
            continue
        #parse data    
        tm = sdata[1][0:2] + ":" + sdata[1][2:4] + ":" + sdata[1][4:6] #time
        lat = decode(sdata[3]) 	     	#latitude
        dirLat = sdata[4]      	#latitude direction N/S
        lon = decode(sdata[5]) 		#longitude
        dirLon = sdata[6]      	#longitude direction E/W
        speed = sdata[7]       	#speed in knots
        trueCourse = sdata[8]   #true course
        dt = sdata[9][0:2] + "-" + sdata[9][2:4] + "-" + sdata[9][4:6] #date
        latitudev = lat.split()
        longitudev = lon.split()
        latitude=str(int(latitudev[0]) + (float(latitudev[2])/60))
        longitude=str(int(longitudev[0]) + (float(longitudev[2])/60)) 
        # print data        
        print("[Info] Date: %s time : %s, latitude : %s(%s), longitude : %s(%s), speed : %s,True Course : %s,"%   (dt,tm,latitude,dirLat,longitude,dirLon,speed,trueCourse))
        # Signature computation by SHA3-256
        tosign=latitude+dirLat+longitude+dirLon+socket.gethostname()+secretseed
        encoded_tosign = tosign.encode()
        bta = bytearray(encoded_tosign)
        signature=hashlib.sha3_256(bta).hexdigest()
        # replace variables
        buf=endpoint.replace("%LAT%",latitude+dirLat)
        buf1=buf.replace("%LONG%",longitude+dirLon)
        buf=buf1.replace("%HOSTNAME%",socket.gethostname())
        buf1=buf.replace("%SPEED%",speed)
        buf=buf1.replace("%SIGNATURE%",signature)
        buf1=buf.replace("%DATE%",dt)
        buf=buf1.replace("%TIME%",tm)
        endpoints=buf1.replace("%TRUECOURSE%",trueCourse)
        if lastspeed==speed and speed==0  and currenttm < (lasttimeurl+intervalsameposition):
            print("[Info] Position not changed, not sending to endpoint for now")
            newread=time.time()+interval
            continue
        # Call endpoint URL
        print("[Info] Contacting endpoint: %s\n"% endpoints)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:     
            with urllib.request.urlopen(endpoints,context=ctx) as response:
                answer = response.read()
        except Exception as e: 
            print("[Error] Endpoint not reachable with error:",e)
        #restart timers for sending URL
        lastspeed=speed
        newread=time.time()+interval
        lasttimeurl=time.time()
   time.sleep(0.1)
   