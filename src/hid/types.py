"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
from enum import Enum, unique
import re

class HidUsageError(Exception):
    """HID usage generic exception"""
    pass

@unique
class HidUsageType(Enum):
    """HID usage types as defined in usage tables document"""
    LINEAR_CONTROL = 'LC'
    ON_OFF_CONTROL = 'OOC'
    MOMENTARY_CONTROL = 'MC'
    ONE_SHOT_CONTROL = 'OSC'
    RE_TRIGGER_CONTROL = 'RTC'
    SELECTOR = 'Sel'
    STATIC_VALUE = 'SV'
    STATIC_FLAG = 'SF'
    DYNAMIC_VALUE = 'DV'
    DYNAMIC_FLAG = 'DF'
    NAMED_ARRAY = 'NAry'
    APPLICATION_COLLECTION = 'CA'
    LOGICAL_COLLECTION = 'CL'
    PHYSICAL_COLLECTION = 'CP'
    USAGE_SWITCH = 'US'
    USAGE_MODIFIER = 'UM'
    # not specified in root document
    BUFFERED_BYTES = 'BB' # no static meaning, data stream
    INLINE_USAGE_SWITCH = 'IUS' # the value of the Modifier is OR-ed in to the top 4 bits of the un-modified Usage ID

class HidUsagePrimitive():
    """Base type for HID usage definitions"""
    def __init__(self, name, types, id_min, id_max):
        if not (id_min > 0 and id_min < 0x10000):
            raise HidUsageError()
        if not (id_max > 0 and id_max < 0x10000):
            raise HidUsageError()
        self._name = name
        self._types = types
        self._id_min = id_min
        self._id_max = id_max

    @property
    def types(self):
        """HidUsageType"""
        return self._types

    def count(self):
        """The number of usages covered by this primitive"""
        return 1 + self._id_max - self._id_min

    @property
    def id_min(self):
        return self._id_min

    @property
    def id_max(self):
        return self._id_max

    def name(self, index = 0):
        """Generate the name of the usage (by the selected index if the usage primitive covers a range)."""
        if index >= self.count():
            raise ValueError('HidUsagePrimitive index is out of range')
        return self._name

class HidUsage(HidUsagePrimitive):
    """Single HID usage"""
    def __init__(self, name, types, id):
        super().__init__(name, types, id, id)

    @property
    def id(self):
        return self._id_min

class HidUsageRange(HidUsagePrimitive):
    """HID usage ID range"""
    def name(self, index = 0):
        """Generate the name of the usage."""
        if index >= self.count():
            raise ValueError('HidUsagePrimitive index is out of range')

        _name_calc_regex = re.compile('([^{}]*)[{]([-+*/n0-9 ]+)[}]([^{}]*)')

        match = _name_calc_regex.fullmatch(self._name)
        if match != None:
            n = index
            s = match.group(1) + str(eval(match.group(2))) + match.group(3)
            return s
        else:
            return super().name(index)

class HidPage():
    """HID usage page"""
    def __init__(self, id, name, description):
        if not (id > 0 and id < 0x10000):
            raise HidUsageError()
        self._id = id
        self._name = name
        self._desc = description
        self._usages = list()

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._desc

    @property
    def id(self):
        return self._id

    def add(self, primitive):
        # TODO: check if the new primitive's IDs aren't in use
        self._usages.append(primitive)

    @property
    def usages(self):
        return self._usages
