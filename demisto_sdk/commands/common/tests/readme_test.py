import io
import os
import sys

import pytest
from demisto_sdk.commands.common.git_tools import git_path
from demisto_sdk.commands.common.hook_validations.readme import ReadMeValidator

VALID_MD = f'{git_path()}/demisto_sdk/tests/test_files/README-valid.md'
INVALID_MD = f'{git_path()}/demisto_sdk/tests/test_files/README-invalid.md'

README_INPUTS = [
    (VALID_MD, True),
    (INVALID_MD, False),
]

MDX_SKIP_NPM_MESSAGE = 'Required npm modules are not installed. To run this test you must run "npm install" ' \
                       'in the root of the project.'


@pytest.mark.parametrize("current, answer", README_INPUTS)
def test_is_file_valid(mocker, current, answer):
    readme_validator = ReadMeValidator(current)
    valid = readme_validator.are_modules_installed_for_verify(readme_validator.content_path)
    if not valid:
        pytest.skip('skipping mdx test. ' + MDX_SKIP_NPM_MESSAGE)
        return
    mocker.patch.dict(os.environ, {'DEMISTO_README_VALIDATION': 'yes', 'DEMISTO_MDX_CMD_VERIFY': 'yes'})
    assert readme_validator.is_valid_file() is answer
    assert not ReadMeValidator._MDX_SERVER_PROCESS


@pytest.mark.parametrize("current, answer", README_INPUTS)
def test_is_file_valid_mdx_server(mocker, current, answer):
    readme_validator = ReadMeValidator(current)
    valid = readme_validator.are_modules_installed_for_verify(readme_validator.content_path)
    if not valid:
        pytest.skip('skipping mdx server test. ' + MDX_SKIP_NPM_MESSAGE)
        return
    mocker.patch.dict(os.environ, {'DEMISTO_README_VALIDATION': 'yes'})
    assert readme_validator.is_valid_file() is answer
    assert ReadMeValidator._MDX_SERVER_PROCESS is not None
    ReadMeValidator.stop_mdx_server()


def test_are_modules_installed_for_verify_false_res(tmp_path):
    r = str(tmp_path / "README.md")
    with open(r, 'w') as f:
        f.write('Test readme')
    readme_validator = ReadMeValidator(r)
    # modules will be missing in tmp_path
    assert not readme_validator.are_modules_installed_for_verify(tmp_path)


def test_is_image_path_valid():
    """
    Given
        - A README file with 2 invalid images paths in it.
    When
        - Run validate on README file
    Then
        - Ensure:
            - Validation fails
            - Both images paths were caught correctly
            - Valid image path was not caught
            - An alternative paths were suggested
    """
    captured_output = io.StringIO()
    sys.stdout = captured_output  # redirect stdout.
    images_paths = ["https://github.com/demisto/content/blob/123/Packs/AutoFocus/doc_files/AutoFocusPolling.png",
                    "https://github.com/demisto/content/blob/123/Packs/FeedOffice365/doc_files/test.png",
                    "https://github.com/demisto/content/raw/123/Packs/valid/doc_files/test.png"]
    alternative_images_paths = [
        "https://github.com/demisto/content/raw/123/Packs/AutoFocus/doc_files/AutoFocusPolling.png",
        "https://github.com/demisto/content/raw/123/Packs/FeedOffice365/doc_files/test.png"]
    readme_validator = ReadMeValidator(INVALID_MD)
    result = readme_validator.is_image_path_valid()
    sys.stdout = sys.__stdout__   # reset stdout.
    assert not result
    assert images_paths[0] and alternative_images_paths[0] in captured_output.getvalue()
    assert images_paths[1] and alternative_images_paths[1] in captured_output.getvalue()
    assert images_paths[2] not in captured_output.getvalue()
