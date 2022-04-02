"""Defines custom exception classes to catch from this module."""

from __future__ import annotations


class LightBerryException(Exception):
    """Custom exception for the LightBerries module."""


class FunctionException(LightBerryException):
    """Exception for LightFunctions to raise."""


class WS281xStringException(LightBerryException):
    """Exception for LightString to raise."""


class ControllerException(LightBerryException):
    """Exception for LightControls to raise."""


class PatternException(LightBerryException):
    """Exception for LightPatterns to raise."""


class PixelException(LightBerryException):
    """Exception for LightPixel to raise."""
