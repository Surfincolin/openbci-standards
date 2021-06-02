# OpenBCI Cyton lsl streaming, with analog auxiliary output.
import time
import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock
import random

import brainflow
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from queue import Queue

class BoardControls:
	def __init__(self, port='/dev/cu.usbserial-DM0258I7'):
		# enable debug logs
		BoardShim.enable_dev_board_logger()

		params = BrainFlowInputParams()
		params.serial_port = port

		self.board = BoardShim(BoardIds.CYTON_BOARD, params)

		self.board.prepare_session()

		# ch1 = 'x1010110X'
		# ch2 = 'x2110110X'
		# ch3 = 'x3110110X'
		# ch4 = 'x4110110X'
		# ch5 = 'x5110110X'
		# ch6 = 'x6110110X'
		# ch7 = 'x7110110X'
		# ch8 = 'x8110110X'

		time.sleep(1)
		print('::: Set Board to Analog :::')
		self.board.config_board('/2')
		time.sleep(1)
		# self.board.config_board(ch1+ch2+ch3+ch4+ch5+ch6+ch7+ch8)
		time.sleep(1)

		self.eegstream = None
		self.auxstream = None

		self.ring_buffer_size = 45000
		self.queue = None
		self.queue_aux = None
		self.start_time = None
		self.sent_samples = 0
		self.fw_delay = 0

	def create_lsl_streams(self):
		# eeg_uid = random.randint(0,255)
		eeg_uid = 22
		aux_uid = 23
		eeg_info = StreamInfo('eeg_data', 'EEG', 8, 250, 'double64', 'openbci_eeg_id_' + str(eeg_uid))
		aux_info = StreamInfo('aux_data', 'AUX', 3, 250, 'double64', 'openbci_aux_id_' + str(aux_uid))

		# chns = eeg_info.desc().append_child('channels')
		# # current channel setup
		# labels = ['T3', 'F7', 'Fp1', 'Fp2', 'F8', 'F4', 'F3', 'T4']
		# for label in labels:
		#     ch = chns.append_child("channel")
		#     ch.append_child_value('label', label)
		#     ch.append_child_value('unit','microvolts')
		#     ch.append_child_value('type','EEG')

		# chns = aux_info.desc().append_child('channels')
		# current channel setup
		# labels = ['D11', 'D12', 'D13']
		# for label in labels:
		#     ch = chns.append_child("channel")
		#     ch.append_child_value('label', label)
		#     ch.append_child_value('unit','millivolts')
		#     ch.append_child_value('type','AUX')

		# eeg_info.desc().append_child_value('manufacturer','OpenBCI Inc.')
		# aux_info.desc().append_child_value('manufacturer','OpenBCI Inc.')

		self.eegstream = StreamOutlet(eeg_info)
		self.auxstream = StreamOutlet(aux_info)

	def start_stream(self):

		self.queue = Queue(maxsize = 1250) # 5 * 250
		self.queue_aux = Queue(maxsize = 1250) # 5 * 250
		self.board.start_stream(self.ring_buffer_size)

		# Let the stream run for 1/2 a second
		time.sleep(1)
		self.start_time = local_clock()
		self.sent_samples = 0
		print('::: Streaming :::')

	def stop_stream(self):
		self.board.stop_stream()
		self.board.release_session()
		print('::: Stream Stopped :::')

	def log_data(self):
		data = self.board.get_board_data()
		# 1:8 --> eeg chans
		# 9:11 --> aux chans
		eeg = data[1:9]
		aux = data[19:22]
		# print(aux)


		# for samples in chunk
		for i in range(len(aux[0])):
				# all chans i_th sample
				# print(aux[:,i].tolist())
				self.queue.put(eeg[:,i].tolist())
				self.queue_aux.put(aux[:,i].tolist())

		elapsed_time = local_clock() - self.start_time
		required_samples = int(250 * elapsed_time) - self.sent_samples

		if required_samples > 0 and self.queue_aux.qsize() >= required_samples:    
		    mychunk = []
		    mychunk_aux = []

		    for i in range(required_samples):
		        mychunk.append(self.queue.get())
		        mychunk_aux.append(self.queue_aux.get())

		    stamp = local_clock() - self.fw_delay 
		    # print(len(mychunk), len(mychunk[0]))
		    self.eegstream.push_chunk(mychunk, stamp)
		    self.auxstream.push_chunk(mychunk_aux, stamp)
		    self.sent_samples += required_samples

		time.sleep(0.2)
		# # for i in range(1,9):
		# 	# self.queue.put(data[:,i].tolist())
		# self.eegstream.push_chunk(data[1:9,:].tolist())
		# self.auxstream.push_chunk(data[19:22,:].tolist())

		# print(data[19:22,:].tolist())




if __name__ == "__main__":
    serial_port = '/dev/cu.usbserial-DM0258I7'

    board = BoardControls(port = serial_port)
    board.create_lsl_streams()
    board.start_stream()
    # time.sleep(1)
    count = 0
    while count < 6000:
	    board.log_data()
	    count += 1

    # time.sleep(1)
    board.stop_stream()

    # # Create PsychoPy window
    # win = psychopy.visual.Window(
    #     screen = 0,
    #     size=[win_w, win_h],
    #     units="pix",
    #     fullscr=False,
    #     color=bg_color,
    #     gammaErrorPolicy = "ignore"
    # );
    
    # # Initialize LSL marker stream
    # mrkstream = CreateMrkStream();
    
    # time.sleep(5)
    
    # # Initialize photosensor
    # photosensor = InitPhotosensor(50)
    # fixation = InitFixation(30)
    # triangle = InitTriangle(np.round(DegToPix(20.3, 48.26, 1080, 4))) # ~181

    # # Run through paradigm
    # Paradigm()

    # board.stop_stream()
    