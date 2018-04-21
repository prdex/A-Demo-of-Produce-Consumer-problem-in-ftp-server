import socket
import threadpool
import time
import os
import socket
import time
import math
import sys
import random
import select
import threading

# this is a multithreaded client program that was used to test
# the server code

client_thread_pool = threadpool.ThreadPool(5)

ip_address = socket.gethostbyname(socket.gethostname())

port_num = 8082

#each 1 is 10 seconds
cache_time = 2

# Stores last 5 accessed items
# (file_path, file_contents, age)
cache_queue = []
file_open=""
response_var = ""
k=0
def connect_to_server_userin():
    global k
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_num)
    print("connecting to %s on port %s\n" % server_address)
    sock.connect(server_address)
    client_thread_pool.add_task(
        get_server_response,
        sock
    )

    client_thread_pool.add_task(
        auto_update_cache
    )

    while True:
        user_in = input()
        k=0
        message = generate_message(user_in)
        cache_res = cache_interaction(sock, message)
        # if there is no cached response
        if cache_res == None:
		    
            #sock.send( message.encode(), ('127.0.0.1', port_num))
            sock.send(message.encode(),('127.0.0.1',port_num))
            if message == "exit":
                os._exit(0)
#        else:
#            print(cache_res)

    sock.close()

def get_server_response(socket):
    global response_var
    global file_open
    global k
    while True:
        data = socket.recv( 1024 )
        response_var = data
        if (data != None):
            # if reading cache item
            if(len(data.split("////")) == 2):
                split_data = data.split("////")
                add_to_cache(split_data[0], split_data[1])
                if k == 0:
                    print(split_data[1])
                if k == 1:
                    text_file = open(file_open, "a+")
                    text_file.write(split_data[1])
                    text_file.close()
            else:
                if k==0:
                    print(data)
       	        if k == 1:
                    text_file = open(file_open, "a+")
                    text_file.write(data)
                    text_file.close();    

#    else:
#        while True:
#            data = socket.recv( 1024 )
#            response_var = data
#            if (data != None):
#                # if reading cache item
#                if(len(data.split("////")) == 2):
#                    split_data = data.split("////")
#                    add_to_cache(split_data[0], split_data[1])
#                    print(split_data[1])
#                else:
#                    print data

def generate_message(input):
    global k
    global file_open
    split_input = input.split(" ")
    if split_input[0] == "upload":
        if len(split_input) != 2:
            print("unrecognised command")
            return ""
        try:
            file = open(split_input[1])
            file_contents = file.read()
            return "%s////%s////%s" % (split_input[0], split_input[1], file_contents)
        except IOError:
            print("no such file in source directory")
            return ""
    elif split_input[0] == "download":
        if len(split_input) != 2:
            print("unrecognised command!")
            return ""
        try:
#            file = open(split_input[1])
#            file_contents = file.read()
            k=1;
            file_open=split_input[1]
            split_input[0]="download"
            return '////'.join(split_input)
        except IOError:
            print("no such file in source directory")
            return ""
    elif split_input[0] == "append":
        try:
            #file = open(split_input[1])
            file_contents = ""
            for temp in range(2,len(split_input)):
                file_contents +=split_input[temp] +" "
            return "%s////%s////%s" % (split_input[0], split_input[1], file_contents)
        except IOError:
            print("no such file in source directory")
            return ""
    else:
        return '////'.join(split_input)

def cache_interaction(connection, message):
    global response_var
    split_message = message.split("////")
    if len(split_message) == 2 and split_message[0] == "read":
        connection.send("pwd")
        time.sleep(1)
        response_message = response_var
        search_term = "%s%s" % (response_message, split_message[1])
        return_message = search_cache(search_term)
        log_cache()
        print(search_term)
        return return_message
    return None

# searches the cache for an item
def search_cache(path):
    for item in cache_queue:
        if item[0] == path:
            return item[1]
    return None

# adds an item to the cache
def add_to_cache(path, contents):
    cache_queue.insert(0, (path, contents, 0))
    if len(cache_queue) > 5:
        cache_queue.pop()

# logs the contents of the cache
def log_cache():
    for item in cache_queue:
        print("%s\t%s\t%d" % (item))

# function removes old items from cache
def auto_update_cache():
    global cache_queue
    while True:
        time.sleep(10)
        new_cache_queue = []
        for item in cache_queue:
            if item[2] < cache_time:
                new_cache_record = (item[0], item[1], item[2] + 1)
                new_cache_queue.append(new_cache_record)
        cache_queue = new_cache_queue

if __name__ == '__main__':
    # Main line for program
    # Create 20 tasks that send messages to the server
    connect_to_server_userin()
    # wait for threads to complete before finishing program
    client_thread_pool.wait_completion()
