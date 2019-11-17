# ws281x_lightberries
Wrapper for rpi_ws281x library that defines a bunch of colorful functions.

This library has only been tested on raspberry pi 2 and raspberry pi 3. The lights I have are ws2811 50ct off of amazon with a custom 5v power supply and level converter.

This library is intended for a string of lights not a matrix configuration.


Installation:
	pip install WS281X_lightberries


Exmaples:

	Demo mode:
		# create the interface to the gpio ping
		lights = LightString(gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
		# create the light function object
		lightFunction = LightFunction(lights=lights)
		# choose a function
		lightFunction.demo(secondsPerMode=5)

	Rainbow that scrolls across the lights:
		# create the interface to the gpio ping
		lights = LightString(gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
		# create the light function object
		lightFunction = LightFunction(lights=lights)
		# choose a function
		lightFunction.Do_Shift_Rainbow()

	Raindrop function:
		# create the interface to the gpio ping
		lights = LightString(gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
		# create the light function object
		lightFunction = LightFunction(lights=lights)
		# choose a function
		lightFunction.Do_Raindrops()

