from __future__ import annotations

from metametameta.validate_sync import check_sync, read_about_file_ast


def test_read_about_file_ast_reads_list_metadata(tmp_path):
    about_path = tmp_path / "__about__.py"
    about_path.write_text(
        '__title__ = "demo-app"\n__dependencies__ = ["click>=8", "rich"]\n',
        encoding="utf-8",
    )

    metadata = read_about_file_ast(about_path)

    assert metadata == {
        "__title__": "demo-app",
        "__dependencies__": ["click>=8", "rich"],
    }


def test_check_sync_accepts_matching_dependency_lists(tmp_path):
    about_path = tmp_path / "__about__.py"
    about_path.write_text(
        '__title__ = "demo-app"\n__dependencies__ = ["click>=8", "rich"]\n',
        encoding="utf-8",
    )

    mismatches = check_sync({"name": "demo-app", "dependencies": ["click>=8", "rich"]}, about_path)

    assert mismatches == []


def test_check_sync_reports_mismatched_dependency_lists(tmp_path):
    about_path = tmp_path / "__about__.py"
    about_path.write_text(
        '__title__ = "demo-app"\n__dependencies__ = ["click>=8", "rich"]\n',
        encoding="utf-8",
    )

    mismatches = check_sync({"name": "demo-app", "dependencies": ["click>=8", "httpx"]}, about_path)

    assert len(mismatches) == 1
    assert "__dependencies__" in mismatches[0]
