# Programming Assignment 1 - Simple Chat Application
Melina Garza, mjg2290

## DESCRIPTION
This programming assignment aims to create a user-friendly chat application that enables multiple clients to interact with each other using User Datagram Protocol (UDP). The application is designed as a single program with dual functionalities: client mode and server mode. In client mode, users can communicate directly with each other, akin to private conversations. Meanwhile, in server mode, the application provides central control for managing clients and offers a platform for group conversations.

## COMMANDS NEEDED TO RUN THE PROGRAM
### Setup
Set permissions

`sudo chmod 777 ChatApp`
### Starting the Server
`./ChatApp -s <port #>`
### Starting the Client
Get the IP address of the server/VM(in the Google Cloud console)
  
  `ip addr show scope global | grep -oP 'inet \K[\d.]+'`
  
Start the client
  
  `./ChatApp -c <client-name> <server-ip(from the above command)> <server-port> <client-port>`

### Example Setup
1. Open a terminal, and run the following commands:
- `sudo chmod 777 ChatApp`
- `./ChatApp -s 9000`
2. Open a second terminal, and run the following commands:
- `ip addr show scope global | grep -oP 'inet \K[\d.]+'`
  output: 10.150.0.2
- `./ChatApp -c client1 10.150.0.2 9000 3000`
3. Repeat step 2 to open multiple clients(make sure each client has a unique name & port #)


## PROGRAM FEATURES

## CODE EXPLANATION
- global vars explanation
- threads etc.

## KNOWN BUGS
- ">>> " is not always displayed at the bottom of the console waiting for input, but if you type in valid commands everything works as expected

## TEST CASES
1. 

2.

3.

4.

**See test.txt for output samples**
