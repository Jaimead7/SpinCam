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
# This example shows how to use the node callbacks.
# 
# The callback API use threading for "async" behaviour.
# Callbacks are created as daemons, so data may be lost when the programm
# is closed.
# Callbacks seems to work only for nodes changed by the program.
# 
# The program will show a list of the available cameras.
# Select the camera you want to display by it's serial number.
# 
# To exit press Esc.
# To show next image, press SpaceBar.
# Hold the SpaceBar to simulate a streaming.
# 
# ================================================================================


from random import randint
from time import sleep, time
from typing import Any

import cv2
import numpy as np

from spincam import (CamConfigStep, Camera, FuncResult, Node, NodeCallbackFunc,
                     get_cam_list_repr, get_sys)


#---------- CAMERA STREAM ----------#
def cam_streaming(cam: Camera) -> None:
    try:
        window_name: str = f'Camera: {cam}'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cam.set_config_seq(config_seq)
        cam.update_nodes_default_values(nodes_default_values)
        cam.set_nodes_default_values()
        cam.execute_config_seq()
        cam.start_acq()
        for route, callback in node_callbacks.items():
            cam.register_node_callback(
                route= route,
                callback= callback
            )
        exit = False
        while True:
            cam.set_node_value(
                'App.Root.deviceSensorControl.Gain',
                2
            )
            print('Executing trigger...')
            cam.execute_node('App.Root.DigitalIOControl.TriggerSoftware')
            ret: FuncResult
            value: float
            ret, value = cam.get_node_value('App.Root.deviceCounterAndTimerControl.counterValue')
            print(f'Counter from main: {value}')
            ret, value = cam.get_node_value('App.Root.deviceSensorControl.Gain')
            print(f'Gain from main: {value}')
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
    except ValueError:
        pass
    except RuntimeError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        cam.unregister_all_node_callbacks()
        cv2.destroyAllWindows()
        print(f'{cam} stream closed.')

#---------- CALLBAKCS ----------#
def callback_func(node: Node) -> FuncResult:
    print(f'{node.parent}: "{node.display_name}" node callback execution...')
    wait_time: int = randint(1, 5)
    start: float = time()
    sleep(wait_time)
    end: float = time()
    print(f'{node.parent}: "{node.display_name}" node callback executed in {end - start:.4f}s, expected {wait_time}s.')
    return FuncResult.SUCCESS

#---------- CONFIG ----------#
nodes_default_values: dict[str, Any] = {
    'App.Root.acquisitionTransferControl.AcquisitionMode': 'Continuous',
    'Stream.Root.StreamInformation.StreamMode': 'TeledyneGigeVision',
    'Stream.Root.BufferHandlingControl.StreamBufferHandlingMode': 'NewestOnly',
    'Stream.Root.BufferHandlingControl.StreamBufferCountManual': 3,
    'App.Root.DigitalIOControl.TriggerSelector': 'FrameStart'
}

config_seq: list[CamConfigStep] = [
    CamConfigStep(step= 1, route= 'App.Root.DigitalIOControl.TriggerMode', value= 'On'),
    CamConfigStep(step= 2, route= 'App.Root.DigitalIOControl.TriggerSource', value= 'Line1'),
    CamConfigStep(step= 3, route= 'App.Root.deviceCounterAndTimerControl.counterSelector', value= 'Counter1'),
    CamConfigStep(step= 4, route= 'App.Root.deviceCounterAndTimerControl.counterMode', value= 'Off'),
    CamConfigStep(step= 5, route= 'App.Root.deviceCounterAndTimerControl.counterStartSource', value= 'AcquisitionStart'),
    CamConfigStep(step= 6, route= 'App.Root.deviceCounterAndTimerControl.counterIncrementalSource', value= 'ValidFrameTrigger'),
    CamConfigStep(step= 7, route= 'App.Root.deviceCounterAndTimerControl.counterResetSource', value= 'Off'),
    CamConfigStep(step= 8, route= 'App.Root.deviceCounterAndTimerControl.counterDuration', value= 1),
    CamConfigStep(step= 9, route= 'App.Root.deviceCounterAndTimerControl.counterMode', value= 'Active'),
    CamConfigStep(step= 10, route= 'App.Root.deviceEventControl.EventSelector', value= 'ValidFrameTrigger'),
    CamConfigStep(step= 11, route= 'App.Root.deviceEventControl.EventNotification', value= 'On'),
    CamConfigStep(step= 12, route= 'App.Root.deviceEventControl.EventSelector', value= 'InvalidFrameTrigger'),
    CamConfigStep(step= 13, route= 'App.Root.deviceEventControl.EventNotification', value= 'On'),
]

node_callbacks: dict[str, NodeCallbackFunc] = {
    'App.Root.deviceEventControl.EventControl.EventValidFrameTriggerData.EventValidFrameTrigger': callback_func,
    'App.Root.deviceSensorControl.Gain': callback_func,
    'App.Root.deviceCounterAndTimerControl.counterValue': callback_func,  # This callback will not work, but the counter is working.
}

#---------- MAIN ----------#
def main() -> None:
    with get_sys() as sys:
        print(get_cam_list_repr(sys.cams))
        cam_selected: str = input('Select a camera by serial number: ')
        if cam_selected not in sys.cams_serial_numbers:
            raise ValueError('Please select a valid serial number.')
        cam: Camera | None = sys.get_cam_by_serial_number(cam_selected)
        if cam is None:
            raise ValueError(f'Error getting "{cam_selected}" camera.')
        cam_streaming(cam)


if __name__ == '__main__':
    main()
