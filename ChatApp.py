import sys
import socket
import json
import threading
import datetime
import ipaddress
import time
import uuid

# Define the global server table
server_table = {}
# Define the global client table
client_table = {}
#keep track of send messages and their ACKs
message_acks = {}
#holds offline messages for each client
save_message = {}

def handle_message(message):
    #handle received messages
    print("TO DO")


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
            entire_message = self.socket.recvfrom(65535)
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
                if message.decode().startswith("[DEREG]:"):
                    #remove message_id from ack dict
                    message_id = message.decode().split(":")[1]
                    message_acks.pop(message_id, None)
                    print("[You are Offline. Bye.]")
                #IF REG ACK from server
                elif message.decode()=="REG: No Offline Messages":
                    print("[You have no offline messages]")
                elif message.decode()=="REG: Offline Messages":
                    print("[You have offline messages:]")
                #offline-message
                elif message.decode().startswith("[OFFLINE]"):
                    msg = message.decode().split("[OFFLINE]")[1]
                    #check to see if this is a delivery confirmation for a offline message
                    if msg.startswith("[OFF]"):
                        print(msg.split("[OFF]")[1])
                    else:
                        print(msg)
                    sender = message.decode().split("[OFFLINE]")[1].split(":")[0]
                    #extract original timestamp
                    start_index = message.decode().index('<') + 1
                    end_index = message.decode().index('>')
                    timestamp = message.decode()[start_index:end_index]

                    #send ACK back to server, confirming they received the offline message
                    #[Offline Message sent at <timestamp> received by <receiver nickname>.]
                    self.socket.sendto(str.encode(f"[OFFLINE ACK]{sender} {timestamp} {self.name}"),sender_address_port)

                #Confirmation that offline message was received
                elif message.decode().startswith("[OFFLINE CONFIRM]"):
                    print(message.decode().split("[OFFLINE CONFIRM]")[1])

                #IF OFFLINE ACK from server
                elif message.decode().startswith("[Offline Message sent at"):
                    print(message.decode())

                #receiving GC message
                elif message.decode().startswith("Group Chat "):
                    print(message.decode())

                #ACK for group chat message
                elif message.decode()=="[GROUP ACK]":
                    print("[Group Message received by Server.]")
                
                #Confirmation that we are still active
                elif message.decode().startswith("[ONLINE CONFIRM]:"):
                    message_id = message.decode().split("[ONLINE CONFIRM]:")[1]
                    #send ACK to server
                    self.socket.sendto(str.encode(f"[ONLINE ACK]:{message_id}"), sender_address_port)
                
                #Save Message Request Error, receiver client is active
                elif message.decode().startswith("SAVE-MSG-ERROR:"):
                    active_client = message.decode().split("SAVE-MSG-ERROR:")[1]
                    print(f"[Client {active_client} exists!!]")

                #else we are receiving updated table
                else:
                    #update client_table
                    global client_table
                    client_table = eval(message)
                    print("[Client table updated.]")
                    print(client_table)

            #IF ACK For Message Received
            elif message.decode().split("=")[0]=="ACK: Message Received":
                sender_and_id = message.decode().split("=")[1]
                sender = sender_and_id.split(" ")[0]
                #remove message from ack queue
                message_id = sender_and_id.split(" ")[1]
                message_acks.pop(message_id, None)
                print(f"[Message received by {sender}.]")
                
                
            
            #else assume it is from client
            #lookup client, print message
            else:
                #find the name of the sender
                sender_nickname = ""
                for client in client_table:
                    ip = client_table[client][0]
                    port = client_table[client][1]
                    if ip==sender_ip_address and port == sender_port:
                        sender_nickname=client
                #extract message_id
                message_id = message.decode().split(":")[0]
                #SEND ACK TO sender!!
                self.socket.sendto(str.encode(f"ACK: Message Received={self.name} {message_id}"),sender_address_port)
                #print out message from other client
                print(sender_nickname+": "+message.decode().split(":")[1])
                

#send message between client-client, have timeout 
def send_with_ack(message,client_socket,client_name,server_ip,server_port):
    global client_table
    message_id = str(uuid.uuid4())
    message_acks[message_id] = False
    #process send message 
    #MAYBE CREATE sender thread that has timeout
    if message.split(" ")[0]=='send':
        receiver_name = message.split(" ")[1]
        message_to_send = message.split(" ")[2]
        #check online status of receiver 
        receiver_status = client_table[receiver_name][2]

        #online, try to send message
        if receiver_status:
            receiver_ip = client_table[receiver_name][0]
            receiver_port = client_table[receiver_name][1]
            #send message to specified client
            message_to_send = f"{message_id}:{message_to_send}"
            client_socket.sendto(str.encode(message_to_send),(receiver_ip,receiver_port))
            #wait for ACK, 100 msec
            time.sleep(.1)
            if message_id in message_acks:
                #send message to server to be saved
                save_msg = f"SAVE: {receiver_name} {client_name} {datetime.datetime.now()} {message_to_send}"
                client_socket.sendto(str.encode(save_msg),(server_ip,server_port))
                #print confirmation of no ACK
                print(f"[No ACK from {receiver_name}, message sent to server.]")
               

        #offline, send save-message to server
        else:
            save_msg = f"SAVE: {receiver_name} {client_name} {datetime.datetime.now()} {message_to_send}"
            client_socket.sendto(str.encode(save_msg),(server_ip,server_port))

    #groupchat
    elif message.split(" ")[0]=="send_all":
        message_to_send = message.split(" ")[1]
        group_msg = f"GROUP:{client_name}: {message_to_send}"
        client_socket.sendto(str.encode(group_msg),(server_ip,server_port))

    #deregistration
    elif message == "dereg":
        # Create a new thread for sending the deregistration request
        deregistration_thread = threading.Thread(target=send_dereg, args=(client_socket,client_name,server_ip,server_port))
        # Start the thread
        deregistration_thread.start()

    #re-register
    elif message == "reg":
        #send reg message to server
        client_socket.sendto(str.encode(f"REG:{client_name}"),(server_ip,server_port))  
        
#send dereg request to server, confirm ACK
def send_dereg(client_socket, client_name, server_ip, server_port):
    
    # Set a timeout of 100 milliseconds for receiving an ACK
    # client_socket.settimeout(0.1)
    retries = 0
    while retries < 5:
        #add message to dict for ack
        message_id = str(uuid.uuid4())
        message_acks[message_id] = False
        #send dereg message to server
        client_socket.sendto(str.encode(f"DEREG:{client_name} {message_id}"),(server_ip,server_port))

        #wait for 100 msec
        time.sleep(0.1)

        if message_id not in message_acks:
            #acked, break out of loop
            break
        else:
            #no response from the server, retry
            print("Retrying..")
        retries+=1
    if retries == 5:
        print("[Server not responding]")
        print("[Exiting]")
        #EXIT -> OH clarification




#ping client to confirm whether or not it is still active
def send_online_confirm(receiver, sender_info, server_socket, formatted_message, timestamp):
    receiver_ip = server_table[receiver][0]
    reciever_port = server_table[receiver][1]
     #add message to dict for ack
    message_id = str(uuid.uuid4())
    message_acks[message_id] = False

    #send ONLINE request to questionable receiver
    server_socket.sendto(str.encode(f"[ONLINE CONFIRM]:{message_id}"), (receiver_ip,reciever_port))

    #set timeout
    time.sleep(0.1)

    #if ACK received
    # send sender, err message, and send the updated table to the client
    if message_id not in message_acks:
        server_socket.sendto(str.encode(f"SAVE-MSG-ERROR:{receiver}"),sender_info)
        server_socket.sendto(str.encode(str(server_table)),sender_info)
    #if no ACK received
    #change status of client to offline, broadcast to all active clients, save the message
    else:
        server_table[receiver][2]=False
        #broadcast
        server_broadcast(server_socket)
        #save message
        save_message[receiver].append(formatted_message) 
        #send ACK to sender client
        server_socket.sendto(str.encode(f"[Offline Message sent at <{timestamp}> received by the server and saved.]"),sender_info)
    
#broadcast client table to all active clients
def server_broadcast(server_socket):
    for client in server_table:
        #send to only online clients
        if server_table[client][2] == True:
            broadcast_client_ip = server_table[client][0]
            broadcast_client_port = server_table[client][1]
            server_socket.sendto(str.encode(str(server_table)),(broadcast_client_ip,broadcast_client_port))
    #...
    print("[Client table updated.]")
    print(server_table)

#thread to handle received messages by server
def server_receiver(server_socket,message,client_address_port,client_ip_address,client_port):
    #boolean to broadcast the table
    broadcast = True

    #dereg message
    if message.startswith("DEREG:"):
        #change client status to False
        dereg_client_id = message.split(":")[1]
        dereg_client = dereg_client_id.split(" ")[0]
        message_id = dereg_client_id.split(" ")[1]
        server_table[dereg_client] = [client_ip_address,client_port,False]
        server_socket.sendto(str.encode(f"[DEREG]:{message_id}"),client_address_port)
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
        
        receiver = message.split(" ")[1]
        sender = message.split(" ")[2]
        timestamp = message.split(" ")[3] + " "+message.split(" ")[4]
        message_to_save = message.split(" ")[5]
        #REFORMAT THE MESSAGE: <name_sender>: <timestamp> <messsage>
        formatted_message = f"{sender}: <{timestamp}> {message_to_save}"

        #if the recipient’s status is online in its table, the server should try to contact client
        #wait for an ack from the client within 100msec, if client is active send err & updated table
        if server_table[receiver][2]==True:
            # Create a new thread for checking to see if client is online
            active_thread = threading.Thread(target=send_online_confirm, args=(receiver,client_address_port,server_socket,formatted_message,timestamp))
            # Start the thread
            active_thread.start()
        else:
            #if recipient client is not active, save message to memory
            #add entry into save-message table
            save_message[receiver].append(formatted_message) 
            #send ACK to sender client
            server_socket.sendto(str.encode(f"[Offline Message sent at <{timestamp}> received by the server and saved.]"),client_address_port)
        broadcast=False
    #ACK TO OFFLINE message
    elif message.startswith("[OFFLINE ACK]"):
        #send ACK to original sender of message
        #[OFFLINE ACK]:{sender} {datetime.datetime.now()} {self.name}
        message = message.split("[OFFLINE ACK]")[1]
        #remove Group Chat beginning
        if message.startswith("Group Chat"):
            message = message.split("Group Chat ")[1]
        #make sure that client isn't jusst re-registering and receiving a queued up delivery confirmation
        if not message.startswith("[OFF]"):
            sender = message.split(" ")[0]
            timestamp = message.split(" ")[1]+" "+message.split(" ")[2]
            receiver = message.split(" ")[3]
            sender_ip = server_table[sender][0]
            sender_port = server_table[sender][1]

            #if original sender is online
            if server_table[sender][2]==True:
                server_socket.sendto(str.encode(f"[OFFLINE CONFIRM][Offline Message sent at <{timestamp}> received by {receiver}.]"),(sender_ip,sender_port))
            #original sender is offline
            else:
                #save to sender's offline messages
                save_message[sender].append(f"[OFF][Offline Message sent at <{timestamp}> received by {receiver}.]") 
                
        broadcast = False
    #ONLINE ACK
    elif message.startswith("[ONLINE ACK]:"):
        message_id = message.split("[ONLINE ACK]:")[1]
        message_acks.pop(message_id, None)
        broadcast = False
    ##GROUP CHAT message
    elif message.startswith("GROUP:"):
        message = message.split("GROUP:")[1]
        #send ACK back to sender
        server_socket.sendto(str.encode("[GROUP ACK]"), client_address_port)

        #get the name of the sender
        sender_name = ""
        for client in server_table:
            if server_table[client][0]==client_ip_address and server_table[client][1]==client_port:
                sender_name = client


        #loop through clients and send GC message
        for client in server_table:
            gc_client_ip = server_table[client][0]
            gc_client_port = server_table[client][1]
            if server_table[client][2]==True:
                #send gc message to active client
                if gc_client_port!=client_port or gc_client_ip!=client_ip_address:
                    server_socket.sendto(str.encode("Group Chat "+ message), (gc_client_ip,gc_client_port))
            else:
                #save message for offline clients
                #message to save
                msg_save = message.split(": ")[1]
                timestamp = datetime.datetime.now()
                formatted_message = f"Group Chat {sender_name}: <{timestamp}> {msg_save}"
                save_message[client].append(formatted_message) 

                #send ACK to sender client
                server_socket.sendto(str.encode(f"[Offline Message sent at <{timestamp}> received by the server and saved.]"),client_address_port)
                
        broadcast = False
    
    #initial registration of client
    else:
        #represents table with client-name as key
        server_table[message] = [client_ip_address,client_port,True]
        #create entry in save-message table for new client
        if message not in save_message:
            save_message[message] = []
        #send ack for client registration
        server_socket.sendto(str.encode("ACK: Registration Successful"),client_address_port)

    #BROADCAST TO THE ALL OF THE CLIENTS, the new updated client table
    if broadcast:
        server_broadcast(server_socket)


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
            sys.exit()
        
        
        #hard-coding, need to get from local machine?
        server_ip = "127.0.0.1"

        #create a socket
        #AF_INET = family addr ipv4
        #SOCK_DGRAM = aka UDP
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        
        #bind to ip address & port
        server_socket.bind((server_ip,server_port))

        #hold info about active/inactive clients
        global server_table

        #save message table, holds offline messages for each client
        global save_message

        #listen for incoming client connections/messages
        try:
            while(True):
                print(">>> ")
                
                #receive message/connection from client
                rec = server_socket.recvfrom(65535)
                message = rec[0].decode()
                client_address_port = rec[1]
                client_ip_address = client_address_port[0]
                client_port = client_address_port[1]

                #start a new thread to handle the received info
                server_receiver_thread = threading.Thread(target=server_receiver, args=(server_socket,message,client_address_port,client_ip_address,client_port))
                server_receiver_thread.start()

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
        if not 1024<=server_port<=65535:
            print("[Invalid server port number, needs to be in range 1024-65535]")
            sys.exit()
        elif not 1024<=client_port<=65535:
            print("[Invalid client port number, needs to be in range 1024-65535]")
            sys.exit()
        else:
            try:
                ipaddress.ip_address(server_ip)
            except:
                print("[Invalid ip address, needs to be in format of #.#.#.#]")
                sys.exit()

        
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
        request = client_socket.recvfrom(65535)
        registraction_ack = request[0].decode()
       
        if registraction_ack == "ACK: Registration Successful":
            print("[Welcome, You are registered.]")

        # receive & sender threads for client created
        receive = ClientReceive(client_socket, client_name, server_ip, server_port)
         # sender = Send(self.sock, self.name)

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
                
                send_thread = threading.Thread(target=send_with_ack, args=(user_input,client_socket,client_name,server_ip,server_port))
                send_thread.start()

        except Exception as e:
            # Handle any other exceptions
            print("An error occurred:", str(e))
            # Stop the thread
            receive.join()
            

#run main
main()

