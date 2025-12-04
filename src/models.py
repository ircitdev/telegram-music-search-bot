"""Models module - data classes for music tracks."""
from dataclasses import dataclass


@dataclass
class Track:
    """Represents a music track."""

    id: str  # YouTube video ID
    title: str  # Song title
    artist: str = "Unknown"  # Artist name
    duration: int = 0  # Duration in seconds
    url: str = ""  # Track URL

    @property
    def formatted_duration(self) -> str:
        """Format duration as MM:SS."""
        duration = int(self.duration)  # Convert to int
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes}:{seconds:02d}"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.artist} - {self.title} ({self.formatted_duration})"
