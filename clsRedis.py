from bombo import *

class clsRedis:
    import redis

    __redisConn = None
    __redis_prefix = ""

    def __init__(self,kPrefix):
        self.__redis_prefix = kPrefix
        self.__redisConn = self.redis.StrictRedis(host=BOMBO_REDIS_HOST, port=BOMBO_REDIS_PORT, db=BOMBO_REDIS_DB)

    #SET
    def set(self,kType,kKey,kValue,kField=""):
        if kType == "hset":
            return self.__hSet(kKey,kField,kValue)

        if kType == "set": 
            return self.__set(kKey,kValue)

    def __set(self,kKey,kValue):
        return self.__redisConn.set(self.__redis_prefix + kKey,kValue)

    def __hSet(self,kKey,kField,kValue):
        return self.__redisConn.hset(self.__redis_prefix + kKey,kField,kValue)

    #GET
    def get(self,kType,kKey,kField=""):
        if kType == "hget": 
            return self.__hGet(kKey,kField)

        if kType == "get":
            return self.__get(kKey)

    def __hGet(self,kKey,kField):  
        return self.__redisConn.hget(self.__redis_prefix + kKey,kField)        
    
    def __get(self,kKey):
        return self.__redisConn.get(self.__redis_prefix + kKey)


    #Bunch values
    def setBunchValues(self,kType,kKey,kDict):
        for k, v in kDict.items():
            if kType == "sets":
                self.set("set",kKey,v)

            if kType == "hashes":
                self.set("hset",kKey,v,k)

    def getBunchValues(self,kType,kKey,kFieldsList):
        result = []
        for field in kFieldsList:
            if kType == "sets":
                result.append(
                    [
                    kKey+":"+kFieldsList,
                    self.get("get",kKey+":"+field)
                    ]
                )

            if kType == "hashes":
                result.append(
                    [
                    field,
                    self.get("hget",kKey,field)
                    ]
                )

        return result