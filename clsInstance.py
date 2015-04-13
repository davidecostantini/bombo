from clsBaseClass import *
from clsRedis import *
from clsDNSRecord import *

class clsInstance(clsBaseClass):
    __ObjCustomer = None
    __AwsInstance = None
    __redisdb = None
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

        if BOMBO_REDIS_HOST:
            self.__redisdb = clsRedis("customer:" + str(kObjCustomer.id) + ":instance:" + self.id)

        self.loadData()

    def loadData(self):
        if not BOMBO_REDIS_HOST:
            return None

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
            self.printMsg ("","[Redis] Pulling for " + self.id + " ...")

            for item in self.__redisdb.getBunchValues("hashes","",values):
                if item[0] == "type":
                    self.Type = item[1]
                elif item[0] == "zone":
                    self.Zone = self.__AwsInstance.placement
                elif item[0] == "vpc_id":
                    self.Vpc_id = self.__AwsInstance.vpc_id
                elif item[0] == "subnet_id":
                    self.Subnet_id = self.__AwsInstance.subnet_id
                elif item[0] == "ami":
                    self.Ami = self.__AwsInstance.image_id
                elif item[0] == "private_ip":
                    self.Private_ip = self.__AwsInstance.private_ip_address
                elif item[0] == "public_ip":
                    self.Public_ip = self.__AwsInstance.ip_address
                elif item[0] == "private_dns":
                    self.Private_dns = self.__AwsInstance.private_dns_name
                elif item[0] == "public_dns":
                    self.Public_dns = self.__AwsInstance.public_dns_name
                elif item[0] == "status":
                    self.Status = self.__AwsInstance.state 

                self.Infom_dns = self.__redisdb.get("hget","","infom_dns")

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

    def updateRedis(self):
        values = {
            "type": self.Type,
            "zone": self.Zone,
            "vpc_id": self.Vpc_id,
            "subnet_id": self.Subnet_id,
            "ami": self.Ami,
            "private_ip": self.Private_ip,
            "public_ip": self.Public_ip,
            "private_dns": self.Private_dns,
            "public_dns": self.Public_dns,
            "infom_dns": self.Infom_dns,
            "poc": self.Poc,
            "environment": self.Environment,
            "key": self.Key,
            "status": self.Status,
            "last_update": self.getDate()
        }    

        try:
            self.printMsg ("","[Redis] Updating " + self.id + " ...")
            self.__redisdb.setBunchValues("hashes","",values)
            self.printMsg ("","---> OK")

        except Exception, e:
            self.printMsg ("updateRedis",e.args[0],True,True)


    def setDns(self,kHostName):
        if self.__ObjDns == None:
            self.ObjDns = clsDNSRecord(self.__ObjCustomer,self.id)

        self.printMsg ("","[AWS] Updating DNS " + kHostName + " => " + self.Private_ip)
        if not self.ObjDns.checkExistance("A",kHostName):
            self.Infom_dns = kHostName
            self.ObjDns.setRecord("A",kHostName,self.Private_ip)
            self.printMsg ("","---> OK")

            if BOMBO_REDIS_HOST:
                self.updateRedis()
        else:
            self.printMsg ("","###> A DNS record for " + kHostName + " already exist.")

    def checkAmiAvailility(self,kAwsConn):
        return len(kAwsConn.get_all_images(image_ids=[self.Ami])) == 1
