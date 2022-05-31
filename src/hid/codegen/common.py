"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import re
from abc import ABCMeta, abstractmethod
import unicodedata # name()

class CodeGenerator(metaclass=ABCMeta):
    """Abstract class for code generation."""

    @classmethod
    def sub_spec_chars(cls, name):
        """ Find list of special characters at the beginning and end of the name
        (followed by whitespace), and replace those with their whitespace-separated
        unicodedata.name() equivalent"""

        spec_chars_regex = re.compile(r'''
            (?P<begin1>[^a-zA-Z0-9\s]+)(?P<core1>\s+(?:.*?\s+)?)(?P<end1>[^a-zA-Z0-9\s]+)
            |
            (?P<begin2>[^a-zA-Z0-9\s]+)(?P<core2>\s+.*)?
            |
            (?P<core3>.*?\s+)(?P<end3>[^a-zA-Z0-9\s]+)
            ''', re.VERBOSE)

        match = spec_chars_regex.fullmatch(name)
        if match == None:
            return name

        begin = ''
        core = ''
        end = ''
        if match.group('end3') != None:
            core = match.expand('\g<core3>')
            end = match.group('end3')
        elif match.group('begin2') != None:
            begin = match.group('begin2')
            core = match.expand('\g<core2>')
        else:
            begin = match.group('begin1')
            core = match.expand('\g<core1>')
            end = match.group('end1')

        b = ''
        e = ''
        for c in begin:
            b += unicodedata.name(c) + ' '
        for c in end:
            e += unicodedata.name(c) + ' '
        result = b.rstrip() + core + e.rstrip()
        return result

    @classmethod
    def str_to_identifier(cls, name):
        """Converts any string to a valid identifier in programming languages."""

        id = cls.sub_spec_chars(name)

        # replace all non-supported characters to whitespace
        id = re.sub('[^\w_]+', ' ', id)
        # replace any section of whitespaces with underscore
        id = re.sub('[\s]+', '_', id)
        # remove leading and trailing underscores
        id = id.strip('_')
        if len(id) == 0:
            # nothing meaningful is left
            return None

        # convert to uppercase
        id = id.upper()

        # if all parts are the same, keep only one part
        ids = id.split('_')
        if len(ids) > 1 and ids.count(ids[0]) == len(ids):
            id = ids[0]

        if id[0].isdigit():
            # digits are only not allowed as first character
            id = '_' + id;
        return id

    @classmethod
    def generate(cls, hid_pages, dest_path):
        import os, shutil
        # delete previous generation
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        os.makedirs(dest_path)

        for page in hid_pages:
            page_name = cls.str_to_identifier(page.name)
            filepath = os.path.join(dest_path, cls.page_filename(page_name))
            with open(filepath, 'w') as file:
                file.write(cls.header(page_name))
                if len(page.usages) == 0:
                    # empty page
                    file.write(cls.numeric(page, page_name, 0))
                elif len(page.usages) == 1 and page.usages[0].id_count() == 0xffff:
                    # special optimization for simple numeric usage pages:
                    # only consider 1-255 as useful range
                    file.write(cls.numeric(page, page_name, 0xff))
                else:
                    # enum style page
                    max_usage = page.usages[-1].id_range()[-1]
                    file.write(cls.enum_begin(page, page_name, max_usage))
                    table = dict()
                    excludes = set()
                    excludes.add(None)

                    # first round is to generate valid names and collect duplicates
                    for usage in page.usages:
                        for id in usage.id_range():
                            name = usage.name(id)
                            usage_name = cls.str_to_identifier(name)

                            if usage_name not in excludes:
                                for value in table.values():
                                    # gather duplicate identifier strings
                                    if value[1] == usage_name:
                                        excludes.add(usage_name)
                                        break

                            table[id] = (name, usage_name)

                    # second round is to write unique 
                    for id in table:
                        name = table[id][0]
                        usage_name = table[id][1]
                        if usage_name not in excludes:
                            file.write(cls.enum_entry(page_name, usage_name, id))
                        else:
                            # if not valid, print a comment instead
                            file.write(cls.enum_comment_entry(page_name, name, id))

                file.write(cls.footer(page_name))
        return

    @classmethod
    @abstractmethod # the decorator order here is fixed
    def page_filename(cls, page_name):
        """Creates the filename for the usage page."""
        pass

    @classmethod
    @abstractmethod
    def header(cls, page_name):
        """The header part of the usage page file."""
        pass

    @classmethod
    @abstractmethod
    def footer(cls, page_name):
        """The footer part of the usage page file."""
        pass

    @classmethod
    @abstractmethod
    def numeric(cls, page, page_name, max_usage = 0xff):
        """Format for a purely numeric usage page (single usage primitive for the entire page)."""
        pass

    @classmethod
    @abstractmethod
    def enum_begin(cls, page, page_name, max_usage):
        """Start of an enumeration style usage page."""
        pass

    @classmethod
    @abstractmethod
    def enum_entry(cls, page_name, usage_name, id):
        """One valid enumeration usage entry."""
        pass

    @classmethod
    @abstractmethod
    def enum_comment_entry(cls, page_name, usage_name, id):
        """One invalid enumeration usage entry, as comment."""
        pass
