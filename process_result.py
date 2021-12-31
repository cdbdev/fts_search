from dataclasses import dataclass

@dataclass
class ProcessResult:
    """Class for keeping track of result"""
    key: str            # holds filename + path
    dat: list[str]      # holds a list of lines in which the pattern occurs