# Usage

By default metametameta writes an `__about__.py` file in your package directory assuming the package name matches your main module:

```bash
metametameta poetry
```

You can specify the project name, source file, or output path:

```bash
metametameta poetry --name "something" --source some.toml --output OUTPUT "mod/meta/__meta__.py"
```

The command line interface provides subcommands for different metadata sources:

```text
usage: metametameta [-h] {setup_cfg,pep621,poetry,importlib} ...
```

Each subcommand accepts the same options:

```text
usage: metametameta poetry [-h] [--name NAME] [--source SOURCE] [--output OUTPUT]
```
