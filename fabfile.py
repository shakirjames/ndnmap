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
"""This script deploys a Django application on Amazon EC2."""

import os
from deploy import ec2
from fabric.api import *
from fabric.utils import abort
from fabric.contrib.console import confirm
from settings import AWS_STORAGE_BUCKET_NAME


# Application name (used for EC2 tag prefix)
APP_NAME = 'ndnmap' 
# Name of application user to create (with restricted privilages)
APP_USER = APP_NAME
# Project path on server
APP_DIR = '/home/{0}/{1}'.format(APP_USER, APP_NAME)
# URL of git, remote repos (read-only)
APP_GIT_REPO = 'git://github.com/shakfu/{0}.git'.format(APP_NAME)
# Name of system user with sudo privilages
ADMIN_USER = ec2.USER
# EBS volume device (for database)
VOL_DEVICE = ec2.VOL_DEVICE
# Mount point for EBS volume
VOL_MOUNT = '/vol'
# Volume size in GB
VOL_SIZE = 10
# EC2 instance type
EC2_TYPE = 'm1.small'
#EC2_TYPE = 't1.micro'
# Database password
DB_PASS = 'nduffNft'
# SiteName for Apache
SITE_NAME = 'example.com'
# Static URL prefix for Django
STATIC_URL = 'http://s3.amazonaws.com/{0}'.format(AWS_STORAGE_BUCKET_NAME)
# Initial data
INITIAL_DATA = '{0}/deploy/initial_data.json'.format(APP_DIR)
# Instance Tag
TAG = APP_NAME


# fabric environment settings
env.tag_ins = TAG
env.tag_vol = '{0} database'.format(TAG) # database volume tag
env.hosts = [ins.public_dns_name for ins in ec2.get_instances(TAG)] # hosts list
env.user = ADMIN_USER


def start(volsize=VOL_SIZE):
    """Start a new instance
    Args:
        volsize: size (GB) of new EBS volume to attach to the instance
    """
    instances = ec2.run(env.tag_ins, count=1, type=EC2_TYPE)
    ins = instances[0]
    vol = ec2.addvol(env.tag_vol, ins.placement, volsize)
    ec2.attvol(ins.id, vol.id)


def kill():
    """Terminate instances"""
    ec2.terminate(TAG)


def ls():
    """Print a list of instances"""
    tag_ins = env.get('tag_ins', None)
    tag_vol = env.get('tag_vol', None)
    print 'Instances:'
    ec2.list_ins(tag_ins)
    print 'Volumes:'
    ec2.list_vol(tag_vol)


def install_database():
    """Install MySQL"""
    # upload install scripts
    put('deploy/install_mysql_ebs.sh','/usr/sbin/install_mysql', 
        mode=0755, use_sudo=True)
    put('deploy/init_app_db.sh', '/usr/sbin/init_app_db',
        mode=0755, use_sudo=True)
    # run scripts
    sudo('install_mysql {0} {1}'.format(VOL_DEVICE, VOL_MOUNT))
    sudo('init_app_db -d {n} -u {n} -p {p}'.format(n=APP_NAME, p=DB_PASS))
    # set the root password (used in backup)
    run('mysqladmin -u root password {0}'.format(DB_PASS))


def install_django():
    """Install Apache, Python, and Django app"""
    put('deploy/install_django.sh','/usr/sbin/install_django', 
        mode=0755, use_sudo=True)
    args = '-n {n} -w {w} -s {s} -P {P} -g {g} -u {u} -p {p} -f {f}'.format(
            n=APP_NAME,
            w=SITE_NAME,
            s=STATIC_URL,
            P=DB_PASS,
            g=APP_GIT_REPO,
            u=APP_USER,
            p=APP_DIR,
            f=INITIAL_DATA)
    sudo('install_django {0}'.format(args))


def deploy_static():
    """Upload static files to S3"""
    local('python manage.py collectstatic --noinput')


def test():
    """Run unit tests"""
    with settings(warn_only=True):
        result = local('python manage.py test gmap', capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")

def reset():
    """Reset the app database"""
    virtual_env = '/home/{0}/env'.format(APP_USER)
    run('{0}/bin/python manage.py reset gmap --noinput'.format(virtual_env))


def push(tag=None, static=False):
    """Update application"""
    # push code to repo
    local('git push origin')
    with cd(APP_DIR):
        sudo('git pull', user=APP_USER)
        sudo('touch deploy/app.wsgi', user=APP_USER)


def deploy():
    """Deploy a LAMP stack"""
    test()
    deploy_static()
    install_database()
    install_django()
