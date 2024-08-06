from pathlib import Path
from typing import Optional


class VersionManager:

    storage_file_name = "default_version.txt"

    def __init__(self, version_directory: Path) -> None:
        self.version_directory: Path = version_directory
        self.default: Optional[str] = None
        if not self.storage_file_exists:
            self.save_default_version(self.app_versions[0])
        else:
            self.load_default_version()

    @property
    def default_storage_path(self):
        return self.version_directory / self.storage_file_name

    @property
    def app_versions(self):
        return sorted([d.name for d in self.version_directory.glob("*") if d.is_dir()])

    @property
    def storage_file_exists(self):
        return self.default_storage_path.is_file()

    def save_default_version(self, version: str) -> None:
        assert (
            version in self.app_versions
        ), f"{version} not in versions {self.app_versions}"
        with open(self.default_storage_path, "w") as file:
            file.write(version)
        self.default = version

    def load_default_version(self) -> str:
        with open(self.default_storage_path, "r") as file:
            self.default = file.read()
        return self.default
