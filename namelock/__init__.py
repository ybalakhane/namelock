"""namelock — fail a call if the agent addresses the wrong person."""

__version__ = "0.1.0"

from .check import Finding, check_text, load_transcript

__all__ = ["Finding", "check_text", "load_transcript"]
