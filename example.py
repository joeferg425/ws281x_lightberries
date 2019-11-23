from LightBerries import LightFunction, LightString, rpi_ws281x

# define your LED strand length
ledCount = 100
# create the underlying ws281x control object
ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
# create the interface to the gpio ping
lights = LightString(ledCount=ledCount, rpi_ws281x=ws281x)#gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
# create the light function object
lightFunction = LightFunction(lights=lights, debug=True)
# choose a function
lightFunction.demo(secondsPerMode=5)

