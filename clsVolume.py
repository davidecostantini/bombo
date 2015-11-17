class clsVolume():
    Mount = ""
    Size = 0
    Type = ""
    Device = ""
    DelOnTerm = False
    Iops = False

    def __init__(self, kMount, kDetail):
        self.__loadData(kMount, kDetail)

    def __loadData(self, kMount, kDetail):
        self.Mount = kMount
        self.Size = kDetail["size"]
        self.Type = kDetail["type"]
        self.Device = kDetail["device"]
        self.DelOnTerm = kDetail["del_on_term"]
        self.Iops = kDetail["iops"]
        self.blockDeviceMapping = kDetail["blockDeviceMapping"]

    ##-----------------------------------##
    ##-----------------------------------##
