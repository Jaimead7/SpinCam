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
# This example shows a list of the interface nodes.
# 
# The program will show a list of the available interfaces.
# Select the interface you want to display the info by it's ID number.
# 
# ================================================================================


from spincam import Iface, get_iface_list_repr, get_sys


def main() -> None:
    try:
        with get_sys() as sys:
            print(get_iface_list_repr(sys.ifaces))
            iface_selected: str = input('Select an interface by id: ')
            if iface_selected not in sys.ifaces_ids:
                raise ValueError('Please select a valid id.')
            iface: Iface | None = sys.get_iface_by_id(iface_selected)
            if iface is None:
                raise ValueError(f'Error getting "{iface_selected}" interface.')
            tree: str = iface.get_nodes_repr()
            print(tree)
    except ValueError as e:
        print(e)
    except RuntimeError as e:
        print(e)
    except KeyboardInterrupt:
        print('\nStopping program...')


if __name__ == '__main__':
    main()
