"""함수 모드 호출 코드를 만들 때 쓰는 형. 언어마다 형 이름을 (기본형, 차원)으로 읽고, JSON 값을 그 언어 리터럴로 쓴다.

기본형: int, long, double, bool, string. 차원: 0(값), 1(배열), 2(2차원 배열).
함수 방식 문제의 인자는 거의 이 안에 든다. 밖의 형은 unsupported_signature로 알린다.
"""

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Type:
    base: str
    dims: int
    ref_str: bool = False  # Rust &str
    native: str = ""  # Rust 수 형 이름(i32, i64, usize, u64, f64). 리터럴 접미사로 쓴다


class Unsupported(Exception):
    pass


def split_params(text):
    """괄호·꺾쇠 안의 쉼표는 나누지 않는다."""
    parts, depth, current = [], 0, ""
    for char in text:
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def _strip(text):
    return re.sub(r"\s+", "", text)


JAVA_BASE = {"int": "int", "Integer": "int", "long": "long", "Long": "long", "double": "double", "Double": "double",
             "boolean": "bool", "Boolean": "bool", "String": "string"}


def java_type(text):
    raw = _strip(text.replace("final ", ""))
    dims = raw.count("[]")
    base = JAVA_BASE.get(raw.replace("[]", ""))
    if base is None or dims > 2:
        raise Unsupported(text)
    return Type(base, dims)


KOTLIN_ARRAY = {"IntArray": "int", "LongArray": "long", "DoubleArray": "double", "BooleanArray": "bool"}
KOTLIN_BASE = {"Int": "int", "Long": "long", "Double": "double", "Boolean": "bool", "String": "string"}


def kotlin_type(text):
    raw = _strip(text)
    dims = 0
    while raw.startswith("Array<") and raw.endswith(">"):
        raw, dims = raw[6:-1], dims + 1
    if raw in KOTLIN_ARRAY:
        raw, dims = raw, dims + 1
        base = KOTLIN_ARRAY[raw]
    else:
        base = KOTLIN_BASE.get(raw)
    if base is None or dims > 2:
        raise Unsupported(text)
    return Type(base, dims)


CPP_BASE = {"int": "int", "long": "long", "longlong": "long", "int64_t": "long", "double": "double", "float": "double",
            "bool": "bool", "string": "string"}


def cpp_type(text):
    raw = _strip(text.replace("const ", "").replace("std::", "").replace("&", ""))
    dims = 0
    while raw.startswith("vector<") and raw.endswith(">"):
        raw, dims = raw[7:-1], dims + 1
    base = CPP_BASE.get(raw)
    if base is None or dims > 2:
        raise Unsupported(text)
    return Type(base, dims)


GO_BASE = {"int": "int", "int32": "int", "int64": "long", "float64": "double", "bool": "bool", "string": "string"}


def go_type(text):
    raw = _strip(text)
    dims = 0
    while raw.startswith("[]"):
        raw, dims = raw[2:], dims + 1
    base = GO_BASE.get(raw)
    if base is None or dims > 2:
        raise Unsupported(text)
    return Type(base, dims)


RUST_BASE = {"i32": "int", "usize": "long", "i64": "long", "u64": "long", "f64": "double", "bool": "bool",
             "String": "string", "&str": "string"}


def rust_type(text):
    raw = _strip(text).replace("&'static", "&")
    if raw.startswith("&Vec<") or raw.startswith("&["):
        raise Unsupported(text)
    dims = 0
    while raw.startswith("Vec<") and raw.endswith(">"):
        raw, dims = raw[4:-1], dims + 1
    base = RUST_BASE.get(raw)
    if base is None or dims > 2:
        raise Unsupported(text)
    return Type(base, dims, ref_str=(raw == "&str"), native=raw if base in ("int", "long", "double") else "")


# 리터럴

def _check(value, typ):
    if typ.dims:
        if not isinstance(value, list):
            raise Unsupported(f"배열이 아닌 값: {value!r}")
        return
    ok = {
        "int": isinstance(value, int) and not isinstance(value, bool),
        "long": isinstance(value, int) and not isinstance(value, bool),
        "double": isinstance(value, (int, float)) and not isinstance(value, bool),
        "bool": isinstance(value, bool),
        "string": isinstance(value, str),
    }[typ.base]
    if not ok:
        raise Unsupported(f"{typ.base}가 아닌 값: {value!r}")


def _float(value):
    text = repr(float(value))
    if text in ("inf", "-inf", "nan"):
        raise Unsupported("유한한 실수만 받습니다")
    return text


def _c_string(value):
    """C++·Rust 공통: 큰따옴표, 역슬래시, 줄바꿈 계열만 바꾸고 나머지는 UTF-8 그대로."""
    out = []
    for char in value:
        if char == "\\":
            out.append("\\\\")
        elif char == '"':
            out.append('\\"')
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif ord(char) < 0x20:
            out.append(f"\\x{ord(char):02x}")
        else:
            out.append(char)
    return '"' + "".join(out) + '"'


def _rust_string(value):
    body = _c_string(value)
    return re.sub(r"\\x([0-9a-f]{2})", lambda m: "\\u{" + m.group(1) + "}", body)


def java(value, typ):
    _check(value, typ)
    names = {"int": "int", "long": "long", "double": "double", "bool": "boolean", "string": "String"}
    if typ.dims == 0:
        return {"int": lambda: str(value), "long": lambda: f"{value}L", "double": lambda: _float(value),
                "bool": lambda: "true" if value else "false", "string": lambda: json.dumps(value)}[typ.base]()
    inner = Type(typ.base, typ.dims - 1)
    items = ", ".join(_java_inner(v, inner) for v in value)
    return f"new {names[typ.base]}{'[]' * typ.dims}{{{items}}}"


def _java_inner(value, typ):
    if typ.dims == 0:
        return java(value, typ)
    _check(value, typ)
    return "{" + ", ".join(_java_inner(v, Type(typ.base, typ.dims - 1)) for v in value) + "}"


def kotlin(value, typ):
    _check(value, typ)
    if typ.dims == 0:
        return {"int": lambda: str(value), "long": lambda: f"{value}L", "double": lambda: _float(value),
                "bool": lambda: "true" if value else "false",
                "string": lambda: json.dumps(value).replace("$", "\\$")}[typ.base]()
    inner = Type(typ.base, typ.dims - 1)
    items = ", ".join(kotlin(v, inner) for v in value)
    if typ.dims == 1:
        maker = {"int": "intArrayOf", "long": "longArrayOf", "double": "doubleArrayOf", "bool": "booleanArrayOf",
                 "string": "arrayOf<String>"}[typ.base]
        return f"{maker}({items})"
    element = {"int": "IntArray", "long": "LongArray", "double": "DoubleArray", "bool": "BooleanArray",
               "string": "Array<String>"}[typ.base]
    return f"arrayOf<{element}>({items})"


def cpp_name(typ):
    base = {"int": "int", "long": "long long", "double": "double", "bool": "bool", "string": "std::string"}[typ.base]
    for _ in range(typ.dims):
        base = f"std::vector<{base}>"
    return base


def cpp(value, typ):
    _check(value, typ)
    if typ.dims == 0:
        return {"int": lambda: str(value), "long": lambda: f"{value}LL", "double": lambda: _float(value),
                "bool": lambda: "true" if value else "false",
                "string": lambda: f"std::string({_c_string(value)})"}[typ.base]()
    inner = Type(typ.base, typ.dims - 1)
    return f"{cpp_name(typ)}{{" + ", ".join(cpp(v, inner) for v in value) + "}"


def go_name(typ):
    base = {"int": "int", "long": "int64", "double": "float64", "bool": "bool", "string": "string"}[typ.base]
    return "[]" * typ.dims + base


def go(value, typ):
    _check(value, typ)
    if typ.dims == 0:
        return {"int": lambda: str(value), "long": lambda: f"int64({value})", "double": lambda: f"float64({_float(value)})",
                "bool": lambda: "true" if value else "false", "string": lambda: json.dumps(value)}[typ.base]()
    inner = Type(typ.base, typ.dims - 1)
    return f"{go_name(typ)}{{" + ", ".join(_go_inner(v, inner) for v in value) + "}"


def _go_inner(value, typ):
    if typ.dims == 0:
        return go(value, typ)
    _check(value, typ)
    return "{" + ", ".join(_go_inner(v, Type(typ.base, typ.dims - 1)) for v in value) + "}"


def rust(value, typ):
    _check(value, typ)
    if typ.dims == 0:
        if typ.base == "string":
            text = _rust_string(value)
            return text if typ.ref_str else f"String::from({text})"
        if typ.base == "bool":
            return "true" if value else "false"
        suffix = typ.native or {"int": "i32", "long": "i64", "double": "f64"}[typ.base]
        return f"{_float(value)}_{suffix}" if typ.base == "double" else f"{value}{suffix}"
    inner = Type(typ.base, typ.dims - 1, typ.ref_str, typ.native)
    return "vec![" + ", ".join(rust(v, inner) for v in value) + "]"


# 큰 인자

BIG = 4000  # JSON으로 이보다 긴 인자는 호출 코드에 리터럴로 박지 않고 파일로 넘긴다
# (Java·Kotlin은 큰 리터럴을 컴파일하지 못하고(code too large), C++·Rust는 컴파일이 수십 초 걸린다. 잰 값)


def _deep(value, typ):
    _check(value, typ)
    if typ.dims:
        for item in value:
            _deep(item, Type(typ.base, typ.dims - 1, typ.ref_str, typ.native))


def file_text(value, typ):
    """큰 인자를 파일에 쓰는 글. 수·참거짓은 빈칸으로 나눈 낱말(맨 앞에 개수), 글 배열은 줄마다 하나(첫 줄에 개수. 2차원은 줄마다 원소 수가 앞선다), 글은 통째로.
    이 형을 파일로 넘길 수 없으면 None(리터럴로 쓴다)."""
    if typ.base == "string":
        if typ.dims == 0:
            return value
        if any("\n" in item or "\r" in item for item in (value if typ.dims == 1 else [s for row in value for s in row])):
            return None
        if typ.dims == 1:
            return "\n".join([str(len(value)), *value])
        return "\n".join([str(len(value)), *[line for row in value for line in (str(len(row)), *row)]])  # 줄마다: 줄 수, (원소 수, 원소들)…
    if typ.base == "double" or typ.dims == 0:
        return None
    word = (lambda v: "1" if v else "0") if typ.base == "bool" else str
    if typ.dims == 1:
        return f"{len(value)}\n" + " ".join(map(word, value))
    return f"{len(value)}\n" + "\n".join(" ".join([str(len(row)), *map(word, row)]) for row in value)


def argument(literal, reader, value, typ, work, name):
    """호출 코드에 쓸 인자 식. 작으면 리터럴(literal), 크면 work/name 파일에 쓰고 그것을 읽는 식(reader(typ, name))."""
    if len(json.dumps(value, ensure_ascii=False)) > BIG:
        _deep(value, typ)
        text = file_text(value, typ)
        if text is not None:
            (work / name).write_bytes(text.encode("utf-8"))
            return reader(typ, name)
    return literal(value, typ)

