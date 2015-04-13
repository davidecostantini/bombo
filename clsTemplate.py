from clsBaseClass import *
from clsVolume import *

class clsTemplate(clsBaseClass):
    __ObjConfig = None

    Name = ""
    Ami = ""
    InstanceType = ""
    BootScript = ""
    InstanceId = ""
    PuppetRoles = ""
    PreCmScript = ""
    PostCmScript = ""

    VolumesList = []

    def __init__(self, kTemplateConfig):
        self.__ObjConfig = self.loadJsonFile("template/" + kTemplateConfig + ".json")
        self.Name = self.__ObjConfig["name"]
        self.__loadData()
        self.__loadVolumes()

    def __loadData(self):
        try:
            self.Ami = self.__ObjConfig["settings"]["ami"]
            self.InstanceType = self.__ObjConfig["settings"]["instance_type"]
            self.BootScript = self.__ObjConfig["settings"]["boot_script"]
            self.InstanceId = self.__ObjConfig["instance_id"]
            self.PuppetRoles = self.__ObjConfig["puppet_roles"]
            self.PreCmScript = self.__ObjConfig["pre_cm_script"]
            self.PostCmScript = self.__ObjConfig["post_cm_script"]

        except Exception, e:
            self.printMsg ("__loadData",e.args[0],True,True)

    def __loadVolumes(self):
        for key,value in self.__ObjConfig['settings']['volumes'].iteritems():
            self.VolumesList.append(clsVolume(key,value))

    def getAWSVolumes(self):
        import boto.ec2.blockdevicemapping
        bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()

        for clsVolume in self.VolumesList:
            vol_tmp = boto.ec2.blockdevicemapping.EBSBlockDeviceType()
            vol_tmp.size = clsVolume.Size
            vol_tmp.delete_on_termination = clsVolume.DelOnTerm
            vol_tmp.volume_type = clsVolume.Type
            bdm[clsVolume.Device] = vol_tmp

        return bdm
    ##-----------------------------------##
    ##-----------------------------------##    