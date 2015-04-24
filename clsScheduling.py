from clsBaseClass import *
from clsInstanceSched import *
import sys

class clsScheduling(clsBaseClass):

    def __getSched(self, kInstanceId,kList):
        for sched in kList:
            if sched.instance.id == kInstanceId:
                return sched
        return clsInstanceSched
           

    def __getInstanceState(self,kInstanceId,kFullInstancesList):
        for sched in kFullInstancesList:
            if sched.instance.id == kInstanceId:
                return sched.instance.state

    def __getDeps(self,kInstance):
        Deps=None
        if kInstance.instance != None:
            Deps=kInstance.instance.tags.get('bombo_autosched:DEPS')
        return Deps   

    def __checkInfiniteLoop(self, kInstanceId,kList):
        ObjTmp=self.__getSched(kInstanceId,kList)
        if ObjTmp.instance != None:
            return "Infinite Loop -> Element " + kInstanceId + " is already added"

    def __MergeList(self, kMainList,kTmpList):
        Tmp=[]
        for i in reversed(kTmpList):
            if self.__getSched(i.instance.id,kMainList).instance == None:
                Tmp.append(i)
            else:
                #if here the instance is already added to list
                #but is required by other instances ergo is a deps
                i.isADeps=True
        return kMainList+Tmp

    def checkSchedInstanceState(self,kInstance):
        import time, sys
        counter = 0
        spinner = self.spinning_cursor()
        instancesReady = []
        tmpCheck="pending"
        while tmpCheck == "pending" or tmpCheck == "stopping":
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            sys.stdout.write('\b')
            time.sleep(2)
            tmpCheck=kInstance.update()

        self.printMsg ("","---> Instance " + str(kInstance.id) + " is now in " + kInstance.state + " state")

    def getScheduledListStop(self,kInstancesStopList,kFullInstancesList):
        Tmp=[]
        for i in reversed(self.getScheduledListStartup(kInstancesStopList,kFullInstancesList)):
            Tmp.append(i)
        return Tmp

    def getScheduledListStartup(self,kInstancesSchedList,kFullInstancesSchedList):
        _Level=0
        checkLoop=False
        Deps = ""
        MainList = []
        TmpList = []

        for sched in kInstancesSchedList:
            Done=False

            tmpSched = sched
            TmpList.append(tmpSched)

            _Level=0
            while Done == False:
                Deps = self.__getDeps(tmpSched)
                #Deps = sched.deps
                #print "deps:"+sched.deps
                tmpSched=self.__getSched(Deps,kFullInstancesSchedList)

                if tmpSched.schedEnabled:
                    checkLoop = self.__checkInfiniteLoop(Deps,TmpList)
                    if checkLoop:
                        print "Infinite loop error!"
                        sys.exit(1)

                if Deps != None:
                    _Level+=1

                    if tmpSched.instance != None:
                        if tmpSched.schedEnabled:
                            if _Level>0:
                                tmpSched.isADeps=True
                            TmpList.append(tmpSched)
                        else:
                            #I have a deps that has not the automated scheduled so I have to check if it is running
                            tmpInstanceStateCheck=self.__getInstanceState(tmpSched.instance.id,kFullInstancesSchedList)
                            if tmpInstanceStateCheck != "running":
                                self.printMsg ("","###> A depencendy instance that was not scheduled for startup is in " + tmpInstanceStateCheck + " state!",True,True)
                else:
                    Done = True

            MainList = self.__MergeList(MainList,TmpList)
            TmpList=[]

        return MainList
