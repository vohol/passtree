#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random, qrcode, sqlite3, sys
import requests, hashlib, getpass, os
from tkinter import *
from cryptography.fernet import Fernet
from datetime import datetime
from colorama import Fore, Style, init
init(autoreset=True)


class Manager():
    def __init__(self):
        #init hide folder for files
        user = getpass.getuser()
        self.path = '/home/' + user + '/'
        try:
            os.mkdir(self.path + '.passtree')
        except FileExistsError:
            pass
        self.cipher_key = ''
        self.init_superuser()
        self.init_key()
        # creating bd if not exist
        # with 2 types; 0 - folder, 1 - passwords
        self.db = sqlite3.connect(self.path + '.passtree/data.db')
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS main_data (
        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parentId INTEGER,
        type INTEGER,
        password TEXT,
        source TEXT
        )""")

    #init superuser with master password for showing passwords
    def init_superuser(self):
        try:
            # open file with key
            file = open(self.path + '.passtree/superuser.txt', 'r')
            file.close()
            return True
        # if we havenot file, we create new and save in file
        except FileNotFoundError:
            self._create_master_pass()

    #child funcrion for init and change_master_pass
    def _create_master_pass(self):
        master_pass = getpass.getpass ("Init new master password: ")
        second_master_pass = getpass.getpass ("Enter new master password again: ")
        if master_pass == second_master_pass:
            hashedPass=hashlib.sha1(master_pass.encode('utf-8')).hexdigest()

            file = open(self.path + '.passtree/superuser.txt', 'w')
            file.write(hashedPass)
            file.close()
            print ('Master Password successfully saved. Do not forget it.')
        else:
            print("Passwords do not match")

    #check master password. child func for decryption and change_master_pass
    def check_superuser(self):
        master_pass = getpass.getpass ("Enter master password: ")
        hashedPass=hashlib.sha1(master_pass.encode('utf-8')).hexdigest()
        if self.init_superuser()==True:
            file = open(self.path + '.passtree/superuser.txt', 'r')
            key_from_file = file.read()
            file.close()
            if hashedPass != key_from_file:
                raise Exception ('Master password is wrong!')
            #return True for decryption function
            else:
                return True

    #function for changing master_pass
    def change_master_pass(self):
        if self.check_superuser():
            self._create_master_pass()

    #init key for decryption&encryption functions
    def init_key(self):
        try:
            # open file with key
            file = open(self.path + '.passtree/key.txt', 'r')

            key_from_file = file.read()
            self.cipher_key = str.encode(key_from_file, encoding='utf-8')
            file.close()
        # if we havenot file, we create new and save in file
        except FileNotFoundError:
            self.cipher_key = Fernet.generate_key()
            file = open(self.path + '.passtree/key.txt', 'w')
            file.write(bytes.decode(self.cipher_key, encoding='utf-8'))
            file.close()

    #create machine strong password
    def gen_new_strong_password(self, quantity):
        symbols ='ABCDEFGHIJKLMNOPQRSTUVWXYZ0abcdefghijklmnopqrstuvwxyz123456789!@#$%^&*<>?,./;:[{}]'
        self.new_password=[]
        [self.new_password.append(random.choice(symbols)) for i in range(quantity)]
        self.new_password = ''.join(str(x) for x in self.new_password)
        return self.new_password

    #function for encrypting
    def encryption(self, password):
        cipher = Fernet(self.cipher_key)
        encrypted_password = cipher.encrypt(str.encode(password, encoding='utf-8'))
        return encrypted_password

    #function for decrypting
    def decryption(self, encrypted_password, imp = False):
        #child function for dry
        def child_decrypt(encrypted_password):
            cipher = Fernet(self.cipher_key)
            decrypted_password =bytes.decode(cipher.decrypt(encrypted_password), encoding='utf-8')
            return decrypted_password
        #for decription just 1 password
        if imp == False:
            if self.check_superuser():
                return child_decrypt(encrypted_password)
        #for import function when we need import many passwords
        else:
            return child_decrypt(encrypted_password)

    #checking on have i been pwned, return True if pwned
    def chech_pwned(self, password):
        hashedPass=hashlib.sha1(password.encode('utf-8')).hexdigest()
        api_request = requests.get(f'https://api.pwnedpasswords.com/range/{hashedPass[:5]}').text.split('\r\n')
        tumbler_value = False

        for i in api_request:
            i = i.split(':')
            #if pwned
            if i[0].lower() == hashedPass[5:]:
                result = i[1]
                print(f'''{Fore.RED}This password has been seen {Style.BRIGHT}{result}{Style.NORMAL} time on cracking password database.

This password has previously appeared in a data breach and should never be used.
If you've ever used it anywhere before, change it!''')
                tumbler_value = True
                return True
        #if not pwned
        if tumbler_value == False:
            print (f'''{Fore.GREEN}This password wasn't found in any of the Passwords previously exposed in data breaches.
That doesn't necessarily mean it's a good password, merely that it's not indexed on cracking password database.''')
            return False

    #functing for show password in qr by tkinter
    def show_qr(self, value_for_qr):
        img = qrcode.make(value_for_qr)
        img.save(self.path + '.passtree/qr.png')
        root = Tk()
        root.title('Temp QR_Password')
        image = PhotoImage(file = self.path + '.passtree/qr.png')
        label = Label(root, image = image)
        label.pack()
        root.mainloop()
        os.remove(self.path + '.passtree/qr.png')

    #function for creating password or chech extisting
    def create_password(self, login, password, folder = None, source=None, check = False):
        #encription
        password=self.encryption(password)
        #creating password in root directory
        if folder != None:
            if folder[-1] == '/':
                folder = folder[:-1]
            folder = folder.split('/')
            #if just 1 folder
            if len(folder) == 1:
                folder=folder[0]
                self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder}'")
                folder_id = self.cur.fetchone()
                if folder_id == None:
                    self.create_folder(folder, from_create_password = True)
                    self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder}'")
                    folder_id = self.cur.fetchone()
            #if more than one folder
            else:
                self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[len(folder)-1]}'")

                folder_id = self.cur.fetchone()

                if folder_id == None:
                    new_folder = '/'.join(folder[:len(folder)])
                    self.create_folder(new_folder, from_create_password = True)
                    self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[len(folder)-1]}'")
                    folder_id = self.cur.fetchone()
        #for creating password in root
        else:
            folder_id=None

        folder_id = folder_id[0] if folder_id != None else None
        self.cur.execute(f"SELECT name FROM main_data WHERE name = '{login}' AND source= '{source}' AND source IS NOT Null")
        if self.cur.fetchone() is not None:
            for value in self.cur.execute(f"SELECT name, source FROM main_data WHERE name = '{login}' and source= '{source}'"):
                print(f'The password {Style.BRIGHT}{Fore.WHITE}{value[1]}{Style.RESET_ALL}:{Style.BRIGHT}{Fore.CYAN}{value[0]}{Style.RESET_ALL} already exists!')
                if check == True:
                    return True
        else:
            if check == True:
                return False
            self.cur.execute(f"INSERT INTO main_data VALUES(Null, ?, ?, ?, ?, ?)", (login, folder_id, 1, password, source))
            self.db.commit()
            print(f'Password {Style.BRIGHT}{Fore.WHITE}{source}{Style.RESET_ALL}:{Style.BRIGHT}{Fore.CYAN}{login}{Style.RESET_ALL} saved!')
            

    def create_folder(self, folder, from_create_password = False):
        if folder[-1] == '/':
            folder = folder[:-1]
        folder = folder.split('/')

        if len(folder) == 1:
            name = folder[0]
            folder_id = None

        # elif len(folder) == 2:
        #     name = folder[1]
        #     self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[0]}'")
        #     folder_id = self.cur.fetchone()
        #     if folder_id == None:
        #         self.create_folder(folder[0])
        #         self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[0]}'")
        #         folder_id = self.cur.fetchone()

        elif len(folder) > 1:
            name = folder[len(folder)-1]
            self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[len(folder)-2]}'")
            folder_id = self.cur.fetchone()

            if folder_id == None:
                new_folder = '/'.join(folder[:len(folder)-1])
                self.create_folder(new_folder)
                self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{folder[len(folder)-2]}'")
                folder_id = self.cur.fetchone()

        folder_id = folder_id[0] if folder_id != None else None
        if folder_id != None:
            self.cur.execute(f"SELECT name FROM main_data WHERE name ='{name}' AND parentId is '{folder_id}'")
        else:
            self.cur.execute(f"SELECT name FROM main_data WHERE name ='{name}' AND parentId is Null")

        if self.cur.fetchone() is None:
            self.cur.execute(f"INSERT INTO main_data VALUES(Null, ?, ?, ?, Null, Null)", (name, folder_id, 0))
            self.db.commit()
            if from_create_password == False:
                print(f'Folder {Fore.WHITE}{Style.BRIGHT}{name}{Style.RESET_ALL} created!')
        else:
            if from_create_password == False:
                for value in self.cur.execute(f"SELECT * FROM main_data WHERE name ='{name}'"):
                    print(f'Folder {Fore.WHITE}{Style.BRIGHT}{value[1]}{Style.RESET_ALL} already exists!')

    #function for delete password or directory
    def delete_object(self, name, source=None, id_for_child=None):
        #delete child directory
        if id_for_child !=None and source==None:
            self.cur.execute(f"SELECT type, source FROM main_data WHERE folder_id = '{id_for_child}' ")
            result = self.cur.fetchone()
            type_of_child,source =result[0],result[1]

            if int(type_of_child) == 1:
                print(f"Account  {Style.BRIGHT}{Fore.WHITE}{source}{Style.RESET_ALL}:{Style.BRIGHT}{Fore.CYAN}{name}{Style.RESET_ALL} deleted!")
            else:
                print(f"Folder {Fore.WHITE}{Style.BRIGHT}{name}{Style.RESET_ALL} deleted!")
            self.cur.execute(f"DELETE FROM main_data WHERE folder_id = '{id_for_child}'")
            self.db.commit()

            #delete child fo child dirs
            self.cur.execute(f"SELECT folder_id,name FROM main_data WHERE parentId = '{id_for_child}' ")
            child_items_for_dels = self.cur.fetchall()
            if child_items_for_dels != []:
                for child in child_items_for_dels:
                    self.delete_object(name = child[1], id_for_child=int(child[0]))
            else:
                pass

        elif source == None and id_for_child ==None:
            name = name.split('/')
            #delete directory with 1 folder
            if len(name)>1:
                parent = name[len(name)-2]
                self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{parent}' AND type == 0")
                id = self.cur.fetchone()[0]
                name = name[len(name)-1]

                self.cur.execute(f"SELECT folder_id,name FROM main_data WHERE name = '{name}' AND type == 0 AND parentId='{id}'")
                items_for_dels = self.cur.fetchall()

                self.cur.execute(f"SELECT folder_id,name FROM main_data WHERE parentId = '{items_for_dels[0][0]}' ")
                child_items_for_dels = self.cur.fetchall()
                if child_items_for_dels != []:
                    for child in child_items_for_dels:
                        self.delete_object(name = child[1], id_for_child=int(child[0]))
                else:
                    pass

                for i in items_for_dels:
                    self.cur.execute(f"DELETE FROM main_data WHERE folder_id = '{i[0]}'")
                    self.db.commit()
                    print(f"Folder {Fore.WHITE}{Style.BRIGHT}{i[1]}{Style.RESET_ALL} deleted!")

            else:
                name = name[0]
                self.cur.execute(f"SELECT folder_id,name FROM main_data WHERE name = '{name}' AND type == 0")
                items_for_dels = self.cur.fetchall()

                if len(items_for_dels) > 1:
                    raise Exception (f'There are at least two folders named {Fore.WHITE}{Style.BRIGHT}"{name}"{Style.RESET_ALL}! Enter the name of the folder with the parent. For example: parent/folder_for_delete')
                elif items_for_dels == []:
                    raise Exception ('No folder with this name!')
                else:
                    self.cur.execute(f"SELECT folder_id,name FROM main_data WHERE parentId = '{items_for_dels[0][0]}' ")
                    child_items_for_dels = self.cur.fetchall()
                    if child_items_for_dels != []:
                        for child in child_items_for_dels:
                            self.delete_object(name = child[1],id_for_child=int(child[0]))
                    else:
                        pass

                for i in items_for_dels:
                    self.cur.execute(f"DELETE FROM main_data WHERE name = '{i[1]}'")
                    self.db.commit()
                    print(f"Folder {Fore.WHITE}{Style.BRIGHT}{i[1]}{Style.RESET_ALL} deleted!")


        elif source != None:
            self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{name}' AND source == '{source}'")
            id = self.cur.fetchall()
            if id ==[]:
                print("This account does not exist.!")
            else:
                self.cur.execute(f"DELETE FROM main_data WHERE folder_id = '{id[0][0]}'")
                self.db.commit()
                print(f"Account {Style.BRIGHT}{Fore.WHITE}{source}{Style.RESET_ALL}:{Style.BRIGHT}{Fore.CYAN}{name}{Style.RESET_ALL} deleted!")

    #funcrion for selecting pass and show his in client
    def select_pass (self,name, source=None):
        self.cur.execute(f"SELECT password FROM main_data WHERE name = '{name}' AND source == '{source}'")
        password = self.cur.fetchall()
        if password ==[]:
            raise Exception ("This account does not exist!")
        #return password for cli
        else:
            return password[0][0]

    #function fith 3 child functions for show tree of directories
    def show_tree(self, directory=None):
        self.dirCount=0
        self.passwordCount=0
        print_dir='root' if directory==None else directory
        print(Fore.BLUE + Style.BRIGHT+print_dir)
        self.walk(directory)
        self.summary()

    #main child function for show_tree witch walk from folder to folder
    def walk(self, directory=None, prefix = ""):
        if directory != None:
            self.cur.execute(f"SELECT folder_id FROM main_data WHERE name = '{directory}' ORDER BY type")
            id = self.cur.fetchone()[0]

            self.cur.execute(f"""SELECT folder_id, name, parentId, type, source
                    FROM main_data WHERE parentId is {id}
                    ORDER BY type""")

        else:
            self.cur.execute(f"""SELECT folder_id, name, parentId, type, source
                    FROM main_data WHERE parentId is Null""")
        filepath =self.cur.fetchall()
        for index in range(len(filepath)):
            self.counter_dir(filepath[index])
            if filepath[index][3] == 1:
                colorama_style=Fore.WHITE + Style.BRIGHT
                if filepath[index][4] is None:
                    source_print= Fore.CYAN + ''
                else:
                    source_print= filepath[index][4] + ': ' + Fore.CYAN
            else:
                colorama_style=source_print=''

            if index == len(filepath) - 1:
                print(prefix + "└── " + colorama_style + source_print+filepath[index][1])
                if filepath[index][3] == 0:
                    self.walk(filepath[index][1], prefix + "    ")
            else:
                print(prefix + "├── " + colorama_style + source_print+filepath[index][1])
                if filepath[index][3] == 0:
                    self.walk(filepath[index][1], prefix + "│   ")

    #child function for show_tree witch print directories and passwords
    def summary(self):
        print_dir = ' directory, ' if self.dirCount == 1 else ' directories, '
        print_password = ' password.' if self.passwordCount == 1 else ' passwords.'
        print ('\n' + str(self.dirCount) + print_dir + str(self.passwordCount) + print_password)

    #child function for show_tree witch count directories and passwords
    def counter_dir(self, obj):
        if obj[3]==0:
            self.dirCount += 1
        else:
            self.passwordCount +=1

    #function for export passes in txt file
    def export_passwords(self, path=None):
        if path == None:
            path = self.path
        else:
            path = self.path + path
            if path[-1] != '/':
                path += '/'

        if self.check_superuser():
            self.cur.execute(f"SELECT name, source, password FROM main_data WHERE type = 1 ")
            passwords = self.cur.fetchall()
            filename = ('passwords'+ str(datetime.today().strftime("%Y-%m-%d-%H.%M.%S")) + '.txt')
            try:
                export_file = open(path + filename, 'w')
            except FileNotFoundError:
                os.makedirs(path)
            export_file = open(path + filename, 'w')

            for i in passwords:
                new = self.decryption(i[2],imp=True)
                print(f'login: {i[0]}   source: {i[1]}  password:{new}', file=export_file)
            export_file.close()
            print(f"Your passwords have been exported successfully in {Fore.WHITE}{Style.BRIGHT}'{path}'{Style.RESET_ALL}")
