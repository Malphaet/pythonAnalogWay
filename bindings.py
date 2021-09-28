#!/bin/python3

################################
# IMPORTS
# import socketserver
import socket
import sys
import threading

################################
# CONFIG VARIABLES
_IPSELF = "192.168.0.140" # Could be usefull for multi IP networks

_HOSTS = [("192.168.0.140",10500)]
_VERBOSE=True

_MSGSIZE=4096

if _VERBOSE:
    def dprint(*args):
        print(*args)
else:
    dprint=lambda x:None
################################
#


_DEVICES_VALUES={
    257:"Eikos2",
    258:"Saphyr",
    259:"Pulse2",
    260:"SmartMatriX2",
    261:"QuickMatriX",
    262:"QuickVu",
    282:"Saphyr - H",
    283:"Pulse2 - H",
    284:"SmartMatriX2 - H",
    285:"QuickMatriX – H"
}

_LAYERS={
    "Audio":7,
    "Logo2":6,
    "Logo1":5,
    "PIP4":4,
    "PIP3":3,
    "PIP2":2,
    "PIP1":1,
    "Frame":0
}

_SRC={
    "No input":0,
    "Input 1":1,"Frame 1":1,
    "Input 2" :2, "Frame 2":2,
    "Input 3 ":3, "Frame 3":3,
    "Input 4" :4, "Frame 4":4,
    "Input 5" :5, "Frame 5":5,
    "Input 6" :6, "Frame 6":6,
    "Input 7" :7, "Frame 7":7,
    "Input 8" :8, "Frame 8":8,
    "Input 9" :9, "Frame 9":9,
    "Input 10" :10, "Frame 10":10,
    "Color":11, "Black":11
}

_FILTER={
    "Auto-Scale":1,
    "Source":2,
    "Pos/Size":4,
    "Transparency":8,
    "Cropping":16,
    "Border":32,
    "Transition":64,
    "Timing":128,
    "Effects":256,
    "Audio layer":512,
    "No filter":0
}


################################
# CLASS DEFINITIONS

class analogController(object):
    "AnalogWay Controller, controls one AnalogWay device"

    def __init__(self,ip,port):
        self.sck=None
        self.ip=ip
        self.port=port

        try:
            dprint('[pAW:INFO] Creating socket')
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dprint('[pAW:INFO] Getting remote IP address')
            host=_IPSELF
            remote_ip = socket.gethostbyname( host )

        except socket.error:
            print('[pAW:ERROR] Failed to create socket')
            sys.exit()
        except socket.gaierror:
            print('[pAW:ERROR] Hostname could not be resolved. Exiting')
            sys.exit()

    def connect(self):
        """The device acts as a server. Once the TCP connection is established, the controller shall
            check that the device is ready, by reading the READY status, until it returns the value 1.
            [*] (* <value>) The controller shall wait and retry until it receives the value 1
        """
        dprint('[pAW:INFO] Connecting to server, {self.ip}:{self.port}'.format(self=self))
        self.sck.connect((self.ip,self.port))
        dprint('[pAW:INFO] Sending data to server')
        self.sendData("*\r\n")
        self.waitfor(b'*1\r\n')

    def getDevice(self):
        """This read only command gives the device type
        [?] (DEV <value>) <values>:_DEVICES_VALUES
        """
        self.sendData("?")
        self.waitfor(b'DEV259\r')

    def getVersion(self):
        """his read only command gives the version number of the command set.
        It is recommended to check that this value matches the one expected by the controller.
        [VEvar] (VEvar<version>)
        """
        pass

    def getStatus(self,value=3):
        """Reading a change of values
        [<value>#] (# <rvalue>) The controller must wait for <rvalue> to equals 0 for the end of enumeration
        <value>:1 All register values 3: Only non default values
        """
        pass

    def _keepAlive(self,val=1):
        """Send a keepalive to check (and ensure) the connection is still up
        [<val1>SYpig] Will return the invert of the value sent: 0x0000 0000 will return 0xFFFF FFFF
        """
        pass

    def changeLayer(self,screen,ProgPrev,layer,src):
        """Change the layer of selected
        [<scrn>,<ProgPrev>,<layer>,<src>PRinp] Change the input on a selected layer
        <scrn> is the RCS² screen number minus 1.
        <ProgPrev> is 0 for Program, 1 for Preview.
        <layer> is a value representing the destination Layer.
        <src> is a value representing the input source.
        """ #Rinp0,1,7,5\r\nPRinp0,1,1
        pass

    def takeAvailable(self,*screens):
        """Test for take availability
        [<scrn>,GCtav] Test take availability on screen <scrn>
        (GCtav<scrn>,0) : Take is unavailable
        (GCtav<scrn>,1) : Take is available"""
        for screen in screens:
            pass

    def take(self,screen):
        """ Take a specific screen
        [Wait for the TAKE availability on all screen] takeAvailable (screen1,screen2,etc...)
        [<scrn>,1GCtak] Launch the TAKE action
        (GCtak<scrn>,1) : Take in progress
        (GCtav<scrn>,0) : Take is unavailable
        (GCtak<scrn>,0) : Take finished <--- Waiting for
        (GCtav<scrn>,1) : Take is available
        """

    def takeAll(self):
        """Take all screens
        [Wait for the TAKE availability on all screen] takeAvailable (screen1,screen2,etc...)
        [1,GCtal] Launch the TAKE ALL action
            Only value 1 is allowed, machine will immediately acknowledge the command, then will do the
            transition on both screens and last will answer with the 0 value after the end of the TAKE ALL command.
        (GCtal1) Take all in progress
        (GCtav<scrn>,0) : Take is unavailable
        (GCtav<scrn>,0) : Take is unavailable
        (GCtal0) : Take all is finished <--- Waiting for
        (GCtak<scrn>,1) : Take is available
        (GCtak<scrn>,1) : Take is available
        """

        pass

    def loadMM(screenF,memory,screenT,ProgPrev,filter):
        """Load a master memory to a screen
        <scrnF>,<mem>,<scrnT>,<prgPrv>,<fltr>,1 GClrq ()
        Filter: This parameter allows excluding some preset elements from recalling
        ProgPrev: This parameter gives the destination preset number, either Program (current preset) or Preview (next preset)
        screenT: This parameter gives the destination screen number. If only one screen is available, due to device type or device mode, the screen number 0 shall be used
        memory: This parameter gives the memory slot number to load. The allowed range of values is 0 to 7, corresponding to memories 1 to 8
        screenF: This parameter gives the origin screen number, the one from which was recorded the preset. Used with the <scrnT> parameter,
                 they allow loading in a screen a preset stored from the other, in matrix mode.

        """
        pass


    def quickFrame(self,screen,action=0):
        """Display (1), Hide(0) a quickFrame
            Display : <scrn>,1CTqfa (CTqfa<scrn>, 1)
            Hide :    <scrn>,0CTqfa (CTqfa<scrn>, 0)
        """
        pass

    def quickFrameAll(self,action):
        """Display/Hide a quickFrame on all screens
            Display: 1CTqfl (CTqfl 1 R F)
            Hide:    0CTqfl (CTqfl 0 R F)
        """

    def connectionSequence(self):
        "Execute the full connection sequence"
        self.connect()
        self.getDevice()
        self.getVersion()
        self.getStatus()

    def waitfor(self,value):
        """Wait for a specific return value, blocking"""
        notfound=True
        while notfound:
            reply=self.sck.recv(_MSGSIZE)
            dprint ("[pAW:INFO] Received:",reply)

            if reply==value:
                dprint("Found")
                return

    def sendData(self,data):
        "Send data through the socket"
        try:
            self.sck.sendall(data.encode())
        except socket.error:
            print ('[pAW:ERROR] Send failed of data :',data)
            sys.exit()

#####################
# TESTING
if __name__ == '__main__':
    ctrl1=analogController(*_HOSTS[0])
    ctrl1.connectionSequence()

    ctrl1.waitfor("")
    # # Receive data
    # print('# Receive data from server')
    # while True:
    #     reply = s.recv(4096)
    #
    #     print (reply)
    # # thread function
    # def threaded(c):
    #     while True:
    #
    #         # data received from client
    #         data = c.recv(1024)
    #         if not data:
    #             print('Bye')
    #
    #             # lock released on exit
    #             print_lock.release()
    #             break
    #
    #         # reverse the given string from client
    #         data = data[::-1]
    #
    #         # send back reversed string to client
    #         c.send(data)
    #
    #     # connection closed
    #     c.close()
    #
    #
    # def Main():
    #     host = ""
    #
    #     # reverse a port on your computer
    #     # in our case it is 12345 but it
    #     # can be anything
    #     port = 12345
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     s.bind((host, port))
    #     print("socket binded to port", port)
    #
    #     # put the socket into listening mode
    #     s.listen(5)
    #     print("socket is listening")
    #
    #     # a forever loop until client wants to exit
    #     while True:
    #
    #         # establish connection with client
    #         c, addr = s.accept()
    #
    #         # lock acquired by client
    #         print_lock.acquire()
    #         print('Connected to :', addr[0], ':', addr[1])
    #
    #         # Start a new thread and return its identifier
    #         start_new_thread(threaded, (c,))
    #     s.close()
    #
    #
    # if __name__ == '__main__':
    #     Main()
