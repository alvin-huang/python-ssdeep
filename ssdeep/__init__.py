import os

import six

from ssdeep.__about__ import (
    __author__, __copyright__, __email__, __license__, __summary__, __title__,
    __uri__, __version__
)
from ssdeep.binding import Binding

binding = Binding()
ffi = binding.ffi


class BaseError(Exception):
    pass

class InternalError(BaseError):
    pass

class Error(Exception):
    def __init__(self, errno=None):
        self.errno = errno

    def __str__(self):
        return "Error: %s" % os.strerror(self.errno)

    def __repr__(self):
        try:
            return "Error(errno.%s)" % errno.errorcode[self.errno]
        except KeyError:
            return "Error(%d)" % self.errno


class Hash(object):
    def __init__(self):
        self._state = binding.lib.fuzzy_new()
        if self._state == ffi.NULL:
            raise InternalError("Unable to create state object")

    def update(self, buf, encoding="utf-8"):
        if self._state == ffi.NULL:
            raise InternalError("State object is NULL")

        if isinstance(buf, six.text_type):
            buf = buf.encode(encoding)

        if not isinstance(buf, six.binary_type):
            raise TypeError(
                "Argument must be of string, unicode or bytes type not "
                "'%r'" % type(buf)
            )

        if binding.lib.fuzzy_update(self._state, buf, len(buf)) != 0:
            binding.lib.fuzzy_free(self._state)
            raise InternalError("Invalid state object")

    def digest(self, elimseq=False, notrunc=False):
        if self._state == ffi.NULL:
            raise InternalError("State object is NULL")

        flags = (binding.lib.FUZZY_FLAG_ELIMSEQ if elimseq else 0) | \
                (binding.lib.FUZZY_FLAG_NOTRUNC if notrunc else 0)

        result = ffi.new("char[]", binding.lib.FUZZY_MAX_RESULT)
        if binding.lib.fuzzy_digest(self._state, result, flags) != 0:
            raise InternalError("Function returned an unexpected error code")

        return ffi.string(result).decode("ascii")

    def __del__(self):
        if self._state != ffi.NULL:
            binding.lib.fuzzy_free(self._state)


def compare(sig1, sig2):
    if isinstance(sig1, six.text_type):
        sig1 = sig1.encode("ascii")
    if isinstance(sig2, six.text_type):
        sig2 = sig2.encode("ascii")

    if not isinstance(sig1, six.binary_type):
        raise TypeError(
            "First argument must be of string, unicode or bytes type not "
            "'%s'" % type(sig1)
        )

    if not isinstance(sig2, six.binary_type):
        raise TypeError(
            "Second argument must be of string, unicode or bytes type not "
            "'%r'" % type(sig2)
        )

    res = binding.lib.fuzzy_compare(sig1, sig2)
    if res < 0:
        raise InternalError("Function returned an unexpected error code")

    return res


def hash(buf, encoding="utf-8"):
    if isinstance(buf, six.text_type):
        buf = buf.encode(encoding)

    if not isinstance(buf, six.binary_type):
        raise TypeError(
            "Argument must be of string, unicode or bytes type not "
            "'%r'" % type(buf)
        )

    # allocate memory for result
    result = ffi.new("char[]", binding.lib.FUZZY_MAX_RESULT)
    if binding.lib.fuzzy_hash_buf(buf, len(buf), result) != 0:
        raise InternalError("Function returned an unexpected error code")

    return ffi.string(result).decode("ascii")


def hash_from_file(filename):
    if not os.path.exists(filename):
        raise IOError("Path not found")
    if not os.path.isfile(filename):
        raise IOError("File not found")
    if not os.access(filename, os.R_OK):
        raise IOError("File is not readable")

    result = ffi.new("char[]", binding.lib.FUZZY_MAX_RESULT)
    if binding.lib.fuzzy_hash_filename(filename.encode("utf-8"), result) != 0:
        raise InternalError("Function returned an unexpected error code")

    return ffi.string(result).decode("ascii")