#!/usr/bin/env python
# -- coding: utf-8 --

"""Type definitions for type checking purposes."""

import os
from typing import TypeVar, NewType

PathLike = TypeVar("PathLike", str, os.PathLike)

JSONString = NewType("JSONString", str)
DateString = NewType("DateString", str)

_Url = NewType("_Url", str)


def URL(s: str) -> _Url:
    if not s.startswith("https://") or s.startswith("http://"):
        raise TypeError(f"{s} is not a valid URL")
    return _Url(s)
