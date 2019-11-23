# About:
Wrapper for rpi_ws281x library that defines a bunch of colorful functions.

This library has only been tested on raspberry pi 2 and raspberry pi 3. The lights I have are ws2811 50ct off of amazon with a custom 5v power supply and level converter.

This library is intended for a string of lights not a matrix configuration.


# Installation:
	pip install lightberries-joeferg425


# Examples:

## Demo mode:
```python
# define your LED strand length
ledCount = 100
# create the underlying ws281x control object
ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
# create the interface to the gpio ping
lights = LightString(ledCount=ledCount, rpi_ws281x=ws281x)
# create the light function object
lightFunction = LightFunction(lights=lights, debug=True)
# choose a function
lightFunction.demo(secondsPerMode=5)
```
## Rainbow that scrolls across the lights:
```python
# define your LED strand length
ledCount = 100
# create the underlying ws281x control object
ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
# create the interface to the gpio ping
lights = LightString(ledCount=ledCount, rpi_ws281x=ws281x)
# create the light function object
lightFunction = LightFunction(lights=lights)
# choose a function
lightFunction.Do_Shift_Rainbow()
```
## Raindrop function:
```python
# define your LED strand length
ledCount = 100
# create the underlying ws281x control object
ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
# create the interface to the gpio ping
lights = LightString(ledCount=ledCount, rpi_ws281x=ws281x)
# create the light function object
lightFunction = LightFunction(lights=lights)
# choose a function
lightFunction.Do_Raindrops()
```
