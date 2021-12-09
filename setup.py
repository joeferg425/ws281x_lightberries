from distutils.core import setup
import setuptools
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    install_requires=[
        "Adafruit-Blinka>=3.0.0",
        "adafruit-circuitpython-neopixel==3.4.0",
        "numpy>=1.15.1",
        "rpi_ws281x==4.2.2",
        "RPi.GPIO>=0.7.0",
        "nptyping>=1.4.4",
    ],
    name="LightBerries",
    version="0.99dev",
    packages=setuptools.find_packages(),
    license="MIT",
    description=("A wrapper for rpi_ws281x that does all the heavy lifting for you."),
    keywords="raspberry pi rpi rpi_ws281x adafruit neopixel",
    url="https://github.com/joeferg425/ws281x_lightberries",
    author="JoeFerg425",
    python_requires=">=3.7",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
)
