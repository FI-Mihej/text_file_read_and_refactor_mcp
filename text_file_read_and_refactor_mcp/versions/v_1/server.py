#!/usr/bin/env python
# coding=utf-8

# Copyright © 2026 ButenkoMS. All rights reserved. Contacts: <gtalk@butenkoms.space>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path
from typing import Any


def _ensure_local_cengal_on_path() -> None:
    project_root = Path(__file__).resolve().parents[2]
    vendored_cengal = project_root / "dependencies" / "Cengal"
    if vendored_cengal.exists():
        sys.path.insert(0, str(vendored_cengal))


_ensure_local_cengal_on_path()

from cengal.text_processing.open_text_file import OpenTextFile
from cengal.text_processing.brackets_processing import (
    Bracket as CengalBoundaryMarker,
    BracketAbsentType as CengalBoundaryAbsentType,
    BracketPair as CengalBoundarySpan,
    Regex,
    Word,
    find_brackets as cengal_find_span_boundaries,
    find_text_in_brackets as cengal_find_span_between_boundaries,
    find_text_with_brackets as cengal_find_span_with_boundaries,
    replace_text_in_brackets as cengal_replace_span_between_boundaries,
    replace_text_with_brackets as cengal_replace_span_with_boundaries,
)
from cengal.text_processing.text_processing import (
    find_dev_word as cengal_find_dev_word,
    find_text as cengal_find_text,
    find_word as cengal_find_word,
    iterlines,
    replace_dev_word as cengal_replace_dev_word,
    replace_slice as cengal_replace_slice,
    replace_text as cengal_replace_text,
    replace_word as cengal_replace_word,
    rfind_dev_word as cengal_rfind_dev_word,
    rfind_text as cengal_rfind_text,
    rfind_word as cengal_rfind_word,
)
from cengal.text_processing.text_patch.brackets import patch_text as cengal_patch_spans_by_boundary_patterns

try:
    from cengal.text_processing.text_processing import (
        expand_slice_to_lines as cengal_expand_slice_to_lines,
    )
except ImportError:
    from cengal.text_processing.text_processing.versions.v_0.processing import (
        expand_slice_to_lines as cengal_expand_slice_to_lines,
    )


SERVER_NAME = "text_file_read_and_refactor_mcp"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"
TOOL_NAME_PREFIX = "text_file__"
SERVER_INSTRUCTIONS = r"""Exposing safe and token-efficient: text-file search,
reading, and refactoring tools. Tools automatically resolve the file BOM and
codepage; edit tools save files with their original encoding and BOM.

## Reading Text Files

At the beginning of any file analysis, always call the `text_file__file_content_length` tool and the `text_file__file_lines_num` tool to determine the file size and the total number of lines before reading its contents.

## Token-Efficient Source Code Analysis

When analyzing a source code file, minimize token usage whenever possible by first examining the declarations of exported classes, functions, and other publicly exposed entities.

For example, when analyzing a Python source file:

* Locate the `__all__` identifier using the `text_file__find_text` tool with `type` set to `dev_word`.
* Determine the line containing `__all__` with the `text_file__expand_slice_to_lines` tool.
* Read the exported identifiers incrementally with the `text_file__read_content_by_line_range` tool:

  * Read the next 5 lines.
  * If the export list continues, read the next 10 lines.
  * If it still continues, read the next 20 lines.
  * Continue increasing the range gradually until the export list is complete.

Next, gather a brief overview of each significant exported identifier.

For every significant identifier:

1. Locate all occurrences using the `text_file__find_text` tool with `type` set to `dev_word`. If the programming language allows identifiers to begin with digits, use `type` set to `word` instead.
2. Attempt to locate its definition in the following order:

  * As a class definition, using `text_file__find_span_between_boundaries` with `boundary_span` like `{"left": "class", "right": "<identifier>"}`.
  * If the resulting span is unrealistically large, continue searching from the previous stopping point until a realistic match is found or the end of the file is reached.
  * If no class definition exists, search for a function definition with `boundary_span` like `{"left": "def", "right": "<identifier>"}` using the same strategy.
  * If necessary, search for a variable definition:
    * Iteratively search for regular function definitions with `boundary_span` like `{"left": "\n", "right": "<identifier>"}`;
    * treat a span length of zero or one character as a successful match, since it covers all newline variants (`\n`, `\r\n`, and `\n\r`).
    * Variable assignments can be found with `boundary_span` like `{"left": "<identifier>", "right": "="}`.

Adapt these search patterns to the syntax of the analyzed programming language. The patterns only need to be sufficiently accurate to support efficient, token-conscious analysis rather than perfectly matching the language grammar.

For C and C++ projects, prefer analyzing the corresponding header file first to discover exported classes and functions. Before reading a header file, always determine its size, since it may be a header-only implementation. For other programming languages, apply an equivalent strategy appropriate to the language.

If the source file does not explicitly declare exported entities, or if internal classes and functions must also be analyzed, enumerate all definitions within the file.

## Boundary Span Arguments

Span-related tools use a `boundary_span` object with `left` and `right` markers. Do not put `start` or `end` inside `boundary_span`; top-level `start` and `stop` are optional numeric search offsets.

Canonical form:

```json
{"left": [{"type": "text", "text": "LEFT"}], "right": [{"type": "text", "text": "RIGHT"}]}
```

For a single plain-text marker on each side, the server also accepts this shorthand:

```json
{"left": "LEFT", "right": "RIGHT"}
```

For Python source files:

* Read the first line of the file before performing any searches, since it cannot be matched by the newline-based search pattern.
* Iteratively search for class definitions using `text_file__find_span_between_boundaries` with `boundary_span` like `{"left": "\n", "right": "class"}`.
* Iteratively search for asynchronous function definitions using `text_file__find_span_between_boundaries` with `boundary_span` like `{"left": "\n", "right": "async def"}`.
* Iteratively search for regular function definitions using `text_file__find_span_between_boundaries` with `boundary_span` like `{"left": "\n", "right": "def"}`.
* Treat a span length of zero or one character as a successful match, since it covers all newline variants (`\n`, `\r\n`, and `\n\r`).

For other programming languages, use equivalent syntax-aware patterns that are sufficiently accurate for efficient token usage rather than perfect language parsing.
""".strip()

JsonObject = dict[str, Any]
ToolHandler = Callable[[JsonObject], Any]

SLICE_SCHEMA: JsonObject = {
    "type": "object",
    "description": "Python-style slice object with optional start, stop, and step integer fields.",
    "properties": {
        "start": {"type": "integer"},
        "stop": {"type": "integer"},
        "step": {"type": "integer", "not": {"const": 0}},
    },
    "additionalProperties": False,
}

SOURCE_FILE_PATH_PROPERTY: JsonObject = {
    "type": "string",
    "description": (
        "Path to the text file to open for this tool call. The file must be "
        "located under one of the server's configured allowed directories."
    ),
}

BOUNDARY_MARKER_SCHEMA: JsonObject = {
    "type": "object",
    "description": (
        "Boundary marker descriptor. type selects how to match it. text is required for text, "
        "word, dev_word, and regex markers, and must be omitted for absent markers."
    ),
    "properties": {
        "type": {"type": "string", "enum": ["text", "word", "dev_word", "regex", "absent"]},
        "text": {
            "type": "string",
            "description": "Boundary marker text, whole-word text, identifier text, or regex pattern.",
        },
    },
    "required": ["type"],
    "additionalProperties": False,
    "allOf": [
        {
            "if": {"properties": {"type": {"enum": ["text", "word", "dev_word", "regex"]}}, "required": ["type"]},
            "then": {"required": ["text"]},
        },
        {
            "if": {"properties": {"type": {"const": "absent"}}, "required": ["type"]},
            "then": {"not": {"required": ["text"]}},
        },
    ],
}

BOUNDARY_MARKER_LIST_SCHEMA: JsonObject = {
    "description": (
        "One or more boundary markers. Canonical form is a non-empty array of marker objects. "
        "A string is shorthand for a single plain text marker; a marker object is shorthand for "
        "a one-item marker array."
    ),
    "oneOf": [
        {
            "type": "array",
            "items": BOUNDARY_MARKER_SCHEMA,
            "minItems": 1,
        },
        BOUNDARY_MARKER_SCHEMA,
        {
            "type": "string",
            "description": "Shorthand for a single plain text boundary marker.",
        },
    ],
}

BOUNDARY_SPAN_SCHEMA: JsonObject = {
    "type": "object",
    "description": (
        "Boundary span described by left and right boundary markers, not by start/end offsets. "
        "Canonical form: {\"left\":[{\"type\":\"text\",\"text\":\"LEFT\"}],"
        "\"right\":[{\"type\":\"text\",\"text\":\"RIGHT\"}]}. "
        "String shorthand is also accepted: {\"left\":\"LEFT\",\"right\":\"RIGHT\"}. "
        "Use an absent marker to mean the start or end of the file content."
    ),
    "properties": {
        "left": BOUNDARY_MARKER_LIST_SCHEMA,
        "right": BOUNDARY_MARKER_LIST_SCHEMA,
    },
    "required": ["left", "right"],
    "additionalProperties": False,
}

SLICE_HELP = (
    "Provide slices as JSON objects matching Python slice(start, stop, step); "
    "omit fields for None, and never use step 0."
)
EDIT_SAVE_NOTE = " The file is saved with its original encoding and BOM."
TOKEN_EFFICIENT_NOTE = (
    " Token-efficient: targets specific file content or returns compact structured "
    "results to reduce unnecessary context."
)


def slice_from_json(value: dict | None) -> slice:
    value = value or {}
    if not isinstance(value, dict):
        raise ValueError("slice must be an object")

    step = value.get("step")
    if step == 0:
        raise ValueError("slice.step must not be 0")
    for name in ("start", "stop", "step"):
        item = value.get(name)
        if item is not None and (not isinstance(item, int) or isinstance(item, bool)):
            raise ValueError(f"slice.{name} must be an integer when provided")

    return slice(
        value.get("start"),
        value.get("stop"),
        step,
    )


def slice_to_json(value: slice | None) -> dict | None:
    if value is None:
        return None

    result = {}

    if value.start is not None:
        result["start"] = value.start

    if value.stop is not None:
        result["stop"] = value.stop

    if value.step is not None:
        result["step"] = value.step

    return result


def boundary_marker_from_json(value: dict) -> CengalBoundaryMarker:
    if not isinstance(value, dict):
        raise ValueError("boundary marker must be an object")

    marker_type = value.get("type")
    text = value.get("text")
    if marker_type in {"text", "word", "dev_word", "regex"} and not isinstance(text, str):
        raise ValueError(f"{marker_type} boundary marker requires string text")
    if marker_type == "absent" and "text" in value:
        raise ValueError("absent boundary marker must omit text")

    if marker_type == "text":
        return CengalBoundaryMarker(text)

    if marker_type == "word":
        return CengalBoundaryMarker(Word(text))

    if marker_type == "dev_word":
        return CengalBoundaryMarker(Word(text, is_dev_word=True))

    if marker_type == "regex":
        return CengalBoundaryMarker(Regex(text))

    if marker_type == "absent":
        return CengalBoundaryMarker(CengalBoundaryAbsentType.data_bounds)

    raise ValueError(f"Unsupported boundary marker type: {marker_type!r}")


def boundary_marker_from_json_for_side(value: dict, *, is_left: bool) -> CengalBoundaryMarker:
    if not isinstance(value, dict):
        raise ValueError("boundary marker must be an object")

    if value.get("type") != "absent":
        return boundary_marker_from_json(value)

    if "text" in value:
        raise ValueError("absent boundary marker must omit text")

    absent_type = CengalBoundaryAbsentType.data_bounds_start if is_left else CengalBoundaryAbsentType.data_bounds_end
    return CengalBoundaryMarker(absent_type)


def boundary_marker_list_from_json_for_side(value: Any, *, is_left: bool, name: str) -> list[CengalBoundaryMarker]:
    if isinstance(value, str):
        return [CengalBoundaryMarker(value)]

    if isinstance(value, dict):
        return [boundary_marker_from_json_for_side(value, is_left=is_left)]

    if isinstance(value, list) and value:
        return [boundary_marker_from_json_for_side(item, is_left=is_left) for item in value]

    raise ValueError(f"{name} must be a string, marker object, or non-empty array of marker objects")


def boundary_span_from_json(value: dict) -> CengalBoundarySpan:
    if not isinstance(value, dict):
        raise ValueError("boundary_span must be an object")

    left = value.get("left")
    right = value.get("right")
    return CengalBoundarySpan(
        boundary_marker_list_from_json_for_side(left, is_left=True, name="boundary_span.left"),
        boundary_marker_list_from_json_for_side(right, is_left=False, name="boundary_span.right"),
    )


def _required_str(arguments: JsonObject, name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")

    return value


def _optional_int(arguments: JsonObject, name: str, default: int | None = None) -> int | None:
    value = arguments.get(name, default)
    if value is None:
        return None

    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer when provided")

    return value


def _optional_bool(arguments: JsonObject, name: str, default: bool) -> bool:
    value = arguments.get(name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")

    return value


def _find_text_type(arguments: JsonObject) -> str:
    value = arguments.get("type", "text")
    if value not in {"text", "word", "dev_word"}:
        raise ValueError("type must be one of: text, word, dev_word")

    return value


def _replace_text_type(arguments: JsonObject) -> str:
    value = arguments.get("text_type", "text")
    if value not in {"text", "word", "dev_word"}:
        raise ValueError("text_type must be one of: text, word, dev_word")

    return value


def _optional_forbidden_chars(arguments: JsonObject, name: str) -> Any:
    value = arguments.get(name)
    if value is None:
        return None

    if isinstance(value, str):
        return set(value)

    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return set(value)

    raise ValueError(f"{name} must be a string or an array of strings when provided")


@dataclass(frozen=True)
class FilesystemAccessControl:
    allowed_directories: tuple[Path, ...]

    @classmethod
    def from_paths(cls, directories: list[str] | tuple[str, ...]) -> "FilesystemAccessControl":
        allowed_directories: list[Path] = []
        for directory in directories:
            root = Path(directory).expanduser().resolve(strict=True)
            if not root.is_dir():
                raise ValueError(f"Allowed path is not a directory: {directory}")
            allowed_directories.append(root)

        return cls(tuple(allowed_directories))

    def list_allowed_directories(self) -> list[str]:
        return [str(directory) for directory in self.allowed_directories]

    def validate_source_file_path(self, source_file_path: str) -> str:
        if not self.allowed_directories:
            raise PermissionError(
                "No accessible directories were configured for "
                f"{SERVER_NAME}; start the server with one or more allowed directory arguments."
            )

        requested_path = Path(source_file_path).expanduser().resolve(strict=True)
        for allowed_directory in self.allowed_directories:
            if requested_path == allowed_directory or requested_path.is_relative_to(allowed_directory):
                return str(requested_path)

        allowed = ", ".join(str(directory) for directory in self.allowed_directories)
        raise PermissionError(
            f"Access denied for {requested_path}; file must be located under one of "
            f"the configured allowed directories: {allowed}"
        )


_FILE_ACCESS = FilesystemAccessControl(())
_FILE_ACCESS_CONFIGURED = False


def configure_allowed_directories(allowed_directories: list[str] | tuple[str, ...], *, force: bool = False) -> None:
    global _FILE_ACCESS, _FILE_ACCESS_CONFIGURED

    if _FILE_ACCESS_CONFIGURED and not force:
        raise RuntimeError("Allowed directories are already configured for this server process")

    _FILE_ACCESS = FilesystemAccessControl.from_paths(allowed_directories)
    _FILE_ACCESS_CONFIGURED = True


def _read_text_file(source_file_path: str) -> tuple[str, str, bytes]:
    source_file_path = _FILE_ACCESS.validate_source_file_path(source_file_path)
    with OpenTextFile(source_file_path, "rb") as text_file_info:
        return (
            text_file_info.text.value,
            text_file_info.encoding,
            text_file_info.bom_bytes,
        )


def _write_text_file(source_file_path: str, content: str, encoding: str, bom_bytes: bytes) -> None:
    source_file_path = _FILE_ACCESS.validate_source_file_path(source_file_path)
    opener = OpenTextFile(source_file_path, "wb", encoding=encoding)
    with opener as text_file_info:
        opener.bom_bytes = bom_bytes
        text_file_info.text.value = content


def _edit_text_file(source_file_path: str, edit: Callable[[str], Any]) -> Any:
    content, encoding, bom_bytes = _read_text_file(source_file_path)
    result = edit(content)
    new_content = result[0] if isinstance(result, tuple) else result
    if not isinstance(new_content, str):
        raise ValueError("edit operation must produce string content")

    _write_text_file(source_file_path, new_content, encoding, bom_bytes)
    return result


def _start_stop(arguments: JsonObject) -> tuple[int | None, int | None]:
    return _optional_int(arguments, "start"), _optional_int(arguments, "stop")


def _word_options(arguments: JsonObject) -> JsonObject:
    return {
        "weak_boundaries": _optional_bool(arguments, "weak_boundaries", True),
        "forbidden_init_chars": _optional_forbidden_chars(arguments, "forbidden_init_chars"),
        "forbidden_fin_chars": _optional_forbidden_chars(arguments, "forbidden_fin_chars"),
        "normalize_forbidden_init_chars": _optional_bool(arguments, "normalize_forbidden_init_chars", False),
        "normalize_forbidden_fin_chars": _optional_bool(arguments, "normalize_forbidden_fin_chars", False),
    }


def _boundary_span_options(arguments: JsonObject) -> JsonObject:
    return {
        "start": _optional_int(arguments, "start"),
        "stop": _optional_int(arguments, "stop"),
        "start_r": _optional_int(arguments, "start_r"),
        "weak_boundaries": _optional_bool(arguments, "weak_boundaries", True),
    }


def _line_content_slice(content: str, line_range: slice) -> slice:
    lines = list(iterlines(content))
    selected_lines = lines[line_range]
    if selected_lines:
        first_line = selected_lines[0][0]
        last_line = selected_lines[-1][0]
        return slice(first_line.start, last_line.stop)

    start, _, _ = line_range.indices(len(lines))
    if start < len(lines):
        insertion_point = lines[start][0].start
    else:
        insertion_point = len(content)

    return slice(insertion_point, insertion_point)


def _jsonable_result(value: Any) -> Any:
    if isinstance(value, slice):
        return slice_to_json(value)

    if isinstance(value, tuple):
        return [_jsonable_result(item) for item in value]

    if isinstance(value, list):
        return [_jsonable_result(item) for item in value]

    if isinstance(value, dict):
        return {key: _jsonable_result(item) for key, item in value.items()}

    return value


def _replacement_result(log: list[tuple[slice, slice]]) -> JsonObject:
    return {
        "replacements": len(log),
        "log": [
            {"old": slice_to_json(old_slice), "new": slice_to_json(new_slice)}
            for old_slice, new_slice in log
        ],
    }


def tool_file_content_length(arguments: JsonObject) -> int:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    return len(content)


def tool_read_slice(arguments: JsonObject) -> str:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    return content[slice_from_json(arguments.get("slice"))]


def tool_file_lines_num(arguments: JsonObject) -> int:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    return len(list(iterlines(content)))


def tool_read_content_by_line_range(arguments: JsonObject) -> str:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    content_slice = _line_content_slice(content, slice_from_json(arguments.get("line_range")))
    return content[content_slice]


def tool_replace_content_by_line_range(arguments: JsonObject) -> tuple[str, slice]:
    source_file_path = _required_str(arguments, "source_file_path")
    text = _required_str(arguments, "text")
    line_range = slice_from_json(arguments.get("line_range"))

    def edit(content: str) -> tuple[str, slice]:
        content_slice = _line_content_slice(content, line_range)
        return cengal_replace_slice(content, content_slice, text)

    return _edit_text_file(source_file_path, edit)


def tool_find_text(arguments: JsonObject) -> slice | None:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    start, stop = _start_stop(arguments)
    text = _required_str(arguments, "text")
    text_type = _find_text_type(arguments)
    rfind = _optional_bool(arguments, "rfind", False)

    if text_type == "word":
        search = cengal_rfind_word if rfind else cengal_find_word
        return search(content, text, start, stop, **_word_options(arguments))

    if text_type == "dev_word":
        search = cengal_rfind_dev_word if rfind else cengal_find_dev_word
        return search(content, text, start, stop, **_word_options(arguments))

    search = cengal_rfind_text if rfind else cengal_find_text
    return search(content, text, start, stop)


def tool_replace_slice(arguments: JsonObject) -> tuple[str, slice]:
    source_file_path = _required_str(arguments, "source_file_path")
    place = slice_from_json(arguments.get("place"))
    text = _required_str(arguments, "text")
    return _edit_text_file(source_file_path, lambda content: cengal_replace_slice(content, place, text))


def tool_replace_text(arguments: JsonObject) -> str:
    source_file_path = _required_str(arguments, "source_file_path")
    old_text = _required_str(arguments, "old_text")
    new_text = _required_str(arguments, "new_text")
    count = _optional_int(arguments, "count", -1)
    start, stop = _start_stop(arguments)
    text_type = _replace_text_type(arguments)

    if text_type == "word":
        return _edit_text_file(
            source_file_path,
            lambda content: cengal_replace_word(
                content,
                old_text,
                new_text,
                count,
                start,
                stop,
                **_word_options(arguments),
            ),
        )

    if text_type == "dev_word":
        return _edit_text_file(
            source_file_path,
            lambda content: cengal_replace_dev_word(
                content,
                old_text,
                new_text,
                count,
                start,
                stop,
                **_word_options(arguments),
            ),
        )

    return _edit_text_file(
        source_file_path,
        lambda content: cengal_replace_text(content, old_text, new_text, count, start, stop),
    )


def tool_expand_slice_to_lines(arguments: JsonObject) -> tuple[slice, slice]:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    place = slice_from_json(arguments.get("place"))
    return cengal_expand_slice_to_lines(content, place)


def tool_find_span_boundaries(arguments: JsonObject) -> JsonObject:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    left, right = cengal_find_span_boundaries(
        content,
        boundary_span_from_json(arguments.get("boundary_span")),
        **_boundary_span_options(arguments),
    )
    return {"left": slice_to_json(left), "right": slice_to_json(right)}


def tool_find_span_between_boundaries(arguments: JsonObject) -> slice | None:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    return cengal_find_span_between_boundaries(
        content,
        boundary_span_from_json(arguments.get("boundary_span")),
        **_boundary_span_options(arguments),
    )


def tool_find_span_with_boundaries(arguments: JsonObject) -> slice | None:
    content, _, _ = _read_text_file(_required_str(arguments, "source_file_path"))
    return cengal_find_span_with_boundaries(
        content,
        boundary_span_from_json(arguments.get("boundary_span")),
        **_boundary_span_options(arguments),
    )


def tool_replace_span_between_boundaries(arguments: JsonObject) -> JsonObject:
    source_file_path = _required_str(arguments, "source_file_path")
    boundary_span = boundary_span_from_json(arguments.get("boundary_span"))
    text = _required_str(arguments, "text")
    count = _optional_int(arguments, "count", -1)

    result, log = _edit_text_file(
        source_file_path,
        lambda content: cengal_replace_span_between_boundaries(content, boundary_span, text, count),
    )
    return {"content": result, **_replacement_result(log)}


def tool_replace_span_with_boundaries(arguments: JsonObject) -> JsonObject:
    source_file_path = _required_str(arguments, "source_file_path")
    boundary_span = boundary_span_from_json(arguments.get("boundary_span"))
    text = _required_str(arguments, "text")
    count = _optional_int(arguments, "count", -1)

    result, log = _edit_text_file(
        source_file_path,
        lambda content: cengal_replace_span_with_boundaries(content, boundary_span, text, count),
    )
    return {"content": result, **_replacement_result(log)}


def tool_patch_spans_by_boundary_patterns(arguments: JsonObject) -> str:
    source_file_path = _required_str(arguments, "source_file_path")
    patch = arguments.get("patch")
    if patch is None:
        converted_patch = [(boundary_span_from_json(arguments.get("boundary_span")), _required_str(arguments, "text"))]
    else:
        if not isinstance(patch, list) or not patch:
            raise ValueError("patch must be a non-empty array")

        converted_patch = []
        for item in patch:
            if not isinstance(item, dict):
                raise ValueError("each patch item must be an object")
            converted_patch.append((boundary_span_from_json(item.get("boundary_span")), _required_str(item, "text")))

    count = _optional_int(arguments, "count", 1)
    return _edit_text_file(
        source_file_path,
        lambda content: cengal_patch_spans_by_boundary_patterns(content, converted_patch, count),
    )


def tool_list_allowed_directories(arguments: JsonObject) -> list[str]:
    if arguments:
        raise ValueError("list_allowed_directories does not accept arguments")

    return _FILE_ACCESS.list_allowed_directories()


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: JsonObject
    handler: ToolHandler

    def as_mcp_tool(self) -> JsonObject:
        description = self.description
        if TOKEN_EFFICIENT_NOTE not in description:
            if description.endswith(EDIT_SAVE_NOTE):
                description = (
                    f"{description[:-len(EDIT_SAVE_NOTE)]}"
                    f"{TOKEN_EFFICIENT_NOTE}"
                    f"{EDIT_SAVE_NOTE}"
                )
            else:
                description = f"{description}{TOKEN_EFFICIENT_NOTE}"

        return {
            "name": self.name,
            "description": description,
            "inputSchema": self.input_schema,
        }


def _object_schema(properties: JsonObject, required: list[str]) -> JsonObject:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _object_schema_with_defs(properties: JsonObject, required: list[str]) -> JsonObject:
    schema = _object_schema(properties, required)
    schema["$defs"] = {
        "BoundaryMarker": BOUNDARY_MARKER_SCHEMA,
        "BoundarySpan": BOUNDARY_SPAN_SCHEMA,
    }
    return schema


def _range_properties(extra: JsonObject | None = None) -> JsonObject:
    properties = {
        "source_file_path": SOURCE_FILE_PATH_PROPERTY,
        "start": {"type": "integer", "description": "Start character offset. Omit for the beginning."},
        "stop": {"type": "integer", "description": "Stop character offset, exclusive. Omit for the end."},
    }
    if extra:
        properties.update(extra)

    return properties


def _word_option_properties() -> JsonObject:
    return {
        "weak_boundaries": {
            "type": "boolean",
            "default": True,
            "description": "Allow looser word-boundary matching around the target text.",
        },
        "forbidden_init_chars": {
            "description": "Characters that must not appear immediately before a matched word, as a string or array of strings.",
            "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
        },
        "forbidden_fin_chars": {
            "description": "Characters that must not appear immediately after a matched word, as a string or array of strings.",
            "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
        },
        "normalize_forbidden_init_chars": {
            "type": "boolean",
            "default": False,
            "description": "Advanced option for non-string content; keep false for normal text files.",
        },
        "normalize_forbidden_fin_chars": {
            "type": "boolean",
            "default": False,
            "description": "Advanced option for non-string content; keep false for normal text files.",
        },
    }


def _find_text_properties() -> JsonObject:
    return _range_properties(
        {
            "text": {"type": "string", "description": "Text to find."},
            "type": {
                "type": "string",
                "enum": ["text", "word", "dev_word"],
                "default": "text",
                "description": "Search mode: exact text, whole word, or identifier-style word.",
            },
            "rfind": {
                "type": "boolean",
                "default": False,
                "description": "When true, find the last match instead of the first match.",
            },
            **_word_option_properties(),
        }
    )


def _replace_text_properties() -> JsonObject:
    return _range_properties(
        {
            "old_text": {"type": "string", "description": "Text to replace."},
            "new_text": {"type": "string", "description": "Replacement text."},
            "count": {"type": "integer", "default": -1, "description": "Maximum replacements; -1 means all."},
            "text_type": {
                "type": "string",
                "enum": ["text", "word", "dev_word"],
                "default": "text",
                "description": "Replacement mode: exact text, whole word, or identifier-style word.",
            },
            **_word_option_properties(),
        }
    )


def _boundary_span_search_properties(extra: JsonObject | None = None) -> JsonObject:
    properties = {
        "source_file_path": SOURCE_FILE_PATH_PROPERTY,
        "boundary_span": BOUNDARY_SPAN_SCHEMA,
        "start": {
            "type": "integer",
            "description": "Inclusive start offset for the left boundary marker search. Omitted means the beginning.",
        },
        "stop": {
            "type": "integer",
            "description": "Exclusive stop offset for boundary span search. Omitted means the end.",
        },
        "start_r": {
            "type": "integer",
            "description": "Minimum start offset for the right boundary marker search. Negative values follow Python indexing semantics.",
        },
        "weak_boundaries": {
            "type": "boolean",
            "default": True,
            "description": "Allow looser word-boundary matching for word and identifier boundary markers.",
        },
    }
    if extra:
        properties.update(extra)

    return properties


def _boundary_span_replacement_properties() -> JsonObject:
    return {
        "source_file_path": SOURCE_FILE_PATH_PROPERTY,
        "boundary_span": BOUNDARY_SPAN_SCHEMA,
        "text": {"type": "string", "description": "Replacement text."},
        "count": {
            "type": "integer",
            "default": -1,
            "description": "Maximum number of replacements. Use -1 for unlimited replacements.",
        }
    }


_UNPREFIXED_TOOLS: dict[str, Tool] = {
    "list_allowed_directories": Tool(
        "list_allowed_directories",
        "Returns the filesystem directories this server is allowed to access. File paths used by other tools must be inside one of these directories.",
        _object_schema({}, []),
        tool_list_allowed_directories,
    ),
    "file_content_length": Tool(
        "file_content_length",
        "Opens the text file, automatically resolving the BOM and codepage. Returns the number of characters in the decoded file content.",
        _object_schema({"source_file_path": SOURCE_FILE_PATH_PROPERTY}, ["source_file_path"]),
        tool_file_content_length,
    ),
    "read_slice": Tool(
        "read_slice",
        f"Opens the text file, automatically resolving the BOM and codepage. Allows you to read any section of the file content (or the entire content) using Python-style slicing. {SLICE_HELP}",
        _object_schema(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "slice": SLICE_SCHEMA,
            },
            ["source_file_path", "slice"],
        ),
        tool_read_slice,
    ),
    "file_lines_num": Tool(
        "file_lines_num",
        "Opens the text file, automatically resolving the BOM and codepage. Returns the number of lines in the decoded file content.",
        _object_schema({"source_file_path": SOURCE_FILE_PATH_PROPERTY}, ["source_file_path"]),
        tool_file_lines_num,
    ),
    "read_content_by_line_range": Tool(
        "read_content_by_line_range",
        f"Opens the text file, automatically resolving the BOM and codepage. Reads complete lines selected by a Python-style line-number slice. {SLICE_HELP}",
        _object_schema(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "line_range": SLICE_SCHEMA,
            },
            ["source_file_path", "line_range"],
        ),
        tool_read_content_by_line_range,
    ),
    "replace_content_by_line_range": Tool(
        "replace_content_by_line_range",
        f"Opens the text file, automatically resolving the BOM and codepage. Replaces complete lines selected by a Python-style line-number slice, then writes the modified content back. {SLICE_HELP}{EDIT_SAVE_NOTE}",
        _object_schema(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "line_range": SLICE_SCHEMA,
                "text": {"type": "string", "description": "Replacement text."},
            },
            ["source_file_path", "line_range", "text"],
        ),
        tool_replace_content_by_line_range,
    ),
    "find_text": Tool(
        "find_text",
        "Opens the text file, automatically resolving the BOM and codepage. Finds the first or last exact text, whole-word, or identifier-style word match within optional start/stop character offsets and returns its slice, or null if not found.",
        _object_schema(_find_text_properties(), ["source_file_path", "text"]),
        tool_find_text,
    ),
    "expand_slice_to_lines": Tool(
        "expand_slice_to_lines",
        f"Opens the text file, automatically resolving the BOM and codepage. Expands a character slice to cover complete lines and returns both the expanded character slice and selected line-number slice. {SLICE_HELP}",
        _object_schema(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "place": SLICE_SCHEMA,
            },
            ["source_file_path", "place"],
        ),
        tool_expand_slice_to_lines,
    ),
    "replace_slice": Tool(
        "replace_slice",
        f"Opens the text file, automatically resolving the BOM and codepage. Replaces the content selected by a Python-style character slice, then writes the modified content back. {SLICE_HELP}{EDIT_SAVE_NOTE}",
        _object_schema(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "place": SLICE_SCHEMA,
                "text": {"type": "string", "description": "Replacement text."},
            },
            ["source_file_path", "place", "text"],
        ),
        tool_replace_slice,
    ),
    "replace_text": Tool(
        "replace_text",
        f"Opens the text file, automatically resolving the BOM and codepage. Replaces exact substring, whole-word, or identifier-style word matches within optional start/stop character offsets, then writes the modified content back.{EDIT_SAVE_NOTE}",
        _object_schema(_replace_text_properties(), ["source_file_path", "old_text", "new_text"]),
        tool_replace_text,
    ),
    "find_span_boundaries": Tool(
        "find_span_boundaries",
        "Opens the text file, automatically resolving the BOM and codepage. Finds matching left and right boundary markers described by the boundary_span object and returns their slices.",
        _object_schema_with_defs(_boundary_span_search_properties(), ["source_file_path", "boundary_span"]),
        tool_find_span_boundaries,
    ),
    "find_span_between_boundaries": Tool(
        "find_span_between_boundaries",
        "Opens the text file, automatically resolving the BOM and codepage. Finds content between matching boundary markers described by the boundary_span object and returns the inner slice, or null if not found.",
        _object_schema_with_defs(_boundary_span_search_properties(), ["source_file_path", "boundary_span"]),
        tool_find_span_between_boundaries,
    ),
    "find_span_with_boundaries": Tool(
        "find_span_with_boundaries",
        "Opens the text file, automatically resolving the BOM and codepage. Finds content plus its surrounding matching boundary markers and returns the full slice, or null if not found.",
        _object_schema_with_defs(_boundary_span_search_properties(), ["source_file_path", "boundary_span"]),
        tool_find_span_with_boundaries,
    ),
    "replace_span_between_boundaries": Tool(
        "replace_span_between_boundaries",
        f"Opens the text file, automatically resolving the BOM and codepage. Replaces only the content between matching boundary markers, preserves the boundary markers, then writes the modified content back.{EDIT_SAVE_NOTE}",
        _object_schema_with_defs(_boundary_span_replacement_properties(), ["source_file_path", "boundary_span", "text"]),
        tool_replace_span_between_boundaries,
    ),
    "replace_span_with_boundaries": Tool(
        "replace_span_with_boundaries",
        f"Opens the text file, automatically resolving the BOM and codepage. Replaces matching boundary markers together with the content between them, then writes the modified content back.{EDIT_SAVE_NOTE}",
        _object_schema_with_defs(_boundary_span_replacement_properties(), ["source_file_path", "boundary_span", "text"]),
        tool_replace_span_with_boundaries,
    ),
    "patch_spans_by_boundary_patterns": Tool(
        "patch_spans_by_boundary_patterns",
        f"Opens the text file, automatically resolving the BOM and codepage. Applies one boundary-span replacement or an ordered list of boundary-span replacements, then writes the modified content back.{EDIT_SAVE_NOTE}",
        _object_schema_with_defs(
            {
                "source_file_path": SOURCE_FILE_PATH_PROPERTY,
                "boundary_span": BOUNDARY_SPAN_SCHEMA,
                "text": {"type": "string", "description": "Replacement text for the top-level boundary span."},
                "patch": {
                    "type": "array",
                    "minItems": 1,
                    "description": "Optional ordered list of boundary-span replacements. Omit when using top-level boundary_span and text.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "boundary_span": BOUNDARY_SPAN_SCHEMA,
                            "text": {"type": "string", "description": "Replacement text for this boundary span."},
                        },
                        "required": ["boundary_span", "text"],
                        "additionalProperties": False,
                    },
                },
                "count": {
                    "type": "integer",
                    "default": 1,
                    "description": "Maximum number of full patch passes. Negative values repeat while patch items keep matching.",
                },
            },
            ["source_file_path"],
        ),
        tool_patch_spans_by_boundary_patterns,
    ),
}


def _exported_tool_name(name: str) -> str:
    return f"{TOOL_NAME_PREFIX}{name}"


TOOLS: dict[str, Tool] = {
    _exported_tool_name(name): dataclass_replace(tool, name=_exported_tool_name(tool.name))
    for name, tool in _UNPREFIXED_TOOLS.items()
}


def _success_response(message_id: Any, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error_response(message_id: Any, code: int, message: str, data: Any = None) -> JsonObject:
    error: JsonObject = {"code": code, "message": message}
    if data is not None:
        error["data"] = data

    return {"jsonrpc": "2.0", "id": message_id, "error": error}


def _tool_call_result(result: Any, is_error: bool = False) -> JsonObject:
    jsonable_result = _jsonable_result(result)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(jsonable_result, ensure_ascii=False),
            }
        ],
        "isError": is_error,
    }


def handle_request(message: JsonObject) -> JsonObject | None:
    message_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    is_notification = "id" not in message

    if method == "initialize":
        if not isinstance(params, dict):
            return _error_response(message_id, -32602, "Request params must be an object")

        protocol_version = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
        return _success_response(
            message_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": SERVER_INSTRUCTIONS,
            },
        )

    if method == "notifications/initialized":
        return None

    if is_notification:
        return None

    if not isinstance(params, dict):
        return _error_response(message_id, -32602, "Request params must be an object")

    if method == "ping":
        return _success_response(message_id, {})

    if method == "tools/list":
        return _success_response(message_id, {"tools": [tool.as_mcp_tool() for tool in TOOLS.values()]})

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(tool_name, str) or tool_name not in TOOLS:
            return _error_response(message_id, -32602, f"Unknown tool: {tool_name!r}")

        if not isinstance(arguments, dict):
            return _error_response(message_id, -32602, "Tool arguments must be an object")

        try:
            result = TOOLS[tool_name].handler(arguments)
        except Exception as exc:
            return _success_response(message_id, _tool_call_result(str(exc), is_error=True))

        return _success_response(message_id, _tool_call_result(result))

    if method == "resources/list":
        return _success_response(message_id, {"resources": []})

    if method == "prompts/list":
        return _success_response(message_id, {"prompts": []})

    return _error_response(message_id, -32601, f"Method not found: {method}")


def run_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError("JSON-RPC message must be an object")
        except Exception as exc:
            response = _error_response(None, -32700, "Parse error", str(exc))
        else:
            response = handle_request(message)

        if response is not None:
            sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
            sys.stdout.buffer.flush()


def main(argv: list[str] | None = None) -> None:
    configure_allowed_directories(sys.argv[1:] if argv is None else argv)
    run_stdio()


if __name__ == "__main__":
    main()
