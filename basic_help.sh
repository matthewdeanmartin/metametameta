# usage: metametameta [-h] {setup_cfg,pep621,poetry,importlib} ...
#
#metametameta: Generate __about__.py from various sources.
#
#positional arguments:
#  {setup_cfg,pep621,poetry,importlib}
#                        sub-command help
#    setup_cfg           Generate from setup.cfg
#    pep621              Generate from PEP 621 pyproject.toml
#    poetry              Generate from poetry pyproject.toml
#    importlib           Generate from installed package metadata
#
#options:
#  -h, --help            show this help message and exit
set -e
clear
metametameta --help
metametameta poetry --help
metametameta setup_cfg --help
metametameta pep621 --help
metametameta importlib --help