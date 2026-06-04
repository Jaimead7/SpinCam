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
# This example shows how to use the system callbacks.
# 
# The callback API use threading for "async" behaviour.
# Callbacks are created as daemons, so callbacks may not finish when the
# programm is closed.
# 
# To exit press Ctr+C.
# 
# ================================================================================


from random import randint
from time import sleep, time
from typing import Any

import cv2
import numpy as np

from spincam import (Camera, FuncResult, Iface, NodeCallbackFunc, NodePtr,
                     System, get_sys)


def callback_func(node_ptr: NodePtr) -> FuncResult:
    print(f'"{node_ptr.display_name}" node callback execution...')
    wait_time: int = randint(1, 5)
    start: float = time()
    sleep(wait_time)
    end: float = time()
    print(f'"{node_ptr.display_name}" node callback executed in {end - start:.2f}s, expected {wait_time}s.')
    return FuncResult.SUCCESS

nodes_default_values: dict[str, Any] = {
    'App.Root.acquisitionTransferControl.AcquisitionMode': 'Continuous',
    'Stream.Root.StreamInformation.StreamMode': 'TeledyneGigeVision',
    'Stream.Root.BufferHandlingControl.StreamBufferHandlingMode': 'NewestOnly',
    'Stream.Root.BufferHandlingControl.StreamBufferCountManual': 3,
    'App.Root.DigitalIOControl.TriggerSelector': 'FrameStart',
    'App.Root.DigitalIOControl.TriggerMode': 'On',
    'App.Root.DigitalIOControl.TriggerSource': 'Software',
    'App.Root.deviceEventControl.EventSelector': 'ValidFrameTrigger',
    'App.Root.deviceEventControl.EventNotification': 'On'
}

node_callbacks: dict[str, NodeCallbackFunc] = {
    'App.Root.deviceSensorControl.Gain': callback_func,
    'App.Root.deviceEventControl.EventControl.EventValidFrameTriggerData.EventValidFrameTrigger': callback_func,
}

def cam_arrival(iface: Iface, cam: Camera) -> FuncResult:
    print(f'{cam.name} connected to {iface}.')
    try:
        window_name: str = f'Camera: {cam}'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cam.stop_acq()
        cam.update_nodes_default_values(nodes_default_values)
        cam.set_nodes_default_values()
        for route, func in node_callbacks.items():
            cam.register_node_callback(route, func)
        cam.start_acq()
        exit = False
        while True:
            print('Executing trigger...')
            cam.execute_node('App.Root.DigitalIOControl.TriggerSoftware')
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
    finally:
        cv2.destroyAllWindows()
    return FuncResult.SUCCESS

def cam_removal(iface: Iface, cam: Camera) -> FuncResult:
    print(f'{cam.name} removed from {iface}.')
    return FuncResult.SUCCESS

def iface_arrival(sys: System, iface: Iface) -> FuncResult:
    print(f'{iface.name} connected.')
    iface.register_iface_events(
        device_arrival_callback= cam_arrival,
        device_removal_callback= cam_removal
    )
    return FuncResult.SUCCESS

def iface_removal(sys: System, iface: Iface) -> FuncResult:
    print(f'{iface.name} removed.')
    return FuncResult.SUCCESS

def main() -> None:
    with get_sys() as system:
        system.register_sys_events(
            iface_arrival_callback= iface_arrival,
            iface_removal_callback= iface_removal,
        )
        system.register_iface_events(
            device_arrival_callback= cam_arrival,
            device_removal_callback= cam_removal
        )
        try:
            input('\nProgram running...\n')
        except KeyboardInterrupt:
            print('\nStopping program...')


if __name__ == "__main__":
    main()
