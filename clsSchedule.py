from clsBaseClass import *
import sys

class clsSchedule(clsBaseClass):

    def __getInstance(self, kInstanceId,kList):
        for instance in kList:
            if instance.id == kInstanceId:
                return instance

    def __getDeps(self, kLevel,kInstance):
        if kInstance.id != 0:
            #print "="*kLevel + str(kInstance[1])
            return kInstance[1]

    def __getDeps(self, kInstanceId,kList):
        if __getInstance(kInstanceId,kList) != None:
            return "Infinite Loop -> Element " + kInstanceId + " is already added"

    def __MergeList(self, kMainList,kTmpList):
        Tmp=[]
        for i in reversed(kTmpList):
            if __getInstance(i[0],kMainList) == None:
                Tmp.append(i)
        return kMainList+Tmp

    def DoScheduledShutdown(self,kResList):
        Tmp=[]
        for i in reversed(__getInstancesListStartup(self,kResList)):
            Tmp.append(i)
        return Tmp

    def DoScheduledStartup(self,kResList):
        _Level=0
        Deps = ""
        MainList = []
        TmpList = []

        for res in kResList:

            for instance in res.instances

                Done=False

                TmpList.append(instance)

                tmpInstance = instance
                _Level=0
                while Done == False:
                    Deps = __getDeps(_Level +1,tmpInstance)
                    checkLoop = __checkInfiniteLoop(Deps,TmpList)
                    if checkLoop:
                        print "Infinite loop error!"
                        sys.exit()
                    if Deps != None and not checkLoop:
                        _Level+=1
                        tmpInstance=__getInstance(Deps,instances)
                        TmpList.append(tmpInstance)
                    else:
                        Done=True
                
                MainList = __MergeList(MainList,TmpList)
                TmpList=[]

        return MainList