"""Defines custom exception classes to catch from this modeule."""


class LightBerryException(Exception):
    """Custom exception for the LightBerries module."""


class LightFunctionException(LightBerryException):
    """Exception for LightFunctions to raise."""


class LightStringException(LightBerryException):
    """Exception for LightString to raise."""


class LightControlException(LightBerryException):
    """Exception for LightControls to raise."""


class LightPatternException(LightBerryException):
    """Exception for LightPatterns to raise."""


class LightPixelException(LightBerryException):
    """Exception for LightPixel to raise."""
