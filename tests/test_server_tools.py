import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text_file_read_and_refactor_mcp.versions.v_1.server import (  # noqa: E402
    SERVER_INSTRUCTIONS,
    configure_allowed_directories,
    handle_request,
    slice_from_json,
    slice_to_json,
    tool_expand_slice_to_lines,
    tool_file_content_length,
    tool_find_span_boundaries,
    tool_find_text,
    tool_find_span_between_boundaries,
    tool_find_span_with_boundaries,
    tool_patch_spans_by_boundary_patterns,
    tool_read_content_by_line_range,
    tool_read_slice,
    tool_replace_text,
    tool_replace_slice,
    tool_replace_span_between_boundaries,
    TOOLS,
)


@pytest.fixture(autouse=True)
def allow_tmp_path(tmp_path):
    configure_allowed_directories([str(tmp_path)], force=True)


def test_slice_json_roundtrip():
    assert slice_from_json({}) == slice(None, None, None)
    assert slice_to_json(slice(1, 5, None)) == {"start": 1, "stop": 5}


def test_slice_json_rejects_zero_step():
    try:
        slice_from_json({"step": 0})
    except ValueError as exc:
        assert "must not be 0" in str(exc)
    else:
        raise AssertionError("slice_from_json accepted step=0")


def test_initialize_returns_llm_instructions():
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
    )

    assert response["id"] == 1
    result = response["result"]
    assert result["instructions"] == SERVER_INSTRUCTIONS
    assert "Reading Text Files" in result["instructions"]
    assert "Token-Efficient Source Code Analysis" in result["instructions"]


def test_read_and_find_tools(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"alpha\nbeta\ngamma\n")

    args = {"source_file_path": str(source)}
    assert tool_file_content_length(args) == len("alpha\nbeta\ngamma\n")
    assert tool_read_slice({**args, "slice": {"start": 6, "stop": 10}}) == "beta"
    assert tool_read_content_by_line_range({**args, "line_range": {"start": 1, "stop": 3}}) == "beta\ngamma\n"
    assert tool_find_text({**args, "text": "beta"}) == slice(6, 10)
    assert tool_find_text({**args, "text": "a", "rfind": True}) == slice(15, 16)


def test_file_access_rejects_unconfigured_roots(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"alpha\n")
    configure_allowed_directories([], force=True)

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "text_file__file_content_length", "arguments": {"source_file_path": str(source)}},
        }
    )

    assert response["id"] == 1
    result = response["result"]
    assert result["isError"] is True
    assert "No accessible directories were configured" in json.loads(result["content"][0]["text"])


def test_file_access_rejects_paths_outside_allowed_root(tmp_path):
    allowed_root = tmp_path / "allowed"
    denied_root = tmp_path / "denied"
    allowed_root.mkdir()
    denied_root.mkdir()
    source = denied_root / "sample.txt"
    source.write_bytes(b"alpha\n")
    configure_allowed_directories([str(allowed_root)], force=True)

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "text_file__file_content_length", "arguments": {"source_file_path": str(source)}},
        }
    )

    assert response["id"] == 1
    result = response["result"]
    assert result["isError"] is True
    assert "Access denied" in json.loads(result["content"][0]["text"])


def test_list_allowed_directories_tool(tmp_path):
    configure_allowed_directories([str(tmp_path)], force=True)

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "text_file__list_allowed_directories", "arguments": {}},
        }
    )

    assert response["id"] == 1
    result = response["result"]
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"]) == [str(tmp_path.resolve())]


def test_allowed_directories_are_immutable_after_configuration(tmp_path):
    configure_allowed_directories([str(tmp_path)], force=True)

    with pytest.raises(RuntimeError, match="already configured"):
        configure_allowed_directories([str(tmp_path)])


def test_expand_slice_to_lines(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"alpha\nbeta\ngamma\n")

    args = {"source_file_path": str(source), "place": {"start": 7, "stop": 13}}

    assert tool_expand_slice_to_lines(args) == (slice(6, 17), slice(1, 3))

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "text_file__expand_slice_to_lines", "arguments": args},
        }
    )

    assert response["id"] == 1
    result_text = response["result"]["content"][0]["text"]
    assert json.loads(result_text) == [{"start": 6, "stop": 17}, {"start": 1, "stop": 3}]


def test_dev_word_replace_does_not_touch_identifier_parts(tmp_path):
    source = tmp_path / "sample.py"
    source.write_bytes(b"foo foo_bar foo\n")

    args = {"source_file_path": str(source)}
    assert tool_find_text({**args, "text": "foo", "type": "dev_word"}) == slice(0, 3)
    assert tool_find_text({**args, "text": "foo", "type": "dev_word", "rfind": True}) == slice(12, 15)
    result = tool_replace_text({**args, "old_text": "foo", "new_text": "bar", "text_type": "dev_word"})

    assert result == "bar foo_bar bar\n"
    assert source.read_text(encoding="utf-8") == "bar foo_bar bar\n"


def test_word_replace_uses_replace_text_text_type(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"foo foobar foo\n")

    result = tool_replace_text(
        {
            "source_file_path": str(source),
            "old_text": "foo",
            "new_text": "bar",
            "text_type": "word",
        }
    )

    assert result == "bar foobar bar\n"
    assert source.read_text(encoding="utf-8") == "bar foobar bar\n"


def test_replace_slice_writes_shorter_content(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"abcdef")

    result, result_slice = tool_replace_slice(
        {"source_file_path": str(source), "place": {"start": 1, "stop": 5}, "text": "X"}
    )

    assert result == "aXf"
    assert result_slice == slice(1, 2)
    assert source.read_text(encoding="utf-8") == "aXf"


def test_boundary_span_find_tools(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"pre <tag>inner</tag> post\n")
    args = {
        "source_file_path": str(source),
        "boundary_span": {
            "left": [{"type": "text", "text": "<tag>"}],
            "right": [{"type": "text", "text": "</tag>"}],
        },
    }

    assert tool_find_span_boundaries(args) == {
        "left": {"start": 4, "stop": 9},
        "right": {"start": 14, "stop": 20},
    }
    assert tool_find_span_between_boundaries(args) == slice(9, 14)
    assert tool_find_span_with_boundaries(args) == slice(4, 20)


def test_boundary_span_string_shorthand(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"pre <tag>inner</tag> post\n")
    args = {
        "source_file_path": str(source),
        "boundary_span": {"left": "<tag>", "right": "</tag>"},
    }

    assert tool_find_span_boundaries(args) == {
        "left": {"start": 4, "stop": 9},
        "right": {"start": 14, "stop": 20},
    }
    assert tool_find_span_between_boundaries(args) == slice(9, 14)
    assert tool_find_span_with_boundaries(args) == slice(4, 20)


def test_absent_boundary_marker(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"alpha END")
    args = {
        "source_file_path": str(source),
        "boundary_span": {
            "left": [{"type": "absent"}],
            "right": [{"type": "text", "text": " END"}],
        },
    }

    assert tool_find_span_boundaries(args) == {
        "left": {"start": 0, "stop": 0},
        "right": {"start": 5, "stop": 9},
    }
    assert tool_find_span_between_boundaries(args) == slice(0, 5)


def test_replace_span_between_boundaries_writes_and_returns_log(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"pre <tag>inner</tag> post\n")
    args = {
        "source_file_path": str(source),
        "boundary_span": {
            "left": [{"type": "text", "text": "<tag>"}],
            "right": [{"type": "text", "text": "</tag>"}],
        },
        "text": "X",
    }

    result = tool_replace_span_between_boundaries(args)

    assert result == {
        "content": "pre <tag>X</tag> post\n",
        "replacements": 1,
        "log": [{"old": {"start": 9, "stop": 14}, "new": {"start": 9, "stop": 10}}],
    }
    assert source.read_text(encoding="utf-8") == "pre <tag>X</tag> post\n"


def test_patch_spans_by_boundary_patterns(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"<a>1</a> <b>2</b>")
    result = tool_patch_spans_by_boundary_patterns(
        {
            "source_file_path": str(source),
            "patch": [
                {
                    "boundary_span": {
                        "left": [{"type": "text", "text": "<a>"}],
                        "right": [{"type": "text", "text": "</a>"}],
                    },
                    "text": "x",
                },
                {
                    "boundary_span": {
                        "left": [{"type": "text", "text": "<b>"}],
                        "right": [{"type": "text", "text": "</b>"}],
                    },
                    "text": "y",
                },
            ],
        }
    )

    assert result == "<a>x</a> <b>y</b>"
    assert source.read_text(encoding="utf-8") == "<a>x</a> <b>y</b>"


def test_patch_spans_by_boundary_patterns_single_pair_form(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_bytes(b"<a>1</a> <a>2</a>")
    result = tool_patch_spans_by_boundary_patterns(
        {
            "source_file_path": str(source),
            "boundary_span": {
                "left": [{"type": "text", "text": "<a>"}],
                "right": [{"type": "text", "text": "</a>"}],
            },
            "text": "x",
        }
    )

    assert result == "<a>x</a> <a>2</a>"
    assert source.read_text(encoding="utf-8") == "<a>x</a> <a>2</a>"


def test_mcp_tools_list():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response["id"] == 1
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert "text_file__find_text" in names
    assert "text_file__rfind_text" not in names
    assert "text_file__find_word" not in names
    assert "text_file__rfind_word" not in names
    assert "text_file__find_dev_word" not in names
    assert "text_file__rfind_dev_word" not in names
    assert "text_file__list_allowed_directories" in names
    assert "text_file__expand_slice_to_lines" in names
    assert "text_file__replace_text" in names
    assert "text_file__replace_word" not in names
    assert "text_file__replace_dev_word" not in names
    assert "text_file__find_span_between_boundaries" in names
    assert "text_file__replace_span_with_boundaries" in names
    assert "text_file__patch_spans_by_boundary_patterns" in names


def test_find_text_schema_exposes_search_type_and_reverse_flag():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = response["result"]["tools"]
    tool = next(item for item in tools if item["name"] == "text_file__find_text")
    properties = tool["inputSchema"]["properties"]

    assert properties["type"]["enum"] == ["text", "word", "dev_word"]
    assert properties["type"]["default"] == "text"
    assert properties["rfind"]["type"] == "boolean"
    assert properties["rfind"]["default"] is False


def test_replace_text_schema_exposes_text_type():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = response["result"]["tools"]
    tool = next(item for item in tools if item["name"] == "text_file__replace_text")
    properties = tool["inputSchema"]["properties"]

    assert properties["text_type"]["enum"] == ["text", "word", "dev_word"]
    assert properties["text_type"]["default"] == "text"


def test_span_tool_schema_exposes_boundary_span_shape():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = response["result"]["tools"]
    tool = next(item for item in tools if item["name"] == "text_file__find_span_between_boundaries")
    boundary_span = tool["inputSchema"]["properties"]["boundary_span"]

    assert "$ref" not in boundary_span
    assert set(boundary_span["properties"]) == {"left", "right"}
    assert {option["type"] for option in boundary_span["properties"]["left"]["oneOf"] if "type" in option} >= {"array", "object", "string"}
    assert "start/end" in boundary_span["description"]


def test_mcp_tool_descriptions_are_client_facing():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = response["result"]["tools"]
    serialized_tools = json.dumps(tools, ensure_ascii=False).lower()
    edit_tool_names = {
        "text_file__replace_content_by_line_range",
        "text_file__replace_slice",
        "text_file__replace_text",
        "text_file__replace_span_between_boundaries",
        "text_file__replace_span_with_boundaries",
        "text_file__patch_spans_by_boundary_patterns",
    }

    assert "cengal" not in serialized_tools
    assert "wrap " not in serialized_tools
    assert "bracket" not in serialized_tools
    assert "brackets" not in serialized_tools
    assert {tool["name"] for tool in tools} == set(TOOLS)
    assert all("token-efficient" in tool["description"].lower() for tool in tools)
    for tool in tools:
        if tool["name"] in edit_tool_names:
            assert tool["description"].endswith("The file is saved with its original encoding and BOM.")
