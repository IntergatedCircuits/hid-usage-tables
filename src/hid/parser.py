"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
from hid.types import *
import re
import os

class HidParserError(HidUsageError):
    """Failed to parse a line in file"""
    def __init__(self, filepath, line):
        super().__init__('HID usage parsing error in file ' + filename + ' (line="' + line + '")')

def parse_types(typestr):
    """Parses the types string into a list of HidUsageType"""

    # get rid of NAry value range
    typestr = typestr.partition('(')[0]

    # split into list
    typesaslist = typestr.split(',')
    types = list()

    for t in typesaslist:
        # lookup in enum table
        typ = HidUsageType(t)
        types.append(typ)

    return types

def parse_page(filepath, shortname):
    """Parses an HID usage page text file into HidPage"""
    page_regex = re.compile('(?P<id>[0-9a-fA-F]{4}) "(?P<name>.*)"\s*')

    single_usage_regex = re.compile(r'''
        (?P<id>[0-9a-fA-F]{2,8}?)[ ]
        (?P<types>
            [a-zA-Z,]*
            (?:NAry\(
                (?P<values>[0-9a-fA-F,:]+)?
            \))?
        )[ ]
        "(?P<name>.*)"\s*
        ''', re.VERBOSE)

    range_usage_regex = re.compile(r'''
        (?P<id_min>[0-9a-fA-F]{2,8})[:](?P<id_max>[0-9a-fA-F]{2,8})[ ]
        (?P<types>
            [a-zA-Z,]*
            (?:NAry\(
                (?P<values>[0-9a-fA-F,:]+)?
            \))?
        )[ ]
        "(?P<name>.*)"\s*
        ''', re.VERBOSE)

    # TODO make use of this
    int_usage_switch_regex = re.compile(r'''
        (?P<id_mask_higher>[*]*)(?P<id_prefix>[0-9a-fA-F]{1,3})(?P<id_mask_lower>[*]*)[ ]
        (?P<types>IUS)[ ]
        "(?P<name>.*)"\s*
        ''', re.VERBOSE)

    page = None
    file = open(filepath, 'r')
    try:
        # first line is the id and name of the page
        line = file.readline()
        match = page_regex.fullmatch(line)
        if match == None:
            raise HidParserError(filepath, line)

        # create this page
        page = HidPage(int(match.group('id'), 16), shortname, match.group('name'))

        # read the usages by lines
        while True:
            line = file.readline()
            if not line: # eof
                break
            if line.isspace(): # empty lines indicate gaps in usage IDs
                continue

            # try to identify as single usage
            match = single_usage_regex.fullmatch(line)
            if match != None:
                types = parse_types(match.group('types'))
                id = int(match.group('id'), 16)
                if id > 0xffff:
                    # Sel values that aren't mapped to valid usage ID
                    # TODO: store them in a separate container, generate separate enums
                    continue

                usage = HidUsage(match.group('name'), types, id)
                page.add(usage)
                continue

            # try to identify as range usage
            match = range_usage_regex.fullmatch(line)
            if match != None:
                types = parse_types(match.group('types'))
                id_min = int(match.group('id_min'), 16)
                id_max = int(match.group('id_max'), 16)
                usage = HidUsageRange(match.group('name'), types, id_min, id_max)
                page.add(usage)
                continue

            # in-id usage switch
            match = int_usage_switch_regex.fullmatch(line)
            if match != None:
                # TODO: create usage primitive specialization
                continue

            #unknown field
            raise HidParserError(filepath, line)

    finally:
        file.close()

    return page

def parse_database(pages_path=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../pages'))):
    """Parse all HID page files on the path"""
    filename_regex = re.compile('(?P<id>[0-9a-fA-F]{4})\-(?P<name>[a-zA-Z0-9_\-]*)\.txt')

    hid_pages = list()
    for filename in os.listdir(pages_path):
        match = filename_regex.fullmatch(filename)
        if (match == None):
            print('File "' + filename + '" not recognized as HID page document')
            continue
        try:
            page = parse_page(os.path.join(pages_path, filename), match.group('name'))
            hid_pages.append(page)
        except HidParserError as ex:
            print(ex)
            continue

    return hid_pages