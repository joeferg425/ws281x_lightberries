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
	data_frame_max_count = 3
	samples = (samp_rate // 5) // data_frame_max_count
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
		# ary = LightFunctions.LightPattern.ConvertPixelArrayToNumpyArray(LightFunctions.LightPattern.RainbowArray(100))
		ary = LightFunctions.LightPattern.ConvertPixelArrayToNumpyArray(LightFunctions.LightPattern.SolidColorArray(100))
		while True:
			data = stream.read(sample_bytes)
			# data = stream.read(sample_bytes, exception_on_overflow = False)
			data = np.frombuffer(data, dtype='Float32')
			data_frame[data_frame_counter*samples:(data_frame_counter+1)*samples] = np.nan_to_num(data)
			# print('data_frame', len(data_frame), min(data_frame), max(data_frame))
			fft_data = np.log2(np.abs(np.fft.fft(data_frame, 2048)))
			fft_data = np.nan_to_num(fft_data)
			fft_data = fft_data[len(fft_data)//2:]
			# idxs = np.where(fft_data < 1/255)
			# print('fft_data', len(fft_data), min(fft_data), max(fft_data))
			count = 100
			index = 1
			chunk_length = len(fft_data) // count
			# print(len(fft_data), chunk_length, sum(fft_data), np.mean(fft_data), np.median(fft_data))
			fft_chunks = np.array([np.sum(fft_data[i:i+chunk_length])/chunk_length for i in range(0, len(fft_data), chunk_length)])
			# if	_max is None:
				# _max = np.zeros(len(fft_chunks))

			# for i in range(len(fft_chunks)):
				# _max[i] = (_max[i] * 0.9) + (fft_chunks[i] * 0.1)
				# fft_chunks[i] /= _max[i]
			# idxs = np.where(fft_chunks < 0)
			# fft_chunks[idxs] = 0
			# fft_chunks /= np.min(fft_chunks)
			# print('fft_chunks', min(fft_chunks), max(fft_chunks))
			# print()
			# print(['{:03.1f}'.format(f) for f in fft_chunks[1:-1]])
			# fft_chunks[0] = 0.01
			# fft_chunks[-1] = 0.01
			_min = np.min(fft_chunks[1:-1])
			if _min < 0:
				fft_chunks -= np.min(fft_chunks[1:-1])
			# fft_chunks[0] = 0.01
			# fft_chunks[-1] = 0.01
			fft_chunks -= np.min(fft_chunks[1:-1])
			# fft_chunks[0] = 0.01
			# fft_chunks[-1] = 0.01
			# print('fft_chunks', min(fft_chunks), max(fft_chunks))
			# print(['{:03.1f}'.format(f) for f in fft_chunks[1:-1]])
			m = np.max(fft_chunks[1:-1])
			if m > _max:
				_max = m
			if not _max == 0:
				fft_chunks /= _max
				nrm = np.sum(fft_chunks) / len(fft_chunks)
				if nrm > 0:
					# fft_chunks *= nrm
					# fft_chunks *= np.e
					# fft_chunks -= 1e-2
					fft_chunks[0] = 0.01
					fft_chunks[-1] = 0.01
					# fft_chunks = np.log(fft_chunks)
					# fft_chunks = np.nan_to_num(fft_chunks)
					# print('\r' + ' '.join(['{:03.1f}'.format(f) for f in fft_chunks]), end='')
					# print('\r' + ' '.join(['{:03.1f}'.format(f) for f in fft_chunks]), end='')
					# idxs = np.where(fft_chunks > 1.0)
					# fft_chunks[idxs] = 1
					# fft_chunks /= np.max(fft_chunks)
					# temp = np.zeros((count,3), dtype=int)
					# print(lf._VirtualLEDArray[:count])
					# print(lf._LEDArray[0])
					# print(['{:03.1f}'.format(f) for f in fft_chunks])
					# print(len(fft_data))
					# stream.stop_stream()
					# stream.close()
					# p.terminate()
					# print('Make lights')
					# lf = LightFunctions.LightFunction(100, 18, 10, 800000, debug=True)
					# print('Set lights')
					if not (abs(fft_chunks[1] - fft_chunks[2]) < 0.001 and \
						abs(fft_chunks[1] - fft_chunks[3]) < 0.001 and \
						abs(fft_chunks[1] - fft_chunks[4]) < 0.001) and not np.isnan(fft_chunks[1]):
						for i in range(count):
							lf._LEDArray[i] = LightFunctions.Pixel(ary[i] * fft_chunks[i])
					# ary = ary.reshape(1,-1) * fft_chunks[:len(ary)]
					# ary = ary.reshape(1,-1)
				# lf._VirtualLEDArray = ary * np.array([fft_chunks[:len(ary)], fft_chunks[:len(ary)], fft_chunks[:len(ary)]]).reshape(1,-1)

			# lf._SetVirtualLEDArray(temp)
			# print('Update lights')
			# lf._CopyVirtualLedsToWS281X()
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