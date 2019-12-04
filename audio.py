import pyaudio
import numpy as np
from LightBerries import LightFunctions
import wave

p = None
stream = None
try:
	#
	form_1 = pyaudio.paInt16 # 16-bit resolution
	chans = 1 # 1 channel
	samp_rate = 44100 # 44.1kHz sampling rate
	data_frame_max_count = 5
	samples = (samp_rate // 4) // data_frame_max_count
	samples = 882
	sample_bytes = samples*2 # 2^12 samples for buffer
	record_secs = 0.5 # seconds to record
	dev_index = 0 # device index found by p.get_device_info_by_index(ii)
	wav_output_filename = 'test1.wav' # name of .wav file
	_max = 0
	p = pyaudio.PyAudio()

	# print(samples, sample_bytes)
	print(p.get_device_info_by_index(0))

	data_frame = np.zeros((samples*data_frame_max_count))
	data_frame_counter = 0
	try:
		lf = LightFunctions.LightFunction(100, 18, 10, 800000, debug=True)

		stream = p.open(format=form_1, rate=samp_rate, channels=chans, \
			input_device_index=dev_index, input=True, frames_per_buffer=sample_bytes)
		frames = []
		ary = LightFunctions.LightPattern.ConvertPixelArrayToNumpyArray(LightFunctions.LightPattern.SolidColorArray(100, LightFunctions.PixelColors.GREEN))
		while True:
			data = stream.read(sample_bytes)
			data = np.frombuffer(data, dtype='Float32')
			data_frame[data_frame_counter*samples:(data_frame_counter+1)*samples] = np.nan_to_num(data)
			fft_data = np.log(np.abs(np.fft.fft(data_frame * 0.5)))
			fft_data = np.nan_to_num(fft_data)
			fft_data = fft_data[len(fft_data)//2:][:1048]
			count = 100
			index = 1
			chunk_length = len(fft_data) // count
			m = np.min(fft_data)
			if m < 0:
				fft_data -= m
			fft_data = fft_data**3
			fft_chunks = np.array([np.sum(fft_data[i:i+chunk_length])/chunk_length for i in range(0, len(fft_data), chunk_length)])
			fft_chunks = fft_chunks**8
			fft_chunks[0] = 0.01
			fft_chunks[-1] = 0.01
			m = np.min(fft_chunks)
			if m < 0:
				fft_chunks -= m
			m = np.max(fft_chunks[1:-1])
			if not m == 0:
				fft_chunks /= m
				nrm = np.sum(fft_chunks) / len(fft_chunks)
				if nrm > 0:
					if not ((fft_chunks[1] > 0.9) and \
						(fft_chunks[2] > 0.9) and \
						(fft_chunks[3] > 0.9)) and not np.isnan(fft_chunks[1]):
						for i in range(count):
							lf._LEDArray[i] = LightFunctions.Pixel(ary[i] * fft_chunks[i])
							# lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i], LightFunctions.Pixel(ary[i] * fft_chunks[i]), 50)
						# [lf._LEDArray[i] = lf._FadeColor(lf._LEDArray[i], LightFunctions.Pixel(ary[i] * fft_chunks[i]), 50) for i in range(count)]
			lf._RefreshLEDs()
			if data_frame_counter < (data_frame_max_count - 1):
				data_frame_counter += 1
			else:
				data_frame = np.roll(data_frame, -samples)
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
# waveFile.setframerate(samp_rate)
# waveFile.writeframes(b''.join(frames))
# waveFile.close()