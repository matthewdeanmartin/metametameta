"""
Entire GUI for metametameta: app, panels, widgets, runner.

Sections are marked with comment banners for easy navigation.
"""

# pylint: disable=too-many-ancestors,import-outside-toplevel

from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

# ── Colour palette (Catppuccin Mocha inspired) ──────────────

CLR_OK = "#22c55e"  # green  -- valid / success
CLR_WARN = "#eab308"  # yellow -- warnings
CLR_ERR = "#ef4444"  # red    -- errors
CLR_DIM = "#9ca3af"  # grey   -- secondary text
CLR_BG = "#1e1e2e"  # dark   -- main background
CLR_BG_ALT = "#252536"  # slightly lighter -- text widgets
CLR_FG = "#cdd6f4"  # light  -- primary text
CLR_ACCENT = "#89b4fa"  # blue   -- headings, active sidebar
CLR_SIDEBAR = "#181825"  # darkest -- sidebar background
CLR_BTN = "#313244"  # button background
CLR_BTN_ACTIVE = "#45475a"  # button hover

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)

# ── Background runner ───────────────────────────────────────


class BackgroundRunner:
    """Run functions off the UI thread, post results back via root.after()."""

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the background runner.

        Args:
            root: The root Tkinter window to use for scheduling callbacks.
        """
        self.root = root

    def run(
        self,
        func: Callable[..., Any],
        *,
        args: tuple[Any, ...] = (),
        on_success: Callable[..., Any] | None = None,
        on_error: Callable[[Exception], Any] | None = None,
    ) -> None:
        """
        Run a function in a background thread.

        Args:
            func: The function to run.
            args: Arguments to pass to the function.
            on_success: Callback to run on success (in the UI thread).
            on_error: Callback to run on error (in the UI thread).
        """

        def worker() -> None:
            """Internal worker function to execute the task and handle callbacks."""
            try:
                result = func(*args)
                if on_success:
                    self.root.after(0, on_success, result)
            except Exception as exc:
                if on_error:
                    self.root.after(0, on_error, exc)

        t = threading.Thread(target=worker, daemon=True)
        t.start()


# ── Reusable widget helpers ─────────────────────────────────


def make_tree(parent: tk.Widget, columns: list[str], height: int = 12) -> ttk.Treeview:
    """Create a themed treeview with scrollbar and colour tags."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Path.Treeview",
        background=CLR_BG_ALT,
        foreground=CLR_FG,
        fieldbackground=CLR_BG_ALT,
        font=FONT_MONO,
        rowheight=22,
    )
    style.configure(
        "Path.Treeview.Heading",
        background=CLR_BTN,
        foreground=CLR_FG,
        font=FONT_UI_BOLD,
    )
    style.map("Path.Treeview", background=[("selected", CLR_BTN_ACTIVE)])

    frame = tk.Frame(parent, bg=CLR_BG)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, style="Path.Treeview")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor=tk.W)

    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    tree.tag_configure("ok", foreground=CLR_OK)
    tree.tag_configure("warn", foreground=CLR_WARN)
    tree.tag_configure("error", foreground=CLR_ERR)
    tree.tag_configure("dim", foreground=CLR_DIM)
    return tree


def make_output(parent: tk.Widget, height: int = 15) -> tk.Text:
    """Read-only scrolled text area for output display."""
    frame = tk.Frame(parent, bg=CLR_BG)
    text = tk.Text(
        frame,
        height=height,
        bg=CLR_BG_ALT,
        fg=CLR_FG,
        insertbackground=CLR_FG,
        font=FONT_MONO,
        wrap=tk.WORD,
        relief=tk.FLAT,
        padx=8,
        pady=8,
        state=tk.DISABLED,
    )
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)

    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    return text


def output_set(text_widget: tk.Text, content: str) -> None:
    """Replace text content (handles enable/disable state)."""
    text_widget.configure(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", content)
    text_widget.configure(state=tk.DISABLED)


def make_toolbar(parent: tk.Widget) -> tk.Frame:
    """Horizontal button bar."""
    toolbar = tk.Frame(parent, bg=CLR_BG)
    toolbar.pack(fill=tk.X, padx=8, pady=(4, 8))
    return toolbar


def toolbar_btn(toolbar: tk.Frame, text: str, command: Callable[[], Any]) -> tk.Button:
    """Themed button inside a toolbar."""
    btn = tk.Button(
        toolbar,
        text=text,
        bg=CLR_BTN,
        fg=CLR_FG,
        activebackground=CLR_BTN_ACTIVE,
        activeforeground=CLR_FG,
        font=FONT_UI,
        relief=tk.FLAT,
        padx=12,
        pady=4,
        cursor="hand2",
        command=command,
    )
    btn.pack(side=tk.LEFT, padx=4)
    return btn


def make_heading(parent: tk.Widget, text: str) -> tk.Label:
    """Section heading label."""
    lbl = tk.Label(parent, text=text, bg=CLR_BG, fg=CLR_ACCENT, font=FONT_HEADING, anchor=tk.W)
    lbl.pack(fill=tk.X, padx=8, pady=(12, 4))
    return lbl


def make_label(parent: tk.Widget, text: str) -> tk.Label:
    """Normal text label."""
    lbl = tk.Label(parent, text=text, bg=CLR_BG, fg=CLR_FG, font=FONT_UI, anchor=tk.W)
    lbl.pack(fill=tk.X, padx=8, pady=(2, 2))
    return lbl


def make_entry_row(parent: tk.Widget, label: str, default: str = "") -> tuple[tk.Frame, tk.Entry, tk.StringVar]:
    """Label + entry on a row. Returns (frame, entry, stringvar)."""
    frame = tk.Frame(parent, bg=CLR_BG)
    frame.pack(fill=tk.X, padx=8, pady=2)
    tk.Label(frame, text=label, bg=CLR_BG, fg=CLR_FG, font=FONT_UI, width=14, anchor=tk.W).pack(side=tk.LEFT)
    var = tk.StringVar(value=default)
    entry = tk.Entry(
        frame, textvariable=var, bg=CLR_BG_ALT, fg=CLR_FG, insertbackground=CLR_FG, font=FONT_MONO, relief=tk.FLAT
    )
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
    return frame, entry, var


# ── Base panel ──────────────────────────────────────────────


class BasePanel(tk.Frame):
    """Base class for all GUI panels."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        """
        Initialize the base panel.

        Args:
            parent: The parent widget.
            runner: The background runner instance.
            status_var: The status bar string variable.
        """
        super().__init__(parent, bg=CLR_BG)
        self.runner = runner
        self.status = status_var


# ── Dashboard panel ─────────────────────────────────────────


class DashboardPanel(BasePanel):
    """Overview: auto-detect source and show current project metadata."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        """
        Initialize the dashboard panel.

        Args:
            parent: The parent widget.
            runner: The background runner instance.
            status_var: The status bar string variable.
        """
        super().__init__(parent, runner, status_var)
        make_heading(self, "Dashboard")
        make_label(self, "Detect your project's metadata source and preview what will be generated.")

        make_toolbar(self)
        self.dir_var = tk.StringVar(value=str(Path.cwd()))
        _, _, self.dir_var = make_entry_row(self, "Project root:", str(Path.cwd()))

        bar2 = make_toolbar(self)
        toolbar_btn(bar2, "Browse...", self.browse)
        toolbar_btn(bar2, "Detect Source", self.detect)

        self.output = make_output(self, height=18)

        # Auto-run detection on panel open
        self.after(50, self.detect)

    def browse(self) -> None:
        """Open a directory browser and update the project root variable."""
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def detect(self) -> None:
        """Initiate auto-detection of the metadata source in the background."""
        self.status.set("Detecting metadata source...")
        self.runner.run(
            self.fetch,
            args=(self.dir_var.get(),),
            on_success=self.display,
            on_error=self.on_error,
        )

    @staticmethod
    def fetch(project_root_str: str) -> dict[str, Any]:
        """
        Fetch metadata from the detected source.

        Args:
            project_root_str: Path to the project root directory.

        Returns:
            Dictionary containing the detected source type and metadata.
        """
        from metametameta.autodetect import detect_source

        root = Path(project_root_str)
        source_type = detect_source(root)

        # Read metadata from the detected source
        from metametameta.from_conda_meta import read_conda_meta_metadata
        from metametameta.from_pep621 import read_pep621_metadata
        from metametameta.from_poetry import read_poetry_metadata
        from metametameta.from_requirements_txt import read_requirements_txt_metadata
        from metametameta.from_setup_cfg import read_setup_cfg_metadata
        from metametameta.from_setup_py import read_setup_py_metadata

        readers = {
            "pep621": lambda: read_pep621_metadata(source=str(root / "pyproject.toml")),
            "poetry": lambda: read_poetry_metadata(source=str(root / "pyproject.toml")),
            "setup_cfg": lambda: read_setup_cfg_metadata(setup_cfg_path=root / "setup.cfg"),
            "setup_py": lambda: read_setup_py_metadata(source=str(root / "setup.py")),
            "requirements_txt": lambda: read_requirements_txt_metadata(source=str(root / "requirements.txt")),
            "conda_meta": lambda: read_conda_meta_metadata(source=str(root / "conda" / "meta.yaml")),
        }
        metadata = readers[source_type]()
        return {"source_type": source_type, "metadata": metadata}

    def display(self, result: dict[str, Any]) -> None:
        """
        Display the detection results in the output area.

        Args:
            result: Dictionary containing the source type and metadata.
        """
        source_type = result["source_type"]
        metadata = result["metadata"]
        lines = [f"Detected source: {source_type}", ""]
        for key, value in metadata.items():
            lines.append(f"  {key}: {value}")
        output_set(self.output, "\n".join(lines))
        self.status.set(f"Detected: {source_type}")

    def on_error(self, exc: Exception) -> None:
        """
        Handle errors during metadata detection.

        Args:
            exc: The exception encountered.
        """
        output_set(self.output, f"Error: {exc}")
        self.status.set("Detection failed")


# ── Generate panel ──────────────────────────────────────────


class GeneratePanel(BasePanel):
    """Generate __about__.py from a chosen source."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        super().__init__(parent, runner, status_var)
        make_heading(self, "Generate __about__.py")
        make_label(self, "Choose a metadata source and generate your __about__.py file.")

        # Source selector
        selector_frame = tk.Frame(self, bg=CLR_BG)
        selector_frame.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(selector_frame, text="Source:", bg=CLR_BG, fg=CLR_FG, font=FONT_UI).pack(side=tk.LEFT)

        self.source_var = tk.StringVar(value="auto")
        sources = ["auto", "pep621", "poetry", "setup_cfg", "setup_py", "importlib", "requirements_txt", "conda_meta"]
        for src in sources:
            tk.Radiobutton(
                selector_frame,
                text=src,
                variable=self.source_var,
                value=src,
                bg=CLR_BG,
                fg=CLR_FG,
                selectcolor=CLR_BTN,
                activebackground=CLR_BG,
                activeforeground=CLR_FG,
                font=FONT_MONO_SMALL,
            ).pack(side=tk.LEFT, padx=4)

        _, _, self.dir_var = make_entry_row(self, "Project root:", str(Path.cwd()))
        _, _, self.name_var = make_entry_row(self, "Package name:", "")
        _, _, self.output_var = make_entry_row(self, "Output file:", "__about__.py")

        toolbar = make_toolbar(self)
        toolbar_btn(toolbar, "Browse...", self.browse)
        toolbar_btn(toolbar, "Preview", self.preview)
        toolbar_btn(toolbar, "Generate", self.generate)

        self.validate_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            toolbar,
            text="Validate",
            variable=self.validate_var,
            bg=CLR_BG,
            fg=CLR_FG,
            selectcolor=CLR_BTN,
            activebackground=CLR_BG,
            activeforeground=CLR_FG,
            font=FONT_UI,
        ).pack(side=tk.LEFT, padx=8)

        # Detected source label
        self.detected_var = tk.StringVar(value="")
        self.detected_label = tk.Label(
            self,
            textvariable=self.detected_var,
            bg=CLR_BG,
            fg=CLR_OK,
            font=FONT_UI_BOLD,
            anchor=tk.W,
        )
        self.detected_label.pack(fill=tk.X, padx=8, pady=(2, 0))

        self.output_text = make_output(self, height=16)

        # Auto-run preview on panel open
        self.after(50, self.preview)

    def browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def preview(self) -> None:
        self.status.set("Generating preview...")
        self.runner.run(
            self.fetch_preview,
            args=(self.source_var.get(), self.dir_var.get(), self.name_var.get()),
            on_success=self.display_preview,
            on_error=self.on_error,
        )

    @staticmethod
    def fetch_preview(source: str, project_root_str: str, name: str) -> dict[str, str]:
        from metametameta.autodetect import detect_source
        from metametameta.general import any_metadict, merge_sections

        root = Path(project_root_str)

        resolved_source = source
        if source == "auto":
            resolved_source = detect_source(root)

        metadata = GeneratePanel.read_metadata(resolved_source, root, name)
        project_name = name or metadata.get("name", "")
        content, names = any_metadict(metadata)
        preview = merge_sections(names, project_name, content)
        return {"preview": preview, "resolved_source": resolved_source}

    @staticmethod
    def read_metadata(source: str, root: Path, name: str) -> dict[str, Any]:
        from metametameta.from_conda_meta import read_conda_meta_metadata
        from metametameta.from_pep621 import read_pep621_metadata
        from metametameta.from_poetry import read_poetry_metadata
        from metametameta.from_requirements_txt import read_requirements_txt_metadata
        from metametameta.from_setup_cfg import read_setup_cfg_metadata
        from metametameta.from_setup_py import read_setup_py_metadata

        readers: dict[str, Callable[..., dict[str, Any]]] = {
            "pep621": lambda: read_pep621_metadata(source=str(root / "pyproject.toml")),
            "poetry": lambda: read_poetry_metadata(source=str(root / "pyproject.toml")),
            "setup_cfg": lambda: read_setup_cfg_metadata(setup_cfg_path=root / "setup.cfg"),
            "setup_py": lambda: read_setup_py_metadata(source=str(root / "setup.py")),
            "requirements_txt": lambda: read_requirements_txt_metadata(source=str(root / "requirements.txt")),
            "conda_meta": lambda: read_conda_meta_metadata(source=str(root / "conda" / "meta.yaml")),
        }

        if source == "importlib":
            if not name:
                raise ValueError("Package name is required for importlib source.")
            from importlib.metadata import metadata as importlib_metadata

            meta = importlib_metadata(name)
            # PackageMetadata is a Mapping but mypy thinks it's only Iterator[str]
            return dict(meta.items()) if meta else {}  # type: ignore[attr-defined]

        return readers[source]()

    def display_preview(self, result: dict[str, str]) -> None:
        output_set(self.output_text, result["preview"])
        resolved = result["resolved_source"]
        self.detected_var.set(f"Detected source: {resolved}")
        self.status.set(f"Preview ready ({resolved})")

    def generate(self) -> None:
        self.status.set("Generating...")
        self.runner.run(
            self.do_generate,
            args=(
                self.source_var.get(),
                self.dir_var.get(),
                self.name_var.get(),
                self.output_var.get(),
                self.validate_var.get(),
            ),
            on_success=self.on_generated,
            on_error=self.on_error,
        )

    @staticmethod
    def do_generate(source: str, project_root_str: str, name: str, output: str, validate: bool) -> str:
        from metametameta.autodetect import detect_source
        from metametameta.from_conda_meta import generate_from_conda_meta
        from metametameta.from_importlib import generate_from_importlib
        from metametameta.from_pep621 import generate_from_pep621
        from metametameta.from_poetry import generate_from_poetry
        from metametameta.from_requirements_txt import generate_from_requirements_txt
        from metametameta.from_setup_cfg import generate_from_setup_cfg
        from metametameta.from_setup_py import generate_from_setup_py

        root = Path(project_root_str)
        if source == "auto":
            source = detect_source(root)

        generators = {
            "pep621": lambda: generate_from_pep621(name=name, source=str(root / "pyproject.toml"), output=output),
            "poetry": lambda: generate_from_poetry(name=name, source=str(root / "pyproject.toml"), output=output),
            "setup_cfg": lambda: generate_from_setup_cfg(name=name, source=str(root / "setup.cfg"), output=output),
            "setup_py": lambda: generate_from_setup_py(name=name, source=str(root / "setup.py"), output=output),
            "requirements_txt": lambda: generate_from_requirements_txt(
                name=name, source=str(root / "requirements.txt"), output=output, validate=validate
            ),
            "conda_meta": lambda: generate_from_conda_meta(
                name=name, source=str(root / "conda" / "meta.yaml"), output=output, validate=validate
            ),
            "importlib": lambda: generate_from_importlib(name=name, output=output),
        }
        generators[source]()
        return f"Generated {output} from {source}"

    def on_generated(self, msg: str) -> None:
        output_set(self.output_text, msg)
        self.status.set(msg)
        messagebox.showinfo("Success", msg)

    def on_error(self, exc: Exception) -> None:
        output_set(self.output_text, f"Error: {exc}")
        self.status.set("Operation failed")


# ── Sync Check panel ────────────────────────────────────────


class SyncCheckPanel(BasePanel):
    """Check if __about__.py is in sync with the metadata source."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        super().__init__(parent, runner, status_var)
        make_heading(self, "Sync Check")
        make_label(self, "Verify that your __about__.py matches the metadata source.")

        _, _, self.dir_var = make_entry_row(self, "Project root:", str(Path.cwd()))
        _, _, self.output_var = make_entry_row(self, "Output file:", "__about__.py")

        toolbar = make_toolbar(self)
        toolbar_btn(toolbar, "Browse...", self.browse)
        toolbar_btn(toolbar, "Check Sync", self.check)

        self.output_text = make_output(self, height=16)

        # Auto-run sync check on panel open
        self.after(50, self.check)

    def browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def check(self) -> None:
        self.status.set("Checking sync...")
        self.runner.run(
            self.do_check,
            args=(self.dir_var.get(), self.output_var.get()),
            on_success=self.display,
            on_error=self.on_error,
        )

    @staticmethod
    def do_check(project_root_str: str, output_filename: str) -> dict[str, Any]:
        from metametameta.autodetect import detect_source
        from metametameta.filesystem import find_existing_package_dir
        from metametameta.validate_sync import check_sync

        root = Path(project_root_str)
        source_type = detect_source(root)

        from metametameta.from_conda_meta import read_conda_meta_metadata
        from metametameta.from_pep621 import read_pep621_metadata
        from metametameta.from_poetry import read_poetry_metadata
        from metametameta.from_requirements_txt import read_requirements_txt_metadata
        from metametameta.from_setup_cfg import read_setup_cfg_metadata
        from metametameta.from_setup_py import read_setup_py_metadata

        readers = {
            "pep621": lambda: read_pep621_metadata(source=str(root / "pyproject.toml")),
            "poetry": lambda: read_poetry_metadata(source=str(root / "pyproject.toml")),
            "setup_cfg": lambda: read_setup_cfg_metadata(setup_cfg_path=root / "setup.cfg"),
            "setup_py": lambda: read_setup_py_metadata(source=str(root / "setup.py")),
            "requirements_txt": lambda: read_requirements_txt_metadata(source=str(root / "requirements.txt")),
            "conda_meta": lambda: read_conda_meta_metadata(source=str(root / "conda" / "meta.yaml")),
        }
        metadata = readers[source_type]()
        project_name = metadata.get("name", "")
        package_dir = find_existing_package_dir(root, project_name)

        if not package_dir:
            return {"source_type": source_type, "mismatches": [f"Package directory not found for '{project_name}'"]}

        about_path = package_dir / output_filename
        mismatches = check_sync(metadata, about_path)
        return {"source_type": source_type, "mismatches": mismatches}

    def display(self, result: dict[str, Any]) -> None:
        mismatches = result["mismatches"]
        source_type = result["source_type"]
        if mismatches:
            lines = [f"Source: {source_type}", "", "OUT OF SYNC -- mismatches found:", ""]
            for m in mismatches:
                lines.append(f"  - {m}")
            output_set(self.output_text, "\n".join(lines))
            self.status.set("Sync check: FAILED")
        else:
            output_set(self.output_text, f"Source: {source_type}\n\nAll in sync!")
            self.status.set("Sync check: PASSED")

    def on_error(self, exc: Exception) -> None:
        output_set(self.output_text, f"Error: {exc}")
        self.status.set("Sync check failed")


# ── Inspect panel ───────────────────────────────────────────


class InspectPanel(BasePanel):
    """Read and display an existing __about__.py using AST, with auto-scan."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        super().__init__(parent, runner, status_var)
        make_heading(self, "Inspect __about__.py")
        make_label(self, "Select a discovered __about__.py or browse to one manually.")

        # Top section: file list + buttons side by side
        top = tk.Frame(self, bg=CLR_BG)
        top.pack(fill=tk.X, padx=8, pady=4)

        # Listbox of discovered files
        list_frame = tk.Frame(top, bg=CLR_BG)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(list_frame, text="Discovered files:", bg=CLR_BG, fg=CLR_DIM, font=FONT_UI, anchor=tk.W).pack(fill=tk.X)
        self.file_listbox = tk.Listbox(
            list_frame,
            height=5,
            bg=CLR_BG_ALT,
            fg=CLR_FG,
            selectbackground=CLR_BTN_ACTIVE,
            selectforeground=CLR_FG,
            font=FONT_MONO_SMALL,
            relief=tk.FLAT,
            activestyle="none",
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_select)
        self.discovered_paths: list[str] = []

        btn_frame = tk.Frame(top, bg=CLR_BG)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))
        toolbar_btn(btn_frame, "Re-scan", self.scan)
        toolbar_btn(btn_frame, "Browse...", self.browse)

        _, _, self.file_var = make_entry_row(self, "Selected:", "")

        toolbar = make_toolbar(self)
        toolbar_btn(toolbar, "Inspect", self.inspect)

        self.tree = make_tree(self, ["Variable", "Value"], height=10)

        # Auto-scan on panel open
        self.after(50, self.scan)

    def scan(self) -> None:
        self.status.set("Scanning for __about__.py...")
        self.runner.run(
            self.do_scan,
            args=(str(Path.cwd()),),
            on_success=self.display_scan,
            on_error=self.on_error,
        )

    @staticmethod
    def do_scan(root_str: str) -> list[str]:
        """Walk up to 2 levels deep, cap at 100 folders, find __about__.py files."""
        root = Path(root_str)
        results: list[str] = []
        folders_visited = 0

        # Level 0: root itself
        candidate = root / "__about__.py"
        if candidate.is_file():
            results.append(str(candidate))

        # Level 1 + 2
        for child in sorted(root.iterdir()):
            if folders_visited >= 100:
                break
            if (
                not child.is_dir()
                or child.name.startswith(
                    (
                        ".",
                        "__pycache__",
                    )
                )
                or child.name in (".git", ".venv", "venv", "node_modules", ".tox", ".eggs")
            ):
                continue
            folders_visited += 1
            candidate = child / "__about__.py"
            if candidate.is_file():
                results.append(str(candidate))

            # Level 2
            try:
                for grandchild in sorted(child.iterdir()):
                    if folders_visited >= 100:
                        break
                    if (
                        not grandchild.is_dir()
                        or grandchild.name.startswith(
                            (
                                ".",
                                "__pycache__",
                            )
                        )
                        or grandchild.name in (".git", ".venv", "venv", "node_modules")
                    ):
                        continue
                    folders_visited += 1
                    candidate = grandchild / "__about__.py"
                    if candidate.is_file():
                        results.append(str(candidate))
            except PermissionError:
                pass
        return results

    def display_scan(self, paths: list[str]) -> None:
        self.discovered_paths = paths
        self.file_listbox.delete(0, tk.END)
        root_str = str(Path.cwd())
        for p in paths:
            # Show relative path for readability
            try:
                display = str(Path(p).relative_to(root_str))
            except ValueError:
                display = p
            self.file_listbox.insert(tk.END, display)
        count = len(paths)
        self.status.set(f"Found {count} __about__.py file{'s' if count != 1 else ''}")
        # Auto-select and inspect the first one
        if paths:
            self.file_listbox.select_set(0)
            self.file_var.set(paths[0])
            self.after(10, self.inspect)

    def on_select(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self.file_listbox.curselection()
        if sel and sel[0] < len(self.discovered_paths):
            self.file_var.set(self.discovered_paths[sel[0]])
            self.inspect()

    def browse(self) -> None:
        f = filedialog.askopenfilename(
            initialdir=str(Path.cwd()),
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if f:
            self.file_var.set(f)
            self.inspect()

    def inspect(self) -> None:
        path = self.file_var.get().strip()
        if not path:
            return
        self.status.set("Inspecting...")
        self.runner.run(
            self.do_inspect,
            args=(path,),
            on_success=self.display,
            on_error=self.on_error,
        )

    @staticmethod
    def do_inspect(file_path_str: str) -> dict[str, Any]:
        from metametameta.validate_sync import read_about_file_ast

        return read_about_file_ast(Path(file_path_str))

    def display(self, metadata: dict[str, Any]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for key, value in metadata.items():
            tag = "ok" if value else "dim"
            self.tree.insert("", tk.END, values=(key, str(value)), tags=(tag,))
        self.status.set(f"Found {len(metadata)} variables")

    def on_error(self, exc: Exception) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert("", tk.END, values=("Error", str(exc)), tags=("error",))
        self.status.set("Inspect failed")


# ── Help panel ──────────────────────────────────────────────


class HelpPanel(BasePanel):
    """Reference information about metametameta."""

    def __init__(self, parent: tk.Widget, runner: BackgroundRunner, status_var: tk.StringVar) -> None:
        super().__init__(parent, runner, status_var)
        make_heading(self, "Help")

        self.output = make_output(self, height=24)
        output_set(self.output, HELP_TEXT)
        self.status.set("Help")


HELP_TEXT = """\
metametameta - Generate __about__.py from various metadata sources

WHAT IT DOES
  Reads project metadata from standard Python packaging files and generates
  a clean __about__.py with dunder variables (__title__, __version__, etc.).

SOURCES SUPPORTED
  pep621           pyproject.toml [project] section (PEP 621)
  poetry           pyproject.toml [tool.poetry] section
  setup_cfg        setup.cfg [metadata] section
  setup_py         setup.py via AST parsing (no execution)
  importlib        Installed package metadata (requires package name)
  requirements_txt requirements.txt dependencies list
  conda_meta       conda/meta.yaml

GUI PANELS
  Dashboard     Auto-detect your project source and preview metadata
  Generate      Choose a source and generate __about__.py
  Sync Check    Verify __about__.py matches the metadata source
  Inspect       Read an existing __about__.py via safe AST parsing
  Help          This panel

GENERATED VARIABLES
  __title__          Project name (from 'name')
  __version__        Version string
  __description__    Short description (or 'summary')
  __author__         Single author name
  __author_email__   Author email
  __credits__        Multiple authors (list)
  __license__        License identifier
  __status__         Development status (from classifiers)
  __keywords__       Keyword list
  __dependencies__   Dependency list
  __homepage__       Project URL

CLI EQUIVALENT
  metametameta auto              Auto-detect and generate
  metametameta pep621            Generate from PEP 621
  metametameta sync-check        Verify sync
  metametameta --help            Full CLI help

KEYBOARD SHORTCUTS
  Ctrl+Q    Quit
  Ctrl+D    Dashboard
  Ctrl+G    Generate
"""


# ── Main application ────────────────────────────────────────


class MetametametaApp:
    """Main application window."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("metametameta")
        self.root.geometry("960x640")
        self.root.minsize(800, 500)
        self.root.configure(bg=CLR_BG)

        self.runner = BackgroundRunner(self.root)
        self.status_var = tk.StringVar(value="Ready")
        self.current_panel: tk.Frame | None = None
        self.sidebar_buttons: dict[str, tk.Button] = {}

        self.build_ui()
        self.bind_keys()
        self.show_panel("dashboard")

    def build_ui(self) -> None:
        # Main horizontal layout: sidebar | content | (help is a panel, not persistent)
        self.sidebar = tk.Frame(self.root, bg=CLR_SIDEBAR, width=140)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Sidebar title
        tk.Label(
            self.sidebar,
            text="mmm",
            bg=CLR_SIDEBAR,
            fg=CLR_ACCENT,
            font=("Segoe UI", 16, "bold"),
            pady=12,
        ).pack(fill=tk.X)

        # Sidebar buttons
        items: list[tuple[str, str]] = [
            ("dashboard", "Dashboard"),
            ("generate", "Generate"),
            ("sync_check", "Sync Check"),
            ("inspect", "Inspect"),
            ("help", "Help"),
        ]
        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                bg=CLR_SIDEBAR,
                fg=CLR_FG,
                activebackground=CLR_BTN_ACTIVE,
                activeforeground=CLR_FG,
                font=FONT_UI,
                relief=tk.FLAT,
                anchor=tk.W,
                padx=16,
                pady=6,
                cursor="hand2",
                command=lambda k=key: self.show_panel(k),  # type: ignore[misc]
            )
            btn.pack(fill=tk.X)
            self.sidebar_buttons[key] = btn

        # Content area
        self.content = tk.Frame(self.root, bg=CLR_BG)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status bar at bottom
        status_bar = tk.Frame(self.root, bg=CLR_SIDEBAR, height=24)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=CLR_SIDEBAR,
            fg=CLR_DIM,
            font=FONT_MONO_SMALL,
            anchor=tk.W,
            padx=8,
        ).pack(fill=tk.BOTH, expand=True)

    def bind_keys(self) -> None:
        self.root.bind("<Control-q>", lambda _: self.root.destroy())
        self.root.bind("<Control-d>", lambda _: self.show_panel("dashboard"))
        self.root.bind("<Control-g>", lambda _: self.show_panel("generate"))

    def show_panel(self, name: str) -> None:
        """Destroy current panel and create a new one."""
        if self.current_panel:
            self.current_panel.destroy()

        # Update sidebar highlight
        for key, btn in self.sidebar_buttons.items():
            if key == name:
                btn.configure(bg=CLR_BTN, fg=CLR_ACCENT)
            else:
                btn.configure(bg=CLR_SIDEBAR, fg=CLR_FG)

        builders: dict[str, type[BasePanel]] = {
            "dashboard": DashboardPanel,
            "generate": GeneratePanel,
            "sync_check": SyncCheckPanel,
            "inspect": InspectPanel,
            "help": HelpPanel,
        }
        panel_cls = builders[name]
        self.current_panel = panel_cls(self.content, self.runner, self.status_var)
        self.current_panel.pack(fill=tk.BOTH, expand=True)

    def run(self) -> None:
        self.root.mainloop()


def launch_gui() -> None:
    """Entry point for the GUI."""
    app = MetametametaApp()
    app.run()


if __name__ == "__main__":
    launch_gui()
