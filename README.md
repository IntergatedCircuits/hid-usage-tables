# HID usage tables database

This repository contains the [HID usage tables][HUT] in a machine-readable format (under `pages`),
and accompanying Python3 scripts (under `src`) to parse them into a database,
and generate code for different programming languages.

## Supported formats

* C++ (to be used with [hid-rp][hid-rp])

Additional languages can be easily added by taking `src/hid/codegen/cpp.py` as a template.

[HUT]: https://www.usb.org/sites/default/files/hut1_22.pdf
[hid-rp]: https://github.com/IntergatedCircuits/hid-rp
