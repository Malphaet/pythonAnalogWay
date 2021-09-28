#!/bin/python3

################################
# IMPORTS
import socketserver



################################
# CONFIG VARIABLES
_HOSTS = [("192.168.0.140","10500")]


################################
#


_DEVICES VALUES={
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
    "Input 2" :2, "frame 2":2,
    "Input 3 ":3, "frame 3":3,
    "Input 4" :4, "frame 4":4,
    "Input 5" :5, "frame 5":5,
    "Input 6" :6, "frame 6":6,
    "Input 7" :7, "frame 7":7,
    "Input 8" :8, "frame 8":8,
    "Input 9" :9, "frame 9":9,
    "Input 10" :10, "frame 10":10,
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
        pass

    def connect(self):
        pass

    def getStatus(self):
        pass

    def _keepAlive(self):
        pass

    def changeLayer(self,screen,ProgPrev,layer,src):
        pass

    def takeAvailable(self,*screens):
        """Test for take availability
        (GCtav<scrn>,0) Test take availability on screen <scrn>
        (GCtav<scrn>,0) : Take is unavailable
        (GCtav<scrn>,1) : Take is available"""
        for screen in screens:
            pass

    def take(self,screen):
        """ Take a specific screen
        [Wait for the TAKE availability on all screen] takeAvailable (screen1,screen2,etc...)
        [Launch the TAKE action] <scrn>,1GCtak
        (GCtak<scrn>,1) : Take in progress
        (GCtav<scrn>,0) : Take is unavailable
        (GCtak<scrn>,0) : Take finished <--- Waiting for
        (GCtav<scrn>,1) : Take is available
        """

    def takeAll(self):
        """Take all screens
        [Wait for the TAKE availability on all screen] takeAvailable (screen1,screen2,etc...)
        [Launch the TAKE ALL action] 1,GCtal
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

################################
# Quickframes


# Changelayer
