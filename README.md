# GPS2URL

GPS2URL reports the gps location to an URL every xx seconds, replacing variables in the url endpoint.


## Hardware Requirements:

- [Raspberry Pi Model B](https://www.raspberrypi.org/products/raspberry-pi-4-model-b/)

- [Sixfab Raspberry Pi Cellular IoT HAT](https://sixfab.com/product/raspberry-pi-lte-m-nb-iot-egprs-cellular-hat/)

it should works with previous versions of Raspberry PI.

## Operating System

GPS2URL requires [Raspberry PI OS(https://www.raspberrypi.org/products/raspberry-pi-4-model-b) 

it has been tested on the version released on 2021-01-11.

## Installation

Make the configuration as illustrated from [SixFab Official Documentation] (https://docs.sixfab.com/docs/getting-started-with-cellular-hat-other-sim)

***ATTENTION *** -  Remember to start the GPS pushing the button PWRKEY on the SixFab board.

Install the following packages:
```bash
apt-get -y install python3 python3-setuptools python3-pip python3-rpi.gpio python3-smbus
```

copy gps2url.py in any folder of your choice.
You can customize the default parameters changing this part of gps2url.py:
```python
############################ CUSTOM DEFAULT PARAMETERS #########################
endpoint="https://yourdomainname.org?lat=%LAT%&long=%LONG%&uid=%HOSTNAME%";
portwrite = "/dev/ttyUSB2"  # used to enabled the gps module
portread = "/dev/ttyUSB1"           # for reading the gps coordinates
interval = 6.0      # report the position every xx seconds
intervalsameposition= 300.0  # report the same position every xxx seconds
secretseed= "478c60b2f1e806f41f4b81d882594e8a54b9d2554dd1df30b9607024a7bb39ac"
################## END CUSTOM PARAMETERS #######################################
```

## Running

To see the possible parameters:

```bash
python3 gps2url.py -h
```

You can pass the following parameters on the command line:

-e <xxxurlxxxx> or --endpoint=<xxxxxxurlxxxxxx>   - It's the url address of
your endpoint that can contain variables replaced with the gps data. See the
section below, "Endpoint Variables". The url endpoint should be embeddead
between the ' '. For example:

python2 gps2url.py --endpoint='https://yourdomainname.org?lat=%LAT%&long=%LONG%&uid=%HOSTNAME%'

-p </dev/ttyUSBx> or --portread=</dev/ttyUSBx> - it's the serial port used to read the GPS data.

-w </dev/ttyUSBx> or --portwrite=</dev/ttyUSBx> - it's the serial port used to configure the modem SixFab Module.

-i <xx>  or --interval=<xx>  - The seconds of interval before sending the data to the endpoint.

-s <xxx> or  --intervalsamepos=<xxx> - The seconds of interval before sending  the position if it is not changed from the last sending.

-x <xxxxxxxxxxxxx> or --secretseed=<xxxxxxxxxxxxxxxx> - A secret seed used to generate a signature for strong authentication. 
It's calculated as SHA3-256( latitude + longitude + hostname + secretseed) and transformed in hex decimal lower case string.
This signature will block spoofing attacks, the scenario where an attacker could inject wrong locations.
The endpoit should verifiy the signature before storing the locations received. 

Here an example:
python3 gps2url.py --endpoint='https://yourdomainname.org?lat=%LAT%&long=%LONG%&uid=%HOSTNAME%' --interval=10 --intervalsamepos=300

you can run in background the application adding:  >/dev/null &

example:
python3 gps2url.py --endpoint='https://yourdomainname.org?lat=%LAT%&long=%LONG%&uid=%HOSTNAME%' --interval=10 --intervalsamepos=300>/dev/null &



## Endpoint Variables
The endpoint URL string can contain the following variables that will be  replaced with the values obtained from the GPS as follows:

%LAT% = latitude in decimal format with a N/S as last byte (N=North, S=South)

%LONG% = longitude in decimal format with a E/W as last byte (E=East, W=West)

%HOSTNAME% = hostname set in the operating system, it can be used as Unique Id

%SPEED% = Speed in Knots

%TRUECOURSE% = direction of movement on the compass a value between 0 and 360

%DATE% = Date from GPS network in format YYYY-MM-DD

%TIME = Time received from GPS network in the format HH:MM:SS

%SIGNATURE% = Strong authentication singature calculated as SHA3-256( %LAT% + %LONG% + %HOSTNAME% + secretseed)

The signature blocks spoofing attacks, the scenario where an attacker could inject wrong locations.
It's important to change the "secretseed" with your own string in production environment.
 The endpoit should verifiy the signature before storing the locations received. 


## Other Info

The GPS module may need some minutes to sync the satellite network once started. 

The GPS DOES not work inside buildings, it must have a clear of sight
visibility with minimum 3 satellites.


