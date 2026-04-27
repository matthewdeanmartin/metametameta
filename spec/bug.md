---

Title: sync-check --output path handling is wrong, and read_about_file_ast misses annotated assignments

Version: metametameta 0.1.8

---
Bug 1: sync-check double-joins the package directory with --output

Description

handle_sync_check resolves the package directory automatically and then joins args.output onto it:

package_dir = _find_existing_package_dir(project_root, project_name)
about_path = package_dir / args.output

If the caller passes the full relative path to --output (e.g. --output phaithon/__about__.py), the result is phaithon/phaithon/__about__.py and the check
fails with "Metadata file not found".

The pep621 subcommand accepts a full path for --output without issue, so users naturally pass the same value to sync-check. The two commands behave
inconsistently.

Reproduce

metametameta sync-check --output phaithon/__about__.py

❌ Error during sync check: Metadata file not found at: …/phaithon/phaithon/__about__.py

Expected

Either (a) --output for sync-check should accept a full path and use it directly (skipping the package_dir / join), or (b) the help text should clearly
state it takes a bare filename, and the pep621 subcommand should be documented consistently.

---
Bug 2: read_about_file_ast silently ignores annotated assignments (ast.AnnAssign)

Description

read_about_file_ast in validate_sync.py walks the AST looking only for ast.Assign nodes:

if isinstance(node, ast.Assign):

Annotated assignments (x: SomeType = value) produce ast.AnnAssign nodes, which are never visited. This means a variable like:

__dependencies__: list[str] = []

is silently skipped, and sync-check then reports '__dependencies__' is missing from __about__.py even though it is present.

This is particularly confusing because the pep621 generator produces plain assignments (no annotation), but if a user or another tool writes the file with
type annotations — which is idiomatic Python — the check incorrectly fails.

Reproduce

Add an annotated assignment to __about__.py:

__dependencies__: list[str] = []

Run:

metametameta sync-check --output __about__.py

❌ Sync check failed. The following items are out of sync:
- '__dependencies__' is missing from __about__.py

Expected

read_about_file_ast should handle ast.AnnAssign nodes in addition to ast.Assign. The fix is straightforward:

for node in ast.walk(tree):
if isinstance(node, ast.AnnAssign):
target = node.target
value_node = node.value
if isinstance(target, ast.Name) and target.id.startswith("__") and value_node is not None:
try:
value = ast.literal_eval(value_node)
if _is_supported_sync_value(value):
metadata[target.id] = value
except ValueError:
logger.debug(f"Skipping non-literal annotation-assignment for {target.id}")
elif isinstance(node, ast.Assign):
# existing logic …

---
Both bugs were encountered together when running make metadata-check on Windows, but neither is platform-specific.