from clsBaseClass import *
from clsDNSRecord import *

class clsInstance(clsBaseClass):
    __ObjCustomer = None
    __AwsInstance = None
    __ObjDns = None

    id = ""
    Type = ""
    Zone = ""
    Vpc_id = ""
    Subnet_id = ""
    Ami = ""
    Private_ip = ""
    Public_ip = ""
    Private_dns = ""
    Public_dns = ""
    Infom_dns = ""
    Poc = ""
    Environment = ""
    Key = ""
    Status = ""
    Public_ip = ""

    VolumesList = []
    SecGroups = []

    def __init__(self,kInstanceId,kObjCustomer,kAwsInstance):
        self.id = kInstanceId
        self.__ObjCustomer = kObjCustomer
        self.__AwsInstance = kAwsInstance

        self.loadData()

    def loadData(self):

        values = {
            "type": "",
            "zone": "",
            "vpc_id": "",
            "subnet_id": "",
            "ami": "",
            "private_ip": "",
            "public_ip": "",
            "private_dns": "",
            "public_dns": "",
            "infom_dns": "",
            "poc": "",
            "environment": "",
            "key": "",
            "status": "",
            "last_update": "",
        }

        try:
            self.printMsg ("","Pulling instance info for " + self.id + " ...")

            self.Zone = self.__AwsInstance.placement
            self.Vpc_id = self.__AwsInstance.vpc_id
            self.Subnet_id = self.__AwsInstance.subnet_id
            self.Ami = self.__AwsInstance.image_id
            self.Private_ip = self.__AwsInstance.private_ip_address
            self.Public_ip = self.__AwsInstance.ip_address
            self.Private_dns = self.__AwsInstance.private_dns_name
            self.Public_dns = self.__AwsInstance.public_dns_name
            self.Status = self.__AwsInstance.state

        except Exception, e:
            self.printMsg ("loadData",e.args[0],True,True)

    def refreshAWS(self):
        try:
            self.printMsg ("","[AWS] Refresh instance " + self.id + " info ...")
            self.Type = self.__AwsInstance.instance_type
            self.Zone = self.__AwsInstance.placement
            self.Vpc_id = self.__AwsInstance.vpc_id
            self.Subnet_id = self.__AwsInstance.subnet_id
            self.Ami = self.__AwsInstance.image_id
            self.Private_ip = self.__AwsInstance.private_ip_address
            self.Public_ip = self.__AwsInstance.ip_address
            self.Private_dns = self.__AwsInstance.private_dns_name
            self.Public_dns = self.__AwsInstance.public_dns_name
            self.Status = self.__AwsInstance.state

        except Exception, e:
            self.printMsg ("refreshAWS",e.args[0],True,True)


    def setDns(self,kHostName):
        if self.__ObjDns == None:
            self.ObjDns = clsDNSRecord(self.__ObjCustomer,self.id)

        self.printMsg ("","[AWS] Updating DNS " + kHostName + " => " + self.Private_ip)
        if not self.ObjDns.checkExistance("A",kHostName):
            self.Infom_dns = kHostName
            self.ObjDns.setRecord("A",kHostName,self.Private_ip)
            self.printMsg ("","---> OK")

        else:
            self.printMsg ("","###> A DNS record for " + kHostName + " already exist.")

    def checkAmiAvailility(self,kAwsConn):
        return len(kAwsConn.get_all_images(image_ids=[self.Ami])) == 1
