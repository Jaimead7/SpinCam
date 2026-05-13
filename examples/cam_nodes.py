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
# This example shows a list of the camera nodes.
# 
# The program will show a list of the available cameras.
# Select the camera you want to display the info by it's serial number.
# 
# ================================================================================


from spincam import (get_available_cam_serial_numbers, get_cam_list_repr,
                     get_camera)


def main() -> None:
    print(get_cam_list_repr())
    cam_selected: str = input('Select a camera by serial number: ')

    if not cam_selected in get_available_cam_serial_numbers():
        raise ValueError('Please select a valid serial number.')

    try:
        with get_camera(cam_selected) as cam:
            tree: str = cam.get_nodes_repr()
            print(tree)
    except ValueError as e:
        print(e)


if __name__ == '__main__':
    main()
