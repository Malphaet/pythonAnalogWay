import re
import socketserver
import sys
import threading
import time

_DELAY = 0.0
_MESSAGE_REGEX = re.compile(r"(?P<preargs>(\d)*(,\d)*)(?P<msg>\D*)(?P<postargs>(\d)*(,\d)*)")
list_connections = []
main_server = None


class Answer(object):
    """Output an answer to a message"""

    def __init__(self, function):
        if type(function) == str:
            self.function = lambda x: function
        else:
            self.function = function

    def __add__(self, other):
        if type(other) == str:
            other = Answer(other)

        def new_funct(match):
            return self.function(match) + other.function(match)

        return Answer(new_funct)

    def __radd__(self, other):
        if type(other) == str:
            def new_funct(match):
                return other + self.function(match)

            return Answer(new_funct)
        else:
            raise TypeError

    def __call__(self, match):
        return self.function(match)


__ = Answer(lambda x: "")
_ARG = Answer(lambda x: x.group("preargs"))
_0 = Answer(lambda x: "0")
_1 = Answer(lambda x: "1")
_MSG = Answer(lambda x: x.group("msg"))
_RN = Answer(lambda x: "\r\n")

_goodanswers = {
    "*\r\n": _MSG + _1 + _RN,
    "?\r\n": Answer("DEV259") + _RN,
    "VEvar": _MSG + _RN,
    "#": _MSG + _0+_RN,
    "PRinp": _MSG + _ARG + _RN + "GCfsc1,1"+_RN,
    "PUscu": _MSG + _ARG+_RN,
    ",GCtav": "GCtav" + _ARG + Answer(",1")+_RN,
    "*": _MSG + _ARG+_RN,
}


class Goodserver(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        """Give good-ish answers to queries"""
        global list_connections
        try:
            while True:
                data = self.request.recv(1024)
                print("Received data", data)
                if data:
                    _match = _MESSAGE_REGEX.match(data.decode("utf-8"))
                    try:
                        answer = _goodanswers[_match.group("msg")](_match)
                    except KeyError:
                        answer = _goodanswers["*"](_match)
                    print("[{}] Received : {} | Sent {}".format(self.request.getpeername(),
                                                                data.decode("utf-8").strip(), answer.strip()))
                    time.sleep(_DELAY)
                    self.request.sendall(answer.encode("utf-8"))
                else:
                    break
        except ConnectionResetError as e:
            print("[{}] Has stopped the connection".format(self.request.getpeername()))
            print(e)
        # list_connections.remove(self.sck)
        # self.sck.close()


def main_listener(host, port):
    """Listening loop"""
    global main_server
    main_server = socketserver.TCPServer((host, port), Goodserver)
    print("Listening on {}:{}".format(host, port))
    main_server.serve_forever()


def Main():
    host, port = "127.0.0.1", 3000

    print("Fake analogController (pulse2) on ({}@{})".format(host, port))

    threading.Thread(target=main_listener, args=(host, port)).start()

    time.sleep(0.5)
    input("Press any key to shutdown...")
    print("Shutting down...")

    main_server.shutdown()
    sys.exit()


if __name__ == '__main__':
    Main()
