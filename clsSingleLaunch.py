from clsTemplate import *

class clsSingleLaunch():
    __ObjConfig = None

    Template = None

    Subnet = ""
    Key = ""
    Qty = 0
    BootScript = ""    
    Hostname = ""
    Env = ""
    Desc = ""

    SecGroups = []

    def __init__(self, kSingleLaunch):
        self.__ObjConfig = kSingleLaunch
        self.__loadData()
        self.__getObjTemplate(kSingleLaunch["template"])

    def __loadData(self):
        self.Subnet = self.__ObjConfig["subnet"]
        self.Key = self.__ObjConfig["key"]

        self.Qty = self.__ObjConfig["qty"]
        self.BootScript = self.__ObjConfig["boot_script"]
        self.Hostname = self.__ObjConfig["hostname"]
        self.Env = self.__ObjConfig["environment"]
        self.Desc = self.__ObjConfig["desc"]
        self.SecGroups = self.__ObjConfig['sec_groups']["list"]

    def __getObjTemplate(self,kTemplate):
        self.Template = clsTemplate(kTemplate)   