"""Custom exceptions for boss-skills."""


class BossArchiveError(Exception):
    """Base exception for boss archive failures."""


class ArchiveExistsError(BossArchiveError):
    """Raised when an archive already exists."""


class ArchiveNotFoundError(BossArchiveError):
    """Raised when an archive is missing."""


class ArchiveNotReadyError(BossArchiveError):
    """Raised when a ready-only action is attempted too early."""


class InvalidCommandError(BossArchiveError):
    """Raised when command arguments are invalid."""


class ExtractionError(BossArchiveError):
    """Raised when a source cannot be extracted."""
