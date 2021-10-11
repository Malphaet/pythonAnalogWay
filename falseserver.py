import socket,time
from _thread import start_new_thread

_DELAY=0.5

def sequenceAnswers(s,addr,seq,delay=_DELAY):
    try:
        name=addr[1]
        print("[{}] Connected".format(name))
        # s.sendall("*\r\n".encode)
        recv=b""
        for elt,resps in seq:
            elt=(elt).encode()
            resps=[(i+"\r\n").encode() for i in resps]
            print("[{}] Waiting for {}".format(name,elt))
            while recv not in elt:
                recv=s.recv(4095)
                print("[{}] Received : {}".format(name,recv))
            for r in resps:
                print("[{}] Sending : {}".format(name,r))
                time.sleep(delay)
                s.sendall(r)
        while True:
            print(s.recv(4096).decode())
    except ConnectionResetError as e:
        print("[{}] Has stopped the connection".format(name))
        print(e)
def Main(delay=_DELAY):
    host = "127.0.0.1"

    # reverse a port on your computer
    # in our case it is 12345 but it
    # can be anything
    port = 3000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("Fake analogController (pulse2) on port ({})".format(port))

    # put the socket into listening mode
    s.listen(5)
    print("Server is listening to incomming connections")

    # a forever loop until client wants to exit
    while True:
        c, addr = s.accept()
        # print(c.recv(4000))
        # c.sendall(b"*\r\n")
        start_new_thread(sequenceAnswers, (c,addr,sequence,delay,))
    s.close()


if __name__ == '__main__':
    sequence=[
        ("*",["VEvar13","#0","VEvar13","*1"]),
        ("?",['DEV259']),
        ("VEvar",["VEvar13"]), #Guess
        ("#3",["#4","PRinp0,1,7,8","PRinp0,1,1,8","#0"]), #Another guess
        ("1SYpig",["SYpig4294967294"]) #Another guess

        ]
    Main(0.5)
