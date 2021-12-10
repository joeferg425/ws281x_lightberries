"""creates custom exception classes to catch"""


class LightBerryException(Exception):
    """a custom exception for LightBerries"""


class LightBerryFunctionException(LightBerryException):
    """exception for LightFunction to raise"""


class LightBerryControlException(LightBerryException):
    """exception for LightFunction to raise"""
