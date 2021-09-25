"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import re

def str_to_identifier(name):
    """Converts any string to a valid identifier in programming languages."""

    # replace all non-supported characters to whitespace
    id = re.sub('[^\w]+', ' ', name)
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

class CodeGenerator():
    """Abstract class for code generation."""

    @classmethod
    def generate(cls, hid_pages, dest_path):
        import os, shutil
        # delete previous generation
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        os.makedirs(dest_path)

        for page in hid_pages:
            page_name = str_to_identifier(page.name)
            filepath = os.path.join(dest_path, cls.page_filename(page))
            file = open(filepath, 'w')
            try:
                file.write(cls.header(page_name))
                if len(page.usages) == 0:
                    # empty page
                    file.write(cls.numeric(page_name, page.id, 0))
                elif len(page.usages) == 1 and page.usages[0].count() == 0xffff:
                    # special optimization for simple numeric usage pages:
                    # only consider 1-255 as useful range
                    file.write(cls.numeric(page_name, page.id, 0xff))
                else:
                    # enum style page
                    max_usage = page.usages[-1].id_max
                    file.write(cls.enum_begin(page_name, page.id, max_usage))
                    table = dict()
                    excludes = list()
                    excludes.append(None)

                    # first round is to generate valid names and collect duplicates
                    for primitive in page.usages:
                        for i in range(primitive.count()):
                            name = primitive.name(i)
                            usage_name = str_to_identifier(name)

                            for value in table.values():
                                # gather duplicates
                                if excludes.count(value[1]) == 0 and value[1] == usage_name:
                                    excludes.append(usage_name)

                            table[primitive.id_min + i] = (name, usage_name)

                    # second round is to write unique 
                    for id in table:
                        name = table[id][0]
                        usage_name = table[id][1]
                        if excludes.count(usage_name) == 0:
                            file.write(cls.enum_entry(usage_name, id))
                        else:
                            # if not valid, print a comment instead
                            file.write(cls.enum_comment_entry(name, id))

                file.write(cls.footer(page_name))

            finally:
                file.close()
