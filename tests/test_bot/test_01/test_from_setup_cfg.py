# from pathlib import Path
# from unittest.mock import patch
#
# import pytest
#
# from metametameta.from_setup_cfg import generate_from_setup_cfg
#
# #
# # @pytest.mark.parametrize(
# #     "source, output, expected_path",
# #     [
# #         ("setup.cfg", "__about__.py", "./test_project/__about__.py"),
# #         ("setup.cfg", "custom_about.py", "./"),  # This will change based on your logic
# #         ("nonexistent.cfg", "__about__.py", "No [metadata] section found in setup.cfg."),
# #     ],
# # )
# # def test_generate_from_setup_cfg(setup_cfg_file, mock_general, source, output, expected_path):
# #     """Test the generate_from_setup_cfg function with various scenarios."""
# #     if source == "setup.cfg":
# #         result = generate_from_setup_cfg(source=setup_cfg_file, output=output)
# #         if "No [metadata] section" in result:
# #             assert result == expected_path
# #         else:
# #             assert Path(result).exists()
# #             assert Path(result).name == output
# #             assert Path(result).parent.name == "test_project"
# #     else:
# #         result = generate_from_setup_cfg(source=source, output=output)
# #         assert result == expected_path
# #
#
# def test_generate_from_setup_cfg_file_not_found(mock_general):
#     """Test handling when setup.cfg file is not found."""
#     # Act
#     result = generate_from_setup_cfg(source="nonexistent.cfg", output="__about__.py")
#
#     # Assert
#     assert result == "No [metadata] section found in setup.cfg."
#
#
# # Run the test cases
#
#
# @pytest.fixture
# def setup_cfg_file(tmp_path):
#     """Create a temporary setup.cfg file."""
#     cfg_content = """
#     [metadata]
#     name = test_project
#     version = 0.1
#     """
#     cfg_file = tmp_path / "setup.cfg"
#     cfg_file.write_text(cfg_content, encoding="utf-8")
#     return cfg_file
#
#
# @pytest.fixture
# def mock_general(mocker):
#     """Mock the general dependency methods for return values."""
#     mock = mocker.patch("metametameta.general")
#     mock.any_metadict.return_value = ("__about__ = 'Test'", ["name", "version"])
#     mock.merge_sections.return_value = "__about__ = 'Test'"
#     return mock
#
#
# def test_generate_from_setup_cfg_file_not_found2(mock_general):
#     """Test handling when setup.cfg file is not found."""
#     result = generate_from_setup_cfg(source="nonexistent.cfg", output="__about__.py")
#
#     # Assert
#     assert result == "No [metadata] section found in setup.cfg."
