<div align="center">
    <h1>SpinCam - <i>A PySpin wrapper</i></h1>
    <a href="https://github.com/Jaimead7/SpinCam/blob/main/LICENSE"><img src="https://img.shields.io/static/v1.svg?label=LICENSE&message=MIT&color=2dba4e&colorA=2b3137"></a>
    <a href="https://pypi.org/project/jaimead7-spincam/"><img src="https://img.shields.io/pypi/v/jaimead7-spincam.svg?color=2dba4e"></a>
</div>

This is a ***Python*** wrapper for [***PySpin***](https://www.teledynevisionsolutions.com/support/support-center/technical-guidance/iis/installing-pyspin-for-the-spinnaker-sdk/).  
***PySpin*** is the python library for the [***Spinnaker SDK***](https://www.teledynevisionsolutions.com/products/spinnaker-sdk) from [***Teledyne***](https://www.teledynevisionsolutions.com/).  
This SDK allows you to connect to ***Teledyne*** cameras.  
This repo includes some tools to create a ***Docker*** image with the ***Spinnaker SDK***.  
Check the [Create Docker Container](docs/create_docker_container.md) file.  

## Authors
> **Jaime Álvarez Díaz**  
> [![email](https://img.shields.io/static/v1.svg?label=Gmail&message=alvarez.diaz.jaime1@gmail.com&logo=gmail&color=2dba4e&logoColor=white&colorA=c71610)](mailto:alvarez.diaz.jaime1@gmail.com)  
[![GitHub Profile](https://img.shields.io/static/v1.svg?label=GitHub&message=Jaimead7&logo=github&color=2dba4e&colorA=2b3137)](https://github.com/Jaimead7)  


## Installation  
- Go to the ***Spinnaker SDK*** and ***PySpin*** [download page](https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/) and download both packages (It may require a login).  
- Follow the [installing instructions](https://www.teledynevisionsolutions.com/support/support-center/technical-guidance/iis/installing-pyspin-for-the-spinnaker-sdk/) for the SDK and ***PySpin***.  
- It is recommended to install ***PySpin*** on a ***Python*** environment.  
- Install ***SpinCam***:
```
py -m pip install jaimead7-spincam
```

## Usage  
See ***[examples](./examples/)***.  
The wrapper is based on the `get_sys` contextmanager.  
The contextmanager will manage the release of the pointer objects.  
This context manager returns a `System` object.  
This `System` object has all the functionality needed to manage cameras and interfaces.  
Check the classes architecture in ***[System API](./docs/schemas.dio)*** schema.  
```python
from spincam import get_sys

with get_sys() as sys:
    ...
```

### Logging
The module use a custom logging system.  
This is based the `spincam_logger` object.  
The file path can be absolute or relative.  
If it is relative, the module will search for `LOGS_PATH` in the environment variables.  
The `LOGS_PATH` will be used as the base route for relative paths.  
If `LOGS_PATH` is not found, it will use the system temp path.  
> For windows it will search for `TEMP` or `TMP` environment variables or the current directory.  
> For other systems it will use `/tmp` path.  
```python
import logging
from pathlib import Path

from spincam import spincam_logger

spincam_logger.level = logging.WARNING
spincam_logger.logs_file_path = Path('<logger_file_path>')
spincam_logger.save_logs = True
```

## License  
This project is licensed under the [MIT](./LICENSE) license.  


## Contributing  
Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.  