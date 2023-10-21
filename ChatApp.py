import sys
import socket
import json


if __name__ == "__main__":

    #2.1 Registration
    #ChatApp <mode> <command-line arguments>
    mode = sys.argv[1]
    numOfArgs = len(sys.argv)

    #server registration
    #$ ChatApp -s <port>
    #the port number should be an integer value in the range 1024-65535.
    if mode == "-s":
        server_port = int(sys.argv[2])
        #invalid port #
        if not 1024<=server_port<=65535:
            print("[Invalid port number, needs to be in range 1024-65535]")
        
        #hard-coding, need to get from local machine?
        server_ip = "127.0.0.1"

        #create a socket
        #AF_INET = family addr ipv4
        #SOCK_DGRAM = aka UDP
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        #bind to ip address & port
        server_socket.bind((server_ip,server_port))

        server_table = {}

        #listen for incoming client connections
        while(True):
            print(">>>")

            #connection from client wanting to register
            rec = server_socket.recvfrom(1024)
            message = rec[0]
            client_address_port = rec[1]
            client_ip_address = client_address_port[0]
            client_port = client_address_port[1]

            #represents table with client-name as key
            server_table[message.decode()] = [client_ip_address,client_port,True]

            #send ack & table
            server_socket.sendto(str.encode(str(server_table)),client_address_port)
            #...
            print("[Client table updated.]")
            print(server_table)
        

    #client registration
    #$ ChatApp -c <name> <server-ip> <server-port> <client-port>
    if mode== "-c":
        client_name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        client_port = int(sys.argv[5])

        #ADD checks for valid ip (decimal) & valid port number
        
        #get ip address of client machine
        client_ip = socket.gethostbyname(socket.gethostname())

        #create a socket
        client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        #bind to ip address & port
        client_socket.bind((client_ip,client_port))

        #initial connection to server 
        client_socket.sendto(str.encode(client_name),(server_ip,server_port))

        #client table
        client_table = {}

        ##successful registration?
        msg = client_socket.recvfrom(1024)
        ack_and_table = msg[0]
        msg_dict = eval(ack_and_table)
        if msg_dict is not None:
            print("[Welcome, You are registered.]")
        
        #if successful update the table
        client_table = msg_dict
        print("[Client table updated.]")
        print(client_table)


        #send messages
        while(True):
              user_input = input(">>>")
              #process send message 
              if user_input.split(" ")[0]=='send':
                  receiver_name = user_input.split(" ")[1]
                  message_to_send = user_input.split(" ")[2]

                  receiver_ip = client_table[receiver_name][0]
                  receiver_port = client_table[receiver_name][1]

                  print(receiver_ip)
                  print(receiver_port)


              #send message to specified client
              #client_socket.sendto(str.encode(user_input),(server_ip,server_port))

              #ack = client_socket.recvfrom(1024)
              #print("ack: "+str(ack))







