"""
author:  Benedek Kupper
date:    2025
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import re

def str_to_identifier(name):
    """Converts any string to a valid identifier in programming languages."""
    # replace all non-supported characters with whitespace
    iden = re.sub(r'[^a-zA-Z0-9]', ' ', name)
    # replace any section of whitespaces with underscores
    iden = re.sub(r'[\s]+', '_', iden)
    # remove leading and trailing underscores
    iden = iden.strip('_')
    if len(iden) == 0:
        # nothing meaningful is left
        return None

    # convert to uppercase
    iden = iden.upper()

    if iden[0].isdigit():
        # digits are not allowed as the first character
        iden = '_' + iden
    return iden

def escape_str(string):
    """Escapes a string for C++."""
    # escape all backslashes with backslash
    # escape all double quotes with backslash
    return string.replace('\\', '\\\\').replace('"', '\\"')
