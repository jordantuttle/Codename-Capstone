#!/usr/bin/python          
import socket#socket stuff
import time
import thread
import Queue
from threading import Thread
import struct
import array
import bluetooth
import bluetooth._bluetooth as bt
import fcntl
import datetime


pulse_objects = Queue.Queue()


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
	info=" "
	closest=''
	sigStrong=-20
	stamp = ' '
	scanResults = []
	nearby_devices = bluetooth.discover_devices(duration=5, lookup_names=True, flush_cache=True)
	if(len(nearby_devices)==0):
		return "none found"
	for addr, name in nearby_devices:
		rssi = bluetooth_rssi(addr)
		if(rssi > sigStrong):
			sigStrong = rssi
			closest = name
	ts = time.time()
	stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	info =stamp+" "+closest+ " rssi:"+str(sigStrong)	

	return info





def gpio(pulse_objects):
	print " Starting GPIO SCAN "#Jon put your code here
	count=0
	gpio=0
	while True:
		if(count % 5 == 0):
			gpio=1
		else:
			gpio=0
		if(gpio == 1):
			pulse_objects.put((gpio))#transfer var from one thread to 
		count=count+1
		

def init(pulse_objects):
	gpio=0
	s = socket.socket()         # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 8000               # Reserve a port for your service.
	s.bind((host, port))        # Bind to the port
	s.listen(5)                 # Now wait for client connection.
	while True:
		client, address = s.accept()
		gpio = pulse_objects.get()#add pushed		
		if(gpio == 1):	
			client.send(scan())
		client.close()

t1 = Thread(target = init, args = (pulse_objects,))
t2 = Thread(target = gpio, args = (pulse_objects,))

t1.start()
t2.start()


