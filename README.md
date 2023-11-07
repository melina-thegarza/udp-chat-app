# Programming Assignment 1 - Simple Chat Application
Name: Melina Garza
Uni: mjg2290

## DESCRIPTION
This programming assignment aims to create a user-friendly chat application that enables multiple clients to interact with each other using User Datagram Protocol (UDP). The application is designed as a single program with dual functionalities: client mode and server mode. In client mode, users can communicate directly with each other, akin to private conversations. Meanwhile, in server mode, the application provides central control for managing clients and offers a platform for group conversations.

## COMMANDS NEEDED TO RUN THE PROGRAM
### Setup
Set permissions

`sudo chmod 777 ChatApp`
### Starting the Server
`./ChatApp -s <port #>`
### Starting the Client
`./ChatApp -c <client-name> 127.0.0.1 <server-port> <client-port>`

### Example Setup
1. Open a terminal, and run the following commands:
- `sudo chmod 777 ChatApp`
- `./ChatApp -s 9000`
2. Open a second terminal, and run the following commands:
- `./ChatApp -c client1 127.0.0.1 9000 3000`
3. Repeat step 2 to open multiple clients(make sure each client has a unique name & port #)


## PROGRAM FEATURES
### Registered client can:
#### Send Direct Messages
- send [client-name] [message]
  
  ex. `send client1 hi`
  
#### Send Group Messages
- send_all [message]
  
  ex. `send_all hello`
  
#### Deregister
- `dereg`

### Deregistered client can:
#### Re-register
- `reg`

## CODE EXPLANATION
### Global variables
#### Client Tables(`server_table` & `client_table`)
- Used a dictionary to keep track of clients:  {key=client-name, value= list[ip_address, port #, status]}
#### Saving Offline Messages
- Used a dictionary, `save_message` to keep track of offline messages for each user: {key=client_name, value = list[message1, message2,...]}
#### Client Status
- Created a global boolean variable `client_registration_status` to keep track of whether the client is registered or deregistered.
- Used to limit user input based on status
#### Message ACK tracking
- Used a dictionary,`message_acks`, as a ledger to keep track of which messages have not been ACKed
- Each time a message is ACKed, its ID is removed from `message_acks`
 
### Threads
To ensure no blocking occurs, both the server and client have threads to separate the handling of receiving and sending messages.

**Server Receiver Thread:** Handles messages received by the server from clients. Processes various message types, and creates new threads for message handling.

**Client Receiver Thread:** Listens for messages received by clients from the server or other clients and creates new threads for message handling.

**Client Handle Message Thread:** Processes messages received by clients, distinguishing between server and client messages, and sends acknowledgments.

**Client Sender Thread:** Sends messages from clients to other clients or the server, ensuring valid commands and handling acknowledgments.


## KNOWN BUGS
- Issue: The ">>> " prompt sometimes starts a new line when prompting for user input, and it is not always displayed at the bottom of the console, waiting for input. However, it still takes in the correct commands and behaves as expected, as shown below.

ex.

 ">>>"

  send client1 message
  
## FUNCTIONS IMPLEMENTED
1. **server_receiver**: thread to handle messages received by the server
2. **send_online_confirmation**: when the server receives a save-message request, we need to confirm whether or not a client is online
3. **server_broadcast**: called when we need the server to broadcast the client_table to all online/active clients
4. **client_receiver**: thread to handle messages received by a client, creates a separate thread to handle actual message(client_handle_message)
5. **client_handle_message**: parses received messages for the client and prints messages to the console
6. **client_sender**: given client input, a client_sender thread is started which is responsible for sending the message and keeping track of ACKs
7. **send_dereg**: when a client `dereg`, this thread handles the deregistration process including timeout and exiting if no ACK is received
8. **send_group_chat**: when a client sends a group chat message, this thread handles sending the message to the server, the timeout, and ensuring that the request is ACKed
9. **check_port_num**: checks to make sure that the given input is a valid port number

## TEST CASES
1. Offline Messaging: If the original sender is offline, include delivery confirmation in their offline messages when they return.

2. Offline Chatting in Group Chats: Silent Leave vs Notified Leave

3. Server Unavailability for Group Chats

4. Error Handling: Handling Invalid Commands, Duplicate User Registration, and Invalid Port Numbers/IP Addresses

**See test.txt for output samples**
