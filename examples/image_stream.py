# MIT License

# Copyright (c) 2026 Jaime Álvarez Díaz
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# ================================================================================
# 
# This example shows how to acquire images from a camera.
# 
# Configure the the camera options by changing the nodes_data dict.
# This dictionary must contain key, value pairs with:
#   • key: str = Complete route of the node. You can use CAM_NODE_ROUTES.
#   • value: Any --> The default value of the node.
# 
# The program will show a list of the available cameras.
# Select the camera you want to display by it's serial number.
# 
# To exit press Esc.
# To show next image, press SpaceBar.
# Hold the SpaceBar to simulate a streaming.
# 
# ================================================================================


from typing import Any

import cv2
import numpy as np

from spincam import Camera, get_cam_list_repr, get_sys

nodes_default_values: dict[str, Any] = {
    'App.Root.acquisitionTransferControl.AcquisitionMode': 'Continuous',
    'Stream.Root.StreamInformation.StreamMode': 'TeledyneGigeVision',
    'Stream.Root.BufferHandlingControl.StreamBufferHandlingMode': 'OldestFirst',
    'Stream.Root.BufferHandlingControl.StreamBufferCountManual': 3,
    'App.Root.DigitalIOControl.TriggerSelector': 'FrameStart',
    'App.Root.DigitalIOControl.TriggerMode': 'Off',
}


def main() -> None:
    try:
        with get_sys() as sys:
            print(get_cam_list_repr(sys.cams))
            cam_selected: str = input('Select a camera by serial number: ')
            if cam_selected not in sys.cams_serial_numbers:
                raise ValueError('Please select a valid serial number.')
            cam: Camera | None = sys.get_cam_by_serial_number(cam_selected)
            if cam is None:
                raise ValueError(f'Error getting "{cam_selected}" camera.')
            window_name: str = f'Camera: {cam_selected}'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cam.update_nodes_default_values(nodes_default_values).set_nodes_default_values()
            cam.start_acq()
            exit = False
            while True:
                img: np.ndarray | None = cam.get_last_img()
                if img is None:
                    exit = True
                    break
                cv2.imshow(window_name, img)
                key: int = -1
                while key == -1:
                    key = cv2.waitKey(1)
                    if key == 27:
                        break
                    elif key == 32:
                        break
                if key == 27 or exit:
                    break
    except ValueError as e:
        print(e)
    except RuntimeError as e:
        print(e)
    except KeyboardInterrupt:
        print('\nStopping program...')
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
