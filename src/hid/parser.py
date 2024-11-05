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
import json

class HidParserError(HidUsageError):
    """Failed to parse a line in file"""
    def __init__(self, filepath=None, line=None, page=None):
        if (filepath is not None):
            super().__init__('HID usage parsing error in file ' + filepath + ' (line="' + line + '")')
        else:
            super().__init__('HID usage parsing error in page ' + page.name())

def parse_types(typestr):
    """Parses the types string into a list of HidUsageType"""

    # get rid of NAry value range
    typestr = typestr.partition('(')[0]

    # split into list
    typesaslist = typestr.split(',')

    # lookup in enum table
    return [HidUsageType(t) for t in typesaslist]

def parse_page(filepath, shortname):
    """Parses an HID usage page text file into HidPage"""
    page_regex = re.compile(r'(?P<id>[0-9a-fA-F]{4}) "(?P<name>.*)"\s*')

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
    with open(filepath, mode='rt', encoding='utf-8') as file:
        # first line is the id and name of the page
        line = file.readline()
        match = page_regex.fullmatch(line)
        if match == None:
            raise HidParserError(filepath=filepath, line=line)

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
            raise HidParserError(filepath=filepath, line=line)

    return page

def local_database_path():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../pages'))

def parse_database(pages_path=local_database_path()):
    """Parse all HID page files on the path"""
    filename_regex = re.compile(r'(?P<id>[0-9a-fA-F]{4})\-(?P<name>[a-zA-Z0-9_\-]*)\.txt')

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

def parse_json_page(page_obj):
    """Parse an HID usage page from USB.org/HID document JSON format usage page object."""

    # create this page
    name = page_obj['Name']
    page = HidPage(page_obj['Id'], name, name)

    if page_obj['Kind'] == 'Defined':
        # single IDs
        for usage_obj in page_obj['UsageIds']:
            types = [HidUsageType(t) for t in usage_obj['Kinds']]
            id = usage_obj['Id']
            usage = HidUsage(usage_obj['Name'], types, id)
            page.add(usage)
    elif page_obj['Kind'] == 'Generated':
        # full range
        gen_obj = page_obj['UsageIdGenerator']
        types = [HidUsageType(t) for t in gen_obj['Kinds']]
        id_min = gen_obj['StartUsageId']
        id_max = gen_obj['EndUsageId']
        usage = HidUsageRange(gen_obj['NamePrefix'], types, id_min, id_max)
        page.add(usage)
    else:
        #unknown
        raise HidParserError(page=page)

    return page

def parse_json(json_path):
    """Parse HID usages from USB.org/HID document JSON attachment."""

    hid_pages = list()

    with open(json_path, mode='rt', encoding='utf-8') as file:
        data = json.load(file)

        for usage_page in data['UsagePages']:
            try:
                page = parse_json_page(usage_page)
                hid_pages.append(page)
            except HidParserError as ex:
                print(ex)
                continue

    return hid_pages
