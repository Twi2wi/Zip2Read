from dataclasses import dataclass

from core.selector import FileSelector


@dataclass
class ExtractRequest:
    zip_path: str
    preset_name: str
    output_format: str
    selector: FileSelector