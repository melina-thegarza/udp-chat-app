import sys
import socket
import json
import threading
import datetime

# Define the global dictionary variable
client_table = {}


class ClientReceive(threading.Thread):
    #receive incoming messages from server & other clients
    def __init__(self,socket,client_name,server_ip,server_port):
        super().__init__()
        self.socket = socket
        self.name = client_name
        self.server_ip = server_ip
        self.server_port= server_port


    def run(self):
         #listen for incoming message
        while(True):
       
            #message from sender
            entire_message = self.socket.recvfrom(1024)
            message = entire_message[0]
            #remove eventually
            if message == "q":
                break
            sender_address_port = entire_message[1]
            sender_ip_address = sender_address_port[0]
            sender_port = sender_address_port[1]

            #if msg is from server, assume it is the client table
            #update table
            if sender_ip_address==self.server_ip and sender_port == self.server_port:
                #IF DEREG ACK from server
                if message.decode()=="DEREG: Success":
                    print("[You are Offline. Bye.]")
                #IF REG ACK from server
                elif message.decode()=="REG: No Offline Messages":
                    print("[You have no offline messages]")
                elif message.decode()=="REG: Offline Messages":
                    print("[You have offline messages:]")
                #offline-message
                elif message.decode().startswith("[OFFLINE]"):
                    print(message.decode().split("[OFFLINE]")[1])
                    sender = message.decode().split("[OFFLINE]")[1].split(":")[0]
                    #send ACK back to server, confirming they received the offline message
                    #[Offline Message sent at <timestamp> received by <receiver nickname>.]
                    self.socket.sendto(str.encode(f"[OFFLINE ACK]{sender} {datetime.datetime.now()} {self.name}"),sender_address_port)

                #Confirmation that offline message was received
                elif message.decode().startswith("[OFFLINE CONFIRM]"):
                    print(message.decode().split("[OFFLINE CONFIRM]")[1])

                #IF OFFLINE ACK from server
                elif message.decode().startswith("[Offline Message sent at"):
                    print(message.decode())
                #else we are receiving updated table
                else:
                    #update client_table
                    global client_table
                    client_table = eval(message)
                    print("[Client table updated.]")
                    print(client_table)

            #IF ACK For Message Received
            elif message.decode().split("=")[0]=="ACK: Message Received":
                 sender = message.decode().split("=")[1]
                 print(f"[Message received by {sender}.]")
            
            #else assume it is from client
            #lookup client, print message
            else:
                #SEND ACK TO sender!!
                self.socket.sendto(str.encode(f"ACK: Message Received={self.name}"),sender_address_port)

                #find the name of the sender
                sender_nickname = ""
                for client in client_table:
                     ip = client_table[client][0]
                     port = client_table[client][1]
                     if ip==sender_ip_address and port == sender_port:
                         sender_nickname=client
                #print out message from other client
                print(sender_nickname+": "+message.decode())
                

            
        


def main():

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

        #hold info about active/inactive clients
        server_table = {}

        #save message table, holds offline messages for each client
        save_message = {}

        #listen for incoming client connections
        try:
            while(True):
                print(">>> ")
                
                #boolean to broadcast the table
                broadcast = True

                #connection from client wanting to register
                rec = server_socket.recvfrom(1024)
                message = rec[0].decode()
                client_address_port = rec[1]
                client_ip_address = client_address_port[0]
                client_port = client_address_port[1]

                #dereg message
                if message.startswith("DEREG:"):
                    #change client status to False
                    dereg_client = message.split(":")[1]
                    server_table[dereg_client] = [client_ip_address,client_port,False]
                    server_socket.sendto(str.encode("DEREG: Success"),client_address_port)
                #re-registration
                elif message.startswith("REG:"):
                    reg_client = message.split(":")[1]
                    server_table[reg_client] = [client_ip_address,client_port,True]
                    #if have online message send, else don't
                    if len(save_message[reg_client])>0:
                        #ACK of reregistration
                        server_socket.sendto(str.encode("REG: Offline Messages"),client_address_port)
                        #loop through offline messages for re-registered client
                        offline_messages = save_message[reg_client]
                        for message in offline_messages:
                            server_socket.sendto(str.encode("[OFFLINE]"+message),client_address_port)
                        #clear the offline messages
                        save_message[reg_client] = []
                    else:
                        #ACK of reregistration
                        server_socket.sendto(str.encode("REG: No Offline Messages"),client_address_port)
                #save-message
                elif message.startswith("SAVE:"):
                #if the recipient’s status is online in its table, the server should try to contact client
                #wait for an ack from the client within 100msec, if client is active send err & updated table

                    #recipient client is not active, save message to memory
                    #add entry into save-message table
                    receiver = message.split(" ")[1]
                    sender = message.split(" ")[2]
                    timestamp = message.split(" ")[3] + " "+message.split(" ")[4]
                    message_to_save = message.split(" ")[5]

                    #REFORMAT THE MESSAGE: <name_sender>: <timestamp> <messsage>
                    formatted_message = f"{sender}: <{timestamp}> {message_to_save}"
                    save_message[receiver].append(formatted_message) 

                    #send ACK to sender client
                    server_socket.sendto(str.encode(f"[Offline Message sent at <{datetime.datetime.now()}> received by the server and saved.]"),client_address_port)
                    broadcast=False
                #ACK TO OFFLINE message
                elif message.startswith("[OFFLINE ACK]"):
                    #send ACK to original sender of message
                    # #[Offline Message sent at <timestamp> received by <receiver nickname>.]
                    #WE NEED to get the timestamp AND recevier nickname, as well as, we need to know who to sent this message
                    #[OFFLINE ACK]:{sender} {datetime.datetime.now()} {self.name}
                    message = message.split("[OFFLINE ACK]")[1]
                    sender = message.split(" ")[0]
                    timestamp = message.split(" ")[1]+message.split(" ")[2]
                    receiver = message.split(" ")[3]
                    sender_ip = server_table[sender][0]
                    sender_port = server_table[sender][1]
                    server_socket.sendto(str.encode(f"[OFFLINE CONFIRM][Offline Message sent at {timestamp} received by {receiver}.]"),(sender_ip,sender_port))
                    broadcast = False
                #initial registration of client
                else:
                    #represents table with client-name as key
                    server_table[message] = [client_ip_address,client_port,True]
                    #create entry in save-message table for new client
                    save_message[message] = []
                    #send ack for client registration
                    server_socket.sendto(str.encode("ACK: Registration Successful"),client_address_port)

                #BROADCAST TO THE ALL OF THE CLIENTS, the new updated client table
                if broadcast:
                    for client in server_table:
                        #send to only online clients
                        if server_table[client][2] == True:
                            broadcast_client_ip = server_table[client][0]
                            broadcast_client_port = server_table[client][1]
                            server_socket.sendto(str.encode(str(server_table)),(broadcast_client_ip,broadcast_client_port))
                    #...
                    print("[Client table updated.]")
                    print(server_table)
        except KeyboardInterrupt:
            print("Stoping Server...")
           

        

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
        global client_table

        ##successful registration?
        request = client_socket.recvfrom(1024)
        registraction_ack = request[0].decode()
       
        if registraction_ack == "ACK: Registration Successful":
            print("[Welcome, You are registered.]")

        # receive & sender threads for client created
        receive = ClientReceive(client_socket, client_name, server_ip, server_port)
         # sender = Send(self.sock, self.name)

        # start receive & sender threads
        # sender.start()
        receive.start()

        #send messages
        try:
            while(True):
                try:
                    user_input = input(">>> ")
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    print("Exiting...")
                    receive.join()
                    
                    
                #process send message 
                #MAYBE CREATE sender thread that has timeout
                if user_input.split(" ")[0]=='send':
                    receiver_name = user_input.split(" ")[1]
                    message_to_send = user_input.split(" ")[2]
                    #check online status of receiver 
                    receiver_status = client_table[receiver_name][2]

                    #online, try to send message
                    if receiver_status:
                        receiver_ip = client_table[receiver_name][0]
                        receiver_port = client_table[receiver_name][1]
                        #send message to specified client
                        client_socket.sendto(str.encode(message_to_send),(receiver_ip,receiver_port))
                    #offline, send save-message to server
                    else:
                        save_msg = f"SAVE: {receiver_name} {client_name} {datetime.datetime.now()} {message_to_send}"
                        client_socket.sendto(str.encode(save_msg),(server_ip,server_port))

                #deregistration
                elif user_input == "dereg":
                    #send dereg message to server
                    client_socket.sendto(str.encode(f"DEREG:{client_name}"),(server_ip,server_port))
                #re-register
                elif user_input == "reg":
                    #send reg message to server
                    client_socket.sendto(str.encode(f"REG:{client_name}"),(server_ip,server_port))

        except Exception as e:
            # Handle any other exceptions
            print("An error occurred:", str(e))
            # Stop the thread
            receive.join()
            

#run main
main()

