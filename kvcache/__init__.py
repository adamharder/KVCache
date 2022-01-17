import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

from kvcache.kvcache import KVCache

try:
    __version__ = metadata.version("cfs")
except metadata.PackageNotFoundError:
    __version__ = "99.99.99"



def int_or_str(value):
    try:
        return int(value)
    except ValueError:
        return value

VERSION = tuple(map(int_or_str, __version__.split(".")))

__all__ = [
    "KVCache",
]