"""
author:  Benedek Kupper
date:    2021
copyright:
         This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
         If a copy of the MPL was not distributed with this file, You can obtain one at
         https://mozilla.org/MPL/2.0/."""
from enum import Enum, unique
from abc import ABCMeta, abstractmethod
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

def check_id(id):
    if not (id > 0 and id < 0x10000):
        raise HidUsageError('Invalid usage ID')

class HidUsagePrimitive(metaclass=ABCMeta):
    """Base type for HID usage definitions"""
    def __init__(self, name, types):
        self._name = name
        self._types = types

    @property
    def types(self):
        """HidUsageType"""
        return self._types

    @abstractmethod
    def id_count(self):
        """The number of usages covered by this primitive"""
        pass

    @abstractmethod
    def id_range(self):
        """The range of IDs"""
        pass

    def name(self, id):
        """Get the name of the usage by ID."""
        return self._name

class HidUsage(HidUsagePrimitive):
    """Single HID usage"""
    def __init__(self, name, types, id):
        super().__init__(name, types)
        check_id(id)
        self._id = id

    def id_count(self):
        return 1

    def id_range(self):
        # range end is invalid
        return range(self._id, self._id + 1)

class HidUsageRange(HidUsagePrimitive):
    """Continuous range of HID usages"""
    def __init__(self, name, types, id_min, id_max):
        super().__init__(name, types)
        check_id(id_min)
        check_id(id_max)
        self._id_min = id_min
        self._id_max = id_max

    def id_count(self):
        """The number of usages covered by this primitive"""
        return 1 + self._id_max - self._id_min

    def id_range(self):
        # range end is invalid
        return range(self._id_min, self._id_max + 1)

    def name(self, id):
        """Generate the name of the usage."""
        if id < self._id_min or id > self._id_max:
            raise HidUsageError('Invalid usage ID')

        _name_calc_regex = re.compile('([^{}]*)[{]([-+*/n0-9 ]+)[}]([^{}]*)')
        # the name shall contain a {} enclosed expression that can be evaluated by substituting n with index
        match = _name_calc_regex.fullmatch(self._name)
        if match != None:
            n = id - self._id_min
            s = match.group(1) + str(eval(match.group(2))) + match.group(3)
            return s
        else:
            raise HidUsageError('HidUsageRange name format invalid')

class HidPage():
    """HID usage page"""
    def __init__(self, id, name, description):
        check_id(id)
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
