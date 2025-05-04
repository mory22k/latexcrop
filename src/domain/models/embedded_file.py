from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EmbeddedFile:
    """
    Domain model for an embedded file attachment.
    Attributes:
        name (str): Filename of the attachment.
        data (bytes): Binary content of the attachment.
    """

    name: str
    data: bytes

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """
        Validate the embedded file's metadata.
        Raises:
            ValueError: If name is empty, contains path separators,
                        or does not have a .tex extension.
        """
        if not self.name:
            raise ValueError("Attachment name must not be empty.")
        if any(sep in self.name for sep in ("\\", "/")):
            raise ValueError("Attachment name must not contain path separators.")
        if not self.name.lower().endswith(".tex"):
            raise ValueError("Embedded file must have a .tex extension.")

    @classmethod
    def from_path(cls, path: Path) -> "EmbeddedFile":
        """
        Create an EmbeddedFile from a filesystem path.
        Args:
            path (Path): Path to a .tex file.
        Returns:
            EmbeddedFile: Instance with loaded content.
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a regular file.
        """
        if not path.exists():
            raise FileNotFoundError(f"File '{path}' not found.")
        if not path.is_file():
            raise ValueError(f"'{path}' is not a file.")
        data = path.read_bytes()
        return cls(name=path.name, data=data)

    @classmethod
    def from_content(cls, name: str, content: str) -> "EmbeddedFile":
        """
        Create an EmbeddedFile from content.
        Args:
            name (str): Filename of the attachment.
            content (str): String content of the attachment.
        Returns:
            EmbeddedFile: Instance with provided content.
        """
        return cls(name=name, data=content.encode("utf-8"))

    def write_to(self, directory: Path) -> Path:
        """
        Write the embedded file's content into the given directory.
        Args:
            directory (Path): Target directory.
        Returns:
            Path: Path to the written file.
        """
        directory.mkdir(parents=True, exist_ok=True)
        dest = directory / self.name
        dest.write_bytes(self.data)
        return dest
