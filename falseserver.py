def sequenceAnswers(seq):


def Main():
    host = "127.0.0.1"

    # reverse a port on your computer
    # in our case it is 12345 but it
    # can be anything
    port = 10500
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)

    # put the socket into listening mode
    s.listen(5)
    print("socket is listening")

    # a forever loop until client wants to exit
    while True:

        # establish connection with client
        c, addr = s.accept()
        # Start a new thread and return its identifier
        start_new_thread(sequenceAnswers, (sequence,))
    s.close()


if __name__ == '__main__':
    sequence=[
        ""
    ]
    Main()
