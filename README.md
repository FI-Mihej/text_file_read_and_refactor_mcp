![GitHub tag (with filter)](https://img.shields.io/github/v/tag/FI-Mihej/text_file_read_and_refactor_mcp) ![Static Badge](https://img.shields.io/badge/OS-Linux_%7C_Windows_%7C_macOS-blue)

![Static Badge](https://img.shields.io/badge/wheels-Linux_%7C_Windows_%7C_macOS-blue) ![Static Badge](https://img.shields.io/badge/Architecture-x86__64_%7C_ARM__64-blue)

![GitHub License](https://img.shields.io/github/license/FI-Mihej/text_file_read_and_refactor_mcp?color=darkgreen) ![Static Badge](https://img.shields.io/badge/API_status-Stable-darkgreen)

# Text File Read And Refactor MCP

Token-efficient Python stdio MCP server exposing safe text-file search,
reading, and refactoring tools. Tools automatically resolve the file BOM and
codepage; edit tools save files with their original encoding and BOM.

# Github repository

Github repository is a curated public mirror of the project. Active development (including experimental code and private research notes) happens in a private repository; selected snapshots are published here periodically.

## Installation

1. Install `uv`:
   https://docs.astral.sh/uv/getting-started/installation/

2. Configure your MCP client to run the server via `uvx`:

```json
{
  "mcpServers": {
    "text-file-read-and-refactor": {
      "command": "uvx",
      "args": [
        "text-file-read-and-refactor-mcp"
      ]
    }
  }
}
```

## Tools

`Slice` concept: an analog of the `slice(start: integer, stop: integer)` - stores the start and end indices of a range.

`Boundary` concept: an analog of the `Boundary(text: string, type: Enum[text, word, dev_word, regex])`

`Span` concept: an analog of the `Span(left_boundary: Boundary, right_boundary: Boundary)`. It allows for search/replace operations such as `give me the text between "my_config_param:" and ";"` or `replace the text between "%my_regex_1%" and "%my_regex_2%" with "my_text"`.

Read-only tools:

- `text_file__list_allowed_directories` - in pseudocode: "text_file__list_allowed_directories() -> List[directory_path]"
- `text_file__file_content_length` - in pseudocode: "text_file__file_content_length() -> integer_characters_num"
- `text_file__read_slice` - in pseudocode: "text_file__read_slice(characters_slice) -> text"
- `text_file__file_lines_num` - in pseudocode: "text_file__file_lines_num() -> integer_lines_num"
- `text_file__read_content_by_line_range` - in pseudocode: "text_file__read_content_by_line_range(lines_slice) -> text"
- `text_file__find_text` - in pseudocode: "text_file__find_text(text, type: Enum[text, word, dev_word]) -> characters_slice"
- `text_file__expand_slice_to_lines` - in pseudocode: "text_file__expand_slice_to_lines(characters_slice) -> lines_slice"
- `text_file__find_span_boundaries` - in pseudocode: "text_file__find_span_boundaries(left_boundary, right_boundary) -> Tuple[left_boundary_characters_slice, right_boundary_characters_slice]"
- `text_file__find_span_between_boundaries` - in pseudocode: "text_file__find_span_between_boundaries(left_boundary, right_boundary) -> text". Example: `text_file__find_span_between_boundaries("my_config_param:", ";")` will return string " my_value".
- `text_file__find_span_with_boundaries` - in pseudocode: "text_file__find_span_with_boundaries(left_boundary, right_boundary) -> text". Example: `text_file__find_span_with_boundaries("my_config_param:", ";")` will return string "my_config_param: my_value;".

Edit tools:

- `text_file__replace_content_by_line_range` - in pseudocode: "text_file__replace_content_by_line_range(text, lines_slice)"
- `text_file__replace_slice` - in pseudocode: "text_file__replace_slice(text, characters_slice)"
- `text_file__replace_text` - in pseudocode: "text_file__replace_slice(old_text, new_text)"
- `text_file__replace_span_between_boundaries` - in pseudocode: "text_file__replace_span_between_boundaries(text, left_boundary, right_boundary)".
- `text_file__replace_span_with_boundaries` - in pseudocode: "text_file__replace_span_with_boundaries(text, left_boundary, right_boundary)".
- `text_file__patch_spans_by_boundary_patterns` - in pseudocode: "text_file__patch_spans_by_boundary_patterns(List[Tuple[text, left_boundary, right_boundary]])".

# Cengal

Based on [Cengal](https://github.com/FI-Mihej/Cengal)

## Projects using Cengal

* [InterProcessPyObjects](https://github.com/FI-Mihej/InterProcessPyObjects) - High-performance package delivers blazing-fast inter-process communication through shared memory, enabling Python objects to be shared across processes with exceptional efficiency. 
* [cengal_app_dir_path_finder](https://github.com/FI-Mihej/cengal_app_dir_path_finder) - A Python module offering a unified API for easy retrieval of OS-specific application directories, enhancing data management across Windows, Linux, and macOS 
* [cengal_cpu_info](https://github.com/FI-Mihej/cengal_cpu_info) - Extended, cached CPU info with consistent output format.
* [cengal_memory_barriers](https://github.com/FI-Mihej/cengal_memory_barriers) - Fast cross-platform memory barriers for Python.
* [flet_async](https://github.com/FI-Mihej/flet_async) - wrapper which makes [Flet](https://github.com/flet-dev/flet) async and brings booth Cengal.coroutines and asyncio to Flet (Flutter based UI)
* [justpy_containers](https://github.com/FI-Mihej/justpy_containers) - wrapper around [JustPy](https://github.com/justpy-org/justpy) in order to bring more security and more production-needed features to JustPy (VueJS based UI)
* [Bensbach](https://github.com/FI-Mihej/Bensbach) - decompiler from Unreal Engine 3 bytecode to a Lisp-like script and compiler back to Unreal Engine 3 bytecode. Made for a game modding purposes
* [Realistic-Damage-Model-mod-for-Long-War](https://github.com/FI-Mihej/Realistic-Damage-Model-mod-for-Long-War) - Mod for both the original XCOM:EW and the mod Long War. Was made with a Bensbach, which was made with Cengal
* [SmartCATaloguer.com](http://www.smartcataloguer.com/index.html) - TagDB based catalog of images (tags), music albums (genre tags) and apps (categories)

# License

Copyright © 2026 ButenkoMS. All rights reserved.

Licensed under the Apache License, Version 2.0.
