"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import sys, os

# add the current package to the path
pkg_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../..'))
sys.path.insert(0, pkg_path)

from hid.parser import parse_database
from hid.codegen.common import *

class CppGenerator(CodeGenerator):
    """Generate c++ header files from HID usage page database."""

    @classmethod
    def page_filename(cls, page_name):
        return f'{page_name.lower()}.hpp'

    @classmethod
    def header(cls, name):
        return (f'#ifndef __HID_PAGE_{name.upper()}_HPP_\n'
                f'#define __HID_PAGE_{name.upper()}_HPP_\n'
                f'\n'
                f'#include "hid/usage.hpp"\n'
                f'\n'
                f'namespace hid::page\n'
                f'{{\n')

    @classmethod
    def numeric(cls, page, name, max_usage):
        return (f'    class {name.lower()};\n'
                f'    template<>\n'
                f'    struct info<{name.lower()}>\n'
                f'    {{\n'
                f'        constexpr static usage_id_type base_id = 0x{page.id << 16:08x};\n'
                f'        constexpr static usage_id_type max_usage = 0x{max_usage:04x} | base_id;\n'
                f'        constexpr static const char* name = "{page.description}";\n'
                f'    }};\n'
                f'    class {name.lower()}\n'
                f'    {{\n'
                f'    public:\n'
                f'        constexpr operator usage_id_type&()\n'
                f'        {{\n'
                f'            return id;\n'
                f'        }}\n'
                f'        constexpr operator usage_id_type() const\n'
                f'        {{\n'
                f'            return id;\n'
                f'        }}\n'
                f'        constexpr {name.lower()}(usage_index_type value)\n'
                f'            : id((value & USAGE_INDEX_MASK) | info<{name.lower()}>::base_id)\n'
                f'        {{\n'
                f'        }}\n'
                f'    private:\n'
                f'        usage_id_type id;\n')

    @classmethod
    def enum_begin(cls, page, name, max_usage):
        return (f'    enum class {name.lower()} : usage_id_type;\n'
                f'    template<>\n'
                f'    struct info<{name.lower()}>\n'
                f'    {{\n'
                f'        constexpr static usage_id_type base_id = 0x{page.id << 16:08x};\n'
                f'        constexpr static usage_id_type max_usage = 0x{max_usage:04x} | base_id;\n'
                f'        constexpr static const char* name = "{page.description}";\n'
                f'    }};\n'
                f'    enum class {name.lower()} : usage_id_type\n'
                f'    {{\n')

    @classmethod
    def enum_entry(cls, name, usage_name, id):
        return (f'        {usage_name.upper()} = 0x{id:04x} | info<{name.lower()}>::base_id,\n')

    @classmethod
    def enum_comment_entry(cls, name, usage_name, id):
        return (f'        // "{usage_name.upper()}" = 0x{id:04x} | info<{name.lower()}>::base_id,\n')

    @classmethod
    def footer(cls, name):
        return (f'    }};\n'
                f'}}\n'
                f'\n'
                f'#endif // __HID_PAGE_{name.upper()}_HPP_\n'
                f'\n')

"""This file can be directly executed to perform code generation."""
if __name__ == "__main__":
    out_path = os.path.abspath(sys.argv[1])
    hid_pages = parse_database()
    CppGenerator.generate(hid_pages, out_path)
    print('Code generation to path "' + out_path + '" is complete.')
