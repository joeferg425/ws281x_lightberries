"""Defines custom exception classes to catch from this module."""

from __future__ import annotations


class LightBerryError(Exception):
    """Custom exception for the LightBerries module."""


class FunctionError(LightBerryError):
    """Exception for LightFunctions to raise."""

class PermissionsError(LightBerryError,PermissionError):
    """Exception for LightFunctions to raise."""


class WS281xStringError(LightBerryError):
    """Exception for LightString to raise."""


class ControllerError(LightBerryError):
    """Exception for LightControls to raise."""


class PatternError(LightBerryError):
    """Exception for LightPatterns to raise."""


class PixelError(LightBerryError):
    """Exception for LightPixel to raise."""
