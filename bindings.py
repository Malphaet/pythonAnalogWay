#!/bin/python3

################################
# IMPORTS
# import socketserver
import socket, threading
import sys,time
import re
from _thread import start_new_thread
################################
# CONFIG VARIABLES
_IPSELF = "192.168.0.140" # Could be usefull for multi IP networks

_HOSTS = [("192.168.0.140",10500)]
_VERBOSE=True

_MSGSIZE=4096
_TIMEOUT=0.5
_MSG_ENDING=b"\r\n"

################################
# BIG DEFINES

_NO_FUNCT=lambda x:None
_SYS_EXIT=lambda x:sys.exit()

if _VERBOSE:
    def dprint(*args):
        print(*args)
    def spec_print(spec,*args):
        dprint("[pAW:{}]".format(spec),*args) #(line@{}) ,sys._getframe().f_lineno
    def iprint(*args):
        spec_print("INFO",*args)
    def wprint(*args):
        spec_print("WARNING",*args)
    def eprint(*args):
        spec_print("ERROR",*args)
else:
    dprint=_NO_FUNCT
    wprint=_NO_FUNCT
    eprint=_NO_FUNCT
    iprint=_NO_FUNCT


class pyNope(object):
    def __init__(self):
        pass

    def __call__(self,*args,**kwargs):
        return self

    def __repr__(self,*args,**kwargs):
        return ''

    def __getattr__(self,*args,**kwargs):
        return self

################################
# VARIABLES


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
# Regex for messages

_WAIT_CONNECT=re.compile('\*1')
_WAIT_DEVICE =re.compile('DEV(?P<device>\d*)')
_WAIT_VERSION=re.compile('VEvar(?P<version>\d*)')
_WAIT_STATUS=re.compile('#(?P<status>\d*)')
_WAIT_KPALIVE=re.compile('SYpig(?P<ping>\d*)')
# PROGRESS "PSprg99"
# GCfrl ?
# GCply
_MESSAGE_REGEX=re.compile("(?P<preargs>(\d)*(,\d)*)(?P<msg>\D*)(?P<postargs>(\d)*(,\d)*)")

_MATCHS={
    "*":"CONNECT",
    "DEV":"DEVICE",
    "VEvar":"VERSION",
    "#":"STATUS",
    "SYpig":"KPALIVE",
    "n":""
}


################################
# CLASS DEFINITIONS

class analogController(object):
    "AnalogWay Controller, controls one AnalogWay device"

    def __init__(self,ip,port,feedbackInterface=pyNope()):
        self.sck=None
        self.ip=ip
        self.port=port
        self.running=True
        self.listening=False

        # Last received match messages
        self.messages={i:None for i in ["CONNECT","DEVICE","VERSION","STATUS","KPALIVE","REGEX"]}

        #
        self.feedback=feedbackInterface # Feedback interface gui or midiRebind
        self._LOCKS={i:threading.Lock() for i in [
            "CONNECT","DEVICE","VERSION","STATUS","KPALIVE","changeLayer",
            "takeAvailable","take","takeAll","loadMM","quickFrame","quickFrameAll"
        ]}

        try:
            iprint('Creating socket')
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            iprint('Getting remote IP address')
            host=_IPSELF
            remote_ip = socket.gethostbyname( host )

        except socket.error:
            print('[pAW:ERROR] Failed to create socket')
            sys.exit()
        except socket.gaierror:
            print('[pAW:ERROR] Hostname could not be resolved. Exiting')
            sys.exit()

    ################################
    # MESSAGE RECEIVE
    # def receive_CONNECT(self,match):
    #     "We received a connect message"
    #     self.messages["CONNECT"]=match
    #     self._LOCKS["connect"].release()
    #     self.feedback.messageReceived("CONNECT",match)
    def receive_GENERIC(self,match):
        "We received a connect message, all the logic will be on the feedback side"
        #     self.messages["CONNECT"]=match
        #     self._LOCKS["connect"].release()
        #     self.feedback.messageReceived("CONNECT",match)
        typ=_MATCHS[match.group("msg")]
        self.messages[typ]=match #why not, not very clever tho
        self._LOCKS[typ].release()
        self.feedback.messageReceived("typ",match)

    ##############################################
    # LOCKS
    def waitLock(self,lockname,function_success=_NO_FUNCT,args_succes=(),function_error=_NO_FUNCT,args_error=()):
        """Wait for the lock <lockname> to be released, non blocking"""
        thd=threading.Thread(target=self._initLockWait,args=(lockname,function_success,args_succes,function_error,args_error))
        thd.start()
        return thd

    def _initLockWait(self,lockname,function_success=_NO_FUNCT,args_succes=(),function_error=_NO_FUNCT,args_error=()):
        """Thread waiting for a lock"""
        print(function_success,args_succes,function_error,args_error)
        iprint("Checking for [{}] lock avaivability".format(lockname))
        if not self._LOCKS[lockname].locked(): #The state it's supposed to be in, but let's not be too sure
            self._LOCKS[lockname].acquire(timeout=0.01)
        # Now wait for the lock to be released
        iprint("Acquired [{}] : Locking".format(lockname))
        status=self._LOCKS[lockname].acquire(timeout=_TIMEOUT)
        if status:
            iprint("Lock [{}] passed succesfully".format(lockname))
            function_success(args_success)
        else:
            iprint("Failed to aquire [{}]".format(lockname))
            function_error(args_error)
        return status

    ################################
    # MESSAGES SUBROUTINS

    def connect(self):
        """The device acts as a server. Once the TCP connection is established, the controller shall
            check that the device is ready, by reading the READY status, until it returns the value 1.
            [*] (* <value>) The controller shall wait and retry until it receives the value 1
        """
        iprint('Connecting to server, {self.ip}:{self.port}'.format(self=self))
        self.sck.connect((self.ip,self.port))

        wait=self.waitLock("CONNECT",function_error=_SYS_EXIT)
        self.sendData("*\r\n")
        iprint("Waiting for",wait)
        wait.join()
        iprint("Finished wait for",wait)


    def getDevice(self):
        """This read only command gives the device type
        [?] (DEV <value>) <values>:_DEVICES_VALUES
        """
        self.sendData("?")

    def getVersion(self):
        """his read only command gives the version number of the command set.
        It is recommended to check that this value matches the one expected by the controller.
        [VEvar] (VEvar<version>)
        """
        self.sendData("VEvar")

    def getStatus(self,value=3):
        """Reading a change of values
        [<value>#] (# <rvalue>) The controller must wait for <rvalue> to equals 0 for the end of enumeration
        <value>:1 All register values 3: Only non default values
        """
        self.sendData('#{}'.format(value))

    def _keepAlive(self,val=1):
        """Send a keepalive to check (and ensure) the connection is still up
        [<val1>SYpig] Will return the invert of the value sent: 0x0000 0000 will return 0xFFFF FFFF
        """
        self.sendData("{}SYpig".format(val))

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
        self.start_listening()
        self.connect()
        # self.getDevice()
        # self.getVersion()
        # self.getStatus()




    #########################################
    # SOCKET METHODS
    def start_listening(self):
        """Start the loop listener"""
        if self.listening:
            return
        start_new_thread(self.socketLoop,())

    def cleanReceive(self):
        "Yield only clean messages"
        self.running=True
        reply_bytes=b""
        while self.running:
            try:
                reply_bytes+=self.sck.recv(_MSGSIZE)
                if reply_bytes.find(_MSG_ENDING)==-1: # Message is not finished
                    continue
                else:
                    reply,reply_bytes=reply_bytes.rsplit(_MSG_ENDING,1)
                    reply=(reply+_MSG_ENDING).decode().split("\r\n")
                    for r in reply[:-1]: # iprint("Yielding:",r)
                        yield r
            except AttributeError as e:
                dprint(e)

    def socketLoop(self):
        """Loop on the socket and create an event for every message received"""
        self.listening=True
        for message in self.cleanReceive():
            try:
                iprint ("Received:",message)
                RX_MTCH=_MESSAGE_REGEX.match(message)
                iprint("preargs:{} - msg:{} - postargs:{}".format(RX_MTCH.group("preargs"),RX_MTCH.group("msg"),RX_MTCH.group("postargs")))
                start_new_thread(self.processMatch,(RX_MTCH,))
            except AttributeError as e:
                dprint("[pAW:ERROR] Regex couldn't find a match")
                dprint(e)

    def processMatch(self,match):
        """Process a match with a message, should only be called by the socketLoop funciton"""
        try:
            name=_MATCHS[match.group("msg")]
            # self.__getattr__("connect_{}".format(name),"GENERIC")(match)

        except KeyError as e:
            dprint("[pAW:ERROR] Can't find matched key:",match)
            print(e)

    def sendData(self,data):
        "Send data through the socket"
        try:
            self.sck.sendall(data.encode())
        except socket.error:
            print ('[pAW:ERROR] Send failed of data :',data)
            sys.exit()

    def limbowait(self):
        "Testing state, only usefull when not on a remote gui/midiRebind"
        while True:
            time.sleep(10)

#####################
# TESTING
if __name__ == '__main__':

    ctrl1=analogController(*_HOSTS[0])
    ctrl1.connectionSequence()
    ctrl1.limbowait()
