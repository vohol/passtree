#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Password Tree

Simple password manager on the command line. Supports tree structure of
data storage.

Usage:
passtree OPTIONS --dir <name-or-path>
passtree OPTIONS --pass (<login> <source>) [<folder-or-path>] [--gen] [--qr] [--cp]
passtree OPTIONS [<folder>]

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Commands:
  tree          A command to display your passwords in a tree view.

                To separately display the contents of one folder. To do
                this, enter the name of the folder after the command
                Example: passtree tree [<folder>]

  create        command to create a password or folders.

                To create folders, use the '--dir' option after create
                command. Then enter the folder name or path using '/'.
                Example: passtree create --dir <name-or-path>

                To create passwords, use the '--pass' option after create
                command. Then be sure to enter the <login> and <source>
                for the object of your password. You can create only one
                password object for <login> in a specific <source>
                Next, enter the folder or path in which you want to create
                a password. If this argument is not specified, the password
                will be created in the home directory.
                To generate a strong password, use the [--gen] option.
                Example: passtree create --pass (<login> <source>)
                [<folder-or-path>] [--gen]

  rm            command to remove a password or folders.
                To remove folders, use the '--dir' option after remove
                command. Then enter the folder name or path using '/'.
                Example: passtree remove --dir <name-or-path>

                To remove passwords, use the '--pass' option after remove
                command. Then be sure to enter the <login> and <source>
                for the object of your password. Enter the path or folder
                is not necessary, because the combination of login and
                resource is unique. Example:
                passtree remove --pass (<login> <source>)

  show          command for show password.

                To show passwords, use the '--pass' option after show
                command. Then be sure to enter the <login> and <source>
                for the object of your password. Enter the path or folder
                is not necessary, because the combination of login and
                resource is unique. Example:
                passtree show --pass (<login> <source>)

                To copy password to clipboard, add the [--cp] option.
                Example: passtree show --pass (<login> <source>) [--cp]

                To display the password as QR, add the [--qr] option.
                Example: passtree show --pass (<login> <source>) [--qr]

  master        command for changing master password.

  export        command to export all passwords to the default /home
                directory.

                To select another directory, specify it after the export
                option in quotation marks separating folders by '/'.
                Example: passtree export ['another/folder']

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Options:
  -d --dir      option for working with folders and paths.
  -p --pass     option for working with password objects.
  -q --qr       option to view passwords like QR-code.
  -c --cp       option to view passwords in PX.
  -g --gen      option to generate a complex password.
  -h --help     show help.
  -v --version  show version.

"""
from docopt import docopt
from passtree_back import Manager

import pyperclip, getpass


args = docopt(__doc__, version='passtree diplom project')
# print(args)
mn = Manager()

#creating folder
if args['--dir'] and args['OPTIONS']=='create':
    mn.create_folder(args['<name-or-path>'])

# creating password
if args['--pass'] and args['OPTIONS']=='create':
    #check existing this login and this source
    if mn.create_password(args['<login>'], password='dog-nail', source = args['<source>'], folder = args['<folder-or-path>'], check = True) == False:
        #init strong password
        if args['--gen']:
            password = mn.gen_new_strong_password(14)
            mn.create_password(args['<login>'], password, source = args['<source>'], folder = args['<folder-or-path>'])
        #init own password
        else:
            password = getpass.getpass ('Enter password: ')
            second_password = getpass.getpass ('Enter password again: ')
            if password == second_password:

                #choise next way if this password is pwned
                if mn.chech_pwned(password) == True:
                    create_or_not = input ('Generate strong password ?[Yes/No] ')
                    #if yes we create password
                    if create_or_not.lower() == 'y' or create_or_not.lower() == 'yes':
                        password = mn.gen_new_strong_password(14)
                    #if doesnt yes
                    else:
                        pass
                    #creating password anyway
                    mn.create_password(args['<login>'], password, source = args['<source>'], folder = args['<folder-or-path>'])
                #creating password if he is not pwned
                else:
                    mn.create_password(args['<login>'], password, source = args['<source>'], folder = args['<folder-or-path>'])
            #first try and second doesnt match
            else:
                print("Passwords do not match")

#delete pass or directory
if args['--dir'] and args['OPTIONS'] == 'rm':
    mn.delete_object(args['<name-or-path>'])
elif args['--pass'] and args['OPTIONS'] == 'rm':
    mn.delete_object(args['<login>'], args['<source>'])

#show tree structure
if args['OPTIONS']=='tree':
    mn.show_tree(args['<folder>'])

#show passwors
if args['OPTIONS'] == 'show':
    password = mn.select_pass(args['<login>'], args['<source>'])
    decrypted_pass = mn.decryption(password)
    #by qr cody
    if args['--qr']:
        mn.show_qr(decrypted_pass)
    elif args['--cp']:
    #copy password to buffer
        pyperclip.copy(decrypted_pass)
        print ("Password copied to clipboard.")
    #by text
    else:
        print(decrypted_pass)

if args['OPTIONS']=='master':
    mn.change_master_pass()

if args['OPTIONS']=='export':
    mn.export_passwords(path = args['<folder>'])
