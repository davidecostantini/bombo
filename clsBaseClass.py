from config import *
from bgcolors import *

class clsBaseClass():
    ##-----------------------------------##
    ##---------BASIC FUNCTIONS-----------##
    ##-----------------------------------##
    def __checkFileExistence(self,fileToCheck):
        import os
        if (not os.path.isfile(fileToCheck)):
            self.printMsg ("","Oops! Someone removed the config file I need to work...... File missing -> " + fileToCheck,True)
            return False
        return True

    def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def getHostname(self):
        from socket import gethostname
        return gethostname()

    def getDate(self):
        import datetime
        return str(datetime.date.today()) + "_" + str(datetime.datetime.time(datetime.datetime.now()))

    def printUsage(self):
        with open('usage.txt', 'r') as f:
            print f.read()
        f.closed

    def printMsg(self,kMsgCod,kMsgDesc,kQuit=False,kError=False,kWhiteTxt=False):
        import sys
        if kError:
            print bcolors.FAIL + ".----------------.  .----------------.  .----------------.  .----------------.  .----------------. '" + bcolors.ENDC
            print bcolors.FAIL + "| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |" + bcolors.ENDC
            print bcolors.FAIL + "| |  _________   | || |  _______     | || |  _______     | || |     ____     | || |  _______     | |" + bcolors.ENDC
            print bcolors.FAIL + "| | |_   ___  |  | || | |_   __ \    | || | |_   __ \    | || |   .'    `.   | || | |_   __ \    | |" + bcolors.ENDC
            print bcolors.FAIL + "| |   | |_  \_|  | || |   | |__) |   | || |   | |__) |   | || |  /  .--.  \  | || |   | |__) |   | |" + bcolors.ENDC
            print bcolors.FAIL + "| |   |  _|  _   | || |   |  __ /    | || |   |  __ /    | || |  | |    | |  | || |   |  __ /    | |" + bcolors.ENDC
            print bcolors.FAIL + "| |  _| |___/ |  | || |  _| |  \ \_  | || |  _| |  \ \_  | || |  \  `--'  /  | || |  _| |  \ \_  | |" + bcolors.ENDC
            print bcolors.FAIL + "| | |_________|  | || | |____| |___| | || | |____| |___| | || |   `.____.'   | || | |____| |___| | |" + bcolors.ENDC
            print bcolors.FAIL + "| |              | || |              | || |              | || |              | || |              | |" + bcolors.ENDC
            print bcolors.FAIL + "| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |" + bcolors.ENDC
            print bcolors.FAIL + "'----------------'  '----------------'  '----------------'  '----------------'  '----------------'" + bcolors.ENDC
            print bcolors.FAIL + "[" + kMsgCod + "] -> " + kMsgDesc + bcolors.ENDC
            if kQuit:
                sys.exit(1)

        if not kWhiteTxt:
            if kMsgDesc[:4] == "--->":
                print bcolors.OKGREEN + kMsgCod + " " + kMsgDesc + bcolors.ENDC
            elif kMsgDesc[:4] == "###>":
                print bcolors.FAIL + kMsgCod + " " + kMsgDesc + bcolors.ENDC
            else:
                print bcolors.OKCYAN + kMsgCod + " " + kMsgDesc + bcolors.ENDC
        else:
            print kMsgCod + " " + kMsgDesc

    def showInitialMsg(self):
        self.printMsg ("",'------------------------',False,False,True)
        self.printMsg ("","HELLO I'm BOMBO, the best cloud boy in town... I'm not fat it's just EASY TO SEE ME!",False,False,True)
        self.printMsg ("",'------------------------',False,False,True)

    def showVersion(self):        
        from sys import version_info
        import bombo
        import boto.ec2
        self.printMsg ("",'------------------------',False,False,True)
        self.printMsg ("","BOMBO version: " + bombo.BOMBO_VERSION,False,False,True)
        self.printMsg ("","Python version: " + str(version_info[0])+str(".")+str(version_info[1])+str(".")+str(version_info[2]),False,False,True)
        self.printMsg ("","Boto version: " + str(boto.Version),False,False,True)
        self.printMsg ("",'------------------------',False,False,True)

    def loadJsonFile(self,filePath):
        import json
        try:
            if self.__checkFileExistence(filePath):
                data = json.loads(open(filePath).read())
                return data
            self.printMsg ("","You're a bad boy! The JSON launch config is not correct. Go and check...",True,True)

        except ValueError:
            self.printMsg ("","You're a bad boy! The JSON launch config is not correct. Go and check...",True,True)

    #Compile userdata script
    def getBootScript(self,kSingleLaunch,kLaunchConfig):
        from string import Template

        #Check which boot script to use
        bootScriptToUse = kSingleLaunch.BootScript or kSingleLaunch.Template.BootScript

        boot_script = open("boot_scripts/" + bootScriptToUse).read()

        return Template(boot_script).substitute(
            puppet_source=kLaunchConfig.Customer.Puppet_repo,
            instance_hostname=kSingleLaunch.Hostname + ("." + kLaunchConfig.Customer.Dns_domain if kLaunchConfig.Customer.Dns_domain != "" else ""),
            instance_id=kSingleLaunch.Template.InstanceId,
            customer_id=kLaunchConfig.Customer.id,

            pre_cm_script_placeholder=kSingleLaunch.Template.PreCmScript if kSingleLaunch.Template.PreCmScript else "test",
            post_cm_script_placeholder=kSingleLaunch.Template.PostCmScript if kSingleLaunch.Template.PostCmScript else "test",

            pre_cm_script_log="/tmp/pre_cm_script_log.log" if kSingleLaunch.Template.PreCmScript else "/dev/null",
            post_cm_script_log="/tmp/post_cm_script_log.log" if kSingleLaunch.Template.PostCmScript else "/dev/null",

            first_puppet_run_log="/tmp/first_puppet_run.log",
            sshkey_known_hosts=open('keys/'+ kLaunchConfig.Customer.Puppet_known_hosts).read().strip(),
            sshkey_deploy_public=open('keys/'+ kLaunchConfig.Customer.Puppet_ssh_private).read().strip(),
            sshkey_deploy_private=open('keys/'+ kLaunchConfig.Customer.Puppet_ssh_pub).read().strip(),
        )

    #User input, pass and array if you want user be force to choose among those
    def user_input(self,desc,array_list=[]):
        from sys import version_info
        py3 = version_info[0] > 2
        goodanswer=False
        while not goodanswer:
            if py3:
                response = input(desc)
            else:
                response = raw_input(desc)

            #Check value if array with expected answers is provided
            if len(array_list) > 0:
                if response in array_list:
                    goodanswer=True
                else:
                    print(response + " doesn't seem a valid answer.")
            else:
                goodanswer=True
        return response