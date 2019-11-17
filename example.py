from LightBerries import LightFunction, LightString

# create the interface to the gpio ping
lights = LightString(gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
# create the light function object
lightFunction = LightFunction(lights=lights)
# choose a function
lightFunction.demo(secondsPerMode=5)

lightFunction.Do_Raindrops()
