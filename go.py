import metametameta

metametameta.generate_from_setup_cfg(output='example/__about_cfg__.py')
metametameta.generate_from_pep621(source="example.toml", output='example/__about_pep621__.py')
metametameta.generate_from_poetry(output='example/__about_poetry__.py')
metametameta.generate_from_importlib("toml",output='example/__about_toml__.py')