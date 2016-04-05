#!/usr/bin/python
import socket
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
import requests
import RPi.GPIO as GPIO


pulse_objects = Queue.Queue()

DETECT_PIN = 5
CYCLE_TIME = 3.5



def bluetooth_rssi(addr):
    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()

    # Connect to device (to whatever you like)
    bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    bt_sock.settimeout(10)
    result = bt_sock.connect_ex((addr, 1))  # PSM 1 - Service Discovery

    try:
        # Get ConnInfo
        reqstr = struct.pack('6sB17s', bt.str2ba(addr), bt.ACL_LINK, '\0' * 17)
        request = array.array('c', reqstr )
        handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack('8xH14x', request.tostring())[0]

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

def scan(pulse_objects):
    print ' Starting BT SCAN \n'
    while True:
        closest = ''  # reset
            sigStrong =- 20
        nearby_devices = bluetooth.discover_devices(duration=5, lookup_names=True, flush_cache=True)
        if(len(nearby_devices) == 0):  #if no devices
            closest = 'none found'
        for addr, name in nearby_devices:  #loops through list of scan results
            rssi = bluetooth_rssi(addr)
            if(rssi > sigStrong):  #sort
                sigStrong = rssi
                closest = name
        pulse_objects.put((closest))  #send value to other thread
        print closest


def gpio(pulse_objects):
    print ' Starting GPIO SCAN \n'
    url='https://localhost:1337/User/create?name='
    urlData=' '
    while True:
        if(GPIO.input(DETECT_PIN)):
            print 'Sensor Touched'
            data=pulse_objects.get()  #recv value of other thread

            # make https://localhost:1337/User/create?name=UUID
            urlData = url + data
            resp = requests.post(urlData)



t1 = Thread(target = gpio, args = (pulse_objects,))
t2 = Thread(target = scan, args = (pulse_objects,))

t1.start()
t2.start()
