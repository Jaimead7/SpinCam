#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Invalid arguments"
    echo "usage: config_udev_silent.sh <groupname> <usr1> [usr2 usr3 ...]"
    exit 1
fi

grpname="$1"
shift
usrnames("$@")

echo "Creating $grpname group..."
groupadd -f $grpname

for usrname in "${usrnames[@]}"; do
    if (getent passwd $usrname > /dev/null)
    then
        echo "Adding user $usrname to group $grpname group."
        usermod -a -G $grpname $usrname
        echo "Added user $usrname to group $grpname."
    else
        echo "User "\""$usrname"\"" does not exist"
    fi
done

echo "Writing the udev rules file...";
UdevFile="/etc/udev/rules.d/40-flir-spinnaker.rules"
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"1e10\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"1724\", GROUP=\"$grpname\"" 1>>$UdevFile

echo "Restarting de udev deamon..."
systemctl restart systemd-udevd.service

exit 0
