from typing import Union

from demisto_sdk.commands.common.constants import WIDGET
from demisto_sdk.commands.common.content.objects.pack_objects.abstract_pack_objects.json_content_object import \
    JSONContentObject
from wcmatch.pathlib import Path


class Widget(JSONContentObject):
    def __init__(self, path: Union[Path, str]):
        super().__init__(path, WIDGET)
