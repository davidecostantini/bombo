class clsInstanceSched():
    instance        = None
    schedEnabled    = False
    deps            = ""
    isADeps         = False
    start           = ""
    end             = ""
    day             = 0

    def __init__(self, kInstance=None, kSchedEnabled="",kDeps="",kStart="",kEnd="",kDay=0):
        self.instance = kInstance
        self.schedEnabled = kSchedEnabled
        self.deps = kDeps
        self.start = kStart
        self.end = kEnd
        self.day = kDay