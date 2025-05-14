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
from ast import literal_eval

class HidUsageError(Exception):
    """HID usage generic exception"""

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

    @classmethod
    def _missing_(cls, value):
        if value == 'BufferedBytes':
            return cls.BUFFERED_BYTES
        return None

def check_id(uid : int):
    if not (uid > 0 and uid < 0x10000):
        raise HidUsageError('Invalid usage ID')

class HidUsagePrimitive(metaclass=ABCMeta):
    """Base type for HID usage definitions"""
    def __init__(self, name : str, types : list):
        self._name = name
        self._types = types

    @property
    def types(self) -> list:
        """HidUsageType"""
        return self._types

    @abstractmethod
    def id_count(self) -> int:
        """The number of usages covered by this primitive"""

    @abstractmethod
    def id_range(self) -> range:
        """The range of IDs"""

    def name(self, uid : int) -> str:
        """Get the name of the usage by ID."""
        return self._name

class HidUsage(HidUsagePrimitive):
    """Single HID usage"""
    def __init__(self, name, types, uid):
        super().__init__(name, types)
        check_id(uid)
        self._id = uid

    def id_count(self) -> int:
        return 1

    def id_range(self) -> range:
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

    def id_count(self) -> int:
        """The number of usages covered by this primitive"""
        return 1 + self._id_max - self._id_min

    def id_range(self) -> range:
        # range end is invalid
        return range(self._id_min, self._id_max + 1)

    def name(self, uid : int):
        """Generate the name of the usage."""
        if uid is None:
            return self._name
        if uid < self._id_min or uid > self._id_max:
            raise HidUsageError('Invalid usage ID')

        _name_calc_regex = re.compile(r'([^{}]*)[{]([-+*/n0-9 ]+)[}]([^{}]*)')
        # the name shall contain a {} enclosed expression that can be evaluated
        # by substituting n with index
        match = _name_calc_regex.fullmatch(self._name)
        if match is not None:
            allowed2eval = {
                'n': uid - self._id_min,
                '__builtins__': None,
                'math': None,
            }
            s = match.group(1) + str(eval(match.group(2), allowed2eval)) + match.group(3)
            return s

        raise HidUsageError('HidUsageRange name format invalid')

class HidPage():
    """HID usage page"""
    def __init__(self, pid : int, name : str, description : str):
        check_id(pid)
        self._id = pid
        self._name = name
        self._desc = description
        self._usages = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._desc

    @property
    def id(self) -> int:
        return self._id

    def add(self, primitive):
        # TODO: check if the new primitive's IDs aren't in use
        self._usages.append(primitive)

    @property
    def usages(self) -> list:
        return self._usages

    @property
    def max_usage(self) -> int:
        if len(self._usages) > 0:
            return self._usages[-1].id_range()[-1]
        return 0

    def usage_ids_names(self) -> dict:
        table = {}
        for usage in self._usages:
            for uid in usage.id_range():
                table[uid] = usage.name(uid)
        return table
