import socket
import threadpool
import os
import filesystem_servermodel

# global threadpool for server
server_thread_pool = threadpool.ThreadPool(500)

port_number = 8082

ip_address = socket.gethostbyname(socket.gethostname())

file_system_manager = filesystem_servermodel.FileSystemManager('FileSystemDir')

def create_server_socket():
    # create socket  and initialise to localhost:8020
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_number)
    print("starting up on %s port %s" % server_address)
    # bind socket to server address and wait for incoming connections4
    sock.bind(server_address)
    sock.listen(1)

    while True:
        # sock.accept returns a 2 element tuple
        connection, client_address = sock.accept()
        # print "Connection from %s, %s\n" % connection, client_address
        # Hand the client interaction off to a seperate thread
        server_thread_pool.add_task(
            start_client_interaction,
            connection,
            client_address
        )


def start_client_interaction(connection, client_address):
    try:
        #A client id is generated, that is associated with this client
        client_id = file_system_manager.add_client(connection)
        while True:
            data = connection.recv(1024)
            split_data = seperate_input_data(data)
            # Respond to the appropriate message
            if data == "KILL_SERVICE":
                kill_service(connection)
            elif split_data[0] == "ls":
                ls(connection, client_id, split_data)
            elif split_data[0] == "cd":
                cd(connection, split_data, client_id)
            elif split_data[0] == "up":
                up(connection, split_data, client_id)
            elif split_data[0] == "read":
                read(connection, split_data, client_id)
            elif split_data[0] == "upload":
                write(connection, split_data, client_id)
            elif split_data[0] == "rmvfile":
                delete(connection, split_data, client_id)
            elif split_data[0] == "download":
                download(connection, split_data, client_id)
            elif split_data[0] == "lock":
                lock(connection, split_data, client_id)
            elif split_data[0] == "append":
                append(connection, split_data, client_id)
            elif split_data[0] == "release":
                release(connection, split_data, client_id)
            elif split_data[0] == "mkdir":
                mkdir(connection, split_data, client_id)
            elif split_data[0] == "rmdir":
                rmdir(connection, split_data, client_id)
            elif split_data[0] == "pwd":
                pwd(connection, split_data, client_id)
            elif split_data[0] == "copy":
                copy(connection, split_data, client_id)
            elif split_data[0] == "newFile":
                newFile(connection, split_data, client_id)
            elif split_data[0] == "exit":
                exit(connection, split_data, client_id)
            else:
                error_response(connection, 1)
    except:
        error_response(connection, 0)
        connection.close()

def kill_service(connection):
    # Kill service
    response = "Killing Service"
    connection.sendall("%s" % response)
    connection.close()
    os._exit(0)

def ls(connection, client_id, split_data):
    response = ""
    if len(split_data) == 1:
        response = file_system_manager.list_directory_contents(client_id)
        connection.sendall(response)
    elif len(split_data) == 2:
        response = file_system_manager.list_directory_contents(client_id, split_data[1])
        connection.sendall(response)
    else:
        error_response(connection, 1)

def cd(connection, split_data, client_id):
    if len(split_data) == 2:
        res = file_system_manager.change_directory(split_data[1], client_id)
        response = ""
        if res  == 0:
            response = "changed directory to %s" % split_data[1]
        elif res == 1:
            response = "directory %s doesn't exist" % split_data[1]
        connection.sendall(response)
    else:
        error_response(connection, 1)

def up(connection, split_data, client_id):
    if len(split_data) == 1:
        file_system_manager.move_up_directory(client_id)
    else:
        error_response(connection, 1)

def download(connection, split_data, client_id):
    if len(split_data) == 2:
        response = file_system_manager.download_item(client_id, split_data[1])
        connection.sendall(response)
    else:
        error_response(connection, 1)

def read(connection, split_data, client_id):
    if len(split_data) == 2:
        response = file_system_manager.read_item(client_id, split_data[1])
        connection.sendall(response)
    else:
        error_response(connection, 1)
def copy(connection, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        connection.sendall("need at least 3 parameters")
    elif len(split_data) == 3:
        response = file_system_manager.copy_item(client_id, split_data[1], split_data[2])
        connection.sendall(response)
    else:
        error_response(connection, 1)
def newFile(connection, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        res=file_system_manager.create_item(client_id, split_data[1])
        if res == 0:
            response = "successfully created"
        elif res == 1:
            response = "file locked"
        elif res == 2:
            response = "cannot write to a directory file"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def append(connection, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        res = file_system_manager.write_item(client_id, split_data[1], "")
        if res == 0:
            response = "append successfull"
        elif res == 1:
            response = "file locked"
        elif res == 2:
            response = "cannot append to a directory file"
        connection.sendall(response)
    elif len(split_data) == 3:
        res = file_system_manager.append_item(client_id, split_data[1], split_data[2])
        connection.sendall(res)
    else:
        error_response(connection, 1)

def write(connection, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        res = file_system_manager.write_item(client_id, split_data[1], "")
        if res == 0:
            response = "write successfull"
        elif res == 1:
            response = "file locked"
        elif res == 2:
            response = "cannot write to a directory file"
        connection.sendall(response)
    elif len(split_data) == 3:
        res = file_system_manager.write_item(client_id, split_data[1], split_data[2])
        if res == 0:
            response = "write successfull"
        elif res == 1:
            response = "file locked"
        elif res == 2:
            response = "cannot write to a directory file"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def delete(connection, split_data, client_id):
    if len(split_data) == 2:
        res = file_system_manager.delete_file(client_id, split_data[1])
        response = ""
        if res == 0:
            response = "delete successfull"
        elif res == 1:
            response = "file locked"
        elif res == 2:
            response = "use rmdir to delete a directory"
        elif res == 3:
            response = "file doesn't exist"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def lock(connection, split_data, client_id):
    if len(split_data) == 2:
        client = file_system_manager.get_active_client(client_id)
        res = file_system_manager.lock_item(client, split_data[1])
        response = ""
        if res == 0:
            response = "file locked"
        elif res == 1:
            response = "file already locked"
        elif res == 2:
            response = "file doesn't exist"
        elif res == 3:
            response = "locking directories is not supported"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def release(connection, split_data, client_id):
    if len(split_data) == 2:
        client = file_system_manager.get_active_client(client_id)
        res = file_system_manager.release_item(client, split_data[1])
        if res == 0:
            response = split_data[1] + " released"
        elif res == -1:
            response = "you do not hold the lock for %s" % split_data[1]
        connection.sendall(response)
    else:
        error_response(connection, 1)

def mkdir(connection, split_data, client_id):
    if len(split_data) == 2:
        response = ""
        res = file_system_manager.make_directory(client_id, split_data[1])
        if res == 0:
            response = "new directory %s created" % split_data[1]
        elif res == 1:
            response = "file of same name exists"
        elif res == 2:
            response = "directory of same name exists"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def rmdir(connection, split_data, client_id):
    if len(split_data) == 2:
        response = ""
        res = file_system_manager.remove_directory(client_id, split_data[1])
        if res == -1:
            response = "%s doesn't exist" % split_data[1]
        elif res == 0:
            response = "%s removed" % split_data[1]
        elif res == 1:
            response = "%s is a file" % split_data[1]
        elif res == 2:
            response = "directory has locked contents"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def pwd(connection, split_data, client_id):
    if len(split_data) == 1:
        response = file_system_manager.get_working_dir(client_id)
        connection.sendall(response)
    else:
        error_response(connection, 1)

def exit(connection, split_data, client_id):
    if len(split_data) == 1:
        file_system_manager.disconnect_client(connection, client_id)
    else:
        error_response(connection, 1)

def error_response(connection, error_code):
    response = ""
    if error_code == 0:
        response = "server error"
    if error_code == 1:
        response = "unrecognised command"
    connection.sendall(response)

#Function to split reveived data strings into its component elements
def seperate_input_data(input_data):
    seperated_data = input_data.split('////')
    return seperated_data

if __name__ == '__main__':
    create_server_socket()
    # wait for threads to complete
    server_thread_pool.wait_completion()
