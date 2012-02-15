#!/bin/sh
# This script installs a MySQL database server that uses an EBS volume.
#
# Author: Shakir James <shak@shakfu.com>
# Based on Eric Hammond's article "Running MySQL on Amazon EC2 with EBS."


VOLUME=$1
MOUNT=$2 # mount point

if [ -z $VOLUME ]; then
    echo "You must specify the volume such as /dev/sdf"
    exit 1;
fi

if [ -z $MOUNT ]; then 
    echo "You must specify the mount point such as /vol"
    exit 2;
fi


# update system
sudo apt-get update
sudo apt-get upgrade -y

# install MySQL (unattended) with *blank* root password
sudo DEBIAN_FRONTEND=noninteractive aptitude install -y mysql-server

# install xfs
sudo apt-get install -y xfsprogs
# formate vol as xfs
grep -q xfs /proc/filesystems || sudo modprobe xfs
sudo mkfs.xfs $VOLUME
# mount it
echo "$VOLUME $MOUNT xfs noatime 0 0" | sudo tee -a /etc/fstab
sudo mkdir -m 000 $MOUNT
sudo mount $MOUNT
# stop mysql
sudo service mysql stop
# move mysql directories to volume
sudo mkdir $MOUNT/etc $MOUNT/lib $MOUNT/log
sudo mv /etc/mysql     $MOUNT/etc/
sudo mv /var/lib/mysql $MOUNT/lib/
sudo mv /var/log/mysql $MOUNT/log/
# bind mount mysql directories in original location
sudo mkdir /etc/mysql
sudo mkdir /var/lib/mysql
sudo mkdir /var/log/mysql

echo "$MOUNT/etc/mysql /etc/mysql     none bind" | sudo tee -a /etc/fstab
sudo mount /etc/mysql

echo "$MOUNT/lib/mysql /var/lib/mysql none bind" | sudo tee -a /etc/fstab
sudo mount /var/lib/mysql

echo "$MOUNT/log/mysql /var/log/mysql none bind" | sudo tee -a /etc/fstab
sudo mount /var/log/mysql

# start mysql running on ebs vol
sudo service mysql start
echo "*** Done. Mysql is now running on EBS backed volume at $VOLUME ***"
