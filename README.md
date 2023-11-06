# Programming Assignment 1 - Simple Chat Application
Melina Garza, mjg2290

## COMMANDS NEEDED TO RUN THE PROGRAM
### Setup
Set permissions
`sudo chmod 777 ChatApp`
### Starting the Server
`./ChatApp -s <port #>`
### Starting the Client
- Get the IP address of the server(in the google cloud console)
  
  `ip addr show scope global | grep -oP 'inet \K[\d.]+'`
  
- Start the client
  
  `./ChatApp -c <client-name> <server-ip(from the above command)> <server-port> <client-port>`

## PROGRAM FEATURES

## CODE EXPLANATION
- global vars explanation
- threads etc.

## KNOWN BUGS

## TEST CASES
1. 

2.

3.

4.

**See test.txt for output samples**
