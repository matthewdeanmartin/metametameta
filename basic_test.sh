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
# Each command's options
# options:
#  -h, --help       show this help message and exit
#  --name NAME      Name of the project (from file if omitted)
#  --source SOURCE  Path to setup.cfg
#  --output OUTPUT  Output file
set -e
metametameta setup_cfg --name example --output example/__about_cfg__.py
echo "-------------------------------------"
metametameta pep621 --name example --output example/__about_pep621__.py
echo "-------------------------------------"
metametameta poetry --name example --output example/__about_poetry__.py
echo "-------------------------------------"
metametameta importlib --name toml --output example/__about_importlib__.py
echo "Using on own source code.."
metametameta setup_cfg
echo "-------------------------------------"
metametameta pep621
echo "-------------------------------------"
metametameta importlib --name metametameta --output example/__about_importlib_for_mmm__.py
echo "-------------Restoring to poetry based------------------------"
metametameta poetry

