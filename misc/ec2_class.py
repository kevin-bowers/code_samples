#!/usr/bin/env python
import boto3
import botocore
import pytz
import time


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class EC2Info:
    def __init__(self, region, profile_name=None):
        self.region = region
        if profile_name:
            session = boto3.Session(profile_name=profile_name)
            self.client = session.client('ec2', region_name=region)
            boto3.setup_default_session(profile_name=profile_name)
            self.ec2 = boto3.resource('ec2', region_name=region)
        else:
            self.client = boto3.client('ec2', region_name=region)
            self.ec2 = boto3.resource('ec2', region_name=region)

    def get_all_instance_details(self, host_name, ip=None, env=None, status=None):
        paginator = self.client.get_paginator('describe_instances')
        instances = []
        filters = []
        if host_name:
            filters = [{'Name': 'tag-value', 'Values': ['*{}*'.format(host_name)]}]
        if env:
            filters.append({'Name': 'tag:Stack', 'Values': [env.upper()]})
        if status:
            filters.append({'Name': 'instance-state-name', 'Values': [status]})
        if ip:
            filters = [{'Name': 'private-ip-address', 'Values': [ip]}]
        for instance in paginator.paginate(Filters=filters).build_full_result()['Reservations']:
            if instance not in instances:
                instances.append(instance)
        return instances

    def get_security_group_details(self, sg_id=None, port=None, env=None, description=None):
        filters = []
        if sg_id:
            filters.append({'Name': 'group-id', 'Values': [sg_id]})
        if port:
            filters.append({'Name': 'ip-permission.from-port', 'Values': ['{}'.format(port)]})
        if env:
            filters.append({'Name': 'tag:Stack', 'Values': [env.upper()]})
        if description:
            filters.append({'Name': 'description', 'Values': ['*{}*'.format(description)]})
        details = self.client.describe_security_groups(Filters=filters)
        return details['SecurityGroups']

    def get_instance_by_id(self, instance_id):
        instance_by_id = self.client.describe_instances(InstanceIds=[instance_id])
        return instance_by_id['Reservations'][0]

    def get_instance_status(self, instance_id):
        try:
            status = self.ec2.meta.client.describe_instance_status(InstanceIds=[instance_id])
            status = status['InstanceStatuses'][0]['InstanceStatus']['Details'][0]['Status']
            if status == 'passed':
                status = bcolors.OKGREEN + bcolors.BOLD + status + bcolors.ENDC
            elif status == 'initializing':
                status = bcolors.WARNING + bcolors.BOLD + status + bcolors.ENDC
            elif status == 'failed':
                status = 'Failed - Check Instance State'
                status = bcolors.FAIL + bcolors.BOLD + status + bcolors.ENDC
        except KeyError:
            pass
            status = 'Failed - Check Instance State'
            status = bcolors.FAIL + bcolors.BOLD + status + bcolors.ENDC
        except IndexError:
            pass
            status = 'None - Instance is stopped'
            status = bcolors.FAIL + bcolors.BOLD + status + bcolors.ENDC
        return status

    def get_instance_system_status(self, instance_id):
        try:
            status = self.ec2.meta.client.describe_instance_status(InstanceIds=[instance_id])
            status = status['InstanceStatuses'][0]['SystemStatus']['Details'][0]['Status']
            if status == 'passed':
                status = bcolors.OKGREEN + bcolors.BOLD + status + bcolors.ENDC
            elif status == 'initializing':
                status = bcolors.WARNING + bcolors.BOLD + status + bcolors.ENDC
        except KeyError:
            pass
            status = 'Failed - Check Instance State'
            status = bcolors.FAIL + bcolors.BOLD + status + bcolors.ENDC
        except IndexError:
            pass
            status = 'None - Instance is stopped'
            status = bcolors.FAIL + bcolors.BOLD + status + bcolors.ENDC
        return status

    def stop_instance(self, instance_id, force=False):
        self.client.stop_instances(InstanceIds=[instance_id], Force=force)
        while True:
            instance_state_by_id = self.get_instance_by_id(instance_id)
            instance_state = instance_state_by_id['Instances'][0]['State']['Name']
            if instance_state != 'stopped':
                instance_state = bcolors.WARNING + instance_state + bcolors.ENDC
                print 'Instance State: {}; Waiting for instance to stop.'.format(instance_state)
                time.sleep(10)
            if instance_state == 'stopped':
                instance_state = bcolors.FAIL + instance_state + bcolors.ENDC
                print 'Instance Status: {}'.format(instance_state)
                break

    def start_instance(self, instance_id):
        status = self.client.start_instances(InstanceIds=[instance_id])
        status = status['StartingInstances'][0]['CurrentState']['Name']
        status = bcolors.OKGREEN + status + bcolors.ENDC
        print 'Instance Status: {}'.format(status)

    def reboot_instance(self, instance_id):
        if self.client.reboot_instances(InstanceIds=[instance_id]):
            return 'Rebooting Instance: {}'.format(instance_id)

    def get_snapshot_details(self, description=None, snapshot_id=None):
        paginator = self.client.get_paginator('describe_snapshots')
        filters = []
        snapshots = []
        if description:
            filters.append({'Name': 'description', 'Values': ['*{}*'.format(description)]})
        if snapshot_id:
            filters.append({'Name': 'snapshot-id', 'Values': [snapshot_id]})
        for snapshot in paginator.paginate(Filters=filters).build_full_result()['Snapshots']:
            if snapshot not in snapshots:
                snapshots.append(snapshot)
        return snapshots

    def delete_snapshot_older_than_days(self, days=7, description=None, dryrun=True):
        delete_time = datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=days)
        print bcolors.WARNING + 'Deleting any snapshots older than {days} days'.format(days=days) + bcolors.ENDC
        if dryrun:
            print bcolors.HEADER + 'This is just a dry run. Nothing will be deleted!' + bcolors.ENDC
        else:
            print bcolors.WARNING + 'DryRun is not set. Deleting snapshots.' + bcolors.ENDC
        snapshots = self.get_snapshot_details(description=description)
        deletion_counter = 0
        size_counter = 0
        print bcolors.HEADER + 'Preparing to delete {} snapshots'.format(len(snapshots)) + bcolors.ENDC
        for snapshot in snapshots:
            start_time = snapshot['StartTime']
            if start_time < delete_time:
                try:
                    self.client.delete_snapshot(SnapshotId=snapshot['SnapshotId'], DryRun=dryrun)
                    print 'Deleted {}'.format(snapshot['SnapshotId'])
                    deletion_counter += 1
                    size_counter += snapshot['VolumeSize']
                except botocore.exceptions.ClientError as error_message:
                    if error_message.response['Error']['Code'] == 'RequestLimitExceeded':
                        print 'Unable to delete {}; Request Limit Exceeded - ' \
                              'sleeping for one minute.'.format(snapshot['SnapshotId'])
                        snapshots.append(snapshot)
                        time.sleep(60)
                    else:
                        print 'Request to delete {} would have succeeded, but something went wrong:\n{}'.format(
                            snapshot['SnapshotId'], error_message)
                        snapshots.append(snapshot)
                    pass

        return bcolors.OKGREEN + 'Deleted {number} snapshots totalling {size} GB'.format(
            number=deletion_counter,
            size=size_counter
        ) + bcolors.ENDC