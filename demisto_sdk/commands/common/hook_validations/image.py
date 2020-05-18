import base64
import glob

from demisto_sdk.commands.common.constants import (DEFAULT_DBOT_IMAGE_BASE64,
                                                   DEFAULT_IMAGE_BASE64,
                                                   IMAGE_REGEX,
                                                   INTEGRATION_REGEX,
                                                   INTEGRATION_REGXES,
                                                   YML_INTEGRATION_REGEXES,
                                                   Errors)
from demisto_sdk.commands.common.tools import (checked_type, get_yaml, os,
                                               print_error, re)


class ImageValidator:
    """ImageValidator was designed to make sure we use images within the permitted limits.

    Attributes:
        file_path (string): Path to the checked file.
        _is_valid (bool): the attribute which saves the valid/in-valid status of the current file.
    """
    IMAGE_MAX_SIZE = 10 * 1024  # 10kB

    def __init__(self, file_path):
        self._is_valid = True

        if checked_type(file_path, INTEGRATION_REGXES) or re.match(IMAGE_REGEX, file_path, re.IGNORECASE):
            self.file_path = file_path
        else:
            if checked_type(file_path, YML_INTEGRATION_REGEXES):
                try:
                    self.file_path = glob.glob(os.path.join(os.path.dirname(file_path), '*.png'))[0]
                except IndexError:
                    print_error(Errors.no_image_given(file_path))
                    self._is_valid = False
                    self.file_path = ''

    def is_valid(self):
        """Validate that the image exists and that it is in the permitted size limits."""
        if self._is_valid is False:  # In case we encountered an IndexError in the init - we don't have an image
            return self._is_valid

        is_existing_image = False
        self.oversize_image()
        if '.png' not in self.file_path:
            is_existing_image = self.is_existing_image()
        if is_existing_image:
            self.is_not_default_image()

        return self._is_valid

    def oversize_image(self):
        """Check if the image if over sized, bigger than IMAGE_MAX_SIZE"""
        if re.match(IMAGE_REGEX, self.file_path, re.IGNORECASE):
            if os.path.getsize(self.file_path) > self.IMAGE_MAX_SIZE:  # disable-secrets-detection
                print_error(Errors.image_too_large(self.file_path))
                self._is_valid = False

        else:
            data_dictionary = get_yaml(self.file_path)

            if not data_dictionary:
                return

            image = data_dictionary.get('image', '')

            if ((len(image) - 22) / 4.0) * 3 > self.IMAGE_MAX_SIZE:  # disable-secrets-detection
                print_error(Errors.image_too_large(self.file_path))
                self._is_valid = False

    def is_existing_image(self):
        """Check if the integration has an image."""
        is_image_in_yml = False
        is_image_in_package = False

        data_dictionary = get_yaml(self.file_path)

        if not data_dictionary:
            return False

        if data_dictionary.get('image'):
            is_image_in_yml = True
        if not re.match(INTEGRATION_REGEX, self.file_path, re.IGNORECASE):
            package_path = os.path.dirname(self.file_path)
            image_path = glob.glob(package_path + '/*.png')
            if image_path:
                is_image_in_package = True
        if is_image_in_package and is_image_in_yml:
            print_error(Errors.image_in_package_and_yml(self.file_path))
            self._is_valid = False
            return False

        if not (is_image_in_package or is_image_in_yml):
            print_error(Errors.no_image_given(self.file_path))
            self._is_valid = False
            return False

        return True

    def load_image_from_yml(self):
        data_dictionary = get_yaml(self.file_path)

        if not data_dictionary:
            print_error(Errors.not_an_image_file(self.file_path))
            self._is_valid = False

        image = data_dictionary.get('image', '')

        if not image:
            print_error(Errors.no_image_field_in_yml(self.file_path))
            self._is_valid = False

        image_data = image.split('base64,')
        if image_data and len(image_data) == 2:
            return image_data[1]

        else:
            print_error(Errors.image_field_not_in_base64(self.file_path))
            self._is_valid = False

    def load_image(self):
        if re.match(IMAGE_REGEX, self.file_path, re.IGNORECASE):
            with open(self.file_path, "rb") as image:
                image_data = image.read()
                image = base64.b64encode(image_data)
                if isinstance(image, bytes):
                    image = image.decode("utf-8")

        else:
            image = self.load_image_from_yml()

        return image

    def is_not_default_image(self):
        """Check if the image is the default one"""
        image = self.load_image()

        if image in [DEFAULT_IMAGE_BASE64, DEFAULT_DBOT_IMAGE_BASE64]:  # disable-secrets-detection
            print_error(Errors.default_image_error())
            self._is_valid = False
            return False
        return True
