#!/usr/bin/env python
#
# Copyright (c) 2011 Shakir James and Washington University in St. Louis.
# All rights reserved
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    3. The name of the author or Washington University may not be used 
#       to endorse or promote products derived from this source code 
#       without specific prior written permission.
#    4. Conditions of any other entities that contributed to this are also
#       met. If a copyright notice is present from another entity, it must
#       be maintained in redistributions of the source code.
#
# THIS INTELLECTUAL PROPERTY (WHICH MAY INCLUDE BUT IS NOT LIMITED TO SOFTWARE,
# FIRMWARE, VHDL, etc) IS PROVIDED BY THE AUTHOR AND WASHINGTON UNIVERSITY 
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR WASHINGTON UNIVERSITY 
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS INTELLECTUAL PROPERTY, EVEN IF 
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""This script manages EC2 instances.

Assumptions
  AWS credentials are stored in environment variables : 
      AWS_ACCESS_KEY_ID:  AWS Access Key ID
      AWS_SECRET_ACCESS_KEY:  AWS Secret Access Key
"""

import logging
from boto import ec2
from os import environ, path, makedirs
from sys import stdout
from time import sleep

# Name of OS user
USER='ubuntu'
# EC2 keypair
try:
    KEYPAIR = environ['EC2_KEYPAIR']
except KeyError:
    KEYPAIR = 'default'
# EC2 security group
SECURITY_GROUPS = ('webserver', )
# EC2 region name (availability zone)
REGION_US_E1 = 'us-east-1' # N. Virginia
# Amazon Machine Image (AMI) 
# 32-bit Ubuntu 10.04 LTS Lucid EBS boot
REGION_US_E1_AMI = 'ami-71dc0b18' 
# Default size of EBS volume in GB (for MySQL)
VOL_SIZE = 10
# Default device to attach volume as
# NOTE renamed to /dev/xvdf on newer Linux versions regardless
VOL_DEVICE = '/dev/sdf' 
# EC2 Metadata tag name
TAG_NAME = 'Name'
# user_data script that runs when instance starts
# NOTE this script runs as root when the instance boots
USER_DATA = """#!/bin/bash
set -e
: # noop
"""


def get_access_key():
    """Return AWS Access Key ID
    Assumptions: 
        AWS_ACCESS_KEY_ID environment variables is set 
    """
    return environ['AWS_ACCESS_KEY_ID']


def get_secret_key():
    """Return AWS Secret Access Key
    Assumptions: 
        AWS_SECRET_ACCESS_KEY environment variables is set 
    """    
    return environ['AWS_SECRET_ACCESS_KEY']


def _ec2connect(region=REGION_US_E1):
    """Return EC2 connection
    Args:
        region: region to connect to
    Assumptions: 
        Environment variables are set: 
            AWS_ACCESS_KEY_ID:  AWS Access Key ID
            AWS_SECRET_ACCESS_KEY:  AWS Secret Access Key
        Alternatively, pass these parameters to ec2.connect_to_region()        
    """
    if region not in _ec2connect.connections:
        _ec2connect.connections[region] = ec2.connect_to_region(region,
                        aws_access_key_id=get_access_key(),
                        aws_secret_access_key=get_secret_key())
    return _ec2connect.connections[region]
_ec2connect.connections = {} # cache ('static' variable)


def _get_filters(tag=None):
    filters = None
    if tag:
        filters = {'tag:{0}'.format(TAG_NAME): tag}
    return filters


def _get_instances(tag=None, instance_ids=None):
    """Return list of instance objects that are running
    Args:
        tag: filter instances where TAG_NAME=tag (optional)
        instance_ids: list of instance ids
    """
    conn = _ec2connect()
    filters = _get_filters(tag)
    rs = conn.get_all_instances(filters=filters, instance_ids=instance_ids)
    # instances may temporarily include recently terminated instances      
    return [i for r in rs for i in r.instances if i.state != u'terminated']


def _get_instance_volumes(instance_id):
    """Return list of volumes attached to instance"""
    conn = _ec2connect()
    vols = [v for v in conn.get_all_volumes() 
            if v.attach_data.instance_id == instance_id]
    return vols


def _wait_for_instances(instances, state=u'running', sleep_time=5.0):
    """Wait for instances' state to change to change state
    Args:
        instances: list of instance objects
        state: instance state to wait for
        sleep_time: poll instances every sleep_time seconds
    """
    # wait for 'running'
    n = len(instances)
    while True:
        stdout.write('.')
        stdout.flush()
        sleep(sleep_time)
        for ins in instances:
            ins.update()
        m = len([ins for ins in instances if ins.state == state])
        if n == m:
            break
    print('\n')


def _wait_for_unattachedvol(volume, sleep_time=5.0):
    """Wait for volume state to change to unattached
    Args:
        volume: boto.ec2.volume object
    """
    state = volume.attachment_state()
    while state is not None:
        stdout.write('.')
        stdout.flush()
        sleep(sleep_time)
        volume.update()
        state = volume.attachment_state()


def run(tag, count=1, type='t1.micro'):
    """Run EC2 instance 
    
    Returns a list of boto.ec2.instance objects.
    
    Args:
      tag: value of the 'name' tag  
      count: number of instances to start
      type: type of instance
    """
    conn = _ec2connect()
    # start instances
    print('Launching {0} {1} ...'.format(count, type))  
    r = conn.run_instances(REGION_US_E1_AMI, 
                    min_count=count,
                    max_count=count,
                    key_name=KEYPAIR,
                    security_groups=SECURITY_GROUPS,
                    user_data=USER_DATA, 
                    instance_type=type)
    # wait for 'running'
    _wait_for_instances(r.instances)
    # tag instances  
    ids = [ins.id for ins in r.instances]
    conn.create_tags(ids, {TAG_NAME: tag})
    for ins in r.instances:
        ins.update() # to print tags
    list_ins(instances=r.instances)
    return r.instances


def get_instances(tag=None):
    """Return list of instance objects that are running"""
    return _get_instances(tag)


def list_ins(tag=None, instances=None):
    """Print information on running instances
    Args:
        instances: list of instance objects that are running
    """
    if instances is None:
        instances = _get_instances(tag)
    if not instances:
        print('\tNo running instances.')
        return
    conn = _ec2connect()
    for ins in instances:
        t = ins.tags.get(TAG_NAME, '')
        d = ins.public_dns_name
        print('\t{0:25} {1:50} {2:15}'.format(t, d, ins.id))


def list_vol(tag=None, device=None):
    """Print information on EBS volumes"""
    conn = _ec2connect()
    vols = conn.get_all_volumes(filters=_get_filters(tag))
    if not vols:
        print('\tNone.')
        return
    for v in vols:
        t = v.tags.get(TAG_NAME, 'root')
        s = v.attachment_state()
        z = v.size
        i = v.attach_data.instance_id
        d = v.attach_data.device
        print('\t{0:25} {1:2}GB {2:15} {3:15} {4} {5}'.format(t, z, v.id, s, i, d ))

def addvol(tag, region, size, snapshot=None):
    """Create an EBS volume to instance
    
    Returns a boto.ec2.volume object.
    
    Args: 
        tag: add tag to volume
        size: size of volume in GB
        snapshot: use snapshot to create volume
    """
    print 'Creating {0}GB volume in {1} ...'.format(size, region)
    conn = _ec2connect()
    vol = conn.create_volume(size, region, snapshot)
    vol.add_tag(TAG_NAME, tag)
    return vol


def attvol(instance_id, volume_id, device=VOL_DEVICE):
    """Create and attach an EBS volume to instance
    Args: 
        instance_id: instance id
        volumne_id: volume id
        device: attach volume as device, e.g. '/dev/sdf' 
    Notes:
        The EBS volume must be in the same location as the instance.
        Not us-east-1, but us-east-1[b|c].
    """
    print 'Attaching {0} to {1} ...'.format(volume_id, instance_id)
    conn = _ec2connect()
    conn.attach_volume(volume_id, instance_id, VOL_DEVICE)


def delvol(volume_id):
    """Delete EBS volume"""
    conn = _ec2connect()
    conn.delete_volume(volume_id)


def getvol(instance_id, device=VOL_DEVICE):
    """Return the volume object mounted as device, otherwise None"""
    vol = None
    for v in _get_instance_volumes(instance_id): 
        if v.attach_data.device == device:
            vol = v
            break
    return vol


def status(tag=None):
    """Print a list of EC2 instance states"""
    instances = _get_instances(tag)
    if not instances:
        print('\tNone.')
        return
    states = {}
    for ins in instances:
        states[ins.state] = states.setdefault(ins.state, 0) + 1
    for state, count in states.iteritems(): 
        print('\t{0} {1}'.format(state, count))


def list(tag=None):
    """Print a list of EC2 instances"""
    print('Instances:')
    list_ins(tag)
    print('\nVolumes:')
    list_vol(tag)


def terminate(tag=None):
    """Terminate instances"""
    print('Terminating instances ...')
    conn = _ec2connect()    
    instances = _get_instances(tag)
    if not instances:
        return
    ids = []
    vols = []
    ips = [ ip.public_ip for ip in conn.get_all_addresses() ] # static ips
    # get list of volumes to delete
    for ins in instances:
        ids.append(ins.id)
        v = getvol(ins.id)
        if v: 
            vols.append(v)
        ip = ins.ip_address
        if ip in ips:
            logging.warning('Elastic IP {0} mapped to {1}.'.format(ip, ins.id))            
    conn.terminate_instances(ids)
    # delete the volumes after trying to terminate instances for two reasons:
    #  1. detaching the volume (before deleting) takes a while and may fail
    #  2. if disableApiTermination=true, instance termination will fail
    _wait_for_instances(instances, state=u'terminated')
    for vol in vols:
        print('Deleting {0} ({1}) ...'.format(vol.id, vol.attach_data.device))
        _wait_for_unattachedvol(vol)
        vol.delete()


def main():
    import optparse
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-c', '--count',
                        dest='count',
                        type='int',
                        metavar='N',
                        default=1,
                        help='number of instances N [default: %default]')
    parser.add_option('-l', '--list',
                        dest='list',
                        default=False,
                        action='store_true',
                        help='print hostnames of running instances')
    parser.add_option('-r',
                        dest='run',
                        default=False,
                        action='store_true',
                        help='run on-demand instances')
    parser.add_option('-t',
                        dest='terminate',
                        default=False,
                        action='store_true',
                        help='terminate instances')
    parser.add_option('-s', '--status',
                        dest='status',
                        default=False,
                        action='store_true',
                        help='print instance states')
    parser.add_option('--region',
                        dest='region',
                        type='string',
                        metavar='REGION',
                        default=REGION_US_E1,
                        help='EC2 region')
    parser.add_option('--tag',
                        dest='tag',
                        type='string',
                        metavar='TAG',
                        help='tag value')                        
    parser.add_option('--type',
                        dest='type',
                        type='string',
                        metavar='TYPE',
                        default='t1.micro',
                        help='instance type TYPE [default: %default]')
    (options, args) = parser.parse_args()
    if options.run:
        try:
            run(options.tag, options.count, options.type)
        except ValueError as msg:
            print('Error: {0}'.format(msg))
    if options.terminate:
        terminate(options.tag)
    elif options.list:
        list(options.tag)
    elif options.status:
        status(options.tag)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()