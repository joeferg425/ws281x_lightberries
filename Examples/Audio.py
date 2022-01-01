#!/usr/bin/python3
"""Example of syncing lights to audio."""
from enum import IntEnum
import time
import multiprocessing
import pyaudio
import scipy.signal
import numpy as np
import matplotlib.pyplot as plt
from LightBerries.LightControl import LightController


class RollingDataFromQueue:
    """Parent class for updating data arrays.

    Uses chunks of data passed through multiprocess queues to update
    a numpy array.
    """

    SAMPLE_RATE = 44100
    CHUNK_COUNT = 1
    DURATION_IN_SECONDS = 1 / 4
    SAMPLE_COUNT_TOTAL = int(SAMPLE_RATE * DURATION_IN_SECONDS)
    SAMPLE_COUNT_PER_CHUNK = SAMPLE_COUNT_TOTAL // CHUNK_COUNT
    LED_COUNT = 100
    SUMMATION = SAMPLE_COUNT_PER_CHUNK // 2 // LED_COUNT
    MOVING_AVERAGE_LENGTH = 4

    def __init__(self, inQ: multiprocessing.Queue, outQ: multiprocessing.Queue) -> None:
        """Parent class for rolling data frames.

        Args:
            inQ: multiprocessing queue for receiving data
            outQ: multiprocessing queue for sending data
        """
        self.inQ = inQ
        self.outQ = outQ
        self.newDataChunk = np.zeros((RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK))
        self.fftData = np.zeros((RollingDataFromQueue.SAMPLE_COUNT_TOTAL // 2))
        self.fftChunks = np.zeros((RollingDataFromQueue.SAMPLE_COUNT_TOTAL // 2))
        self.dataFrame = np.zeros((RollingDataFromQueue.SAMPLE_COUNT_TOTAL))
        self.plotData = np.zeros((RollingDataFromQueue.LED_COUNT))

        # self.window = np.hamming(RollingDataFromQueue.SAMPLE_COUNT_TOTAL)
        self.window = np.hamming(RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK)

    def getNewData(self) -> bool:
        """Gets data from multiprocess queue and processes it.

        Returns:
            success boolean
        """
        try:
            # check the queue - throws an exception if empty
            self.newDataChunk = self.inQ.get_nowait()
            # roll the data frame so we can insert/overwrite oldest data with new
            self.dataFrame = np.roll(self.dataFrame, RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK)
            # add the new data to the frame
            self.dataFrame[-RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK :] = self.newDataChunk

            # do FFT on one of the data sets
            # self.fftData = 10 * np.log10(np.abs(np.fft.fft(DATA_FRAME)*self.window))
            self.fftData = 10 * np.log10(np.abs(np.fft.fft(self.newDataChunk) * self.window))

            # make FFT adjustments
            lenfftData = len(self.fftData)
            self.fftData = self.fftData[lenfftData // 2 :]
            lenfftData = len(self.fftData)
            self.fftData = np.nan_to_num(self.fftData)

            # chunk the data up for display in fewer segments
            chunkLength = lenfftData // LightOutput.LED_COUNT
            self.fftChunks = np.array(
                [
                    np.sum(self.fftData[i : i + chunkLength]) / chunkLength
                    for i in range(0, lenfftData, chunkLength)
                ]
            )
            # mask any artifacts at the ends
            self.fftChunks[-1] = np.mean(self.fftChunks)
            # trim array
            self.fftChunks = self.fftChunks[: LightOutput.LED_COUNT]
            # remove low-frequency bias
            self.fftChunks = scipy.signal.detrend(self.fftChunks)
            # normalize so data starts from zero
            self.fftChunks -= np.min(self.fftChunks)
            # cube it to exaggurate differences
            self.fftChunks **= 3
            # rescale to zero
            self.fftChunks -= np.min(self.fftChunks)
            # finish normalization down to one
            self.fftChunks /= np.max(self.fftChunks)
            # scale to range (0 - 255)
            self.fftChunks *= 255

            # do moving average calculation
            self.plotData = (
                self.plotData
                * (RollingDataFromQueue.MOVING_AVERAGE_LENGTH - 1)
                / RollingDataFromQueue.MOVING_AVERAGE_LENGTH
            )
            self.plotData += self.fftChunks * 1 / RollingDataFromQueue.MOVING_AVERAGE_LENGTH
            # return true for new data
            return True
        except multiprocessing.queues.Empty:
            # return false for empty queue
            return False


class LightOutput(RollingDataFromQueue):
    """Outputs audio FFT to light controller object."""

    def __init__(self, inQ: multiprocessing.Queue, outQ: multiprocessing.Queue) -> None:
        """Outputs audio FFT to light controller object.

        Args:
            inQ: multiprocessing queue for receiving data
            outQ: multiprocessing queue for sending data
        """
        super().__init__(inQ, outQ)
        # create light controller object
        self.lightController = LightController(LightOutput.LED_COUNT, 18, 10, 800000)
        self.lightController.off()
        self.lightController.refreshLEDs()

        # run routine
        self.run()

    def run(self):
        """Run the process."""
        try:
            while True:
                # see if we got data
                if self.getNewData():
                    # define callback function
                    def SetPixel(irgb):
                        try:
                            i = irgb[0]
                            rgb = irgb[1]
                            value = int(rgb)
                            # bypass virtual LED array in LightBerries to try for better update speeds
                            self.lightController.ws28xxLightString.pixelStrip.setPixelColor(i, value)
                        except SystemExit:  # pylint:disable=try-except-raise
                            raise
                        except KeyboardInterrupt:  # pylint:disable=try-except-raise
                            raise
                        except Exception as ex:
                            print(f"Failed to set pixel {i} in WS281X to value {value}: {str(ex)}")

                    # copy this class's array into the ws281x array using fast mapping method
                    list(
                        map(
                            SetPixel,
                            enumerate(self.plotData),
                        )
                    )

                    # call ws281x update method to display modified LED values
                    self.lightController.ws28xxLightString.pixelStrip.show()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {LightOutput.__name__}: {str(ex)}")
        finally:
            # clean up the LightBerry object
            self.lightController.off()
            self.lightController.copyVirtualLedsToWS281X()
            self.lightController.refreshLEDs()
            # pause for object destruction
            time.sleep(0.2)
            # put any data in queue, this will signify "exit" status
            self.outQ.put("quit")
            # double-check deletion
            del self.lightController


class PlotChoice(IntEnum):
    """Enumeration of plot types.

    Args:
        IntEnum: integer enumeration
    """

    TIME_DOMAIN = 0
    LARGE_FFT = 1
    CHUNK_FFT = 2
    AVERAGED_FFT = 3
    TIME_DOMAIN_CHUNK = 4


class PlotAxisChoice(IntEnum):
    """Enumeration of plot axis scaling.

    Args:
        IntEnum: integer enumeration
    """

    STANDARD = 0
    LOGARITHMIC = 1


class PlotOutput(RollingDataFromQueue):
    """Plots audio FFT to matplotlib's pyplot graphic."""

    def __init__(self, inQ: multiprocessing.Queue, outQ: multiprocessing.Queue) -> None:
        """Plots audio FFT to matplotlib's pyplot graphic.

        Args:
            inQ: multiprocessing queue for receiving data
            outQ: multiprocessing queue for sending data
        """
        super().__init__(inQ, outQ)
        # set pyplot to use live updating plots
        plt.ion()
        # make a selection for what to plot
        self.plotChoice = PlotChoice.AVERAGED_FFT
        # plot axis scaling
        self.plotAxisType = PlotAxisChoice.STANDARD
        # run the process
        self.run()

    def run(self):
        """Run the process."""
        figure = None
        axis = None
        line = None
        try:
            while True:
                # try to get new data
                if self.getNewData():
                    # if not first plot
                    if line is not None:
                        # update with correct data
                        if self.plotChoice == PlotChoice.CHUNK_FFT:
                            line.set_ydata(self.fftChunks)
                        elif self.plotChoice == PlotChoice.AVERAGED_FFT:
                            line.set_ydata(self.plotData)
                        elif self.plotChoice == PlotChoice.LARGE_FFT:
                            line.set_ydata(self.fftData)
                        elif self.plotChoice == PlotChoice.TIME_DOMAIN_CHUNK:
                            line.set_ydata(self.newDataChunk)
                        else:
                            line.set_ydata(self.dataFrame)
                        # adjust axis/scaling so that data is visible
                        axis.relim()
                        axis.autoscale_view(True, True, True)
                        # redraw
                        figure.canvas.draw()
                        # pause/update figure on screen
                        plt.pause(0.1)
                    else:
                        # create figure with one plot
                        figure, axis = plt.subplots(1)
                        # plot logarithmic or not
                        if self.plotAxisType == PlotAxisChoice.LOGARITHMIC:
                            # do first plot of data
                            if self.plotChoice == PlotChoice.CHUNK_FFT:
                                (line,) = axis.semilogy(self.fftChunks)
                            elif self.plotChoice == PlotChoice.AVERAGED_FFT:
                                (line,) = axis.semilogy(self.plotData)
                            elif self.plotChoice == PlotChoice.LARGE_FFT:
                                (line,) = axis.semilogy(self.fftData)
                            elif self.plotChoice == PlotChoice.TIME_DOMAIN_CHUNK:
                                (line,) = axis.semilogy(self.newDataChunk)
                            else:
                                (line,) = axis.semilogy(self.dataFrame)
                        # do standard plot scaling
                        else:
                            if self.plotChoice == PlotChoice.CHUNK_FFT:
                                (line,) = axis.plot(self.fftChunks)
                            elif self.plotChoice == PlotChoice.AVERAGED_FFT:
                                (line,) = axis.plot(self.plotData)
                            elif self.plotChoice == PlotChoice.LARGE_FFT:
                                (line,) = axis.plot(self.fftData)
                            elif self.plotChoice == PlotChoice.TIME_DOMAIN_CHUNK:
                                (line,) = axis.plot(self.newDataChunk)
                            else:
                                (line,) = axis.plot(self.dataFrame)
                        # draw/show the figure
                        plt.show()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {PlotOutput.__name__}: {str(ex)}")
        finally:
            self.outQ.put("quit")


class ProcessChoice(IntEnum):
    """Enumeration of process function (plot or lights).

    Args:
        IntEnum: integer enumeration
    """

    PLOT = 0
    LIGHTS = 1


if __name__ == "__main__":

    PY_AUDIO = None
    AUDIO_STREAM = None
    PROCESS_CHOICE = ProcessChoice.LIGHTS
    try:
        # create queues for sending & receiving data across processes
        inq: multiprocessing.Queue = multiprocessing.Queue()
        outq: multiprocessing.Queue = multiprocessing.Queue()

        # choose between plotting and updating LEDs
        if PROCESS_CHOICE == ProcessChoice.LIGHTS:
            process = multiprocessing.Process(target=LightOutput, args=(inq, outq))
        else:
            process = multiprocessing.Process(target=PlotOutput, args=(inq, outq))

        # start the selected process
        process.start()

        # setup audio stream
        PY_AUDIO = pyaudio.PyAudio()
        # can use this to find correct device if it is not working
        # for i in range(PY_AUDIO.get_device_count()):
        # print(PY_AUDIO.get_device_info_by_index(i))
        DEVICE_INDEX = 0
        print("Using following Audio device:\n", PY_AUDIO.get_device_info_by_index(DEVICE_INDEX))
        # 16-bit resolution
        AUDIO_FORMAT = pyaudio.paInt16
        # 1 channel
        CHANNEL = 1
        # 16-bit audio is (2-bytes * SAMPLE_COUNT_PER_STREAM_CHUNK)
        BYTES_PER_CHUNK = RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK * 2

        try:
            # create the streaming audio object
            AUDIO_STREAM = PY_AUDIO.open(
                format=AUDIO_FORMAT,
                rate=RollingDataFromQueue.SAMPLE_RATE,
                channels=CHANNEL,
                input_device_index=DEVICE_INDEX,
                input=True,
                frames_per_buffer=BYTES_PER_CHUNK,
            )
            # set flag for first run
            FIRST_RUN = True
            # loop forever
            while True:
                # check for output data from process signifying "exit" status
                try:
                    msg = outq.get_nowait()
                    # if we get anything, break out of loop
                    break
                except multiprocessing.queues.Empty:
                    pass
                # read new data chunk
                data = AUDIO_STREAM.read(RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK)
                # turn raw data into numpy array
                data = np.frombuffer(data, dtype=np.int16)
                # print some info the first time we read data
                if FIRST_RUN is True:
                    print("Audio chunk data length is", len(data))
                    FIRST_RUN = False
                # put the data in the queue going to the processing function
                inq.put_nowait(data)
        except KeyboardInterrupt:
            pass
        except Exception:
            raise
        finally:
            # always try to clean up the memory
            if AUDIO_STREAM is not None:
                AUDIO_STREAM.stop_stream()
                AUDIO_STREAM.close()
    except KeyboardInterrupt:
        pass
    except Exception:
        raise
    finally:
        # always try to clean up the memory
        if PY_AUDIO is not None:
            PY_AUDIO.terminate()
    # hang out in case cleanup is happening in the other process
    time.sleep(0.2)
