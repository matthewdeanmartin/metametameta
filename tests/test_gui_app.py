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
        self.counter = 0

    def get_children(self) -> list[str]:
        return list(self.items)

    def delete(self, item: str) -> None:
        self.deleted.append(item)
        self.items.pop(item, None)

    def insert(self, _parent: str, _index: str, values: tuple[str, str], tags: tuple[str, ...]) -> str:
        item_id = f"item-{self.counter}"
        self.counter += 1
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
        self.target = target
        self.daemon = daemon
        self.started = False

    def start(self) -> None:
        self.started = True
        self.target()


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
    runner = app.BackgroundRunner(root)
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

    result = app.DashboardPanel.fetch(str(tmp_path))

    assert result["source_type"] == "setup_cfg"
    assert result["metadata"]["name"] == "demo-app"
    assert result["metadata"]["path"].endswith("setup.cfg")


def test_generate_fetch_preview_auto_detects_and_formats_preview(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "pep621")
    monkeypatch.setattr(app.GeneratePanel, "read_metadata", lambda source, root, name: {"name": "demo-app"})
    monkeypatch.setattr(
        "metametameta.general.any_metadict", lambda metadata: ('__title__ = "demo-app"\n', ["__title__"])
    )
    monkeypatch.setattr(
        "metametameta.general.merge_sections",
        lambda names, project_name, content: f"{project_name}|{','.join(names)}|{content.strip()}",
    )

    result = app.GeneratePanel.fetch_preview("auto", str(tmp_path), "")

    assert result == {
        "preview": 'demo-app|__title__|__title__ = "demo-app"',
        "resolved_source": "pep621",
    }


def test_generate_read_metadata_importlib_requires_name():
    with pytest.raises(ValueError, match="Package name is required"):
        app.GeneratePanel.read_metadata("importlib", Path("."), "")


def test_generate_read_metadata_importlib_uses_package_metadata(monkeypatch):
    monkeypatch.setattr("importlib.metadata.metadata", lambda name: SimpleNamespace(items=lambda: [("Name", name)]))

    metadata = app.GeneratePanel.read_metadata("importlib", Path("."), "demo-app")

    assert metadata == {"Name": "demo-app"}


def test_generate_do_generate_auto_uses_detected_generator(monkeypatch, tmp_path):
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "requirements_txt")
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        "metametameta.from_requirements_txt.generate_from_requirements_txt",
        lambda **kwargs: calls.append(kwargs),
    )

    message = app.GeneratePanel.do_generate("auto", str(tmp_path), "demo-app", "__about__.py", True)

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
    monkeypatch.setattr("metametameta.filesystem.find_existing_package_dir", lambda root, project_name: None)

    result = app.SyncCheckPanel.do_check(str(tmp_path), "__about__.py")

    assert result == {
        "source_type": "pep621",
        "mismatches": ["Package directory not found for 'demo-app'"],
    }


def test_sync_check_returns_mismatches(monkeypatch, tmp_path):
    package_dir = tmp_path / "demo_app"
    package_dir.mkdir()
    monkeypatch.setattr("metametameta.autodetect.detect_source", lambda root: "pep621")
    monkeypatch.setattr("metametameta.from_pep621.read_pep621_metadata", lambda source=None: {"name": "demo-app"})
    monkeypatch.setattr("metametameta.filesystem.find_existing_package_dir", lambda root, project_name: package_dir)
    monkeypatch.setattr("metametameta.validate_sync.check_sync", lambda metadata, about_path: ["version mismatch"])

    result = app.SyncCheckPanel.do_check(str(tmp_path), "__about__.py")

    assert result == {"source_type": "pep621", "mismatches": ["version mismatch"]}


def test_dashboard_panel_methods(monkeypatch):
    panel = object.__new__(app.DashboardPanel)
    panel.dir_var = FakeVar("C:/demo")
    panel.status = FakeStatus()
    panel.runner = FakeRunner()
    output_calls: list[tuple[object, str]] = []
    panel.output = object()
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "output_set", lambda widget, content: output_calls.append((widget, content)))

    app.DashboardPanel.browse(panel)
    assert panel.dir_var.get() == "C:/chosen"

    app.DashboardPanel.detect(panel)
    assert panel.status.messages[-1] == "Detecting metadata source..."
    assert panel.runner.calls[-1]["func"] == panel.fetch
    assert panel.runner.calls[-1]["args"] == ("C:/chosen",)

    app.DashboardPanel.display(panel, {"source_type": "pep621", "metadata": {"name": "demo-app", "version": "1.0"}})
    assert output_calls[-1][1] == "Detected source: pep621\n\n  name: demo-app\n  version: 1.0"
    assert panel.status.messages[-1] == "Detected: pep621"

    app.DashboardPanel.on_error(panel, RuntimeError("bad"))
    assert output_calls[-1][1] == "Error: bad"
    assert panel.status.messages[-1] == "Detection failed"


def test_generate_panel_methods(monkeypatch):
    panel = object.__new__(app.GeneratePanel)
    panel.source_var = FakeVar("auto")
    panel.dir_var = FakeVar("C:/demo")
    panel.name_var = FakeVar("demo-app")
    panel.output_var = FakeVar("__about__.py")
    panel.validate_var = SimpleNamespace(get=lambda: True)
    panel.detected_var = FakeVar()
    panel.status = FakeStatus()
    panel.runner = FakeRunner()
    panel.output_text = object()
    output_calls: list[tuple[object, str]] = []
    info_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "output_set", lambda widget, content: output_calls.append((widget, content)))
    monkeypatch.setattr(app.messagebox, "showinfo", lambda title, msg: info_calls.append((title, msg)))

    app.GeneratePanel.browse(panel)
    assert panel.dir_var.get() == "C:/chosen"

    app.GeneratePanel.preview(panel)
    assert panel.status.messages[-1] == "Generating preview..."
    assert panel.runner.calls[-1]["func"] == panel.fetch_preview
    assert panel.runner.calls[-1]["args"] == ("auto", "C:/chosen", "demo-app")

    app.GeneratePanel.display_preview(panel, {"preview": "preview text", "resolved_source": "pep621"})
    assert output_calls[-1][1] == "preview text"
    assert panel.detected_var.get() == "Detected source: pep621"
    assert panel.status.messages[-1] == "Preview ready (pep621)"

    app.GeneratePanel.generate(panel)
    assert panel.status.messages[-1] == "Generating..."
    assert panel.runner.calls[-1]["func"] == panel.do_generate
    assert panel.runner.calls[-1]["args"] == ("auto", "C:/chosen", "demo-app", "__about__.py", True)

    app.GeneratePanel.on_generated(panel, "generated ok")
    assert output_calls[-1][1] == "generated ok"
    assert panel.status.messages[-1] == "generated ok"
    assert info_calls[-1] == ("Success", "generated ok")

    app.GeneratePanel.on_error(panel, RuntimeError("broken"))
    assert output_calls[-1][1] == "Error: broken"
    assert panel.status.messages[-1] == "Operation failed"


def test_sync_check_panel_methods(monkeypatch):
    panel = object.__new__(app.SyncCheckPanel)
    panel.dir_var = FakeVar("C:/demo")
    panel.output_var = FakeVar("__about__.py")
    panel.status = FakeStatus()
    panel.runner = FakeRunner()
    panel.output_text = object()
    output_calls: list[tuple[object, str]] = []
    monkeypatch.setattr(app.filedialog, "askdirectory", lambda initialdir: "C:/chosen")
    monkeypatch.setattr(app, "output_set", lambda widget, content: output_calls.append((widget, content)))

    app.SyncCheckPanel.browse(panel)
    assert panel.dir_var.get() == "C:/chosen"

    app.SyncCheckPanel.check(panel)
    assert panel.status.messages[-1] == "Checking sync..."
    assert panel.runner.calls[-1]["func"] == panel.do_check
    assert panel.runner.calls[-1]["args"] == ("C:/chosen", "__about__.py")

    app.SyncCheckPanel.display(panel, {"source_type": "pep621", "mismatches": []})
    assert output_calls[-1][1] == "Source: pep621\n\nAll in sync!"
    assert panel.status.messages[-1] == "Sync check: PASSED"

    app.SyncCheckPanel.display(panel, {"source_type": "pep621", "mismatches": ["version mismatch"]})
    assert "OUT OF SYNC" in output_calls[-1][1]
    assert "version mismatch" in output_calls[-1][1]
    assert panel.status.messages[-1] == "Sync check: FAILED"

    app.SyncCheckPanel.on_error(panel, RuntimeError("broken"))
    assert output_calls[-1][1] == "Error: broken"
    assert panel.status.messages[-1] == "Sync check failed"


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

    paths = app.InspectPanel.do_scan(str(tmp_path))

    assert str(tmp_path / "__about__.py") in paths
    assert str(pkg_dir / "__about__.py") in paths
    assert str(nested_dir / "__about__.py") in paths
    assert str(hidden_dir / "__about__.py") not in paths


def test_inspect_panel_scan_browse_inspect_and_do_inspect(monkeypatch):
    panel = object.__new__(app.InspectPanel)
    panel.status = FakeStatus()
    panel.runner = FakeRunner()
    panel.file_var = FakeVar("")
    monkeypatch.setattr(app.filedialog, "askopenfilename", lambda initialdir, filetypes: "C:/chosen.py")
    monkeypatch.setattr(app.Path, "cwd", lambda: Path("C:/cwd"))
    monkeypatch.setattr("metametameta.validate_sync.read_about_file_ast", lambda path: {"__title__": "demo-app"})

    app.InspectPanel.scan(panel)
    assert panel.status.messages[-1] == "Scanning for __about__.py..."
    assert panel.runner.calls[-1]["func"] == panel.do_scan
    assert panel.runner.calls[-1]["args"] == (str(Path("C:/cwd")),)

    app.InspectPanel.browse(panel)
    assert panel.file_var.get() == "C:/chosen.py"

    app.InspectPanel.inspect(panel)
    assert panel.status.messages[-1] == "Inspecting..."
    assert panel.runner.calls[-1]["func"] == panel.do_inspect
    assert panel.runner.calls[-1]["args"] == ("C:/chosen.py",)

    panel.file_var = FakeVar("   ")
    before = len(panel.runner.calls)
    app.InspectPanel.inspect(panel)
    assert len(panel.runner.calls) == before

    assert app.InspectPanel.do_inspect("C:/chosen.py") == {"__title__": "demo-app"}


def test_inspect_display_scan_populates_list_and_schedules_inspect(monkeypatch, tmp_path):
    panel = object.__new__(app.InspectPanel)
    panel.discovered_paths = []
    panel.file_listbox = FakeListbox()
    panel.file_var = FakeVar()
    panel.status = FakeStatus()
    scheduled: list[tuple[int, object]] = []
    monkeypatch.setattr(app.Path, "cwd", lambda: tmp_path)
    panel.after = lambda delay, callback: scheduled.append((delay, callback))
    panel.inspect = lambda: None

    path = str(tmp_path / "pkg" / "__about__.py")
    app.InspectPanel.display_scan(panel, [path])

    assert panel.discovered_paths == [path]
    assert panel.file_listbox.items == [str(Path(path).relative_to(tmp_path))]
    assert panel.file_listbox.selected == [0]
    assert panel.file_var.get() == path
    assert panel.status.messages[-1] == "Found 1 __about__.py file"
    assert scheduled == [(10, panel.inspect)]


def test_inspect_on_select_and_display_and_error_paths():
    panel = object.__new__(app.InspectPanel)
    panel.discovered_paths = ["first.py", "second.py"]
    panel.file_listbox = FakeListbox()
    panel.file_listbox.selected = [1]
    panel.file_var = FakeVar()
    panel.status = FakeStatus()
    tree = FakeTree()
    tree.insert("", "end", ("old", "value"), ("ok",))
    panel.tree = tree
    inspect_calls: list[str] = []
    panel.inspect = lambda: inspect_calls.append("called")

    app.InspectPanel.on_select(panel, None)
    assert panel.file_var.get() == "second.py"
    assert inspect_calls == ["called"]

    app.InspectPanel.display(panel, {"__title__": "demo-app", "__empty__": ""})
    inserted = list(panel.tree.items.values())
    assert (("__title__", "demo-app"), ("ok",)) in inserted
    assert (("__empty__", ""), ("dim",)) in inserted
    assert panel.status.messages[-1] == "Found 2 variables"

    app.InspectPanel.on_error(panel, RuntimeError("broken"))
    assert list(panel.tree.items.values()) == [(("Error", "broken"), ("error",))]
    assert panel.status.messages[-1] == "Inspect failed"


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
    panel.current_panel = current
    panel.sidebar_buttons = {"dashboard": FakeButton(), "help": FakeButton()}
    panel.content = object()
    panel.runner = object()
    panel.status_var = object()

    app.MetametametaApp.show_panel(panel, "help")

    assert current.destroyed is True
    assert created == [(panel.content, panel.runner, panel.status_var)]
    assert isinstance(panel.current_panel, FakeHelp)
    assert panel.current_panel.pack_calls == [{"fill": app.tk.BOTH, "expand": True}]
    assert panel.sidebar_buttons["help"].calls[-1] == {"bg": app.CLR_BTN, "fg": app.CLR_ACCENT}
    assert panel.sidebar_buttons["dashboard"].calls[-1] == {"bg": app.CLR_SIDEBAR, "fg": app.CLR_FG}


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
    assert "GUI PANELS" in app.HELP_TEXT
    assert "Dashboard" in app.HELP_TEXT
    assert "Inspect" in app.HELP_TEXT


def test_known_meta_lists_expected_fields():
    from metametameta.known import meta

    assert meta == ["name", "version", "description", "authors", "license", "homepage", "keywords"]
