import socket,time
from _thread import start_new_thread

_DELAY=0.5

import re
_MESSAGE_REGEX=re.compile("(?P<preargs>(\d)*(,\d)*)(?P<msg>\D*)(?P<postargs>(\d)*(,\d)*)")

class Answer(object):
    "Output an answer to a message"
    def __init__(self,function):
        if type(function)==str:
            self.function=lambda x:function
        else:
            self.function=function

    def __add__(self,other):
        if type(other)==str:
            other=Answer(other)
        def new_funct(match):
            return self.function(match)+other.function(match)
        return Answer(new_funct)

    def __radd__(self,other):
        if type(other)==str:
            def new_funct(match):
                return other+self.function
            return new_funct
        else:
            raise TypeError

    def __call__(self,match):
        return self.function(match)

__=Answer(lambda x:"")
_ARG=Answer(lambda x:x.group("preargs"))
_0=Answer(lambda x:"0")
_1=Answer(lambda x:"1")
_MSG=Answer(lambda x:x.group("msg"))
_RN=Answer(lambda x:"\r\n")

_goodanswers={
    "*\r\n":_MSG+_1+_RN,
    "?\r\n":Answer("DEV259")+_RN,
    "VEvar":_MSG+_RN,
    "#":_MSG+_0,
    "PRinp":_MSG+_ARG,
    "PUscu":_MSG+_ARG,
    "_":_MSG+_ARG,
}
def goodServer(s,addr,delay=_DELAY):
    "Give good-ish answers to queries"
    try:
        while True:
            recv=s.recv(3000)
            match=_MESSAGE_REGEX.match(recv.decode())
            try:
                msg=_goodanswers[match.group("msg")](match)
            except KeyError:
                msg=_goodanswers["_"](match)
            print("[{}] Received : {} | Sending {}".format(addr[1],recv,msg.strip("\r\n")))
            s.sendall((msg+"\r\n").encode())
    except ConnectionResetError as e:
        print("[{}] Has stopped the connection".format(addr[1]))
        print(e)

def Main(delay=_DELAY):
    host = "127.0.0.1"

    # reverse a port on your computer
    # in our case it is 12345 but it
    # can be anything
    port = 3000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("Fake analogController (pulse2) on ({}@{})".format(host,port))

    # put the socket into listening mode
    s.listen(5)
    print("Server is listening to incomming connections")

    # a forever loop until client wants to exit
    while True:
        c, addr = s.accept()
        # print(c.recv(4000))
        # c.sendall(b"*\r\n")
        start_new_thread(goodServer, (c,addr,delay,))
    s.close()


if __name__ == '__main__':
    Main(0.05)
