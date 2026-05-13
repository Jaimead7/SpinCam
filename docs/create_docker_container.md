# Create ***Docker*** container with Spinnaker and ***PySpin***

## Download Sinnaker SDK and PySpin  
- Go to the ***Spinnaker SDK*** and ***PySpin*** [download page](https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/) and download both packages (It may require a login).  
> Dowload the Ubuntu 22.04 and Python 3.10 versions for your system.  
> For other versions you may need to change the [Dockerfile](../docker/Dockerfile) base image or ***Python*** version.  
> [spinnaker_silent_install.sh](../docker/tools/spinnaker_silent_install.sh) it was tested only on Ubuntu 22.04 - 64-bit. Other versions may fail.  
- Copy the `.tar.gz` files in the [docker/packages](../docker/packages/) folder.  
> Use `pyspin.tar.gz` name for the ***PySpin*** file.  
> Use `spinnaker-sdk.tar.gz` name for the ***Spinnaker*** file.  
> For other names change the [Dockerfile](../docker/Dockerfile).  

## Configure the [spinnaker_silent_install.sh](../docker/tools/spinnaker_silent_install.sh) script  
This script is configured to install a minimal version of ***Spinnaker*** and ***PySpin*** to run ***SpinCam***.  
Follow the comments in the scripts in order to install more features.  
The scripts are based on the installation scripts provided by ***Spinnaker***.  

## Copy the [docker](../docker/) folder
Copy all the files of the [docker](../docker/) folder to your project repository.  

## Check the [.dockerignore](../docker/.dockerignore)
Check the content of the [.dockerignore](../docker/.dockerignore) file and change it to you needs.  

## Adjust Dockerfile
Adjust the [Dockerfile](../docker/Dockerfile) final content to your application needs.  
- On the pyspin-installer stage, set your python dependencies.  
- On the builder stage, copy the files of your project.  
- On the production stage, select your entrypoint.  