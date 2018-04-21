import datetime
import threadpool
import time
import os
import shutil

class Client:
    # Initialise a new File System client
    def __init__(self, id, socket, path_to_root):
        self.id = id
        self.socket = socket
        self.dir_level = 0
        # Path to root is the path to the root of the file_system
        self.dir_path = [path_to_root]

    #
    # Functions for working with directories
    #

    # Move into the passed directory
    def change_directory(self, dir_name ):
        self.dir_level = self.dir_level + 1
        self.dir_path.append( dir_name )

    # Move up a directory level
    # Return 0 : Success
    # Return 1 : At top directory level
    def move_up_directory(self):
        if self.dir_level > 0:
            self.dir_path.pop()
            self.dir_level = self.dir_level - 1
            return 0
        else:
            return 1

    #
    # Testing functions
    #
    def log_member_data(self):
        print("")
        print("dir_path: " + (self.dir_path).__repr__())
        print("socket: " + (self.socket).__repr__())
        print("id: %d" % self.id)
        print("dir_level: %d" % self.dir_level)
        print("")

class FileSystemManager:

    # List for storing active clients
    active_clients = []

    # Next ID to be assigned to new client and events
    next_client_id = 0
    next_event_id = 0

    # List of events and IDs
    # ( event_id , command, time )
    events = []

    # List of the paths of currently locked files
    # ( client_id, time, path )
    locked_files = []

    # ThreadPool will contain threads managing the autorelease
    # of locks
    file_system_manager_threadpool = threadpool.ThreadPool(1)

    # Create new File System Manager and initialise the root
    def __init__(self, root_path):
        self.root_path = root_path
        #Add autorelease function to a new thread
        self.file_system_manager_threadpool.add_task(
            self.auto_release
        )

    # Generate a client ID and update next_client_id
    def gen_client_id(self):
        return_client_id = self.next_client_id
        self.next_client_id = self.next_client_id + 1
        return return_client_id

    # Generate a client ID and update next_event_id
    def gen_event_id(self):
        return_event_id = self.next_event_id
        self.next_event_id = self.next_event_id + 1
        return return_event_id

    #
    # Functions for interacting with clients
    #

    # Adds a new client to the file system manager
    # Returns the id of the client
    def add_client(self, connection):
        new_client_id = self.gen_client_id();
        new_client = Client(new_client_id, connection, self.root_path)
        self.active_clients.append(new_client)
        return new_client_id

    def remove_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients.pop(i)
            i = i + 1

    def get_active_client(self, client_id):
        for client in self.active_clients:
            if client.id == client_id:
                return client

    def update_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients[i] = client_in
            i = i + 1

    # checks if a client exists which has the same id as the one passed in
    def client_exists(self, id_in):
        for client in self.active_clients:
            if ( client.id == id_in ):
                return True
        return False

    # disconnect client from server
    def disconnect_client(connection, client_id):
        # get client
        client = self.get_active_client(client_id)
        # remove client from active clients
        self.remove_client(client)
        # disconnect socket
        connection.sendall("disconnected")
        connection.close()
        # add event
        self.add_event("disconnect client %d" % client_id)

    #
    # Functions for interacting with events
    #

    def add_event(self, command):
        new_event_id = self.gen_event_id()
        event_timestamp = datetime.datetime.now()
        new_event_record = (new_event_id, command, event_timestamp)
        self.events.append(new_event_record)
        print("%d\t%s\t%s" % (new_event_record[0], new_event_record[2], new_event_record[1]))

    def log_events(self):
        print("EID\tTIME\t\t\t\tCOMMAND")
        for event in self.events:
            print("%d\t%s\t%s" % (event[0], event[2], event[1]))

    #
    # Functions for moving directories
    #

    # Changes directory
    # Return 0 : Change successfull
    # Return 1 : Directory doesn't exist
    def change_directory(self, dir_name, client_id):
        client = self.get_active_client(client_id)
        # Check if directory exists
        new_dir_path = self.resolve_path(client_id, dir_name)
        is_dir_val = os.path.isdir("./" + new_dir_path)
        # Exit if directory does not exist
        if is_dir_val == False:
            return 1
        # Change directory if it does
        client.change_directory(dir_name)
        self.update_client(client)
        self.add_event("cd " + dir_name)
        return 0

    def move_up_directory(self, client_id):
        client = self.get_active_client(client_id)
        client.move_up_directory()
        self.update_client(client)
        self.add_event("up")

    # Lists contents of directory
    # returns response string
    def list_directory_contents(self, client_id, item_name = ""):
        path = self.resolve_path(client_id, item_name)
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "No such directory %s" % item_name
        elif item_type == 0:
            return "Cannot list contents of %s" % item_name
        else:
            item_list = os.listdir("./" + path)
            return_string = "Type\tPath"
            for item in item_list:
                list_item_type = self.item_exists(client_id, item)
                if list_item_type == 0:
                    return_string = return_string + "\n" + "f\t" + item
                elif list_item_type == 1:
                    return_string = return_string + "\n" + "d\t" + item
            return return_string

    # Passed the name of an item this function returns the path
    # to that item
    def resolve_path(self, client_id, item_name):
        client = self.get_active_client(client_id)
        file_path = ""
        for path_element in client.dir_path:
            file_path = file_path + "%s/" % path_element
        file_path = file_path + item_name
        return file_path

    # Passed the name of an item this function returns the path
    # to that item
    def get_working_dir(self, client_id):
        client = self.get_active_client(client_id)
        file_path = ""
        for path_element in client.dir_path:
            file_path = file_path + "%s/" % path_element
        return file_path

    #
    # Functions for interacting with locking
    #

    # Locks an item if it is not locked
    # Return 0 : Item was locked
    # Return 1 : Item was already locked
    # Return 2 : Item doesn't exist
    # Return 3 : Item is a directory
    def lock_item(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        # if item is not a file or doesnt exist exit
        item_type = self.item_exists(client.id, item_name)
        if item_type == -1:
            return 2
        elif item_type == 1:
            return 3
        if self.check_lock(client, item_name) ==  True:
            return 1
        else:
            lock_timestamp = datetime.datetime.now()
            lock_record = (client.id, lock_timestamp, file_path)
            self.locked_files.append(lock_record)
            self.add_event("lock " + file_path)
            return 0

    # Unlocks an item if it was locked
    def release_item(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        i = 0
        item_released = False
        for locked_file in self.locked_files:
            if file_path == locked_file[2]:
                if client.id == locked_file[0]:
                    self.locked_files.pop(i)
                    self.add_event("release " + file_path)
                    item_released = True
            i = i + 1
        if item_released:
            return 0
        else:
            return -1

    # Checks if an item is locked
    # Return True : Item is locked
    # Returns False : Item is not locked
    def check_lock(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        for locked_file in self.locked_files:
            if locked_file[2] == file_path:
                return True
        return False

    # Traverses the list of locked items and releases locked item if
    # client does not exist
    # Run in a thread initialized in the __init__ function
    def auto_release(self):
        while True:
            # auto release occurs every minute
            time.sleep(60)
            new_locked_file_list = []
            for locked_file in self.locked_files:
                for client in self.active_clients:
                    if locked_file[0] == client.id:
                        new_locked_file_list.append(locked_file)
            self.locked_files = new_locked_file_list
            self.add_event("lock auto-release")

    def log_locks(self):
        print("LID\tTIME\t\t\t\tPATH")
        for locked_file in self.locked_files:
            print("%d\t%s\t%s" % locked_file)

    #
    # Functions for interacting with items
    #

    # Returns whether or not a passed file path has a corresponding file
    # Return -1 : Item doesnt exist
    # Return 0 : Item exists as file
    # Return 1 : Item exists as directory

    def item_exists(self, client_id, item_name):
        file_path = self.resolve_path(client_id, item_name)
        is_file = os.path.isfile("./"+file_path)
        if is_file == True:
            return 0
        is_dir = os.path.isdir("./"+file_path)
        if is_dir == True:
            return 1
        else:
            return -1

    # Returns the path and contents of a file as a string
    def download_item(self, client_id, item_name):
        # check if item exists
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "It doesn't exist"
        elif item_type == 1:
            return "It is a directory"
        elif item_type == 0:
            # read item
            client = self.get_active_client(client_id)
            lock_res = self.lock_item(client, item_name)
            if lock_res == 1:
            	return "File is locked"
            file_path = self.resolve_path(client_id, item_name)
            file = open(file_path, 'r')
            file_contents = file.read()
            # add event
            self.add_event("download " + file_path)
            return_string = "%s////%s" % (file_path, file_contents)
            self.release_item(client, item_name)
            return return_string


    # Returns the path and contents of a file as a string
    def read_item(self, client_id, item_name):
        # check if item exists
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "%s doesn't exist" % item_name
        elif item_type == 1:
            return "%s is a directory" % item_name
        elif item_type == 0:
            # read item
            file_path = self.resolve_path(client_id, item_name)
            file = open(file_path, 'r')
            file_contents = file.read()
            # add event
            self.add_event("read " + file_path)
            return_string = "%s////%s" % (file_path, file_contents)
            return return_string

    # Writes a passed string to a file with a passed name
    # Return 0 : Write successfull
    # Return 1 : Write unsuccessfull, File locked
    # Return 2 : Write unsuccessfull, File is a directory
    def write_item(self, client_id, item_name, file_contents):
        item_type = self.item_exists(client_id, item_name)
        # exit if the item is a directory
        if item_type == 1:
            return 2
        # lock_item
        client = self.get_active_client(client_id)
        lock_res = self.lock_item(client, item_name)
        # Exit if file is locked
        if lock_res == 1:
            return 1
        # write to it
        file_path = self.resolve_path(client_id, item_name)
        file = open(file_path, 'w+')
        file.truncate()
        file.write(file_contents)
        # add write event
        self.add_event("write " + file_path)
        # If item had previously never existed
        if lock_res == 2:
            return 0
        # release it
        self.release_item(client, item_name)
        return 0
    def create_item(self, client_id, item_name):
        item_type = self.item_exists(client_id, item_name)
        # exit if the item is a directory
        if item_type == 1:
            return 2
        file_path = self.resolve_path(client_id, item_name)
        file = open(file_path, 'w+')
        return 0
    def append_item(self, client_id, item_name, file_contents):
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "%s doesn't exist" % item_name
        elif item_type == 1:
            return "%s is a directory" % item_name
        elif item_type == 0:
            client = self.get_active_client(client_id)
            lock_res = self.lock_item(client, item_name)
            # Exit if file is locked
            if lock_res == 1:
                return "file locked"
            # read item
            file_path = self.resolve_path(client_id, item_name)
            file = open(file_path, 'a')
            file.write("\n")
            file_contents = file.write(file_contents)
            # add event
            #self.add_event("read " + file_path)
            #return_string = "%s////%s" % (file_path, file_contents)
            self.release_item(client, item_name)
            return "success"
    def copy_item(self, client_id, item_name, dest):
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "%s doesn't exist" % item_name
        elif item_type == 1:
            return "%s is a directory" % item_name
        elif item_type == 0:
            client = self.get_active_client(client_id)
            lock_res = self.lock_item(client, item_name)
            # Exit if file is locked
            if lock_res == 1:
                return "file locked"
            file_path = self.resolve_path(client_id, item_name)
            #connection.sendall(file_path)
            file_path1=self.resolve_path(client_id, dest)
            shutil.copy(file_path,file_path1)
            self.release_item(client, item_name)
            return "success"
    # Deletes a file
    # Return 0 : Delete successfull
    # Return 1 : Delete unsuccessfull, File locked
    # Return 2 : Delete unsuccessfull, File is a Directory
    # Return 3 : Delete unsuccessfull, File Doesn't exist
    def delete_file(self, client_id, item_name):
        item_type = self.item_exists(client_id, item_name)
        # exit if the item does not exist
        if item_type == -1:
            return 3
        # exit if the item is a directory
        if item_type == 1:
            return 2
        # lock_item
        client = self.get_active_client(client_id)
        lock_res = self.lock_item(client, item_name)
        # Exit if file is locked
        if lock_res == 1:
            return 1
        # delete file
        file_path = self.resolve_path(client_id, item_name)
        os.remove(file_path)
        # add delete event
        self.add_event("delete " + file_path)
        # release it
        self.release_item(client, item_name)
        return 0

    # Makes new directory in current directory
    # return 0 : successfull
    # return 1 : file of same name exists
    # return 2 : directory of same name exists
    def make_directory(self, client_id, directory_name):
        path = self.resolve_path(client_id, directory_name)
        exists = self.item_exists(client_id, directory_name)
        # is file
        if exists == 0:
            return 1
        # is dir
        elif exists == 1:
            return 2
        # doesn't exist
        elif -1:
            os.makedirs(path)
            self.add_event("mkdir " + path)
            return 0

    # remove directory
    # return -1 : directory doesn't exist
    # return 0 : successfull
    # return 1 : is a file
    # return 2 : directory has locked contents
    def remove_directory(self, client_id, directory_name):
        path = self.resolve_path(client_id, directory_name)
        item_type = self.item_exists(client_id, directory_name)
        if item_type == -1:
            return -1
        elif item_type == 0:
            return 1
        elif item_type == 1:
            directory_has_locked_elements = False
            for lock_record in self.locked_files:
                if lock_record[2][0:len(path)] == path:
                    directory_has_locked_elements = True
            if directory_has_locked_elements:
                return 2
            else:
                shutil.rmtree(path)
                self.add_event("rmdir " + path)
                return 0

    #
    # Testing functions
    #
    def log_member_data(self):
        print("")
        print("active_clients: "+ (self.active_clients).__repr__())
        print("events: "+ (self.events).__repr__())
        print("locked_files: "+ (self.locked_files).__repr__())
        print("next_client_id: %d" % self.next_client_id)
        print("next_event_id: %d" % self.next_event_id)
        print("")
