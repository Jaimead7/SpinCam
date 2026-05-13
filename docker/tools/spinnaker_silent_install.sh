#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Invalid arguments."
    echo "usage: spinnaker_silent_install.sh <.tar.gz>"
    exit 1
fi

spinnaker_tar="$1"

if [ ! -e "$spinnaker_tar" ]; then
    echo "Invalid file. File doesn't exists."
    exit 1
fi

if [[ ! "$spinnaker_tar" == *.tar.gz ]]; then
    echo "Invalid file. File must be a .tar.gz file."
    exit 1
fi

spinnaker_folder=$(dirname "$spinnaker_tar")

echo "Unpacking sdk..."
tar -xzf $spinnaker_tar -C $spinnaker_folder
libs_folder=$spinnaker_folder/spinnaker-*-amd64

echo "Auto-complete ui questions..."
echo "libgentl libspinnaker/accepted-flir-eula boolean true" | debconf-set-selections
# This seams to not work outside a container.
# libgentl force the analytics-consent on the preinst script.
echo "libgentl libspinnaker/analytics-consent boolean false" | debconf-set-selections

echo "Installing Spinnaker packages..."
# Uncomment any package you need for your container.
# To run SpinCam only libgentl and libspinnaker are needed.
# Essential packages
dpkg -i $libs_folder/libgentl_*.deb  # GenTL transport layer interface
dpkg -i $libs_folder/libspinnaker_*.deb  # C++ library
dpkg -i $libs_folder/libspinvideo_*.deb  # Video functionality
dpkg -i $libs_folder/spinupdate_*.deb  # Firmware update CLI tool
# Optional
# dpkg -i $libs_folder/libspinnaker-c_*.deb  # C library
# dpkg -i $libs_folder/libspinvideo-c_*.deb  # Video functionality for C
# dpkg -i $libs_folder/libspinnaker-dev_*.deb  # C++ dev files
# dpkg -i $libs_folder/libspinnaker-c-dev_*.deb  # C dev files
# dpkg -i $libs_folder/libspinvideo-dev_*.deb  # Video functionality dev files
# dpkg -i $libs_folder/libspinvideo-c-dev_*.deb  # Video functionality dev files for C
# apt-get install -y $libs_folder/spinview-qt_*.deb  # SpinView app
# dpkg -i $libs_folder/spinview-qt-dev_*.deb  # SpinView dev tools
# dpkg -i $libs_folder/spinnaker-doc_*.deb # Documentation files
# dpkg -i $libs_folder/spinupdate-dev_*.deb  # Firmware update CLI tool dev tools
# Checks
# dpkg -i $libs_folder/spinnaker_*.deb  # Metapackage of the SDK. Needs libspinnaker, libspinnaker-c, libspinvideo, libspinvideo-c. It contains PySpin examples.

# For configuring udev rules for USB cameras uncomment these lines.
# Change the user names, user group and rules as it fits your docker config.
# usage: config_udev_silent.sh <groupname> <usr1> [usr2 usr3 ...]
echo "Launching udev configuration script..."
sh config_udev_silent.sh spinnaker root

# For configuring usb USB-FS memory size to 1000 MB at startup (via /etc/rc.local) uncomment these lines.
echo "Launching USB-FS configuration script..."
sh config_usbfs_silent.sh

# Configure paths to the Spinnaker_GenTL.cti
echo "Launching GenTL configuration script..."
sh config_gentl_silent.sh 64

# Exit
echo "Installation complete. You will need to reboot your system for all changes to take effect"

exit 0