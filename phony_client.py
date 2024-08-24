import socket
import threading
import sys
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
outbound_packet_buffer = [] # List of shit to remove and send

def recieve_server_response():
    while 1:
        # String parsing? Slow? Never
        packet = ""
        while 1:
            d = clientsocket.recv(1)
            if d == b"\\":
                break
            elif d == b'\xff':
                print(addr, "disconnected.")
                return
            else:
                packet += d.decode("utf8")

        # Then actually handle it I guess
        handle_server_response(packet)

def send_client_response():
    while 1:
        if len(outbound_packet_buffer) > 0:
            packet = outbound_packet_buffer.pop(0)
            clientsocket.send(packet)

def recieve_server_response():
    while 1:
        # String parsing? Slow? Never
        packet = ""
        while 1:
            d = clientsocket.recv(1)
            if d == b"\\":
                break
            elif d == b'\xff':
                print(addr, "disconnected.")
                return
            else:
                packet += d.decode("utf8")

        # Then actually handle it I guess
        print("")
        print(packet)
        print("")


if __name__ == "__main__":
    clientsocket.connect( (sys.argv[1], int(sys.argv[2])) )
    send_thread = threading.Thread(target=send_client_response, args=())
    recv_thread = threading.Thread(target=recieve_server_response, args=())
    send_thread.start()
    recv_thread.start()
    while 1:
        a = input("> ")
        outbound_packet_buffer.append((a+"\\").encode())
