from clsBaseClass import *
from clsRedis import *
from clsInstance import *

class clsCustomer(clsBaseClass):
    import boto.ec2

    __awsConnection = None
    __redisdb = None
    __ObjConfig = None
    __Instances = ""

    id = 0
    Name = ""
    Access_key = ""
    Secret_key = ""
    Puppet_repo=""
    Puppet_known_hosts = ""
    Puppet_ssh_private = ""
    Puppet_ssh_pub = ""
    Dns_domain = ""
    Region = ""
    BckVolumesRetention = 1

    Instances = 0 #Instance number

    def __init__(self, kCustomerId,kCustomersJsonConfig = ""):
        self.id = kCustomerId

        if BOMBO_REDIS_HOST:
            self.__redisdb = clsRedis("customer:" + str(kCustomerId))

        if kCustomersJsonConfig != "":
            self.__ObjConfig = kCustomersJsonConfig
        else:
            self.__ObjConfig = BOMBO_CUSTOMERS_CONFIG

        self.loaData()

    def doAwsConnection(self):
        if not self.__awsConnection == None:
            return self.__awsConnection

        try:
            self.printMsg ("","[AWS] Connecting to region " + self.Region + "...")

            self.__awsConnection = self.boto.ec2.connect_to_region(
                self.Region,
                aws_access_key_id=self.Access_key,
                aws_secret_access_key=self.Secret_key)
            self.printMsg ("","---> OK")

        except Exception, e:
            self.printMsg ("loadAws",e.args[0],True,True)


    def updateRedis(self):
        values = {
            "name": self.Name,
            "dns_domain": self.Dns_domain,
            "region": self.Region,
            "puppet_repo": self.Puppet_repo
        }

        try:
            self.printMsg ("","[Redis] Updating " + self.Name + " ...")
            self.__redisdb.set("hset","",len(self.getInstances()),"instances")
            self.__redisdb.setBunchValues("hashes","",values)
            self.printMsg ("","---> OK")

        except Exception, e:
            self.printMsg ("updateRedis",e.args[0],True,True)


    def loaData(self):
        self.printMsg ("","[BOMBO] Loading customer...")

        jsonCustomersList = self.loadJsonFile(self.__ObjConfig)

        try:
            self.Name = jsonCustomersList[str(self.id)]["name"]
            self.Dns_domain = jsonCustomersList[str(self.id)]["settings"]["dns_domain"]
            self.Region = jsonCustomersList[str(self.id)]["settings"]["region"]
            self.Puppet_repo = jsonCustomersList[str(self.id)]["settings"]["puppet_repo"]
            self.Access_key = jsonCustomersList[str(self.id)]["settings"]["access_key"]
            self.Secret_key = jsonCustomersList[str(self.id)]["settings"]["secret_key"]
            self.BckVolumesRetention = jsonCustomersList[str(self.id)]["settings"]["bck_volumes_retention"]

            #Get from Redis
            if BOMBO_REDIS_HOST:
                self.instances = self.__redisdb.get("hget","","instances")

            #Sensitive info
            self.Puppet_known_hosts = jsonCustomersList[str(self.id)]["settings"]["puppet_known_hosts"]
            self.Puppet_ssh_private = jsonCustomersList[str(self.id)]["settings"]["puppet_ssh_private"]
            self.Puppet_ssh_pub = jsonCustomersList[str(self.id)]["settings"]["puppet_ssh_pub"]

            self.printMsg ("","---> " + self.Name)
            return True

        except Exception, e:
            self.printMsg ("loadData",e.args[0],True,True)
        

    def getInstances(self):
        if self.__Instances == "":
            self.__Instances = self.getAllInstances()
        return self.__Instances

    def getAwsInstance(self,kInstanceId):
        if kInstanceId == "":
            self.printMsg ("","Ooh no, you must specify the Instance ID!",True,True)

        return self.getAllAwsInstances(kInstanceId)        


    def getAllAwsInstances(self,kInstanceId=""):
        import boto

        self.doAwsConnection()

        self.printMsg ("","[BOMBO] Getting instance details...")  
        if kInstanceId != "":
            reservations = self.__awsConnection.get_all_instances(instance_ids=[kInstanceId])
            if not reservations[0].instances:
                self.printMsg ("","Ooh no, i can't find the instance -> " + kInstanceId + "!",True,True)             
            result = reservations[0].instances[0]
            self.printMsg ("","---> " + result.id) 
        else:
            reservations = self.__awsConnection.get_all_instances()           
            result = reservations[0].instances
            self.printMsg ("","---> Found " + str(len(result)) + " instances") 
        
        return result


    def getInstance(self,kInstanceId):
        if kInstanceId == "":
            self.printMsg ("","Ooh no, you must specify the Instance ID!",True,True)

        return self.getAllInstances(kInstanceId)[0]

    def getAllInstances(self,kInstanceId=""):
        import boto

        self.doAwsConnection()
        
        InstancesCollection = []

        self.printMsg ("","[BOMBO] Getting instance details...")  
        if kInstanceId != "":
            reservations = self.__awsConnection.get_all_instances(instance_ids=[kInstanceId])
            if not reservations[0].instances:
                self.printMsg ("","Ooh no, i can't find the instance -> " + kInstanceId + "!",True,True)
          
            InstancesCollection.append(
                clsInstance(
                    reservations[0].instances[0].id,
                    self,
                    reservations[0].instances[0]
                    )
                )
            self.printMsg ("","---> " + reservations[0].instances[0].id) 
        else:
            reservations = self.__awsConnection.get_all_instances()

            for inst in reservations:
                InstancesCollection.append(
                    clsInstance(
                        inst.instances[0].id,
                        self,
                        inst.instances[0]
                        )
                    )

            #Update Instances count
            if BOMBO_REDIS_HOST:
                self.__redisdb.set("hset","",len(reservations),"instances")

            self.printMsg ("","---> Found " + str(len(InstancesCollection)) + " instances") 

        return InstancesCollection