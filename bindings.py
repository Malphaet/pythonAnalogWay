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

_MSGSIZE=4096
_TIMEOUT=4
_TIMEOUT_BIG=5
_TIMEOUT_HUGE=20
_MSG_ENDING=b"\r\n"

################################
# BIG DEFINES

_NO_FUNCT=lambda *x:None
def _SYS_EXIT(system,*args):
    system.fatal=True
    sys.exit()

_VERBOSE=3

nopeF=lambda *x:None
def printl(label=""):
    def _pl(*args):
        print(label,*args)
    return _pl

eprint=printl("[pAW:ERROR]")
dprint,ddprint,iprint,wprint=nopeF,nopeF,nopeF,nopeF

if _VERBOSE>=1:
    wprint=printl("[pAW:WARNING]")
if _VERBOSE>=2:
    iprint=printl("[pAW:INFO]")
if _VERBOSE>=3:
    dprint=printl("[pAW:DEBUG]")
if _VERBOSE>=4:
    ddprint=printl("[pAW:DDEBUG]")


class pyNope(object):
    def __init__(self):
        pass

    def receiveMessage(self,*args):
        iprint("An order has been received :",args)

    def __call__(self,*args,**kwargs):
        return self

    def __repr__(self,*args,**kwargs):
        return ''

    def __getattr__(self,*args,**kwargs):
        return self

class pyYep(object):
    def __init__(self,*args,**kwargs):
        pass
    def __call__(self,*args,**kwargs):
        return True

    def __repr__(self,*args,**kwargs):
        return "1"

    def __getattr__(self,arg):
        return True

    def __equals__(self,*args):
        return True

    def __true__(self,*args):
        return True
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

# PROGRESS "PSprg99"
# GCfrl ?
# 0,0GCtio ?
_MESSAGE_REGEX=re.compile("(?P<preargs>(\d*)*(,\d*)*)(?P<msg>\D*)(?P<postargs>(\d*)*(,\d*)*)")

_MATCHS={
    "*":"CONNECT",
    "DEV":"DEVICE",
    "VEvar":"VERSION",
    "#":"STATUS", # #0
    "SYpig":"KPALIVE",
    "PRinp":"LAYERINP", #?
    "GCtak":"TAKE", #GCtak<scrn>,0
    "GCtav":"TAKEAVL",
    "GCtal":"TAKEALL", #GCtal0
    "GClrq":"LOADMM", #GClrq ?
    "CTqfl":"QUICKFA", #X,1CTqfl
    "CTqfa":"QUICKF", #1CTqfa
    "PUscu":"SCRNUPD", #1PUscu
    "GCfsc":"FREEZE",
    "GCfra":"FREEZEALL",
    "GCfrl":"FREEZELAYER",
    "GCply":"DISPLAYLAYER",
    "ISsva":"DETECTED", # Undocumented
    "E":"ERROR"
}

_ALL_MESSAGE_TYPES=[
    "CONNECT","DEVICE","VERSION","STATUS","KPALIVE","LAYERINP",
    "TAKEAVL","TAKE","TAKEALL","LOADMM","QUICKFA","QUICKF",
    "SCRNUPD","FREEZE","FREEZEALL","FREEZELAYER","DISPLAYLAYER",
    "ERROR","DETECTED",
]

_UPDATE_MSG=[
    "LAYERINP","QUICKFA","QUICKF","TAKE","FREEZELAYER","FREEZEALL","DISPLAYLAYER","DETECTED","STATUS",
]
# RELOAD_PROGRAM
# FREEZE_SCREEN
# FREEZE_ALL
################################
# CLASS DEFINITIONS

class analogController(object):
    "AnalogWay Controller, controls one AnalogWay device"

    def __init__(self,ip,port,feedbackInterface=pyNope(),screens=2):
        self.screens=screens
        self.sck=None
        self.ip=ip
        self.port=port
        self.running=True
        self.listening=False
        self.fatal=False
        self.lastping=0
        self.st_quickframe=[False,False]
        self.st_takeavailable=[False,False]
        self.st_quickframeall=False
        self._connectedLock=threading.Lock()
        self._connectedLock.acquire() # Waiting for connection
        self.st_freeze=[False,False]
        self.st_freeze_all=False
        self.st_freeze_layer=[False,False]
        self.feedback=feedbackInterface # Feedback interface gui or midiRebind
        self._LOCKS={i:threading.Lock() for i in _ALL_MESSAGE_TYPES} #LAYERINP could actually be a huge clusterlock, not for now tho
        # for i in range(2):
        #     for j in range(2):
        #         for k in range(8):
        #             self._LOCKS["LAYERINP{}_{}_{}".format(i,j,k)]=threading.Lock()
        self.POSTMATCHACTIONS={i:self.getAttr("POSTMATCH_{}".format(i),self.POSTMATCH_GENERIC) for i in _ALL_MESSAGE_TYPES}
        self._all_commands={
            "CONNECT":self.connectionSequence,
            "LAYERINP":self.changeLayer,
            "QUICKFA":self.quickFrameAll,
            "QUICKF":self.quickFrame,
            "TAKE":self.take,
            "TAKEALL":self.takeAll,
            "FREEZELAYER":self.freezeLayer,
            "FREEZEALL":self.freezeScreenAll,
            "SCRNUPD":self.updateFinishedAll,
            "LOADMM":self.loadMM,
        }
        self._commandlist=self._all_commands
        try:
            dprint('Creating socket')
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # iprint('Getting remote IP address')
            # remote_ip = socket.gethostbyname(_IPSELF)
            # iprint(remote_ip)
        except socket.error:
            eprint('Failed to create socket')
            sys.exit()
        except socket.gaierror:
            eprint('Hostname could not be resolved. Exiting')
            sys.exit()

    def receiveCommand(self,command,*args,**kwargs):
        "Receive a command froman external source and handle it internally"
        try:
            self._all_commands[command](*args,**kwargs)
        except KeyError as e:
            eprint("The command received {} isn't in the list of supported commands ({})".format(command,self._commandlist.keys()))
            eprint(e)

    def addFeedbackInterface(self,feedback):
        "Add the feedback interface TODO: Several feedback interfaces ?"
        self.feedback=feedback

    def getAttr(self,attribute,default):
        "A custom attribute fetcher"
        try:
            return self.__getattribute__(attribute)
        except:
            return default

    ################################
    # RECEIVE ANALISIS
    def POSTMATCH_GENERIC(self,match):
        "Expects a 0 as last argument to proceed"
        self.st_takeavailable=[False,False]
        if match.group("postargs").split(",")[-1]!="0":
            return False
        return True

    def POSTMATCH_CONNECT(self,match):
        "Accepts the classic *"
        return True

    def POSTMATCH_DEVICE(self,match):
        "Accepts any device"
        return True

    def POSTMATCH_VERSION(self,match):
        "Accepts any version"
        return True

    def POSTMATCH_LAYERINP(self,match):
        "Accepts any layer configuration"
        self.st_takeavailable=[False,False]
        return True

    def POSTMATCH_KPALIVE(self,match):
        "Accepts only the invert of last ping"
        if match.group("postargs")!=str(0xFFFFFFFF^self.lastping):
            wprint("Sent {:b} | Expected {:b} and got {:b}".format(self.lastping,0xFFFFFFFF^self.lastping,int(match.group("postargs"))))
            return True
        return True

    def POSTMATCH_ERROR(self,match):
        "Error message"
        self.st_takeavailable=[False,False]
        eprint("An error has occured on the machine side:")
        if match.group("postargs")=="10":
            eprint("Command name error. It is usually due to a command field (i.e. five letters) that does not match any legal command string")
        elif match.group("postargs")=="11":
            eprint("Index value out of range. It is usually due to a wrong index value.")
        elif match.group("postargs")=="12":
            eprint("Index number error. It is usually due to an incorrect number of indexes, too much or not enough.")

    def POSTMATCH_QUICKF(self,match):
        "Update quickframe status"
        self.st_takeavailable=[False,False]
        screen,status=match.group("postargs").split(",")
        screen,status=int(screen),int(status)
        self.st_quickframe[screen]=status
        return True

    def POSTMATCH_QUICKFA(self,match):
        "Update quickFrameAll status"
        self.st_takeavailable=[False,False]
        status=int(match.group("postargs"))
        for i in range(len(self.st_quickframe)):
            self.st_quickframe[i]=status
        self.st_quickframeall=status
        return True

    def POSTMATCH_TAKEAVL(self,match):
        "Take available answer 1"
        # Write take availability
        scr,avail=match.group("postargs").split(",")
        if avail=="1":
            self.st_takeavailable[int(scr)]=True
            return True
        self.st_takeavailable[int(scr)]=False
        return False

    def POSTMATCH_TAKE(self,match):
        "Take answer 1"
        self.st_takeavailable=[False,False]
        if match.group("postargs")[-1]=="0":
            return True
        return False

    def POSTMATCH_SCRNUPD(self,match):
        "Take answer 1"
        if match.group("postargs")[-1]=="1":
            return True
        return False

    def POSTMATCH_FREEZEALL(self,match):
        "Take answer 1"
        if match.group("postargs")[-1]=="1":
            return True
        return False

    def POSTMATCH_DISPLAYLAYER(self,match):
        "Returns the displayed layer"
        return True

    def POSTMATCH_FREEZELAYER(self,match):
        "Returns the layer,screen and status of the freeze"
        return True

    def POSTMATCH_DETECTED(self,match):
        "Return the status of the input"
        return True

    def POSTMATCH_LOADMM(self,match):
        "Result of a load master memory"
        return True

    # def POSTMATCH_TAKEAVL(self,match):
    #     "Take available answer 1"
    #     if match.group("postargs")[-1]=="1":
    #         return True
    #     return False

    ################################
    # MESSAGE RECEIVE
    def genericRECEIVE(self,match):
        "We received a connect message, all the logic will be on the feedback side"
        try:
            typ=_MATCHS[match.group("msg")]
            # self.messages[typ]=match # Not very clever tho
            if typ in _UPDATE_MSG:
                self.feedback.receiveMessage(typ,match)
            status=self.POSTMATCHACTIONS[typ](match)
            if status:
                self._LOCKS[typ].release()
            else:
                dprint("Ignoring message",match)
                return status
        except RuntimeError as e:
            dprint("Lock [{}] is already released (async terminated earlier)".format(typ))
            dprint("This message is either comming from the device or garbage data")
            dprint(e)
            
        except KeyError as e:
            eprint("There is no lock associated with {}".format(typ))
            eprint(e)
        return False

    ##############################################
    # LOCKS
    def waitLock(self,lockname,function_success=_NO_FUNCT,args_success=(),function_error=_NO_FUNCT,args_error=(),timeout=_TIMEOUT):
        """Wait for the lock <lockname> to be released, non blocking"""
        thd=threading.Thread(target=self._initLockWait,args=(lockname,function_success,args_success,function_error,args_error,timeout))
        thd.start()
        return thd

    def _initLockWait(self,lockname,function_success=_NO_FUNCT,args_success=(),function_error=_NO_FUNCT,args_error=(),timeout=_TIMEOUT):
        """Thread waiting for a lock"""
        dprint("Checking for [{}] lock avaivability".format(lockname))
        if not self._LOCKS[lockname].locked(): #The state it's supposed to be in, but let's not be too sure
            self._LOCKS[lockname].acquire(timeout=0.01)
        # Now wait for the lock to be released
        dprint("Acquired [{}] : Locking".format(lockname))
        status=self._LOCKS[lockname].acquire(timeout=timeout)
        if status:
            dprint("Lock [{}] passed succesfully".format(lockname))
            function_success(args_success)
        else:
            eprint("Failed to aquire [{}]".format(lockname))
            function_error(args_error)
        return status

    ################################
    # MESSAGES SUBROUTINS

    def passthroughSEND(self,name,send,*args,**kwargs):
        "Send a message without any wait or lock"
        dprint("Sending passthrough message ({})".format(send))
        self.sendData(send)

    def genericSEND(self,lock,send,fatal=True,*args,**kwargs):
        "Generic send and join method, with all the logic on the controler side"
        dprint("Acquiring {}".format(lock.lower()))
        # self.st_takeavailable=[False,False] # ?
        wait=self.waitLock(lock,function_error=_SYS_EXIT,args_error=(self),*args,**kwargs)
        self.sendData(send)
        wait.join()
        if fatal and self.fatal:
            _SYS_EXIT(self)

    def connect(self):
        """The device acts as a server. Once the TCP connection is established, the controller shall
            check that the device is ready, by reading the READY status, until it returns the value 1.
            [*] (* <value>) The controller shall wait and retry until it receives the value 1
        """
        try:
            iprint('Connecting to server, {self.ip}:{self.port}'.format(self=self))
            self.sck.connect((self.ip,self.port))
            self._connectedLock.release()
            self.genericSEND("CONNECT","*\r\n")
        except ConnectionRefusedError:
            eprint("Connection to AnalogWay server {self.ip}:{self.port} is impossible".format(self=self))
            raise ConnectionRefusedError
    def getDevice(self):
        """This read only command gives the device type
        [?] (DEV <value>) <values>:_DEVICES_VALUES
        """
        self.genericSEND("DEVICE","?\r\n")

    def getVersion(self):
        """his read only command gives the version number of the command set.
        It is recommended to check that this value matches the one expected by the controller.
        [VEvar] (VEvar<version>)
        """
        self.genericSEND("VERSION","VEvar\r\n")

    def getStatus(self,value=1,timeout=_TIMEOUT_HUGE):
        """Reading a change of values
        [<value>#] (# <rvalue>) The controller must wait for <rvalue> to equals 0 for the end of enumeration
        <value>:1 All register values 3: Only non default values
        """
        self.genericSEND("STATUS",'{}#'.format(value),timeout=timeout)

    def _keepAlive(self,val=0x0000):
        """Send a keepalive to check (and ensure) the connection is still up
        [<val1>SYpig] Will return the invert of the value sent: 0x0000 0000 will return 0xFFFF FFFF
        """
        self.lastping=val
        self.genericSEND("KPALIVE","{}SYpig".format(val),timeout=_TIMEOUT_BIG)

    def changeLayer(self,screen,ProgPrev,layer,src):
        """Change the layer of selected
        [<screen>,<ProgPrev>,<layer>,<src>PRinp] Change the input on a selected layer
        <screen> is the RCS² screen number minus 1. (2)
        <ProgPrev> is 0 for Program, 1 for Preview. (2) # Not gonna livechange, so it's ignored
        <layer> is a value representing the destination Layer. (7)
        <src> is a value representing the input source. (10)
        """
        self.genericSEND("LAYERINP","{screen},{ProgPrev},{layer},{src}PRinp".format(screen=screen,ProgPrev=ProgPrev,layer=layer,src=src),timeout=_TIMEOUT)

    def takeAvailable(self,*screens):
        """Test for take availability
        [<scrn>,GCtav] Test take availability on screen <scrn>
        (GCtav<scrn>,0) : Take is unavailable
        (GCtav<scrn>,1) : Take is available"""
        self.st_takeavailable=[False,False]
        for screen in screens:
            self.genericSEND("TAKEAVL","{screen},GCtav".format(screen=screen),timeout=_TIMEOUT_HUGE)
            # self.genericSEND("TAKEAVL","{screen},GCtav".format(screen=screen),timeout=_TIMEOUT_HUGE)

    def takeAvailableAll(self):
        self.takeAvailable(*range(self.screens))

    def take(self,screen):
        """ Take a specific screen
        [Wait for the TAKE availability on all screen] takeAvailable (screen1,screen2,etc...)
        [<scrn>,1GCtak] Launch the TAKE action
        (GCtak<scrn>,1) : Take in progress
        (GCtav<scrn>,0) : Take is unavailable
        (GCtak<scrn>,0) : Take finished <--- Waiting for
        (GCtav<scrn>,1) : Take is available
        """
        # Check if take available on all screens
        self.updateFinished(screen)
        if self.st_takeavailable[screen]:
            self.genericSEND("TAKE","{screen},1GCtak".format(screen=screen),timeout=_TIMEOUT_HUGE)

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
        # Wait for all screens to be available
        # self.takeAvailable(0)#*range(self.screens))
        self.updateFinishedAll()
        if self.st_takeavailable[0]&self.st_takeavailable[1]:
            self.genericSEND("TAKEALL","1GCtal",timeout=_TIMEOUT_BIG)
        else:
            self.takeAvailableAll()
            self.takeAll()

    def loadMM(self,screenF,memory,screenT,ProgPrev,filter): # Changed it to be correct, care since no debug
        """Load a master memory to a screen
        <screenF>,<memory>,<screenT>,<ProgPrev>,<filter>,1 GClrq ()
        Filter: This parameter allows excluding some preset elements from recalling
        ProgPrev: This parameter gives the destination preset number, either Program (current preset) or Preview (next preset)
        screenT: This parameter gives the destination screen number. If only one screen is available, due to device type or device mode, the screen number 0 shall be used
        memory: This parameter gives the memory slot number to load. The allowed range of values is 0 to 7, corresponding to memories 1 to 8
        screenF: This parameter gives the origin screen number, the one from which was recorded the preset. Used with the <scrnT> parameter,
                 they allow loading in a screen a preset stored from the other, in matrix mode.

        """
        #self.genericSEND("LOADMM","{screenF},{memory},{screenT},{ProgPrev},{filter},1GClrq".format(screenF=screenF,memory=memory,screenT=screenT,ProgPrev=ProgPrev,filter=filter),timeout=_TIMEOUT)
        self.passthroughSEND("LOADMM","{screenF},{memory},{screenT},{ProgPrev},{filter},1GClrq".format(screenF=screenF,memory=memory,screenT=screenT,ProgPrev=ProgPrev,filter=filter),timeout=_TIMEOUT)


    def quickFrame(self,screen,action=None):
        """Display (1), Hide(0) a quickFrame
            Display : <scrn>,1CTqfa (CTqfa<scrn>, 1)
            Hide :    <scrn>,0CTqfa (CTqfa<scrn>, 0)
        """
        if action == None:
            action=not self.st_quickframe[screen]
        self.genericSEND("QUICKF","{screen},{action:b}CTqfa".format(screen=screen,action=action))
        # self.sendDirect("{screen},{action}CTqfa".format(screen=screen,action=action).encode())
        self.st_quickframe[screen]=action

    def quickFrameAll(self,action=None):
        """Display/Hide a quickFrame on all screens
            Display: 1CTqfl (CTqfl 1 R F)
            Hide:    0CTqfl (CTqfl 0 R F)
        """
        if action == None:
            action=not self.st_quickframeall
        self.genericSEND("QUICKFA","{action:b}CTqfl".format(action=action))
        self.st_quickframeall=action

    def freezeScreen(self,screen,action=False):
        """Freeze screen <screen>
            <screen>,1GCfsc: Freeze screen
            <screen>,0GCfsc: Un Freeze screen ?
        """
        if action==None:
            action=not self.st_freeze[screen]
        self.genericSEND("FREEZE","{screen},{action:b}GCfsc".format(screen=screen,action=action))
        self.st_freeze[screen]=not action

    def freezeScreenAll(self,action=None):
        """Freeze all screens
            1GCfra: Freeze screen
        """
        if action==None:
            action=self.st_freeze_all
        self.genericSEND("FREEZEALL","{action:b}GCfra".format(action=action))
        self.st_freeze_all=not self.st_freeze_all

    def freezeLayer(self,layer,screen,action=None):
        """Freeze layer <layer> on <screen>
        <layer>,<screen>,<action>GCfrl: Freeze screen
        """
        if action==None:
            action=self.st_freeze_layer[layer]
        self.genericSEND("FREEZELAYER","{layer},{screen},{action:b}GCfrl".format(layer=layer,screen=screen,action=action))
        self.st_freeze_layer[layer]=not self.st_freeze_layer[layer]

    def displayed(self,layer):
        """Change the previewed layer
            <layer>GCply
        """
        self.genericSEND("DISPLAYLAYER","{layer}GCply".format(layer=layer))

    def updateFinished(self,screen):
        """Updates are finished being sent
             <screen>,1PUscu : Updates on screen <screen> are done
        """
        self.genericSEND("SCRNUPD","{screen},1PUscu".format(screen=screen))

    def updateFinishedAll(self):
        for screen in range(self.screens):
            self.updateFinished(screen)

    def connectionSequence(self):
        "Execute the full connection sequence"
        self.start_listening()
        self.connect()
        self.getDevice()
        self.getVersion()
        self.getStatus(3)


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
                # f = open("datadump.txt", "ab+")
                received=self.sck.recv(_MSGSIZE)
                # f.write(received)
                # f.close()
                reply_bytes+=received
                if reply_bytes.find(_MSG_ENDING)==-1: # Message is not finished
                    continue
                else:
                    reply,reply_bytes=reply_bytes.rsplit(_MSG_ENDING,1)
                    reply=(reply+_MSG_ENDING).decode().split("\r\n")
                    for r in reply[:-1]: # iprint("Yielding:",r)
                        yield r
            except AttributeError as e:
                dprint(e)
            except OSError as e:
                eprint(e)
                eprint('The socket connection is experiencing issues')


    def socketLoop(self):
        """Loop on the socket and create an event for every message received"""
        self.listening=True
        self._connectedLock.acquire(_TIMEOUT_BIG) # Wait for connection
        for message in self.cleanReceive():
            try:
                iprint ("<<< Received:",message)
                RX_MTCH=_MESSAGE_REGEX.match(message)
                dprint("preargs:{} - msg:{} - postargs:{}".format(RX_MTCH.group("preargs"),RX_MTCH.group("msg"),RX_MTCH.group("postargs")))
                start_new_thread(self.processMatch,(RX_MTCH,)) # Here lies the problem, damned if I do, damned if I don't
            except AttributeError as e:
                eprint("Regex couldn't find a match")
                eprint(e)

    def processMatch(self,match):
        """Process a match with a message, should only be called by the socketLoop funciton"""
        try:
            name=_MATCHS[match.group("msg")]
            # self.__getattribute__("receive_{}".format(name),default="GENERIC")(match)
            return self.genericRECEIVE(match)
        except KeyError as e:
            # dprint("[pAW:ERROR] Can't find matched key:",match)
            # print(e)
            pass

    def sendDirect(self,direct):
        "Directly sent to the socket"
        try:
            iprint(">>> Sending direct: {}".format(direct))
            self.sck.sendall(direct)
        except:
            eprint("Error sending data: ",direct)

    def sendData(self,data):
        "Send data through the socket"
        try:
            iprint(">>> Sending data: {}".format(data.replace("\n","")))
            self.sck.sendall((data).encode())
        except socket.error:
            print ('[pAW:ERROR] Send failed of data :',data)
            sys.exit()

    def limbowait(self):
        "Testing state, only usefull when not on a remote gui/midiRebind"
        while not self.fatal:
            time.sleep(_TIMEOUT_HUGE)

    def pingLoop(self):
        "Another limbo wait, this time with pings"
        while not self.fatal:
            self._keepAlive(val=0b1000)
            time.sleep(_TIMEOUT_HUGE)

    def keepPinging(self,timer=_TIMEOUT_HUGE):
        "Keep pinging"
        if self.fatal:
            sys.exit()
        threading.Timer(timer,self.keepPinging,(timer,)).start()
        self._keepAlive()

    def __del__(self):
        self.sck.close()

    def close(self):
        self.__del__()
        # threading.Timer(self._keepPinging(timer),timer)
#####################
# TESTING
if __name__ == '__main__':
    #_HOSTS=[["127.0.0.1",3000]] # Test server
    # _TIMEOUT_HUGE=5

    ctrl1=analogController(*_HOSTS[0])
    ctrl1.receiveCommand("CONNECT")
    # ctrl1.connectionSequence()
    # while True:
    #     for i in range(8):
    #         ctrl1.changeLayer(0,1,1,i+1)
    #         time.sleep(0.5)
    #         ctrl1.changeLayer(0,1,2,i+1)
    #         time.sleep(1)
    # try:
    #     while True:
    #         txt=input("> ")
    #         ctrl1.sendDirect(txt.encode())
    # except KeyboardInterrupt:
    #     ctrl1.close()

    # ctrl1.changeLayer(0,0,1,1)
    ctrl1.receiveCommand("LAYERINP",0,1,1,3)
    ctrl1.receiveCommand("SCRNUPD")
    ctrl1.receiveCommand("TAKEALL")
    # time.sleep(1)
    # # ctrl1.freezeScreenAll(1)
    # ctrl1.freezeLayer(0,0,1)
    # ctrl1.freezeLayer(1,0,1)
    # time.sleep(1)
    # ctrl1.displayed(1)
#     # ctrl1.freezeScreenAll(1)

#     # import random

#     while True:
#     #     ctrl1.changeLayer(0,1,1,random.randint(0,7))
#     #     ctrl1.updateFinishedAll()
#     #     ctrl1.takeAvailableAll()
#     #     ctrl1.takeAll()
#         input(">>>")
#         ctrl1.displayed(1)
#         ctrl1.updateFinishedAll()
#         ctrl1.freezeLayer(0,1)
# #     time.sleep(1)
# #     # ctrl1.takeAvailable((1,))
# # # take(self,screen)
# # # takeAll(self)
# # # loadMM(screenF,memory,screenT,ProgPrev,filter)
# #     # ctrl1.quickFrame(0)
# #     # time.sleep(1)
# #     # ctrl1.quickFrame(0)
# #     # time.sleep(1)
# #     # ctrl1.quickFrame(0)
# # #
# #     # ctrl1.quickFrameAll(action=1)
# #     # time.sleep(1)
# #     # ctrl1.quickFrameAll()

#     # ctrl1.takeAvailable(1)


# #     ctrl1.keepPinging()
