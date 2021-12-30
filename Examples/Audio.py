#!/usr/bin/python3
"""example syncing lights to audio"""
import time
import multiprocessing
import pyaudio  # pylint: disable = import-error
import numpy as np
from LightBerries import LightControl
from LightBerries import LightPatterns
from LightBerries.LightPixels import Pixel, EnumLEDOrder
import scipy

# import matplotlib.pyplot as plt
from LightBerries.LightControl import LightController
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray, SolidColorArray, PixelColors


SAMPLE_RATE = 44100
CHUNK_COUNT = 4
SAMPLE_COUNT_TOTAL = 44100
SAMPLE_COUNT_PER_CHUNK = SAMPLE_COUNT_TOTAL // CHUNK_COUNT
DATA_FRAME = np.zeros((SAMPLE_COUNT_TOTAL))
LED_COUNT = 100
PLOT_DATA = np.zeros((LED_COUNT))


def PlotStuff(_):
    """plots audio FFT to graphic plot and/or lights"""
    global DATA_FRAME, PLOT_DATA  # pylint: disable = global-statement
    # plt.ion()
    line1 = None
    line2 = None
    line3 = None
    i = 0
    plotTime = False
    plotFfts = False
    plotFftChunks = False
    LIGHT_CONTROL = LightController(LED_COUNT, 18, 10, 800000, debug=True)
    LIGHT_CONTROL.off()
    LIGHT_CONTROL.refreshLEDs()

    try:
        while True:
            msg = None
            try:
                msg = q.get_nowait()
            except multiprocessing.queues.Empty:
                pass
            if not msg is None:
                DATA_FRAME = np.roll(DATA_FRAME, SAMPLE_COUNT_PER_CHUNK)
                DATA_FRAME[-SAMPLE_COUNT_PER_CHUNK:] = msg
                # fftData = 10 * np.log10(np.abs(np.fft.fft(DATA_FRAME)))
                fftData = 10 * np.log10(np.abs(scipy.fft(DATA_FRAME)))
                fftData = fftData[len(fftData) // 2 :]
                fftData = np.nan_to_num(fftData)

                # print(len(fft_data), lf._LEDCount)
                chunkLength = len(fftData) // LIGHT_CONTROL.privateLEDCount
                fftMin = np.min(fftData)
                if fftMin < 0:
                    fftData -= fftMin
                fftData = fftData ** 3
                fftChunks = np.array(
                    [
                        np.sum(fftData[i : i + chunkLength]) / chunkLength
                        for i in range(0, len(fftData), chunkLength)
                    ]
                )
                fftChunks = fftChunks ** 8
                if plotFftChunks:
                    if line3 is None:
                        figure3, axis3 = plt.subplots(1)
                        (line3,) = axis3.semilogy(fftChunks)
                        plt.show()
                    else:
                        line3.set_ydata(fftChunks)
                        axis3.relim()
                        axis3.autoscale_view(True, True, True)
                        figure3.canvas.draw()

                if plotFfts:
                    figure1, axis1 = plt.subplots(1)
                    # if msg[0] == 'f':
                    print("fft")
                    # msg = msg
                    if line1 is None:
                        # freqs = sp.fftpack.fftfreq(len(msg))
                        # l1, = a1.semilogy(freqs, msg)

                        # dataFrame[i*sampleCountPerChunk:(i+1)*sampleCountPerChunk] = msg
                        # msg = 10 * np.log(np.abs(np.fft.fft(dataFrame)))

                        msg = 10 * np.log10(np.abs(np.fft.fft(DATA_FRAME)))
                        msg = msg[len(msg) // 2 :]
                        msg = np.nan_to_num(msg)
                        # l1, = a1.plot(msg)
                        (line1,) = axis1.semilogy(msg)
                        # a1.set_ylim(1e-10, 10)
                        plt.show()
                    else:
                        # dataFrame[i*sampleCountPerChunk:(i+1)*sampleCountPerChunk] = msg
                        # msg = 10 * np.log(np.abs(np.fft.fft(dataFrame)))

                        print(msg)
                        line1.set_ydata(msg)
                        axis1.relim()
                        axis1.autoscale_view(True, True, True)
                        figure1.canvas.draw()

                msg_len = len(DATA_FRAME)

                x = LIGHT_CONTROL.virtualLEDCount
                y = int(np.floor(msg_len / x))

                msg = np.reshape(DATA_FRAME[: (x * y)], (x, y))
                msg = np.apply_along_axis(np.sum, 1, msg)
                # msg = msg.astype(np.int32)
                msg -= np.min(msg)
                msg = msg / np.max(msg)
                msg *= float(255 * 2 / 3)
                msg = np.array(msg, dtype=np.int32)
                PLOT_DATA = PLOT_DATA * 1 / 3
                PLOT_DATA += msg
                LIGHT_CONTROL.setVirtualLEDArray(
                    LightPatterns.ConvertPixelArrayToNumpyArray(
                        [Pixel(int(p), order=EnumLEDOrder.RGB) for p in PLOT_DATA]
                    )
                )
                LIGHT_CONTROL.copyVirtualLedsToWS281X()
                LIGHT_CONTROL.refreshLEDs()
                if plotTime:
                    figure2, axis2 = plt.subplots(1)
                    if line2 is None:
                        # print(msg)
                        # last = np.zeros(len(msg)*2)
                        # last[len(last)//2:] = msg
                        (line2,) = axis2.plot(DATA_FRAME)
                        plt.show()
                    else:
                        # last[:len(last)//2] = last[len(last)//2:]
                        # last[len(last)//2:] = msg
                        line2.set_ydata(DATA_FRAME)
                        # l2.set_xlim()
                        axis2.relim()
                        axis2.autoscale_view(True, True, True)
                        figure2.canvas.draw()

                # LightController.setVirtualLEDArray(msg)
                i += 1
                if i >= CHUNK_COUNT:
                    i = 0

    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print("error in loop", ex)
        raise

    print("off?")
    LIGHT_CONTROL.off()
    LIGHT_CONTROL.copyVirtualLedsToWS281X()
    LIGHT_CONTROL.refreshLEDs()
    time.sleep(0.2)
    del LIGHT_CONTROL


q: multiprocessing.Queue = multiprocessing.Queue()
process = multiprocessing.Process(target=PlotStuff, args=(q,))
process.start()

PY_AUDIO = None
AUDIO_STREAM = None
try:
    #
    form_1 = pyaudio.paInt16  # 16-bit resolution
    CHANNEL = 1  # 1 channel
    BYTES_PER_CHUNK = SAMPLE_COUNT_PER_CHUNK * 2  # 2^12 sampleCountPerChunk for buffer
    # record_secs = 0.5 # seconds to record
    DEVICE_INDEX = 0  # device index found by p.get_device_info_by_index(ii)
    WAV_OUTPUT_FILENAME = "test1.wav"  # name of .wav file
    # _max = 0
    PY_AUDIO = pyaudio.PyAudio()
    # print(sampleCountPerChunk, sample_bytes)
    print(PY_AUDIO.get_device_info_by_index(0))

    DATA_FRAME_COUNTER = 0
    # fft_data = np.log(np.abs(sp.fftpack.fft(dataFrame * 0.5)))
    # fft_data = np.log(np.abs(np.fft.fft(dataFrame * 0.5)))
    # fft_data = np.nan_to_num(fft_data)
    # fft_data = fft_data[len(fft_data)//2:][:1048]
    # line = a.plot(fft_data)
    # line = None

    try:

        AUDIO_STREAM = PY_AUDIO.open(
            format=form_1,
            rate=SAMPLE_RATE,
            channels=CHANNEL,
            input_device_index=DEVICE_INDEX,
            input=True,
            frames_per_buffer=BYTES_PER_CHUNK,
        )
        # frames: List[] = []
        while True:
            data = AUDIO_STREAM.read(SAMPLE_COUNT_PER_CHUNK)
            data = np.frombuffer(data, dtype=np.int16)
            print(len(data))
            # dataFrame[data_frame_counter*sampleCountPerChunk:
            # (data_frame_counter+1)*sampleCountPerChunk] = np.nan_to_num(data)
            # fft_data = 10 * np.log(np.abs(np.fft.fft(dataFrame * 0.5)))
            # fft_data = np.nan_to_num(fft_data)
            # fft_data = fft_data[len(fft_data)//2:][:1048]
            q.put_nowait(data)
            # q.put_nowait(('t',data.copy()))
            # q.put_nowait(('f',data))
            # q.put_nowait(('f',fft_data))
            # if line is None:
            # 	line, = a.plot(fft_data)
            # 	print(line)
            # 	plt.show()
            # 	print('first')
            # else:
            # 	line.set_ydata(fft_data)
            # 	f.canvas.draw()
            # 	print('another')
            # count = 100
            # index = 1
            # chunk_length = len(fft_data) // count
            # m = np.min(fft_data)
            # if m < 0:
            # 	fft_data -= m
            # fft_data = fft_data**3
            # fft_chunks = np.array([np.sum(fft_data[i:i+chunk_length])/
            # chunk_length for i in range(0, len(fft_data), chunk_length)])
            # fft_chunks = fft_chunks**8
            # fft_chunks[0] = 0.01
            # fft_chunks[-1] = 0.01
            # m = np.min(fft_chunks)
            # if m < 0:
            # 	fft_chunks -= m
            # m = np.max(fft_chunks[1:-1])
            # if not m == 0:
            # 	fft_chunks /= m
            # 	nrm = np.sum(fft_chunks) / len(fft_chunks)
            # 	if nrm > 0:
            # 		if not ((fft_chunks[1] > 0.9) and \
            # 			(fft_chunks[2] > 0.9) and \
            # 			(fft_chunks[3] > 0.9)) and not np.isnan(fft_chunks[1]):
            # 			for i in range(count):
            # 				lf._LEDArray[i] = Pixel(ary[i] * fft_chunks[i])
            # 				# lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i],
            # Pixel(ary[i] * fft_chunks[i]), 50)
            # 			# [lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i],
            # Pixel(ary[i] * fft_chunks[i]), 50) for i in range(count)]
            # lf._refreshLEDs()
            # if data_frame_counter < (chunkCount - 1):
            # 	data_frame_counter += 1
            # else:
            # 	data_frame = np.roll(dataFrame, -sampleCountPerChunk)
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        if not AUDIO_STREAM is None:
            # print("finished recording")
            AUDIO_STREAM.stop_stream()
            AUDIO_STREAM.close()
except KeyboardInterrupt:
    pass
except:
    raise
finally:
    if not PY_AUDIO is None:
        PY_AUDIO.terminate()
time.sleep(0.2)
LIGHT_CONTROL = None
# waveFile = wave.open(wav_output_filename, 'wb')
# waveFile.setnchannels(chans)
# waveFile.setsampwidth(p.get_sample_size(form_1))
# waveFile.setframerate(sampleRate)
# waveFile.writeframes(b''.join(frames))
# waveFile.close()
