from clsBaseClass import *
from clsRedis import *

class clsDNSRecord(clsBaseClass):
    import boto.route53

    __ObjCustomer = None
    __awsConnection = None
    __redisdb = None
 
    __instanceId = ""

    Type = ""
    Name = ""
    Host = ""

    def __init__(self, kObjCustomer,kInstanceId = ""):
        self.__ObjCustomer = kObjCustomer
        self.__awsConnection = self.boto.route53.connect_to_region(
            'universal',
            aws_access_key_id=self.__ObjCustomer.Access_key,
            aws_secret_access_key=self.__ObjCustomer.Secret_key)

        if kInstanceId != "":
            self.__instanceId = kInstanceId
            self.getRecordByInstanceId(kInstanceId)

    def getAwsRecords(self,kType="", kName=""):
        try:
            zone_id=self.__awsConnection.get_zone(self.__ObjCustomer.Dns_domain+ ".").id
            if kType == "":
                return self.__awsConnection.get_all_rrsets(zone_id)
            else:
                for rrecord in self.__awsConnection.get_all_rrsets(zone_id):
                    if rrecord.type==kType and rrecord.name==kName:
                        return rrecord
                return False

        except Exception, e:
            self.printMsg ("getAwsRecords",str(e.args[0]) + " - " + str(e.args[2]),True,True)

    def checkExistance(self,kType,kName):
        list = self.getAwsRecords()
        for item in list:
            if item.type == kType and item.name.split('.')[0] == kName :
                return True
        return False

    def getRecordByInstanceId(self, kInstanceId):
        if not BOMBO_REDIS_HOST:
            return None

        if self.__redisdb == None:
            self.__redisdb = clsRedis("customer:" + str(self.__ObjCustomer.id) + ":instance:" + kInstanceId)

        return self.__redisdb.get("hget","","infom_dns")

    def getRecordByType(self, kType, kName):
        return self.getAwsRecords(self,kType, kName)

    def setRecord(self, kType, kName, kValue):
        kName = (kName if kName[-1] == "." else kName + "." + self.__ObjCustomer.Dns_domain + ".")
        zone = self.__awsConnection.get_zone(self.__ObjCustomer.Dns_domain)
        if self.checkExistance(kType,kName):
            if kType == "A":
                status = zone.update_a(kName, kValue,ttl=1800);

            if kType == "CNAME":
                status = zone.update_cname(kName, kValue,ttl=1800);

        else:
            status = zone.add_record(kType, kName, kValue,ttl=1800);

    def updateRedis(self, kType, kName, kValue):
        self.__redisdb = clsRedis("dns:" + self.__instanceId)
        self.__redisdb.set("hset","",kType,"type")
        self.__redisdb.set("hset","",kName,"name")
        self.__redisdb.set("hset","",kValue,"value")