git2md metametameta \
  --ignore __init__.py __pycache__ \
  --output SOURCE.md

# ├── builtin_plugins.py
  #├── commands/
  #│   ├── best_effort_runner.py
  #│   ├── clean_all.py
  #│   ├── compile_all.py
  #│   ├── compile_bash_reader.py
  #│   ├── compile_not_bash.py
  #│   ├── copy2local.py
  #│   ├── decompile_all.py
  #│   ├── detect_drift.py
  #│   ├── doctor.py
  #│   ├── doctor_checks.py
  #│   ├── graph_all.py
  #│   ├── init_project.py
  #│   ├── inline_clone_and_run.py
  #│   ├── input_change_detector.py
  #│   ├── lint_all.py
  #│   ├── map_commit.py
  #│   ├── map_deploy.py
  #│   ├── pipeline_docs.py
  #│   ├── pipeline_trigger.py
  #│   ├── precommit.py
  #│   ├── show_config.py
  #│   ├── upgrade_pinned_templates.py
  #│   └── validate_all.py
  #├── config.py
  #├── errors/
  #│   ├── exceptions.py
  #│   └── exit_codes.py
  #├── hookspecs.py
  #├── install_help.py
  #├── plugins.py
  #├── schemas/
  #│   └── NOTICE.txt
  #├── watch_files.py
  #└── __main__.py