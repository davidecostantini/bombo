class clsInstanceSched():
    instance        = None
    schedEnabled    = False
    start           = ""
    end             = ""
    day             = 0

    def __init__(self, kInstance=None, kSchedEnabled="",kStart="",kEnd="",kDay=0):
        self.instance = kInstance
        self.schedEnabled = kSchedEnabled
        self.start = kStart
        self.end = kEnd
        self.day = kDay