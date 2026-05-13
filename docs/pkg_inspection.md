# Package inspection
Utils used to create the [***Spinnaker*** silent install scripts](../docker/tools/) to install ***Spinnaker SKD*** in silent mode for a ***Docker*** container.

### Check package name
```bash
sudo dpkg -f *.deb Package
```

### Extract control files
```bash
dpkg --control *.deb <folder>
```
### Extract package files
```bash
dpkg-deb -x <package>.deb <folder>  # Extract files
dpkg-deb -e <package>.deb <folder>  # Extract control info
```

### List all the questions
```bash
cat <extract folder> | grep -A 3 "Template: "
```

### Configure default answares
```bash
# One line for each question
echo "<lib name> <question name> <type> <default value>" | sudo debconf-set-selections
```

### Check if rule is ok
```bash
sudo apt install debconf-utils
debconf-get-selections | grep "<package>"
```

### Install package
```bash
sudo dpkg -i <package>.deb
```

### Check package
```bash
dpkg -l | grep <package>
```