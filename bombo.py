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
from clsScheduling import *
from clsInstanceSched import *

BOMBO_VERSION="1.3.2"

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

    def __loadData(self):
        self.__getObjCustomer(self.__ObjConfig["customer_id"])
        self.Subnet = self.__ObjConfig["subnet"]
        self.Key = self.__ObjConfig["key"]
        self.LaunchList = self.__getLaunchList(self.__ObjConfig['launch'])

        #Check if region was overloaded in the launch config
        self.Region = self.__ObjConfig["region"] if self.__ObjConfig["region"] else self.Customer.Region      

        self.SNAPSHOT_MAX_AGE = self.__ObjConfig["SNAPSHOT_MAX_AGE"]

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
        spinner = self.spinning_cursor()
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

    def __setTag(self,kSingleLaunch,kLaunchConfig,kReservation):
        import boto.ec2
        self.printMsg ("","[BOMBO] You're getting older mate, I'm tagging the instances so you can identify them!")


        for instance in kReservation.instances:
            self.printMsg ("",'[AWS] Assigning the tag NAME:' + kSingleLaunch.Hostname )
            self.__awsConnection.create_tags([instance.id], {"Name":kSingleLaunch.Hostname})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag HOSTNAME:' + kSingleLaunch.Hostname )
            self.__awsConnection.create_tags([instance.id], {"HOSTNAME":kSingleLaunch.Hostname})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag ENVIRONMENT:' + kSingleLaunch.Env )
            self.__awsConnection.create_tags([instance.id], {"ENVIRONMENT":kSingleLaunch.Env})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag DESC:' + kSingleLaunch.Desc )
            self.__awsConnection.create_tags([instance.id], {"DESC":kSingleLaunch.Desc})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag CM_Roles:' + str(kSingleLaunch.Template.CmRoles))
            self.__awsConnection.create_tags([instance.id], {"CM_Roles": str(kSingleLaunch.Template.CmRoles)})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag LAUNCH: Launched with BOMBO ver. ' + BOMBO_VERSION)
            self.__awsConnection.create_tags([instance.id], {"BOMBO": str(BOMBO_VERSION)})
            self.printMsg ("",'---> DONE' )

            self.printMsg ("",'[AWS] Assigning the tag bombo_autosched:SCHEDULE' )
            self.__awsConnection.create_tags([instance.id], {"bombo_autosched:SCHEDULE": "N,08:00-20:00,5,N,08:00-20:00,5,A"})
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
            spinner = self.spinning_cursor()
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
            if instance.tags.get('Name') :
                vol.add_tag("Name", "### Copy of :" + instance.tags.get('Name') + " ###")
            else:
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
        spinner = self.spinning_cursor()
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
        spinner = self.spinning_cursor()
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

       # self.printMsg ("","Extracting tags from source instance...")
       # TagsList = self.getTagsFromInstance(kInstanceId)

       # self.printMsg ("","Applying tags to the new instance...")
       # self.setTagsToInstance(TagsList, instance.id)

        self.printMsg ("","---> New instance tagged...")


        self.printMsg ("","Stopping NEW instance...")
        self.__awsConnection.stop_instances(
            instance_ids=reservation.instances[0].id,
            force=True)
        counter = 0
        spinner = self.spinning_cursor()
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
        spinner = self.spinning_cursor()
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


    def BackupInstance(self,kCustomerId,kRegion,kInstanceId,kKeepInstanceOn = False, kFlushOldBackup = False):
        from datetime import datetime, timedelta
        import sys, time
        import boto.ec2
        import boto.vpc

        # Will tag all the volumes on the instances requested, then make a snapshot of the volumes, then tag the snapshots, then purge
        self.showInitialMsg()

        if kKeepInstanceOn==True:
            self.printMsg ("","###> You choose to backup the instances without switching them off, please check when done if it was completed successfully!")

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
        
        self.printMsg ("","Getting instances details...")
        if kInstanceId == "all":
            instances = [i for r in self.__awsConnection.get_all_reservations() for i in r.instances]
        else:
            instances = [i for r in self.__awsConnection.get_all_instances(instance_ids=[kInstanceId]) for i in r.instances]
        
        self.printMsg ("","---> " + str(len(instances)) + " Found")
        VolumesSnapshotMatchList = []

        pointer=0
        for instance in instances:
            pointer+=1
            self.printMsg ("","###--------------------------------------------------------------------------------###")
            self.printMsg ("","Working on " + instance.id + " [" + str(pointer) + " of " + str(len(instances)) + "]")
        
            self.printMsg ("","Getting volumes...")
            vols = self.__awsConnection.get_all_volumes(filters={'attachment.instance-id': instance.id})
            self.printMsg ("","---> " + str(len(vols)) + " Volumes found")

            self.printMsg ("","Tagging instance...")
            self.__awsConnection.create_tags([instance.id], {"bombo_backup": datetime.today().strftime('%d-%m-%Y %H:%M:%S')})
            self.printMsg ("","---> " + "bombo_backup - " + datetime.today().strftime('%d-%m-%Y %H:%M:%S'))

            InstanceInitialStatusOn=False

            if kKeepInstanceOn!= True:
                
                if instance.update() != "stopped":
                    InstanceInitialStatusOn=True
                    self.printMsg ("","Stopping the instance...")
                    instances_to_stop = self.__awsConnection.stop_instances(instance_ids=instance.id)
                    counter = 0
                    spinner = self.spinning_cursor()
                    while counter != len(instances_to_stop):
                        sys.stdout.write(spinner.next())
                        sys.stdout.flush()
                        sys.stdout.write('\b')

                        for instance in instances_to_stop:
                            if instance.update() == "stopped":
                                counter += 1
                        time.sleep(2)
                else:
                    self.printMsg ("","Instance is already stopped...")
                self.printMsg ("","---> Done")

            #Empty list
            VolumesSnapshotMatchList = []
            for vol in vols:
                self.printMsg ("","Tagging volume " + vol.id + "...")
                vol.add_tag("bombo_backup:INSTANCE", instance.id)
                vol.add_tag("bombo_backup:STATUS", vol.attach_data.status)
                vol.add_tag("bombo_backup:DEVICE", vol.attach_data.device)
                vol.add_tag("bombo_backup:DATE", datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
                #sg commented out....changes the tags on the original volumes...no need for this imho
                #if instance.tags.get('Name') :
                #    vol.add_tag("Name", "### Copy of: " + instance.tags.get('Name') + " ###" )
                #else:
                #    vol.add_tag("Name", "### Copied ###")
                self.printMsg ("","---> Done")

                self.printMsg ("","Snapshot volume " + vol.id + "...")
                snapshot = self.__awsConnection.create_snapshot(vol.id, "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)

                VolumesSnapshotMatchList.append([vol,snapshot])

                self.printMsg ("","---> Launching snapshot [" + str(vol.id) + "] => " + "INSTANCE: " + instance.id + " - DEVICE:" + vol.attach_data.device)
            
            self.printMsg ("","Waiting for the snapshots to be ready for instance " + instance.id)

            counter = 0
            progress = 0
            singleValue = ""
            spinner = self.spinning_cursor()
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
                VolumesSnapshotMatch[1].add_tag("bombo_backup:DATE", datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
                VolumesSnapshotMatch[1].add_tag("bombo_backup:INSTANCE", instance.id)
                VolumesSnapshotMatch[1].add_tag("bombo_backup:DEVICE", VolumesSnapshotMatch[0].attach_data.device)
                if instance.tags.get('bombo_autosched:SCHEDULE') :
                    VolumesSnapshotMatch[1].add_tag("bombo_autosched:SCHEDULE", instance.tags.get('bombo_autosched:SCHEDULE'))
                    
                #if instance.tags.get('Name') :
                #    VolumesSnapshotMatch[1].add_tag("Name", "### BACKUP of :" + instance.tags.get('Name') + " ###")
                #else:
                VolumesSnapshotMatch[1].add_tag("Name", "### BACKUP ###")

                self.printMsg ("","Snapshot " + str(VolumesSnapshotMatch[1].id))
                self.printMsg ("","---> " + "bombo_backup:DATE " + str(datetime.today().strftime('%d-%m-%Y %H:%M:%S')))
                self.printMsg ("","---> " + "bombo_backup:INSTANCE " + str(instance.id))
                self.printMsg ("","---> " + "bombo_backup:DEVICE " + VolumesSnapshotMatch[0].attach_data.device)

            if kKeepInstanceOn == False and InstanceInitialStatusOn == True:
                self.printMsg ("","Restarting instance...")
                self.__awsConnection.start_instances(instance_ids=instance.id)
                self.printMsg ("","---> Done...")

            self.printMsg ("","###--------------------------------------------------------------------------------###")
            
        #
        # Purge old snapshots
        # Snapshots have been made, now to purge the old ones
        if kFlushOldBackup:
            deletion_counter = 0
            size_counter = 0
            
            delete_time = datetime.utcnow() - timedelta(days=ObjCustomer.BckVolumesRetention)
            self.printMsg ("","Deleting any snapshots older than {days} days".format(days=ObjCustomer.BckVolumesRetention))

            snapshots = self.__awsConnection.get_all_snapshots()

            for snapshot in snapshots:
                if 'bombo_backup:INSTANCE' in snapshot.tags:
                    if snapshot.tags.get('bombo_backup:INSTANCE') == kInstanceId:

                        start_time = datetime.strptime(snapshot.start_time,'%Y-%m-%dT%H:%M:%S.000Z')

                        if start_time < delete_time:
                            print ('Deleting {id}'.format(id=snapshot.id)) + " made on " + str(snapshot.tags.get('bombo_backup:DATE')) + " attached to " + str(snapshot.tags.get('bombo_backup:INSTANCE')) + " mounted on " + str(snapshot.tags.get('bombo_backup:DEVICE'))
                            deletion_counter = deletion_counter + 1
                            size_counter = size_counter + snapshot.volume_size

                            snapshot.delete(dry_run=False)
                            
                #else:
                #    # The snapshot does not have a name tag. Which means it wasn't created by Bombo
                #    start_time = datetime.strptime(snapshot.start_time,'%Y-%m-%dT%H:%M:%S.000Z')
                #    if start_time < delete_time:
                #        anon_deletion_counter = anon_deletion_counter + 1
                #        anon_size_counter = anon_size_counter + snapshot.volume_size
            print 'Deleted {number} snapshots totalling {size} GB'.format(number=deletion_counter,size=size_counter)
            #print 'Anonymous snapshots that could be deleted: {number} snapshots totalling {size} GB'.format(number=anon_deletion_counter,size=anon_size_counter)

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
####################################################################
##############################################
    def UpdateSnapshots(self,kCustomer):
        from datetime import datetime, date, timedelta
        import sys, time, string
        import boto.ec2
        import boto.vpc
        
        #Set the age of snapshots to delete in days
        maxAge = kCustomer.BckVolumesRetention
      
        
        ObjCustomer = clsCustomer(kCustomer)
        self.printMsg ("","Connecting ...")
        self.__awsConnection = boto.ec2.connect_to_region(
            ObjCustomer.Region,
            aws_access_key_id=ObjCustomer.Access_key,
            aws_secret_access_key=ObjCustomer.Secret_key)
        self.printMsg ("","---> " + "Connected")
        
        #
        # Make a snapshot of each instance's volumes
                #self.BackupInstance(kCustomer,"eu-west-1","i-7bff97da",True)
        #Identify the region all of the instances & Backitup (which will create a snapshot)
        instances = [i for r in self.__awsConnection.get_all_reservations()  for i in r.instances]      
        for instance in instances:
            region = str(instance.region).split(":")[1]
            self.BackupInstance(kCustomer,region,instance.id,True)
        #
        # Purge old snapshots
        # Snapshots have been made, now to purge the old ones
        delete_time = datetime.utcnow() - timedelta(days=maxAge)
        self.printMsg ("","Deleting any snapshots older than {days} days".format(days=maxAge))

        snapshots = self.__awsConnection.get_all_snapshots(filters={'attachment.instance-id': 'i-11111111'})

        deletion_counter = 0
        size_counter = 0
        # Counters for snapshots with no Name 
        anon_deletion_counter = 0
        anon_size_counter = 0
        
        for snapshot in snapshots:
            if snapshot.tags.get('bombo_backup:INSTANCE') : 
                start_time = datetime.strptime(snapshot.start_time,'%Y-%m-%dT%H:%M:%S.000Z')

                if start_time < delete_time:
                    print ('Deleting {id}'.format(id=snapshot.id)) + " " + str(snapshot.tags)
                    deletion_counter = deletion_counter + 1
                    size_counter = size_counter + snapshot.volume_size
                    # Set this to TRUE to prevent deletion
                    snapshot.delete(dry_run=False)
            else:
                # The snapshot does not have a name tag. Which means it wasn't created by Bombo
                start_time = datetime.strptime(snapshot.start_time,'%Y-%m-%dT%H:%M:%S.000Z')
                if start_time < delete_time:
                    anon_deletion_counter = anon_deletion_counter + 1
                    anon_size_counter = anon_size_counter + snapshot.volume_size
        print 'Deleted {number} snapshots totalling {size} GB'.format(number=deletion_counter,size=size_counter)
        print 'Anonymous snapshots that could be deleted: {number} snapshots totalling {size} GB'.format(number=anon_deletion_counter,size=anon_size_counter)

        
        

             
####################################################################
##############################################       
                
    def ApplyPowerSchedule(self,kCustomer):
        from datetime import datetime, date
        import sys, time, string
        import boto.ec2
        import boto.vpc

        fullInstancesSchedList = []
        taskInstancesSchedListStartup = []
        taskInstancesSchedListStop = []

        self.showInitialMsg()
        ObjCustomer = clsCustomer(kCustomer)

        self.printMsg ("","Connecting ...")
        self.__awsConnection = boto.ec2.connect_to_region(
            ObjCustomer.Region,
            aws_access_key_id=ObjCustomer.Access_key,
            aws_secret_access_key=ObjCustomer.Secret_key)
        self.printMsg ("","---> " + "Connected")

        self.printMsg ("","Getting schedule details...")
        #reservations = self.__awsConnection.get_all_reservations()
        instances = [i for r in self.__awsConnection.get_all_reservations()  for i in r.instances]

        for instance in instances:

            ObjInstanceSched = clsInstanceSched()

            # Check if the instance has both of the required tang + the flag to enable scheduling
            schedValues=""
            if instance.tags.get('bombo_autosched:SCHEDULE') :
                schedValues                      = instance.tags.get('bombo_autosched:SCHEDULE').upper().split(",")
                ObjInstanceSched.start           = schedValues[1].split("-")[0].replace(":"," ")
                ObjInstanceSched.end             = schedValues[1].split("-")[1].replace(":"," ")
                ObjInstanceSched.day             = int(schedValues[2])
                ObjInstanceSched.schedEnabled    = (True if schedValues[0] == "Y" else False)
                ObjInstanceSched.deps            = str(instance.tags.get('bombo_autosched:DEPS'))


            #Adding instance even if SCHEDULING is not enabled
            ObjInstanceSched.instance            = instance

            #Populating full Instances list with Scheduling option info
            fullInstancesSchedList.append(ObjInstanceSched)

            if ObjInstanceSched.schedEnabled:
                # The Schedule wants to be applied. Extract the timerange and power on/off
                try:
                    # Check if the current time + day of week is inside the bombo_autosched:SCHEDULE range
                    if date.isoweekday(date.today()) <= ObjInstanceSched.day and ObjInstanceSched.start <= time.strftime("%H %M",time.localtime()) < ObjInstanceSched.end :
                        # It is inside the working schedule range, power it up if it is shutdown
                        if instance.state == "stopped" :
                            #Adding reservation to list
                            taskInstancesSchedListStartup.append(ObjInstanceSched)

                    else:
                        # It is currently outside of the scheduled working hours, shut it down if it is running
                        if instance.state == "running" :
                            taskInstancesSchedListStop.append(ObjInstanceSched)

                # Capture an error if bombo_autosched:SCHEDULE  isn't formatted correctly
                except IndexError:
                    self.printMsg ("","###> Error with the tag bombo_autosched:SCHEDULE (expecting <Y/N>,hh:mm-hh:mm,<days>), found:   " + instance.tags.get('bombo_autosched:SCHEDULE') + " on instance: " + instance.id )


            # tag all the instances with the Auto Scheduling tags if it does not already exist, but set it to be ignored.
            #if not instance.tags.get('bombo_autosched:SCHEDULE'):
            #    self.__awsConnection.create_tags([instance.id], {"bombo_autosched:SCHEDULE": "N,08:00-20:00,5"})

        ObjScheduling = clsScheduling()

        listToStart=ObjScheduling.getScheduledListStartup(taskInstancesSchedListStartup,fullInstancesSchedList)
        self.printMsg ("","Found " + str(len(listToStart)) + " instances to start!")
        for i in listToStart:
            self.printMsg ("","Starting instance [" +  i.instance.id + "]")
            tmpInstance=self.__awsConnection.start_instances(i.instance.id)

            if i.isADeps:
                self.printMsg ("","This instance is a depenency, so I'm waiting for the instance to be up and running")
                ObjScheduling.checkSchedInstanceState(tmpInstance[0])

        listToStop=ObjScheduling.getScheduledListStop(taskInstancesSchedListStop,fullInstancesSchedList)
        self.printMsg ("","Found " + str(len(listToStop)) + " instances to stop!")
        for i in listToStop:
            self.printMsg ("","Stopping instance [" +  i.instance.id + "]")
            tmpInstance=self.__awsConnection.stop_instances(i.instance.id)

            self.printMsg ("","Waiting for the instance to be stopped")
            ObjScheduling.checkSchedInstanceState(tmpInstance[0])

        self.printMsg ("","--->Finished with the scheduling")
