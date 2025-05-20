"""
author:  Benedek Kupper
date:    2025
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
import sys
import os

# add the current package to the path
pkg_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../..'))
sys.path.insert(0, pkg_path)

from hid.parser import parse_database
from hid.codegen.common import str_to_identifier, escape_str

class CppBuilder():
    """Generate c++ header files from HID usage page database."""

    def __init__(self, dest_path):
        self.dest_path = dest_path

    def usage_value_type(self, page):
        return 'std::uint8_t' if page.max_usage < 256 else 'std::uint16_t'

    def page_filename(self, page_name):
        return f'{page_name.lower()}.hpp'

    def header(self, name, includes = '#include "hid/usage.hpp"\n'):
        return (f'#ifndef __HID_PAGE_{name.upper()}_HPP_\n'
                f'#define __HID_PAGE_{name.upper()}_HPP_\n'
                 '\n'
                f'{includes}'
                 '\n'
                 'namespace hid::page\n'
                 '{\n')

    def numeric(self, page, name):
        value_type = self.usage_value_type(page)
        usage_name = page.usages[0].name(None) if len(page.usages) else page.description + ' '
        return (f'class {name.lower()};\n'
                 'template <>\n'
                f'constexpr inline auto get_info<{name.lower()}>()\n'
                 '{\n'
                f'    return info(0x{page.id:04x}, 0x{page.max_usage:04x}, "{escape_str(page.description)}",\n'
                f'                [](hid::usage_id_t id) {{ return id ? "{escape_str(usage_name)}{{}}" : nullptr; }});\n'
                 '}\n'
                f'class {name.lower()}\n'
                 '{\n'
                 'public:\n'
                 '    constexpr operator usage_id_t() const { return id; }\n'
                f'    explicit constexpr {name.lower()}({value_type} value)\n'
                 '        : id(value)\n'
                 '    {}\n'
                f'    {value_type} id{{}};\n'
                 '};\n')

    def enum(self, page, name):
        table = page.usage_ids_names()
        value_type = self.usage_value_type(page)
        cases = ''.join(
                f'                    case 0x{uid:04x}: return "{escape_str(usage_name)}";\n'
                for uid, usage_name in table.items())

        enumerators = ''.join(
                f'    {str_to_identifier(usage_name).upper()} = 0x{uid:04x},\n'
                for uid, usage_name in table.items())

        return (f'enum class {name.lower()} : {value_type};\n'
                f'template <>\n'
                f'constexpr inline auto get_info<{name.lower()}>()\n'
                 '{\n'
                f'    return info(0x{page.id:04x}, 0x{page.max_usage:04x}, "{escape_str(page.description)}",\n'
                 '                [](hid::usage_id_t id) {\n'
                 '                    switch (id) {\n'
                f'{cases}'
                 '                    default:     return (const char*)nullptr;\n'
                 '                    }\n'
                f'                }}, 0x{page.ius_mask:04x});\n'
                 '}\n'
                f'enum class {name.lower()} : {value_type}\n'
                 '{\n'
                f'{enumerators}'
                 '};\n')

    def footer(self, name):
        return ('} // namespace hid::page\n'
                 '\n'
                f'#endif // __HID_PAGE_{name.upper()}_HPP_\n')

    def open_page_file(self, page_name):
        filepath = os.path.join(self.dest_path, self.page_filename(page_name))
        return open(filepath, 'w', encoding='utf-8')

    def numeric_page(self, page):
        page_name = str_to_identifier(page.name).lower()
        with self.open_page_file(page_name) as file:
            file.write(self.header(page_name))
            file.write(self.numeric(page, page_name))
            file.write(self.footer(page_name))
            return page_name

    def enum_page(self, page):
        page_name = str_to_identifier(page.name).lower()
        with self.open_page_file(page_name) as file:
            file.write(self.header(page_name))
            file.write(self.enum(page, page_name))
            file.write(self.footer(page_name))
            return page_name

    def summary_file(self, pages):
        name = 'all'
        headers = ''.join(
                f'#include "{page}.hpp"\n'
                for page in pages)
        cases = ''.join(
                f'    case   get_info<{page}>().page_id:\n'
                f'    return get_info<{page}>();\n'
                for page in pages)
        with self.open_page_file(name) as file:
            file.write(self.header(name, headers))
            file.write(
                 'constexpr inline auto get_page_info(page_id_t page_id)\n'
                 '{\n'
                 '    switch (page_id) {\n'
                f'{cases}'
                 '    default:\n'
                 '    return get_info<hid::nullusage_t>();\n'
                 '    }\n'
                 '}\n'
            )
            file.write(self.footer(name))


# This file can be directly executed to perform code generation.
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python3 cpp.py <output_path>')
        sys.exit(1)
    out_path = os.path.abspath(sys.argv[1])
    hid_pages = parse_database()

    # delete previous generation
    if os.path.exists(out_path):
        import shutil
        shutil.rmtree(out_path)
    os.makedirs(out_path)

    builder = CppBuilder(out_path)
    page_names = []
    for p in hid_pages:
        if len(p.usages) <= 1:
            page_names.append(builder.numeric_page(p))
        else:
            page_names.append(builder.enum_page(p))
    builder.summary_file(page_names)

    print(f'HID usages code generation to path "{out_path}" is complete.')
