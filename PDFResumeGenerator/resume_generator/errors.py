"""Exception hierarchy. Each error carries the process exit code the CLI uses."""


class ResumeError(Exception):
    exit_code = 1


class ConfigError(ResumeError):
    """The YAML file could not be read or parsed."""
    exit_code = 1


class ValidationError(ResumeError):
    """The YAML parsed, but its content is missing fields or has bad values."""
    exit_code = 1

    def __init__(self, problems):
        self.problems = list(problems)
        count = len(self.problems)
        header = f"{count} problem{'s' if count != 1 else ''} found in resume content:"
        super().__init__("\n".join([header] + [f"  - {p}" for p in self.problems]))


class LayoutError(ResumeError):
    """Content cannot be laid out within the template (overflow, collisions)."""
    exit_code = 3


class FontError(ResumeError):
    exit_code = 4


class OutputError(ResumeError):
    exit_code = 4
