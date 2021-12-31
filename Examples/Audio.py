#!/usr/bin/python3
"""Example syncing lights to audio."""
from enum import IntEnum
import time
import multiprocessing
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from LightBerries.LightControl import LightController


class RollingDataFromQueue:
    """Parent class for rolling data frames."""

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
            self.newDataChunk = self.inQ.get_nowait()
            self.dataFrame = np.roll(self.dataFrame, RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK)
            self.dataFrame[-RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK :] = self.newDataChunk

            # self.fftData = 10 * np.log10(np.abs(np.fft.fft(DATA_FRAME)*self.window))
            self.fftData = 10 * np.log10(np.abs(np.fft.fft(self.newDataChunk) * self.window))
            lenfftData = len(self.fftData)
            self.fftData = self.fftData[lenfftData // 2 :]
            lenfftData = len(self.fftData)
            self.fftData = np.nan_to_num(self.fftData)

            chunkLength = lenfftData // LightOutput.LED_COUNT
            self.fftChunks = np.array(
                [
                    np.sum(self.fftData[i : i + chunkLength]) / chunkLength
                    for i in range(0, lenfftData, chunkLength)
                ]
            )
            self.fftChunks[-1] = np.mean(self.fftChunks)
            self.fftChunks = self.fftChunks[: LightOutput.LED_COUNT]
            if np.min(self.fftChunks) < 0:
                self.fftChunks += np.min(self.fftChunks)
            else:
                self.fftChunks -= np.min(self.fftChunks)
            self.fftChunks **= 3
            if np.min(self.fftChunks) < 0:
                self.fftChunks += np.min(self.fftChunks)
            else:
                self.fftChunks -= np.min(self.fftChunks)
            self.fftChunks /= np.max(self.fftChunks)
            self.fftChunks *= 255
            self.plotData = (
                self.plotData
                * (RollingDataFromQueue.MOVING_AVERAGE_LENGTH - 1)
                / RollingDataFromQueue.MOVING_AVERAGE_LENGTH
            )
            self.plotData += self.fftChunks * 1 / RollingDataFromQueue.MOVING_AVERAGE_LENGTH
            return True
        except multiprocessing.queues.Empty:
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
        self.lightController = LightController(LightOutput.LED_COUNT, 18, 10, 800000, debug=True)
        self.lightController.off()
        self.lightController.refreshLEDs()

        self.run()

    def run(self):
        """Run the process."""
        try:
            while True:
                if self.getNewData():
                    # self.lightController.setVirtualLEDArray(
                    # LightPatterns.ConvertPixelArrayToNumpyArray(
                    # [Pixel(int(p), order=EnumLEDOrder.RGB) for p in self.fftChunks]
                    # )
                    # )
                    def SetPixel(irgb):
                        try:
                            i = irgb[0]
                            rgb = irgb[1]
                            value = int(rgb)
                            self.lightController.ws28xxLightString.pixelStrip.setPixelColor(i, value)
                        except SystemExit:  # pylint:disable=try-except-raise
                            raise
                        except KeyboardInterrupt:  # pylint:disable=try-except-raise
                            raise
                        except Exception as ex:
                            print(f"Failed to set pixel {i} in WS281X to value {value}: {str(ex)}")

                    # copy this class's array into the ws281x array
                    list(
                        map(
                            SetPixel,
                            enumerate(self.plotData),
                        )
                    )

                    self.lightController.ws28xxLightString.pixelStrip.show()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {LightOutput.__name__}: {str(ex)}")
        finally:
            self.outQ.put("quit")
            self.lightController.off()
            self.lightController.copyVirtualLedsToWS281X()
            self.lightController.refreshLEDs()
            time.sleep(0.2)
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


class PlotOutput(RollingDataFromQueue):
    """Plots audio FFT to graphic."""

    def __init__(self, inQ, outQ) -> None:
        """Plots audio FFT to graphic.

        Args:
            inQ: multiprocessing queue for receiving data
            outQ: multiprocessing queue for sending data
        """
        super().__init__(inQ, outQ)
        plt.ion()
        self.plotChoice = PlotChoice.AVERAGED_FFT
        self.run()

    def run(self):
        """Run the process."""
        line = None
        try:
            while True:
                if self.getNewData():
                    if self.plotChoice == PlotChoice.CHUNK_FFT:
                        if line is None:
                            figure, axis = plt.subplots(1)
                            # (line,) = axis.semilogy(self.fftChunks)
                            (line,) = axis.plot(self.fftChunks)
                            plt.show()
                        else:
                            line.set_ydata(self.fftChunks)
                            axis.relim()
                            axis.autoscale_view(True, True, True)
                            figure.canvas.draw()
                            plt.pause(0.1)

                    elif self.plotChoice == PlotChoice.AVERAGED_FFT:
                        if line is None:
                            figure, axis = plt.subplots(1)
                            # (line,) = axis.semilogy(self.plotData)
                            (line,) = axis.plot(self.plotData)
                            plt.show()
                        else:
                            line.set_ydata(self.plotData)
                            axis.relim()
                            axis.autoscale_view(True, True, True)
                            figure.canvas.draw()
                            plt.pause(0.1)

                    elif self.plotChoice == PlotChoice.LARGE_FFT:
                        if line is None:
                            figure, axis = plt.subplots(1)
                            # (line,) = axis.semilogy(self.fftData)
                            (line,) = axis.plot(self.fftData)
                            plt.show()
                        else:
                            line.set_ydata(self.fftData)
                            axis.relim()
                            axis.autoscale_view(True, True, True)
                            figure.canvas.draw()
                            plt.pause(0.1)

                    else:
                        if line is None:
                            figure, axis = plt.subplots(1)
                            (line,) = axis.plot(self.dataFrame)
                            plt.show()
                        else:
                            line.set_ydata(self.dataFrame)
                            axis.relim()
                            axis.autoscale_view(True, True, True)
                            figure.canvas.draw()
                            plt.pause(0.1)

        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {PlotOutput.__name__}: {str(ex)}")
        finally:
            self.outQ.put("quit")


if __name__ == "__main__":

    PY_AUDIO = None
    AUDIO_STREAM = None
    try:
        inq: multiprocessing.Queue = multiprocessing.Queue()
        outq: multiprocessing.Queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=LightOutput, args=(inq, outq))
        # process = multiprocessing.Process(target=PlotOutput, args=(inq, outq))
        process.start()
        form_1 = pyaudio.paInt16  # 16-bit resolution
        CHANNEL = 1  # 1 channel
        BYTES_PER_CHUNK = (
            RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK * 2
        )  # 2^12 sampleCountPerChunk for buffer
        DEVICE_INDEX = 0  # device index found by p.get_device_info_by_index(ii)
        PY_AUDIO = pyaudio.PyAudio()
        print(PY_AUDIO.get_device_info_by_index(0))

        try:
            AUDIO_STREAM = PY_AUDIO.open(
                format=form_1,
                rate=RollingDataFromQueue.SAMPLE_RATE,
                channels=CHANNEL,
                input_device_index=DEVICE_INDEX,
                input=True,
                frames_per_buffer=BYTES_PER_CHUNK,
            )
            FIRST_RUN = True
            while True:
                try:
                    msg = outq.get_nowait()
                    break
                except multiprocessing.queues.Empty:
                    pass
                data = AUDIO_STREAM.read(RollingDataFromQueue.SAMPLE_COUNT_PER_CHUNK)
                data = np.frombuffer(data, dtype=np.int16)
                if FIRST_RUN is True:
                    print("Audio chunk data length is", len(data))
                    FIRST_RUN = False
                inq.put_nowait(data)
        except KeyboardInterrupt:
            pass
        except Exception:
            raise
        finally:
            if AUDIO_STREAM is not None:
                AUDIO_STREAM.stop_stream()
                AUDIO_STREAM.close()
    except KeyboardInterrupt:
        pass
    except Exception:
        raise
    finally:
        if PY_AUDIO is not None:
            PY_AUDIO.terminate()
    time.sleep(0.2)
    LIGHT_CONTROL = None
