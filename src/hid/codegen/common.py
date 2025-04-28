"""
author:  Benedek Kupper
date:    2025
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import re
from abc import ABCMeta, abstractmethod

def string_to_identifier(name):
    """Converts any string to a valid identifier in programming languages."""
    # replace all non-supported characters with whitespace
    id = re.sub(r'[^a-zA-Z0-9]', ' ', name)
    # replace any section of whitespaces with underscores
    id = re.sub(r'[\s]+', '_', id)
    # remove leading and trailing underscores
    id = id.strip('_')
    if len(id) == 0:
        # nothing meaningful is left
        return None

    # convert to uppercase
    id = id.upper()

    if id[0].isdigit():
        # digits are not allowed as the first character
        id = '_' + id
    return id

class CodeDirector:
    """Director class to orchestrate the code generation process."""

    def __init__(self, builder, str_to_identifier):
        """
        Initialize the Director with a builder and a symbol builder function.

        :param builder: An instance of a CodeBuilder subclass.
        :param str_to_identifier: A function to convert strings to valid identifiers.
        """
        self.builder = builder
        self.str_to_identifier = str_to_identifier

    def generate(self, hid_pages, dest_path):
        """Generate code using the builder."""
        import os
        import shutil
        # delete previous generation
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        os.makedirs(dest_path)

        for page in hid_pages:
            page_name = self.str_to_identifier(page.name)
            filepath = os.path.join(dest_path, self.builder.page_filename(page_name))
            with open(filepath, 'w') as file:
                file.write(self.builder.header(page_name))
                if len(page.usages) == 0:
                    # empty page
                    file.write(self.builder.numeric(page, page_name, 0))
                elif len(page.usages) == 1 and page.usages[0].id_count() == 0xffff:
                    file.write(self.builder.numeric(page, page_name, page.usages[0].id_count()))
                else:
                    # enum style page
                    max_usage = page.usages[-1].id_range()[-1]
                    file.write(self.builder.enum_begin(page, page_name, max_usage))
                    table = dict()
                    excludes = set()
                    excludes.add(None)

                    # first round is to generate valid names and collect duplicates
                    for usage in page.usages:
                        for id in usage.id_range():
                            name = usage.name(id)
                            usage_name = self.str_to_identifier(name)

                            if usage_name not in excludes:
                                for value in table.values():
                                    # gather duplicate identifier strings
                                    if value[1] == usage_name:
                                        excludes.add(usage_name)
                                        break

                            table[id] = (name, usage_name)

                    # second round is to write unique entries
                    for id in table:
                        name = table[id][0]
                        usage_name = table[id][1]
                        if usage_name not in excludes:
                            file.write(self.builder.enum_entry(page_name, usage_name, id))
                        else:
                            # if not valid, print a comment instead
                            file.write(self.builder.enum_comment_entry(page_name, name, id))

                file.write(self.builder.footer(page_name))
        return


class CodeBuilder(metaclass=ABCMeta):
    """Abstract interface for code builders."""

    @abstractmethod
    def page_filename(self, page_name):
        """Creates the filename for the usage page."""
        pass

    @abstractmethod
    def header(self, page_name):
        """The header part of the usage page file."""
        pass

    @abstractmethod
    def footer(self, page_name):
        """The footer part of the usage page file."""
        pass

    @abstractmethod
    def numeric(self, page, page_name, max_usage = 0xff):
        """Format for a purely numeric usage page (single usage primitive for the entire page)."""
        pass

    @abstractmethod
    def enum_begin(self, page, page_name, max_usage):
        """Start of an enumeration style usage page."""
        pass

    @abstractmethod
    def enum_entry(self, page_name, usage_name, id):
        """One valid enumeration usage entry."""
        pass

    @abstractmethod
    def enum_comment_entry(self, page_name, usage_name, id):
        """One invalid enumeration usage entry, as comment."""
        pass
