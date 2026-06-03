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
# Callbacks are created as daemons, so data may be lost when the programm
# is closed.
# 
# To exit press Ctr+C.
# 
# ================================================================================


from spincam import Camera, FuncResult, Iface, System, get_sys


def cam_arrival(cam: Camera) -> FuncResult:
    print(f'"{cam.name}" connected.')
    return FuncResult.SUCCESS

def cam_removal(cam: Camera) -> FuncResult:
    print(f'"{cam.name}" removed.')
    return FuncResult.SUCCESS

def iface_arrival(sys: System, iface: Iface) -> FuncResult:
    print(f'"{iface.name}" connected.')
    iface.register_device_events(
        device_arrival_callback= cam_arrival,
        device_removal_callback= cam_removal
    )
    return FuncResult.SUCCESS

def iface_removal(sys: System, iface: Iface) -> FuncResult:
    print(f'"{iface.name}" removed.')
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
