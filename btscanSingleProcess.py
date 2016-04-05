import time
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt
import fcntl
import random
import requests#import RPi.GPIO as GPIO



DETECT_PIN = 5
CYCLE_TIME = 3.5


def bluetooth_rssi(addr):
    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()

    # Connect to device (to whatever you like)
    bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bt_sock.settimeout(10)
    result = bt_sock.connect_ex((addr, 1))	# PSM 1 - Service Discovery

    try:
        # Get ConnInfo
        reqstr = struct.pack("6sB17s", bt.str2ba(addr), bt.ACL_LINK, "\0" * 17)
        request = array.array("c", reqstr )
        handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack("8xH14x", request.tostring())[0]

        # Get RSSI
        cmd_pkt=struct.pack('H', handle)
        rssi = bt.hci_send_req(hci_sock, bt.OGF_STATUS_PARAM,
                     bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, cmd_pkt)
        rssi = struct.unpack('b', rssi[3])[0]

        # Close sockets
        bt_sock.close()
        hci_sock.close()

        return rssi

    except:
        return None

def scan():
	sigStrong = -20
	closest = ' '
	nearby_devices = bluetooth.discover_devices(duration = 5, lookup_names = True, flush_cache = True)
	if(len(nearby_devices) == 0):
		return "none found"
	for addr, name in nearby_devices:
		rssi = bluetooth_rssi(addr)
		if(rssi > sigStrong):
			sigStrong = rssi
			closest = name	
	return closest


def gpio():
	print " Starting GPIO SCAN \n"
	url = 'https://localhost:1337/User/create?name='
	urlData = ' '
	while True:	
		if(int(random.random()) % 2 == 0): #GPIO.input(DETECT_PIN)
			print "Sensor Touched"	
			data = scan()
			data = data.replace(' ', '')# to get rid of spaces in UUID so post wont fail
			print data
			#urlData = url + data #makes https://localhost:1337/User/create?name=UUID
			#resp = requests.post(urlData)



gpio()

