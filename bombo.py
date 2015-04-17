from config import *
from bgcolors import *
from clsRedis import *
from clsBaseClass import *
from clsCustomer import *
from clsInstance import *
from clsDNSRecord import *
from clsVolume import *
from clsTemplate import *
from clsSingleLaunch import *

BOMBO_VERSION="1.1"

class LaunchConfig(clsBaseClass):
    __ObjConfig = None

    Customer=None
    Subnet=""
    Key=""
    Region=""

    LaunchList = []

    def __init__(self, kLaunchConfig):
        self.__ObjConfig = self.loadJsonFile("launch/" + kLaunchConfig + ".json")
        self.__loadData()
        self.LaunchList = self.__getLaunchList(self.__ObjConfig['launch'])

    def __loadData(self):
        self.__getObjCustomer(self.__ObjConfig["customer_id"])
        self.Subnet = self.__ObjConfig["subnet"]
        self.Key = self.__ObjConfig["key"]
        self.Region = self.__ObjConfig["region"] if self.__ObjConfig["region"] else self.Customer.Region #Check if region was overloaded in the launch config

    def __getObjCustomer(self,kCustomerId):
        self.CustomerId = kCustomerId
        self.Customer = clsCustomer(kCustomerId)

    def __getLaunchList(self,kJsonList):
        TmpList=[]
        for key,value in kJsonList.iteritems():
            TmpList.append(clsSingleLaunch(value))
        return TmpList
    ##-----------------------------------##
    ##-----------------------------------##

class bombo(clsBaseClass):
    __ObjLaunchConfig = ""
    __awsConnection = ""

    def __init__(self, kTemplateConfig=""):
        if kTemplateConfig:
            self.__ObjLaunchConfig=LaunchConfig(kTemplateConfig)

    def Launch(self,kTemplateConfig="",kIsTest=False):
        self.showInitialMsg()

        if (self.user_input("Do you really want play with cloud stuff? \nPlease be careful and don't mess everything.... (y,n) ",["y","n"]).upper() == "Y"):
            if kTemplateConfig:
                self.__ObjLaunchConfig=LaunchConfig(kTemplateConfig)
            self.__runProcess(kIsTest)
        else:
            self.printMsg("","Well done! I knew you are a coward.... ahahahahahahah....",True)

    def __runProcess(self,kIsTest):
        import time
        import boto.ec2

        ObjTmp = None

        self.printMsg ("","[AWS] Connecting ...")

        #Connecting to region
        self.__awsConnection = boto.ec2.connect_to_region(
            self.__ObjLaunchConfig.Region,
            aws_access_key_id=self.__ObjLaunchConfig.Customer.Access_key,
            aws_secret_access_key=self.__ObjLaunchConfig.Customer.Secret_key)

        for singleLaunch in self.__ObjLaunchConfig.LaunchList:
            #Return Reservation
            tmpReservation=self.__singleLaunch(kIsTest,singleLaunch,self.__ObjLaunchConfig)

            #Sleep to avoid INSTANCE NOT FOUND error
            time.sleep(4)

            if (self.__checkLaunchStatus(tmpReservation)):
                self.printMsg ("","Ooh no, I can't believe there was an error during the launch..... you made a mistake as usual!",True,True)

            for inst in tmpReservation.instances:
                ObjTmp = clsInstance(inst.id,self.__ObjLaunchConfig.Customer,inst)
                ObjTmp.Infom_dns = singleLaunch.Hostname + "." + self.__ObjLaunchConfig.Customer.Dns_domain

                #Load data from AWS in memory
                ObjTmp.refreshAWS()

                #Add DNS record if DNS domain specified
                if self.__ObjLaunchConfig.Customer.Dns_domain:
                    ObjTmp.setDns(singleLaunch.Hostname)

                self.printMsg ("","[BOMBO] Instance" + inst.id + " saved")

            #Tagging instances launched
            self.__setTag(singleLaunch,self.__ObjLaunchConfig,tmpReservation)


    def __singleLaunch(self,kIsTest,kSingleLaunch,kLaunchConfig):
        import boto.ec2

        self.printMsg ("","[BOMBO] Launching... " + kSingleLaunch.Template.InstanceId)

        #Check if parameter have been overloaded
        subnetToUse = kSingleLaunch.Subnet or kLaunchConfig.Subnet
        keyToUse = kSingleLaunch.Key or kLaunchConfig.Key

        #Launch instances
        reservation = self.__awsConnection.run_instances(
            image_id = kSingleLaunch.Template.Ami,
            instance_type = kSingleLaunch.Template.InstanceType,
            key_name = keyToUse,
            security_group_ids = kSingleLaunch.SecGroups,
            user_data= self.getBootScript(kSingleLaunch,kLaunchConfig),
            min_count=1,
            max_count=kSingleLaunch.Qty,
            #ebs_optimized=EBS_OPTMZ,
            subnet_id=subnetToUse,
            additional_info=kSingleLaunch.Desc,
            block_device_map = kSingleLaunch.Template.getAWSVolumes(),
            dry_run=kIsTest,
        )
        self.printMsg ("",'---> ' + str(kSingleLaunch.Qty) + ' DONE' )

        return reservation

    def __checkLaunchStatus(self,kReservation,kEssentialInfo=False):
        import time, sys
        counter = 0
        spinner = self.__spinning_cursor()
        instancesReady = []
        while counter != len(kReservation.instances):

            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            sys.stdout.write('\b')

            for instance in kReservation.instances:
                if instance.update() != "pending":
                    counter += 1

        for instance in kReservation.instances:
            self.printMsg ("","#####################################################")
            self.printMsg ("","[BOMBO] Hey mate, instance " + str(instance.id) + " is now ready to be messed by you....")
            
            if not kEssentialInfo:
                if (instance.public_dns_name != ""):
                    self.printMsg ("","---> Public DNS: " + instance.public_dns_name)
                self.printMsg ("","---> Private IP: " + instance.private_ip_address)
                self.printMsg ("","---> Private DNS: " + instance.private_dns_name)
                self.printMsg ("","#####################################################")

    def __spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def __setTag(self,kSingleLaunch,kLaunchConfig,kReservation):
        import boto.ec2
        self.printMsg ("","[BOMBO] You're getting older mate, I'm tagging the instances so you can identify them!")


        for instance in kReservation.instances:
            self.printMsg ("",'[AWS] Assignin the tag NAME:' + kSingleLaunch.Hostname )
            self.__awsConnection.create_tags([instance.id], {"NAME":kSingleLaunch.Hostname})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assignin the tag HOSTNAME:' + kSingleLaunch.Hostname )
            self.__awsConnection.create_tags([instance.id], {"HOSTNAME":kSingleLaunch.Hostname})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assignin the tag ENVIRONMENT:' + kSingleLaunch.Env )
            self.__awsConnection.create_tags([instance.id], {"ENVIRONMENT":kSingleLaunch.Env})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assignin the tag DESC:' + kSingleLaunch.Desc )
            self.__awsConnection.create_tags([instance.id], {"DESC":kSingleLaunch.Desc})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assignin the tag PUPPET_ROLES:' + str(kSingleLaunch.Template.PuppetRoles))
            self.__awsConnection.create_tags([instance.id], {"PUPPET_ROLES": str(kSingleLaunch.Template.PuppetRoles)})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assignin the tag LAUNCH: Launched with BOMBO ver. ' + BOMBO_VERSION)
            self.__awsConnection.create_tags([instance.id], {"BOMBO": str(BOMBO_VERSION)})
            self.printMsg ("",'---> DONE' )
            
            self.printMsg ("",'[AWS] Assignin the tag bombo_autosched:ENABLE' )
            self.__awsConnection.create_tags([instance.id], {"bombo_autosched:ENABLE": "N"})
            self.printMsg ("",'---> DONE' )
            
            self.printMsg ("",'[AWS] Assignin the tag bombo_autosched:SCHEDULE' )
            self.__awsConnection.create_tags([instance.id], {"bombo_autosched:SCHEDULE": "08:00-20:00,5"})
            self.printMsg ("",'---> DONE' )

    def searchSimilarAMI(self,kAwsConn,kInstance):
        #print "Return TMP AMI for ID"
        #return "ami-0f55d978"
        result=kAwsConn.get_all_images(filters={\
            'architecture': kInstance.architecture,\
            'virtualization_type': kInstance.virtualization_type,\
            'state': "available",\
            'hypervisor': kInstance.hypervisor,\
            'root-device-type': kInstance.root_device_type ,\
            'image-type': 'machine'\
            })

        if len(result) > 0:
            self.printMsg ("","---> " + str(len(result)) + " AMI found, choosing the first:" + result[0].id)
            return result[0].id
        else:
            self.printMsg ("","The old AMI is not available anymore and I wasn't able to find an AMI that fits the requirement (Of course is not my fault)!",True,True)


    def CopyInstance(self,kCustomerId,kRegion,kInstanceId,kSubnet,kKeepInstanceOn = False):
        from datetime import datetime
        import sys, time
        import boto.ec2
        import boto.vpc

        self.showInitialMsg()

        if kKeepInstanceOn:
            self.printMsg ("","###> You choose to copy the instance without switching it off, please check when done if it was completed successfully!")

        ObjCustomer = clsCustomer(kCustomerId)

        self.printMsg ("","Connecting ...")
        self.__awsConnection = boto.ec2.connect_to_region(
            kRegion,
            aws_access_key_id=ObjCustomer.Access_key,
            aws_secret_access_key=ObjCustomer.Secret_key)
        self.printMsg ("","---> " + "Connected")

        self.printMsg ("","Getting instance details...")
        reservations = self.__awsConnection.get_all_instances(instance_ids=[kInstanceId])
        instance = reservations[0].instances[0]
        self.printMsg ("","---> " + instance.id)

        self.printMsg ("","Getting subnet details...")
        self.__awsVpcConnection = boto.vpc.connect_to_region(
            kRegion,
            aws_access_key_id=ObjCustomer.Access_key,
            aws_secret_access_key=ObjCustomer.Secret_key)
        subnets = self.__awsVpcConnection.get_all_subnets(subnet_ids=[kSubnet])
        old_vpc_id =  subnets[0].vpc_id
        old_azone = subnets[0].availability_zone
        self.printMsg ("","---> Found " + kSubnet + " linked to " + old_vpc_id + " in " + old_azone)

        if kKeepInstanceOn == False:
            self.printMsg ("","Stopping the instance...")
            instances_to_stop = self.__awsConnection.stop_instances(instance_ids=kInstanceId)
            counter = 0
            spinner = self.__spinning_cursor()
            while counter != len(instances_to_stop):
                sys.stdout.write(spinner.next())
                sys.stdout.flush()
                sys.stdout.write('\b')

                for instance in instances_to_stop:
                    if instance.update() == "stopped":
                        counter += 1
                time.sleep(2)
            self.printMsg ("","---> Done")

        self.printMsg ("","Getting volumes...")
        vols = self.__awsConnection.get_all_volumes(filters={'attachment.instance-id': instance.id})
        self.printMsg ("","---> " + str(len(vols)) + " Volumes found")

        self.printMsg ("","Tagging instance...")
        self.__awsConnection.create_tags([instance.id], {"bombo_moving": kSubnet + " - " + datetime.today().strftime('%d-%m-%Y %H:%M:%S')})
        self.printMsg ("","---> " + kSubnet + " - " + datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

        #self.printMsg ("","Copying tags...")
        #TagsList = []
        #TagsList = setTagsToInstance([instance.id])
        #self.printMsg ("","Finished copying tags")
        
        
        VolumesSnapshotMatchList = []

        for vol in vols:
            self.printMsg ("","Tagging volume " + vol.id + "...")
            vol.add_tag("Name", "### Copied ###")
            vol.add_tag("bombo_moving:INSTANCE", instance.id)
            vol.add_tag("bombo_moving:STATUS", vol.attach_data.status)
            vol.add_tag("bombo_moving:DEVICE", vol.attach_data.device)

            self.printMsg ("","Snapshot volume " + vol.id + "...")
            snapshot = self.__awsConnection.create_snapshot(vol.id, "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)

            VolumesSnapshotMatchList.append([vol,snapshot])

            self.printMsg ("","---> Done with [" + str(vol.id) + "] => " + "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)

        self.printMsg ("","Waiting for the snapshots to be ready...")

        counter = 0
        progress = 0
        singleValue = ""
        spinner = self.__spinning_cursor()
        while progress < (100 * len(VolumesSnapshotMatchList)):
            progress = 0
            for VolumesSnapshotMatch in VolumesSnapshotMatchList:
                singleValue = VolumesSnapshotMatch[1].update()
                if len(singleValue)==0:
                    singleValue="0%"
                progress = progress + int(singleValue[:-1])
                time.sleep(2)

            sys.stdout.flush()
            sys.stdout.write('\r')
            sys.stdout.write(spinner.next() + " Waiting for " + str(len(VolumesSnapshotMatchList)) + " snapshots => Progress: " + str(progress / len(VolumesSnapshotMatchList)) + "%")
        sys.stdout.write('\n')

        self.printMsg ("","---> Snapshots ready...")

        NewInstanceVolumeList = []

        self.printMsg ("","Creating volumes from snapshot...")
        for VolumesSnapshotMatch in VolumesSnapshotMatchList:
            new_vol_tmp = self.__awsConnection.create_volume(
                size=VolumesSnapshotMatch[0].size,
                volume_type = VolumesSnapshotMatch[0].type,
                snapshot=VolumesSnapshotMatch[1],
                zone=old_azone
                )
            new_vol_tmp.add_tag("bombo_moving:DATE", datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
            new_vol_tmp.add_tag("bombo_moving:SOURCE", kInstanceId + " -> " + VolumesSnapshotMatch[0].attach_data.device)
            NewInstanceVolumeList.append([VolumesSnapshotMatch[0].attach_data.device,new_vol_tmp])
            self.printMsg ("","---> [" + VolumesSnapshotMatch[0].attach_data.device + "] - " + VolumesSnapshotMatch[0].type + ", " + str(VolumesSnapshotMatch[0].size) + " GB created")
        self.printMsg ("","---> Volumes ready...")


        self.printMsg ("","Check AMI availability " + instance.image_id + "...")
        ObjInstance = clsInstance(instance.id,ObjCustomer,instance)

        if ObjInstance.checkAmiAvailility(self.__awsConnection):
            self.printMsg ("","---> AMI Available")
            ObjInstance.Ami = instance.image_id
        else:
            self.printMsg ("","###> AMI NOT Available, searching for a similar AMI [" + instance.architecture +" - " + instance.virtualization_type +" - " + instance.hypervisor +" - " + instance.root_device_type + "]")
            ObjInstance.Ami = self.searchSimilarAMI(self.__awsConnection,instance)

        self.printMsg ("","Launching new instance on " + kSubnet + "...")
        reservation = self.__awsConnection.run_instances(
            image_id = ObjInstance.Ami,
            instance_type = instance.instance_type,
            key_name = instance.key_name,
            #private_ip_address = "10.0.34.100",
            #security_group_ids = kSingleLaunch.SecGroups,
            subnet_id=kSubnet,
            dry_run=False,
        )

        counter = 0
        spinner = self.__spinning_cursor()
        while counter != len(reservation.instances):
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            sys.stdout.write('\b')

            for instance in reservation.instances:
                if instance.update() != "pending":
                    counter += 1
                time.sleep(2) #Must wait even when the instance is ready, otherwise we got instance not found by AWS

        self.printMsg ("","---> [" + reservation.instances[0].id + "] => Instance launched")

        self.printMsg ("","Tagging new instance...")
        self.__awsConnection.create_tags([instance.id], {"bombo_moving:SOURCE_INSTANCE":kInstanceId})
        self.__awsConnection.create_tags([instance.id], {"bombo_moving:DATE":datetime.today().strftime('%d-%m-%Y %H:%M:%S')})
        
        self.printMsg ("","Extracting tags from source instance...")
        TagsList = self.getTagsFromInstance(kInstanceId)
       
        self.printMsg ("","Applying tags to the new instance...")
        self.setTagsToInstance(TagsList, instance.id)

        self.printMsg ("","---> New instance tagged...")


        self.printMsg ("","Stopping NEW instance...")
        self.__awsConnection.stop_instances(
            instance_ids=reservation.instances[0].id,
            force=True)
        counter = 0
        spinner = self.__spinning_cursor()
        while counter != len(reservation.instances):
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            sys.stdout.write('\b')

            for instance in reservation.instances:
                if instance.update() == "stopped":
                    counter += 1
                time.sleep(2)

        self.printMsg ("","---> Done")

        self.printMsg ("","Getting volumes list of the new instance...")
        new_instance_vols = self.__awsConnection.get_all_volumes(filters={'attachment.instance-id': reservation.instances[0].id})
        self.printMsg ("","---> " + str(len(vols)) + " volumes found, deleting all..")
        for new_instance_vol in new_instance_vols:
            new_instance_vol.detach(
                force=True)
            self.printMsg ("","---> " + str(new_instance_vol.id) + " detached....")

            new_instance_vol.delete
            self.printMsg ("","---> " + str(new_instance_vol.id) + " and now deleted!")

        counter = 0
        spinner = self.__spinning_cursor()
        while counter < len(new_instance_vols):
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            sys.stdout.write('\b')

            for vol_check_detach in new_instance_vols:
                if vol_check_detach.update() == "available":
                    counter += 1
                time.sleep(2)

        self.printMsg ("","Attaching volumes to the new instance...")
        for NewInstanceVolume in NewInstanceVolumeList:
            self.__awsConnection.attach_volume(
                instance_id = reservation.instances[0].id,
                volume_id = NewInstanceVolume[1].id,
                device = NewInstanceVolume[0])
            self.printMsg ("","---> " + NewInstanceVolume[0] + " attached to " + str(reservation.instances[0].id))

        self.printMsg ("","Starting the NEW instance...")
        self.__awsConnection.start_instances(instance_ids=reservation.instances[0].id)
        self.printMsg ("","---> Done")

        self.printMsg ("","Hopefully everything went well......")


    def BackupInstance(self,kCustomerId,kRegion,kInstanceId,kKeepInstanceOn = False):
        from datetime import datetime
        import sys, time
        import boto.ec2
        import boto.vpc

        self.showInitialMsg()

        if kKeepInstanceOn:
            self.printMsg ("","###> You choose to backup the instance without switching it off, please check when done if it was completed successfully!")

        ObjCustomer = clsCustomer(kCustomerId)

        self.printMsg ("","Connecting ...")
        try:
            self.__awsConnection = boto.ec2.connect_to_region(
                kRegion,
                aws_access_key_id=ObjCustomer.Access_key,
                aws_secret_access_key=ObjCustomer.Secret_key)

        except:
            self.printMsg("AWS","Ops! I found problems during connection..." + str(sys.exc_info()[0]),True,True)

        self.printMsg ("","---> " + "Connected")

        self.printMsg ("","Getting instance details...")
        reservations = self.__awsConnection.get_all_instances(instance_ids=[kInstanceId])
        instance = reservations[0].instances[0]
        self.printMsg ("","---> " + instance.id)

        if kKeepInstanceOn == False:
            self.printMsg ("","Stopping the instance...")
            instances_to_stop = self.__awsConnection.stop_instances(instance_ids=kInstanceId)
            counter = 0
            spinner = self.__spinning_cursor()
            while counter != len(instances_to_stop):
                sys.stdout.write(spinner.next())
                sys.stdout.flush()
                sys.stdout.write('\b')

                for instance in instances_to_stop:
                    if instance.update() == "stopped":
                        counter += 1
                time.sleep(2)
            self.printMsg ("","---> Done")

        self.printMsg ("","Getting volumes...")
        vols = self.__awsConnection.get_all_volumes(filters={'attachment.instance-id': instance.id})
        self.printMsg ("","---> " + str(len(vols)) + " Volumes found")

        self.printMsg ("","Tagging instance...")
        self.__awsConnection.create_tags([instance.id], {"bombo_backup": datetime.today().strftime('%d-%m-%Y %H:%M:%S')})
        self.printMsg ("","---> " + "bombo_backup - " + datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

        VolumesSnapshotMatchList = []

        for vol in vols:
            self.printMsg ("","Tagging volume " + vol.id + "...")
            vol.add_tag("bombo_backup:INSTANCE", instance.id)
            vol.add_tag("bombo_backup:STATUS", vol.attach_data.status)
            vol.add_tag("bombo_backup:DEVICE", vol.attach_data.device)
            vol.add_tag("bombo_backup:DATE", datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

            self.printMsg ("","Snapshot volume " + vol.id + "...")
            snapshot = self.__awsConnection.create_snapshot(vol.id, "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)

            VolumesSnapshotMatchList.append([vol,snapshot])

            self.printMsg ("","---> Done with [" + str(vol.id) + "] => " + "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)

        self.printMsg ("","Waiting for the snapshots to be ready...")

        counter = 0
        progress = 0
        singleValue = ""
        spinner = self.__spinning_cursor()
        while progress < (100 * len(VolumesSnapshotMatchList)):
            progress = 0
            for VolumesSnapshotMatch in VolumesSnapshotMatchList:
                singleValue = VolumesSnapshotMatch[1].update()
                if len(singleValue)==0:
                    singleValue="0%"
                progress = progress + int(singleValue[:-1])
                time.sleep(2)

            sys.stdout.flush()
            sys.stdout.write('\r')
            sys.stdout.write(spinner.next() + " Waiting for " + str(len(VolumesSnapshotMatchList)) + " snapshots => Progress: " + str(progress / len(VolumesSnapshotMatchList)) + "%")
        sys.stdout.write('\n')

        self.printMsg ("","---> Snapshots ready...")

        self.printMsg ("","Tagging Snapshots...")
        for VolumesSnapshotMatch in VolumesSnapshotMatchList:
            VolumesSnapshotMatch[1].add_tag("Name", "### Backup ###")
            VolumesSnapshotMatch[1].add_tag("bombo_backup:DATE", datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
            VolumesSnapshotMatch[1].add_tag("bombo_backup:INSTANCE", instance.id)
            VolumesSnapshotMatch[1].add_tag("bombo_backup:DEVICE", vol.attach_data.device)

            self.printMsg ("","Snapshot " + str(VolumesSnapshotMatch[1].id))
            self.printMsg ("","---> " + "bombo_backup:DATE " + str(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
            self.printMsg ("","---> " + "bombo_backup:INSTANCE " + str(instance.id))
            self.printMsg ("","---> " + "bombo_backup:DEVICE " + vol.attach_data.device)

        self.printMsg ("","Hopefully everything went well......")

        
        
        
        
        
    def getTagsFromInstance (self,kInstanceId):
        #Returns a dictionary containing all of the tags from the supplied instance ID
        #TagsList = {}
        reservations = self.__awsConnection.get_all_instances(kInstanceId)
        
        #for tag in reservations[0].instances[0].tags:
        #    TagsList[tag] = reservations[0].instances[0].tags.get(tag)
        #return TagsList
        
        return reservations[0].instances[0].tags
    
    def setTagsToInstance(self, TagsList,kInstanceId):
        reservations = self.__awsConnection.get_all_instances(kInstanceId)
        instance = reservations[0].instances[0]
        
        for tag in TagsList:
            if not instance.tags.get(tag):
                self.printMsg ("","Adding TAG:" + tag)
                self.__awsConnection.create_tags([kInstanceId], {tag:TagsList[tag]})

    def ApplyPowerSchedule(self,kCustomer):
        from datetime import datetime, date
        import sys, time, string
        import boto.ec2
        import boto.vpc
        
        resStartList = []
        
        self.showInitialMsg()
        ObjCustomer = clsCustomer(kCustomer)

        self.printMsg ("","Connecting ...")
        self.__awsConnection = boto.ec2.connect_to_region(
            ObjCustomer.Region,
            aws_access_key_id=ObjCustomer.Access_key,
            aws_secret_access_key=ObjCustomer.Secret_key)
        self.printMsg ("","---> " + "Connected")

        self.printMsg ("","Getting schedule details...")
        reservations = self.__awsConnection.get_all_reservations()
        
        for res in reservations:
            for instance in res.instances:

                # Check if the instance has both of the required tang + the flag to enable scheduling
                if instance.tags.get('bombo_autosched:SCHEDULE') : 
                    ApplySchedule = instance.tags.get('bombo_autosched:SCHEDULE').split(",")[0].upper()
                else:
                    ApplySchedule = "N"
                
                if ApplySchedule == "Y":
                    # The Schedule wants to be applied. Extract the timerange and power on/off
                    try:
                        schedValues = instance.tags.get('bombo_autosched:SCHEDULE').split(",")
                        apply       = schedValues[0]
                        start       = schedValues[1].split("-")[0].replace(":"," ")
                        end         = schedValues[1].split("-")[1].replace(":"," ")
                        day         = int(schedValues[2])
                        
                        # Check if the current time + day of week is inside the bombo_autosched:SCHEDULE range
                        if date.isoweekday(date.today()) <= day and start <= time.strftime("%H %M",time.localtime()) < end :
                            # It is inside the working schedule range, power it up if it is shutdown
                            if instance.state == "stopped" :
                                self.printMsg ("","Starting instance "+ instance.id)
                                reservation = self.__awsConnection.start_instances(instance.id)
                                
                                #Adding reservation to list
                                resStartList.append(res)
                                
                        else:
                            # It is currently outside of the scheduled working hours, shut it down if it is running
                            if instance.state == "running" : 
                                self.printMsg ("","Stopping instance "+ instance.id)
                                self.__awsConnection.stop_instances(instance.id)

                    # Capture an error if bombo_autosched:SCHEDULE  isn't formatted correctly
                    except IndexError:
                        self.printMsg ("","---> Error with the tag bombo_autosched:SCHEDULE (expecting hh:mm-hh:mm,<num>), found:   " + instance.tags.get('bombo_autosched:SCHEDULE') + " on instance: " + instance.id )
  
  
                # tag all the instances with the Auto Scheduling tags
                #if not instance.tags.get('bombo_autosched:SCHEDULE'):
                #    self.__awsConnection.create_tags([instance.id], {"bombo_autosched:SCHEDULE": "N,08:00-20:00,5"})
                    
                
        #Check launch status
        for res in resStartList:
            self.__checkLaunchStatus(res,True)

        self.printMsg ("","---> " + "Finished with the scheduling")