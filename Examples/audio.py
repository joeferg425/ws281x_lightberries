import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing
from LightBerries.LightControl import LightController
from LightBerries.Pixels import Pixel
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray, SolidColorArray, PixelColors


sampleRate = 44100
chunkCount = 4
sampleCountTotal = 20000
sampleCountPerChunk = sampleCountTotal // chunkCount
dataFrame = np.zeros((sampleCountTotal))


def plot_stuff(q):
    global dataFrame
    plt.ion()
    l1 = None
    l2 = None
    l3 = None
    i = 0
    last = None
    plot_time = False
    plot_ffts = False
    plot_fft_chunks = True
    lf = LightController(100, 18, 10, 800000, debug=True)
    lfArray = ConvertPixelArrayToNumpyArray(SolidColorArray(100, PixelColors.GREEN))

    try:
        while True:
            msg = None
            try:
                msg = q.get_nowait()
            except multiprocessing.queues.Empty:
                pass
            if not msg is None:
                dataFrame = np.roll(dataFrame, sampleCountPerChunk)
                dataFrame[-sampleCountPerChunk:] = msg
                fft_data = 10 * np.log10(np.abs(np.fft.fft(dataFrame)))
                fft_data = fft_data[len(fft_data) // 2 :]
                fft_data = np.nan_to_num(fft_data)

                # print(len(fft_data), lf._LEDCount)
                chunk_length = len(fft_data) // lf.__LEDCount
                m = np.min(fft_data)
                if m < 0:
                    fft_data -= m
                fft_data = fft_data ** 3
                fft_chunks = np.array(
                    [
                        np.sum(fft_data[i : i + chunk_length]) / chunk_length
                        for i in range(0, len(fft_data), chunk_length)
                    ]
                )
                fft_chunks = fft_chunks ** 8
                if plot_fft_chunks:
                    if l3 is None:
                        f3, a3 = plt.subplots(1)
                        (l3,) = a3.semilogy(fft_chunks)
                        plt.show()
                    else:
                        l3.set_ydata(fft_chunks)
                        a3.relim()
                        a3.autoscale_view(True, True, True)
                        f3.canvas.draw()

                if plot_ffts:
                    f1, a1 = plt.subplots(1)
                    # if msg[0] == 'f':
                    print("fft")
                    msg = msg
                    if l1 is None:
                        # freqs = sp.fftpack.fftfreq(len(msg))
                        # l1, = a1.semilogy(freqs, msg)

                        # dataFrame[i*sampleCountPerChunk:(i+1)*sampleCountPerChunk] = msg
                        # msg = 10 * np.log(np.abs(np.fft.fft(dataFrame)))

                        msg = 10 * np.log10(np.abs(np.fft.fft(dataFrame)))
                        msg = msg[len(msg) // 2 :]
                        msg = np.nan_to_num(msg)
                        # l1, = a1.plot(msg)
                        (l1,) = a1.semilogy(msg)
                        # a1.set_ylim(1e-10, 10)
                        plt.show()
                    else:
                        # dataFrame[i*sampleCountPerChunk:(i+1)*sampleCountPerChunk] = msg
                        # msg = 10 * np.log(np.abs(np.fft.fft(dataFrame)))

                        print(msg)
                        l1.set_ydata(msg)
                        a1.relim()
                        a1.autoscale_view(True, True, True)
                        f1.canvas.draw()
                    # elif msg[0] == 't':
                    # print('time')
                    # msg = msg[1]
                if plot_time:
                    f2, a2 = plt.subplots(1)
                    if l2 is None:
                        # print(msg)
                        # last = np.zeros(len(msg)*2)
                        # last[len(last)//2:] = msg
                        (l2,) = a2.plot(dataFrame)
                        plt.show()
                    else:
                        # last[:len(last)//2] = last[len(last)//2:]
                        # last[len(last)//2:] = msg
                        l2.set_ydata(dataFrame)
                        # l2.set_xlim()
                        a2.relim()
                        a2.autoscale_view(True, True, True)
                        f2.canvas.draw()
                i += 1
                if i >= chunkCount:
                    i = 0

    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print("error in loop", ex)
        raise


q: multiprocessing.Queue = multiprocessing.Queue()
process = multiprocessing.Process(target=plot_stuff, args=(q,))
process.start()

p = None
stream = None
try:
    #
    form_1 = pyaudio.paInt16  # 16-bit resolution
    chans = 1  # 1 channel
    bytesPerChunk = sampleCountPerChunk * 2  # 2^12 sampleCountPerChunk for buffer
    # record_secs = 0.5 # seconds to record
    dev_index = 0  # device index found by p.get_device_info_by_index(ii)
    wav_output_filename = "test1.wav"  # name of .wav file
    _max = 0
    p = pyaudio.PyAudio()
    # print(sampleCountPerChunk, sample_bytes)
    print(p.get_device_info_by_index(0))

    data_frame_counter = 0
    # fft_data = np.log(np.abs(sp.fftpack.fft(dataFrame * 0.5)))
    # fft_data = np.log(np.abs(np.fft.fft(dataFrame * 0.5)))
    # fft_data = np.nan_to_num(fft_data)
    # fft_data = fft_data[len(fft_data)//2:][:1048]
    # line = a.plot(fft_data)
    # line = None

    try:

        stream = p.open(
            format=form_1,
            rate=sampleRate,
            channels=chans,
            input_device_index=dev_index,
            input=True,
            frames_per_buffer=bytesPerChunk,
        )
        # frames: List[] = []
        while True:
            data = stream.read(sampleCountPerChunk)
            data = np.frombuffer(data, dtype=np.int16)
            print(len(data))
            # dataFrame[data_frame_counter*sampleCountPerChunk:(data_frame_counter+1)*sampleCountPerChunk] = np.nan_to_num(data)
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
            # fft_chunks = np.array([np.sum(fft_data[i:i+chunk_length])/chunk_length for i in range(0, len(fft_data), chunk_length)])
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
            # 				# lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i], Pixel(ary[i] * fft_chunks[i]), 50)
            # 			# [lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i], Pixel(ary[i] * fft_chunks[i]), 50) for i in range(count)]
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
        if not stream is None:
            # print("finished recording")
            stream.stop_stream()
            stream.close()
except KeyboardInterrupt:
    pass
except:
    raise
finally:
    if not p is None:
        p.terminate()
lf = None
# waveFile = wave.open(wav_output_filename, 'wb')
# waveFile.setnchannels(chans)
# waveFile.setsampwidth(p.get_sample_size(form_1))
# waveFile.setframerate(sampleRate)
# waveFile.writeframes(b''.join(frames))
# waveFile.close()
