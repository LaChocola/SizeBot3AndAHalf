import pydoc
import inspect
import traceback
import re
from functools import reduce

re_num = "\\d+\\.?\\d*"


def clamp(minVal, val, maxVal):
    return max(minVal, min(maxVal, val))


def prettyTimeDelta(totalSeconds):
    SECONDS_PER_YEAR = 86400 * 365
    SECONDS_PER_DAY = 86400
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60

    seconds = int(totalSeconds)
    years, seconds = divmod(seconds, SECONDS_PER_YEAR)
    days, seconds = divmod(seconds, SECONDS_PER_DAY)
    hours, seconds = divmod(seconds, SECONDS_PER_HOUR)
    minutes, seconds = divmod(seconds, SECONDS_PER_MINUTE)

    s = ""
    if totalSeconds >= SECONDS_PER_YEAR:
        s += f"{years:d} years, "
    if totalSeconds >= SECONDS_PER_DAY:
        s += f"{days:d} days, "
    if totalSeconds >= SECONDS_PER_HOUR:
        s += f"{hours:d} hours, "
    if totalSeconds >= SECONDS_PER_MINUTE:
        s += f"{minutes:d} minutes, "
    s += f"{seconds:d} seconds"


def tryInt(val):
    try:
        val = int(val)
    except ValueError:
        pass
    return val


def hasPath(root, path):
    """Get a value using a path in nested dicts/lists"""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [tryInt(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return False
    return True


def getPath(root, path, default=None):
    """Get a value using a path in nested dicts/lists"""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [tryInt(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return default
    return branch


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(lambda o, a: getattr(o, a, None), attr.split("."), obj)


def chunkList(lst, chunklen):
    while lst:
        yield lst[:chunklen]
        lst = lst[chunklen:]


def chunkStr(s, chunklen, prefix="", suffix=""):
    """chunkStr(3, "ABCDEFG") --> ['ABC', 'DEF', 'G']"""
    innerlen = chunklen - len(prefix) - len(suffix)
    if innerlen <= 0:
        raise ValueError("Cannot fit prefix and suffix within chunklen")

    if not s:
        return prefix + s + suffix

    while len(s) > 0:
        chunk = s[:innerlen]
        s = s[innerlen:]
        yield prefix + chunk + suffix


def chunkMsg(m):
    p = "```\n"
    if m.startswith("Traceback") or m.startswith("eval error") or m.startswith("Executing eval"):
        p = "```python\n"
    return chunkStr(m, chunklen=2000, prefix=p, suffix="\n```")


def chunkLines(s, chunklen):
    """Split a string into groups of lines that don't go over the chunklen. Individual lines longer the chunklen will be split"""
    lines = s.split("\n")

    linesout = []
    while lines:
        linesout.append(lines.pop(0))
        if len("\n".join(linesout)) > chunklen:
            if len(linesout) == 1:
                line = linesout.pop()
                lines.insert(0, line[chunklen:])
                linesout.append(line[:chunklen])
            else:
                lines.insert(0, linesout.pop())
            yield "\n".join(linesout)
            linesout = []
    if linesout:
        yield "\n".join(linesout)


def removeBrackets(s):
    s = re.sub(r"[\[\]<>]", "", s)
    return s


def formatTraceback(err):
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def pformat(name, value):
    if value is None:
        return f"{name}?"
    if callable(value):
        return f"{name}()"
    if isinstance(value, (list, tuple)):
        return f"{name}[]"
    if isinstance(value, set):
        return f"{name}{{}}"
    if isinstance(value, dict):
        return f"{name}{{:}}"
    return name


def pdir(o):
    """return a list of an object's attributes, with type notation"""
    return [pformat(n, v) for n, v in ddir(o).items()]


def ddir(o):
    """return a dictionary of an object's attributes"""
    return {n: v for n, v in inspect.getmembers(o) if not n.startswith("_")}
    # return {n: getattr(o, n, None) for n in dir(o) if not n.startswith("_")}


def getFullname(o):
    moduleName = o.__class__.__module__
    if moduleName == "builtins":
        moduleName = ""
    if moduleName:
        moduleName = f"{moduleName}."

    className = o.__class__.__name__
    fullname = f"{moduleName}{className}"
    return fullname


def formatError(err):
    fullname = getFullname(err)

    errMessage = str(err)
    if errMessage:
        errMessage = f": {errMessage}"

    return f"{fullname}{errMessage}"


def tryOrNone(fn, *args, ignore=(), **kwargs):
    try:
        result = fn(*args, **kwargs)
    except ignore:
        result = None
    return result


class iset(set):
    def __init__(self, iterable):
        iterable = (i.casefold() for i in iterable)
        super().__init__(iterable)

    def add(self, item):
        item = item.casefold()
        return super().add(item)

    def __contains__(self, item):
        item = item.casefold()
        return super().__contains__(item)

    def discard(self, item):
        item = item.casefold()
        return super().discard(item)

    def remove(self, item):
        item = item.casefold()
        return super().remove(item)


def strHelp(topic):
    return pydoc.plain(pydoc.render_doc(topic))


def minmax(first, second):
    small, big = first, second
    if small > big:
        small, big = big, small
    return small, big


def removeCodeBlock(s):
    re_codeblock = re.compile(r"^\s*```(?:python)?(.*)```\s*$", re.DOTALL)
    s_nocodeblock = re.sub(re_codeblock, r"\1", s)
    if s_nocodeblock != s:
        return s_nocodeblock

    re_miniblock = re.compile(r"^\s*`(.*)`\s*$", re.DOTALL)
    s_nominiblock = re.sub(re_miniblock, r"\1", s)
    if s_nominiblock != s:
        return s_nominiblock

    return s
