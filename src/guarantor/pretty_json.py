# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
"""Prettify JSON

Usage:

    pjson --help
    cat my.json | pjson

"""

import sys
import json
import errno
import typing as typ
import datetime as dt
import functools as ft

PY2 = sys.version_info.major < 3

INT_TYPES   = (int,)
NUM_TYPES   = INT_TYPES + (float,)
BASIC_TYPES = NUM_TYPES + (str, bytes) + (type(None),)


def _decode_object(obj: typ.Any, encoding: str) -> typ.Any:
    """Decode all bytes values into strings."""
    if isinstance(obj, bytes):
        return obj.decode(encoding)
    if isinstance(obj, (list, tuple)):
        return [(val.decode(encoding) if isinstance(val, bytes) else val) for val in obj]
    if isinstance(obj, dict):
        dict_type = type(obj)
        dec_obj   = dict_type()

        for key, val in obj.items():
            dec_key = key.decode(encoding) if isinstance(key, bytes) else key
            dec_val = val.decode(encoding) if isinstance(val, bytes) else val
            dec_obj[dec_key] = dec_val
        return dec_obj
    return obj


def _get_alignment_fmt(
    values     : typ.Iterable,
    val_strings: typ.Union[typ.List, typ.KeysView, typ.ValuesView],
) -> typ.Tuple[str, bool]:
    fmt = "{}"
    if all(isinstance(val, INT_TYPES) for val in values):
        # align to the right
        fmt          = "{{:>{}}}".format(max(map(len, val_strings)))
        use_raw_vals = True
    elif all(isinstance(val, float) for val in values):
        # align by decimal
        fmt = "{{:{}.{}f}}".format(
            max(map(len, val_strings)),
            max((len(val.split(".")[-1]) for val in val_strings)),
        )
        use_raw_vals = True
    elif all(isinstance(val, (str, bytes)) for val in values):
        # align to the left
        fmt          = "{{:<{}}}".format(max(map(len, val_strings)))
        use_raw_vals = False
    else:
        use_raw_vals = False

    return fmt, use_raw_vals


TypBasicTypes = typ.Union[str, bytes, int, float, None]
AllValsByKey  = typ.Dict[str, typ.Set[TypBasicTypes]]


def _get_all_vals_by_key(objects: typ.Iterable[typ.Dict]) -> typ.Optional[AllValsByKey]:
    all_vals_by_key: AllValsByKey = {}
    for obj in objects:
        for key, val in obj.items():
            if not isinstance(key, str) or not isinstance(val, BASIC_TYPES):
                return None

            if key in all_vals_by_key:
                all_vals_by_key[key].add(val)
            else:
                all_vals_by_key[key] = {val}

    return all_vals_by_key


def _dict_aligment(
    objects     : typ.Iterable[typ.Dict],
    max_elem_len: int,
    allow_nan   : bool,
    sort_keys   : bool,
    sorted_key  : typ.Optional[typ.Callable],
) -> typ.Optional[typ.List[str]]:
    all_vals_by_key = _get_all_vals_by_key(objects)
    if all_vals_by_key is None:
        return None

    if sort_keys:
        keys = sorted(all_vals_by_key.keys(), key=sorted_key)
    else:
        keys = list(all_vals_by_key.keys())

    keys.sort(key=lambda key: -len(all_vals_by_key[key]))

    key_items      = []
    val_fmt_by_key = {}
    for key in keys:
        vals = all_vals_by_key[key]
        key_items.append((key, '"' + key + '"'))
        val_strings = [json.dumps(val, allow_nan=allow_nan) for val in vals]
        val_fmt, use_raw_vals = _get_alignment_fmt(vals, val_strings)
        val_fmt_by_key[key] = (val_fmt, use_raw_vals)

    sub_elems = []
    for obj in objects:
        sub_elem_parts = []
        for key, key_str in key_items:
            if key in obj:
                val = obj[key]
                val_fmt, use_raw_vals = val_fmt_by_key[key]
                val_str = val_fmt.format(val if use_raw_vals else json.dumps(val))
                sub_elem_parts.append(key_str + ": " + val_str)
        sub_elem = "{" + ", ".join(sub_elem_parts) + "}"
        if len(sub_elem) > max_elem_len:
            return None
        sub_elems.append(sub_elem)

    return sub_elems


def _dumps_aligned_oneline_objs(
    objects     : typ.Iterable,
    max_elem_len: int,
    allow_nan   : bool,
    sort_keys   : bool,
    sorted_key  : typ.Optional[typ.Callable],
    encoding    : str,
    _dumps      : callable,
) -> typ.Optional[typ.List[str]]:
    if all(isinstance(o, dict) for o in objects):
        sub_elems = _dict_aligment(objects, max_elem_len, allow_nan, sort_keys, sorted_key)
    else:
        sub_elems = None

    if sub_elems is None:
        # fallback to default, without alignment
        return [_dumps(val) for val in objects]
    else:
        return sub_elems


def _quotation(json_key: str) -> str:
    return json_key if json_key.startswith('"') else f'"{json_key}"'


def _dumps_dict(
    obj         : typ.Dict,
    sort_keys   : bool,
    max_elem_len: int,
    allow_nan   : bool,
    align       : bool,
    _depth      : int,
    sorted_key  : typ.Optional[typ.Callable],
    _dumps      : typ.Callable,
    pad         : str,
    encoding    : str,
) -> typ.Tuple[str, str, typ.List[str], str]:
    sub_items = {json.dumps(key): json.dumps(val) for key, val in obj.items()}
    keys_len  = sum(map(len, sub_items.keys()))
    vals_len  = sum(map(len, sub_items.values()))
    total_len = 2 + len(sub_items) * 4 + keys_len + vals_len

    k_fmt = v_fmt = "{}"
    keys        : typ.Iterable[typ.Any]
    if sort_keys:
        keys = sorted(obj, key=sorted_key)
    else:
        keys = obj.keys()

    use_raw_keys = False
    use_raw_vals = False
    if total_len <= max_elem_len or len(sub_items) < 2:
        # single line, so don't do any alignment
        joiner = ", "
        prefix = "{"
        suffix = "}"
    else:
        if align and all(isinstance(key, BASIC_TYPES) for key in obj.keys()):
            k_fmt, use_raw_keys = _get_alignment_fmt(obj.keys(), sub_items.keys())

        if align and all(isinstance(val, NUM_TYPES) for val in obj.values()):
            v_fmt, use_raw_vals = _get_alignment_fmt(obj.values(), sub_items.values())

        joiner = ",\n" + _depth * pad
        prefix = "{\n" + _depth * pad
        suffix = "\n" + (_depth - 1) * pad + "}"
        _depth += 1

    if align and all(isinstance(val, dict) for val in obj.values()):
        sub_elems = _dumps_aligned_oneline_objs(
            [obj[key] for key in keys],
            max_elem_len=max_elem_len,
            allow_nan=allow_nan,
            sort_keys=sort_keys,
            sorted_key=sorted_key,
            encoding=encoding,
            _dumps=_dumps,
        )
        sub_item_output = [
            ((key if use_raw_keys else _quotation(json.dumps(key))), sub_elem)
            for key, sub_elem in zip(keys, sub_elems)
        ]
    else:
        sub_item_output = [
            (
                (key if use_raw_keys else _quotation(json.dumps(key))),
                (obj[key] if use_raw_vals else _dumps(obj[key], _depth=_depth)),
            )
            for key in keys
        ]

    if use_raw_keys:
        k_fmt = '"' + k_fmt + '"'

    kv_fmt = k_fmt + ": " + v_fmt

    sub_elems = [kv_fmt.format(*k_v) for k_v in sub_item_output]
    return (prefix, joiner, sub_elems, suffix)


PJSON_SPECIFIC_KWARGS = {"max_elem_len", "align", "_depth", "sorted_key", "encoding"}


def internal_dumps(
    obj         : typ.Any,
    indent      : int  = 4,
    sort_keys   : bool = True,
    max_elem_len: int  = 60,
    allow_nan   : bool = True,
    align       : bool = True,
    _depth      : int  = 1,
    sorted_key  : typ.Optional[typ.Callable] = None,
    encoding    : str = "utf-8",
) -> str:
    _dumps = ft.partial(
        internal_dumps,
        indent=indent,
        sort_keys=sort_keys,
        max_elem_len=max_elem_len,
        allow_nan=allow_nan,
        align=align,
        _depth=_depth + 1,
        sorted_key=sorted_key,
        encoding=encoding,
    )

    obj = _decode_object(obj, encoding)

    pad = indent * " "

    if isinstance(obj, (tuple, list)):
        # decode all bytes values
        if align and len(obj) > 1:
            sub_elems = _dumps_aligned_oneline_objs(
                obj,
                max_elem_len=max_elem_len,
                allow_nan=allow_nan,
                sort_keys=sort_keys,
                sorted_key=sorted_key,
                encoding=encoding,
                _dumps=_dumps,
            )
        else:
            sub_elems = [_dumps(val) for val in obj]

        total_len           = 2 + len(sub_elems) * 2 + sum(map(len, sub_elems))
        has_container_types = any(isinstance(val, (tuple, list, dict)) for val in obj)
        if total_len <= max_elem_len and not has_container_types:
            joiner = ", "
            prefix = "["
            suffix = "]"
        else:
            joiner = ",\n" + _depth * pad
            prefix = "[\n" + _depth * pad
            suffix = "\n" + (_depth - 1) * pad + "]"
    elif isinstance(obj, dict):
        prefix, joiner, sub_elems, suffix = _dumps_dict(
            obj,
            sort_keys=sort_keys,
            max_elem_len=max_elem_len,
            allow_nan=allow_nan,
            align=align,
            _depth=_depth,
            sorted_key=sorted_key,
            _dumps=_dumps,
            pad=pad,
            encoding=encoding,
        )
    elif isinstance(obj, (dt.datetime, dt.date)):
        return '"' + obj.isoformat() + '"'
    elif isinstance(obj, BASIC_TYPES):
        return json.dumps(obj, allow_nan=allow_nan)
    else:
        raise TypeError("'{}' is not a searializable type.".format(type(obj)))

    return prefix + joiner.join(sub_elems) + suffix


@ft.wraps(json.dumps)
def dumps(*args, **kwargs) -> str:
    # pylint:disable=broad-except  ; that's the idea

    # failsafe: fallback to builtin json dumps
    builtin_kwargs = {key: val for key, val in kwargs.items() if key not in PJSON_SPECIFIC_KWARGS}
    failsafe_json_data: typ.Any = json.dumps(*args, **builtin_kwargs)

    json_data: typ.Any
    try:
        json_data = internal_dumps(*args, **kwargs)
        if json.loads(json_data) != json.loads(failsafe_json_data):
            # make sure we always generate valid json
            json_data = failsafe_json_data
    # except (ValueError, LookupError, TypeError, AttributeError):
    except Exception:
        json_data = failsafe_json_data

    if isinstance(json_data, bytes):
        # py2 json.dumps returns str (which is bytes)
        return json_data.decode('utf-8')
    elif isinstance(json_data, str):
        # py3 json.dumps returns str (which is not bytes)
        return json_data
    else:
        # should be unreachable
        raise TypeError(type(json_data))


def dump(obj, fp, *args, **kwargs) -> None:
    # pylint:disable=invalid-name ; fp name is to match json.dump
    fp.write(dumps(obj, *args, **kwargs))


loads = json.loads
load  = json.load


def main(args: typ.Sequence[str] = sys.argv[1:]) -> int:
    # pylint:disable=dangerous-default-value ; mypy will catch any mutation of args
    if "--help" in args:
        print(__doc__)
        return 0

    kw_items = (kv.lstrip("-").replace("-", "_").split("=", 1) for kv in args if "=" in kv)

    # pylint:disable=unnecessary-comprehension ; it's needed to pacify mypy
    kwargs: typ.Dict[str, typ.Any] = {key: val for key, val in kw_items}

    for key, val in list(kwargs.items()):
        if val.isdigit():
            kwargs[key] = int(val)

    in_data_raw = sys.stdin.read()
    if in_data_raw:
        in_data = json.loads(in_data_raw)
        out_data: str = dumps(in_data, **kwargs)
        try:
            print(out_data)
        except IOError as ex:
            if ex.errno != errno.EPIPE:
                raise

    return 0


if __name__ == '__main__':
    sys.exit(main())
