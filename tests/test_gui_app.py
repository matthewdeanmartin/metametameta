from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from metametameta.gui import app


class FakeVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class FakeStatus:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def set(self, value: str) -> None:
        self.messages.append(value)


class FakeListbox:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.selected: list[int] = []

    def delete(self, _start: int, _end: str) -> None:
        self.items.clear()

    def insert(self, _index: str, value: str) -> None:
        self.items.append(value)

    def select_set(self, index: int) -> None:
        self.selected = [index]

    def curselection(self) -> tuple[int, ...]:
        return tuple(self.selected)


class FakeTree:
    def __init__(self) -> None:
        self.items: dict[str, tuple[tuple[str, str], tuple[str, ...]]] = {}
        self.deleted: list[str] = []
        self._counter = 0

    def get_children(self) -> list[str]:
        return list(self.items)

    def delete(self, item: str) -> None:
        self.deleted.append(item)
        self.items.pop(item, None)

    def insert(self, _parent: str, _index: str, values: tuple[str, str], tags: tuple[str, ...]) -> str:
        item_id = f"item-{self._counter}"
        self._counter += 1
        self.items[item_id] = (values, tags)
        return item_id


class FakePanel:
    def __init__(self) -> None:
        self.destroyed = False

    def destroy(self) -> None:
        self.destroyed = True


class FakeButton:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def configure(self, **kwargs: str) -> None:
        self.calls.append(kwargs)


class ImmediateThread:
    def __init__(self, target, daemon: bool) -> None:
        self._target = target
        self.daemon = daemon
        self.started = False

    def start(self) -> None:
        self.started = True
        self._target()


class FakeRoot:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object, tuple[object, ...]]] = []

    def after(self, delay: int, callback, *args) -> None:
        self.after_calls.append((delay, callback, args))
        callback(*args)


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run(self, func, *, args=(), on_success=None, on_error=None) -> None:
        self.calls.append(
            {
                "func": func,
                "args": args,
                "on_success": on_success,
                "on_error": on_error,
            }
        )


def test_background_runner_dispatches_success_and_error(monkeypatch):
    created_threads: list[ImmediateThread] = []

    def fake_thread(*, target, daemon):
        thread = ImmediateThread(target, daemon)
        created_threads.append(thread)
        return thread

    monkeypatch.setattr(app.threading, "Thread", fake_thread)
    root = FakeRoot()
    runner = app._BackgroundRunner(root)
    events: list[tuple[str, object]] = []

    runner.run(lambda x: x + 1, args=(2,), on_success=lambda result: events.append(("ok", result)))
    runner.run(
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        on_error=lambda exc: events.append(("err", str(exc))),
    )

    assert [thread.daemon for thread in created_threads] == [True, True]
    assert all(thread.started for thread in created_threads)
    assert events == [("ok", 3), ("err", "boom")]
    assert len(root.after_calls) == 2


def test_dashboard_fetch_reads_detected_source(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "setup_cfg")
    monkeypatch.setattr(
        "metametameta.from_setup_cfg.read_setup_cfg_metadata",
        lambda setup_cfg_path: {"name": "demo-app", "version": "1.2.3", "path": str(setup_cfg_path)},
    )

    result = app.DashboardPanel._fetch(str(tmp_path))

    assert result["source_type"] == "setup_cfg"
    assert result["metadata"]["name"] == "demo-app"
    assert result["metadata"]["path"].endswith("setup.cfg")


def test_generate_fetch_preview_auto_detects_and_formats_preview(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "pep621")
    monkeypatch.setattr(app.GeneratePanel, "_read_metadata", lambda source, root, name: {"name": "demo-app"})
    monkeypatch.setattr("metametameta.general.any_metadict", lambda metadata: ('__title__ = "demo-app"\n', ["__title__"]))
    monkeypatch.setattr(
        "metametameta.general.merge_sections",
        lambda names, project_name, content: f"{project_name}|{','.join(names)}|{content.strip()}",
    )

    result = app.GeneratePanel._fetch_preview("auto", str(tmp_path), "")

    assert result == {
        "preview": 'demo-app|__title__|__title__ = "demo-app"',
        "resolved_source": "pep621",
    }


def test_generate_read_metadata_importlib_requires_name():
    with pytest.raises(ValueError, match="Package name is required"):
        app.GeneratePanel._read_metadata("importlib", Path("."), "")


def test_generate_read_metadata_importlib_uses_package_metadata(monkeypatch):
    monkeypatch.setattr("importlib.metadata.metadata", lambda name: SimpleNamespace(items=lambda: [("Name", name)]))

    metadata = app.GeneratePanel._read_metadata("importlib", Path("."), "demo-app")

    assert metadata == {"Name": "demo-app"}


def test_generate_do_generate_auto_uses_detected_generator(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "requirements_txt")
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        "metametameta.from_requirements_txt.generate_from_requirements_txt",
        lambda **kwargs: calls.append(kwargs),
    )

    message = app.GeneratePanel._do_generate("auto", str(tmp_path), "demo-app", "__about__.py", True)

    assert message == "Generated __about__.py from requirements_txt"
    assert calls == [
        {
            "name": "demo-app",
            "source": str(tmp_path / "requirements.txt"),
            "output": "__about__.py",
            "validate": True,
        }
    ]


def test_sync_check_reports_missing_package_dir(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "pep621")
    monkeypatch.setattr("metametameta.from_pep621.read_pep621_metadata", lambda source=None: {"name": "demo-app"})
    monkeypatch.setattr("metametameta.filesystem._find_existing_package_dir", lambda root, project_name: None)

    result = app.SyncCheckPanel._do_check(str(tmp_path), "__about__.py")

    assert result == {
        "source_type": "pep621",
        "mismatches": ["Package directory not found for 'demo-app'"],
    }


def test_sync_check_returns_mismatches(monkeypatch, tmp_path):
    package_dir = tmp_path / "demo_app"
    package_dir.mkdir()
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "pep621")
    monkeypatch.setattr("metametameta.from_pep621.read_pep621_metadata", lambda source=None: {"name": "demo-app"})
    monkeypatch.setattr("metametameta.filesystem._find_existing_package_dir", lambda root, project_name: package_dir)
    monkeypatch.setattr("metametameta.validate_sync.check_sync", lambda metadata, about_path: ["version mismatch"])

    result = app.SyncCheckPanel._do_check(str(tmp_path), "__about__.py")

    assert result == {"source_type": "pep621", "mismatches": ["version mismatch"]}


def test_dashboard_panel_methods(monkeypatch):
    panel = object.__new__(app.DashboardPanel)
    panel._dir_var = FakeVar("C:/demo")
    panel._status = FakeStatus()
    panel._runner = FakeRunner()
    output_calls: list[tuple[object, str]] = []
    panel._output = object()
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "_output_set", lambda widget, content: output_calls.append((widget, content)))

    app.DashboardPanel._browse(panel)
    assert panel._dir_var.get() == "C:/chosen"

    app.DashboardPanel._detect(panel)
    assert panel._status.messages[-1] == "Detecting metadata source..."
    assert panel._runner.calls[-1]["func"] == panel._fetch
    assert panel._runner.calls[-1]["args"] == ("C:/chosen",)

    app.DashboardPanel._display(panel, {"source_type": "pep621", "metadata": {"name": "demo-app", "version": "1.0"}})
    assert output_calls[-1][1] == "Detected source: pep621\n\n  name: demo-app\n  version: 1.0"
    assert panel._status.messages[-1] == "Detected: pep621"

    app.DashboardPanel._on_error(panel, RuntimeError("bad"))
    assert output_calls[-1][1] == "Error: bad"
    assert panel._status.messages[-1] == "Detection failed"


def test_generate_panel_methods(monkeypatch):
    panel = object.__new__(app.GeneratePanel)
    panel._source_var = FakeVar("auto")
    panel._dir_var = FakeVar("C:/demo")
    panel._name_var = FakeVar("demo-app")
    panel._output_var = FakeVar("__about__.py")
    panel._validate_var = SimpleNamespace(get=lambda: True)
    panel._detected_var = FakeVar()
    panel._status = FakeStatus()
    panel._runner = FakeRunner()
    panel._output_text = object()
    output_calls: list[tuple[object, str]] = []
    info_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "_output_set", lambda widget, content: output_calls.append((widget, content)))
    monkeypatch.setattr(app.messagebox, "showinfo", lambda title, msg: info_calls.append((title, msg)))

    app.GeneratePanel._browse(panel)
    assert panel._dir_var.get() == "C:/chosen"

    app.GeneratePanel._preview(panel)
    assert panel._status.messages[-1] == "Generating preview..."
    assert panel._runner.calls[-1]["func"] == panel._fetch_preview
    assert panel._runner.calls[-1]["args"] == ("auto", "C:/chosen", "demo-app")

    app.GeneratePanel._display_preview(panel, {"preview": "preview text", "resolved_source": "pep621"})
    assert output_calls[-1][1] == "preview text"
    assert panel._detected_var.get() == "Detected source: pep621"
    assert panel._status.messages[-1] == "Preview ready (pep621)"

    app.GeneratePanel._generate(panel)
    assert panel._status.messages[-1] == "Generating..."
    assert panel._runner.calls[-1]["func"] == panel._do_generate
    assert panel._runner.calls[-1]["args"] == ("auto", "C:/chosen", "demo-app", "__about__.py", True)

    app.GeneratePanel._on_generated(panel, "generated ok")
    assert output_calls[-1][1] == "generated ok"
    assert panel._status.messages[-1] == "generated ok"
    assert info_calls[-1] == ("Success", "generated ok")

    app.GeneratePanel._on_error(panel, RuntimeError("broken"))
    assert output_calls[-1][1] == "Error: broken"
    assert panel._status.messages[-1] == "Operation failed"


def test_sync_check_panel_methods(monkeypatch):
    panel = object.__new__(app.SyncCheckPanel)
    panel._dir_var = FakeVar("C:/demo")
    panel._output_var = FakeVar("__about__.py")
    panel._status = FakeStatus()
    panel._runner = FakeRunner()
    panel._output_text = object()
    output_calls: list[tuple[object, str]] = []
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "_output_set", lambda widget, content: output_calls.append((widget, content)))

    app.SyncCheckPanel._browse(panel)
    assert panel._dir_var.get() == "C:/chosen"

    app.SyncCheckPanel._check(panel)
    assert panel._status.messages[-1] == "Checking sync..."
    assert panel._runner.calls[-1]["func"] == panel._do_check
    assert panel._runner.calls[-1]["args"] == ("C:/chosen", "__about__.py")

    app.SyncCheckPanel._display(panel, {"source_type": "pep621", "mismatches": []})
    assert output_calls[-1][1] == "Source: pep621\n\nAll in sync!"
    assert panel._status.messages[-1] == "Sync check: PASSED"

    app.SyncCheckPanel._display(panel, {"source_type": "pep621", "mismatches": ["version mismatch"]})
    assert "OUT OF SYNC" in output_calls[-1][1]
    assert "version mismatch" in output_calls[-1][1]
    assert panel._status.messages[-1] == "Sync check: FAILED"

    app.SyncCheckPanel._on_error(panel, RuntimeError("broken"))
    assert output_calls[-1][1] == "Error: broken"
    assert panel._status.messages[-1] == "Sync check failed"


def test_inspect_scan_finds_about_files_without_descending_into_hidden_dirs(tmp_path):
    (tmp_path / "__about__.py").write_text("", encoding="utf-8")
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__about__.py").write_text("", encoding="utf-8")
    nested_dir = pkg_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "__about__.py").write_text("", encoding="utf-8")
    hidden_dir = tmp_path / ".git"
    hidden_dir.mkdir()
    (hidden_dir / "__about__.py").write_text("", encoding="utf-8")

    paths = app.InspectPanel._do_scan(str(tmp_path))

    assert str(tmp_path / "__about__.py") in paths
    assert str(pkg_dir / "__about__.py") in paths
    assert str(nested_dir / "__about__.py") in paths
    assert str(hidden_dir / "__about__.py") not in paths


def test_inspect_panel_scan_browse_inspect_and_do_inspect(monkeypatch):
    panel = object.__new__(app.InspectPanel)
    panel._status = FakeStatus()
    panel._runner = FakeRunner()
    panel._file_var = FakeVar("")
    monkeypatch.setattr(app.filedialog, "askopenfilename", lambda initialdir, filetypes: "C:/chosen.py")
    monkeypatch.setattr(app.Path, "cwd", lambda: Path("C:/cwd"))
    monkeypatch.setattr("metametameta.validate_sync.read_about_file_ast", lambda path: {"__title__": "demo-app"})

    app.InspectPanel._scan(panel)
    assert panel._status.messages[-1] == "Scanning for __about__.py..."
    assert panel._runner.calls[-1]["func"] == panel._do_scan
    assert panel._runner.calls[-1]["args"] == (str(Path("C:/cwd")),)

    app.InspectPanel._browse(panel)
    assert panel._file_var.get() == "C:/chosen.py"

    app.InspectPanel._inspect(panel)
    assert panel._status.messages[-1] == "Inspecting..."
    assert panel._runner.calls[-1]["func"] == panel._do_inspect
    assert panel._runner.calls[-1]["args"] == ("C:/chosen.py",)

    panel._file_var = FakeVar("   ")
    before = len(panel._runner.calls)
    app.InspectPanel._inspect(panel)
    assert len(panel._runner.calls) == before

    assert app.InspectPanel._do_inspect("C:/chosen.py") == {"__title__": "demo-app"}


def test_inspect_display_scan_populates_list_and_schedules_inspect(monkeypatch, tmp_path):
    panel = object.__new__(app.InspectPanel)
    panel._discovered_paths = []
    panel._file_listbox = FakeListbox()
    panel._file_var = FakeVar()
    panel._status = FakeStatus()
    scheduled: list[tuple[int, object]] = []
    monkeypatch.setattr(app.Path, "cwd", lambda: tmp_path)
    panel.after = lambda delay, callback: scheduled.append((delay, callback))
    panel._inspect = lambda: None

    path = str(tmp_path / "pkg" / "__about__.py")
    app.InspectPanel._display_scan(panel, [path])

    assert panel._discovered_paths == [path]
    assert panel._file_listbox.items == [str(Path(path).relative_to(tmp_path))]
    assert panel._file_listbox.selected == [0]
    assert panel._file_var.get() == path
    assert panel._status.messages[-1] == "Found 1 __about__.py file"
    assert scheduled == [(10, panel._inspect)]


def test_inspect_on_select_and_display_and_error_paths():
    panel = object.__new__(app.InspectPanel)
    panel._discovered_paths = ["first.py", "second.py"]
    panel._file_listbox = FakeListbox()
    panel._file_listbox.selected = [1]
    panel._file_var = FakeVar()
    panel._status = FakeStatus()
    tree = FakeTree()
    tree.insert("", "end", ("old", "value"), ("ok",))
    panel._tree = tree
    inspect_calls: list[str] = []
    panel._inspect = lambda: inspect_calls.append("called")

    app.InspectPanel._on_select(panel, None)
    assert panel._file_var.get() == "second.py"
    assert inspect_calls == ["called"]

    app.InspectPanel._display(panel, {"__title__": "demo-app", "__empty__": ""})
    inserted = list(panel._tree.items.values())
    assert (("__title__", "demo-app"), ("ok",)) in inserted
    assert (("__empty__", ""), ("dim",)) in inserted
    assert panel._status.messages[-1] == "Found 2 variables"

    app.InspectPanel._on_error(panel, RuntimeError("broken"))
    assert list(panel._tree.items.values()) == [(("Error", "broken"), ("error",))]
    assert panel._status.messages[-1] == "Inspect failed"


def test_show_panel_switches_sidebar_state(monkeypatch):
    created: list[tuple[object, object, object]] = []

    class FakeDashboard(FakePanel):
        def __init__(self, parent, runner, status_var) -> None:
            super().__init__()
            created.append((parent, runner, status_var))
            self.pack_calls: list[dict[str, object]] = []

        def pack(self, **kwargs) -> None:
            self.pack_calls.append(kwargs)

    class FakeHelp(FakeDashboard):
        pass

    monkeypatch.setattr(app, "DashboardPanel", FakeDashboard)
    monkeypatch.setattr(app, "HelpPanel", FakeHelp)
    panel = object.__new__(app.MetametametaApp)
    current = FakePanel()
    panel._current_panel = current
    panel._sidebar_buttons = {"dashboard": FakeButton(), "help": FakeButton()}
    panel._content = object()
    panel._runner = object()
    panel._status_var = object()

    app.MetametametaApp._show_panel(panel, "help")

    assert current.destroyed is True
    assert created == [(panel._content, panel._runner, panel._status_var)]
    assert isinstance(panel._current_panel, FakeHelp)
    assert panel._current_panel.pack_calls == [{"fill": app.tk.BOTH, "expand": True}]
    assert panel._sidebar_buttons["help"].calls[-1] == {"bg": app._CLR_BTN, "fg": app._CLR_ACCENT}
    assert panel._sidebar_buttons["dashboard"].calls[-1] == {"bg": app._CLR_SIDEBAR, "fg": app._CLR_FG}


def test_launch_gui_constructs_and_runs_app(monkeypatch):
    events: list[str] = []

    class FakeApp:
        def __init__(self) -> None:
            events.append("init")

        def run(self) -> None:
            events.append("run")

    monkeypatch.setattr(app, "MetametametaApp", FakeApp)

    app.launch_gui()

    assert events == ["init", "run"]


def test_help_text_mentions_gui_panels():
    assert "GUI PANELS" in app._HELP_TEXT
    assert "Dashboard" in app._HELP_TEXT
    assert "Inspect" in app._HELP_TEXT


def test_known_meta_lists_expected_fields():
    from metametameta.known import meta

    assert meta == ["name", "version", "description", "authors", "license", "homepage", "keywords"]
