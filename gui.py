# gui.py

from psychopy import visual, core, event
import math
import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

class PsychoGUI:
	def __init__(self, fullscreen=False):
		# mon = monitors.Monitor('DELL U2718Q')
		window_size = [1280, 720]

		self.win = visual.Window(
			screen=0,
			pos=[20,20],
			size=window_size,
			monitor='testMonitor',
			units='deg',
			useRetina=True,
			fullscr=fullscreen,
			color=[-1, -1, -1],
			gammaErrorPolicy='ignore'
		);

		self.win.init_size = window_size

	def get_win(self):
		return self.win

class Letter:
	def __init__(self, letter, size, position, window):
		self.letter = letter
		self.win = window
		self.stim = visual.TextStim(
			win=window,
			text=letter,
			pos=position,
			height=size[1],
			units='pix',
			color=[255,255,255],
			colorSpace=('rgb')
		)

		# required for flashing (TestStim won't update without changing the text itself)
		self.overlay = visual.Rect(
			win=window,
			size=size,
			units='pix',
			lineWidth=0,
			lineColor=[-1, -1, -1],
			fillColor=[-1, -1, -1],
			colorSpace=('rgb'),
			pos=position,
			name='off'
		)

	def get_letter(self):
		return self.letter

	def draw(self):
		self.stim.draw()
		self.overlay.draw()

	def off(self):
		self.overlay.opacity = 0.7

	def on(self):
		self.overlay.opacity = 0.0

	def update(self, size, position):
		self.stim.height = size[1]
		self.overlay.size = size
		self.stim.position = position
		self.overlay.position = position


class Speller:
	def __init__(self, size, position, window):
		"""
		size - array [w,h]
		"""
		chars = [chr(x) for x in range(65,91)]
		numbers = list(range(1,10))
		space = ['_']

		# TODO: clean this up, breaks if there isn't a perfect square root of full_list
		full_list = chars + numbers + space
		dim = math.ceil(len(full_list)**0.5)
		character_grid = np.reshape(full_list, (dim, dim))

		self.win = window
		self.ch_ctrl = []
		ch_ctrl_mat = []

		ltr_size = 60
		w_adj = size[0]-ltr_size
		h_adj = size[1]-ltr_size
		h_spacing = w_adj/(dim-1)
		v_spacing = h_adj/(dim-1)
		placement = [-w_adj/2 + position[0], h_adj/2 + position[1]]
		for row in character_grid:
			r_container = []
			for ch in row:
				l = Letter(letter=ch, size=[ltr_size,ltr_size], position=placement, window=window)
				self.ch_ctrl.append(l)
				r_container.append(l)
				placement = [placement[0] + h_spacing, placement[1]]

			ch_ctrl_mat.append(r_container)
			placement = [-w_adj/2  + position[0], placement[1] - v_spacing]

		# create a list of row and columns for simple indexing 0-12
		ch_ctrl_mat = np.array(ch_ctrl_mat)
		self.ch_ctrl_2 = [ch_ctrl_mat[r,:] for r in range(dim)] + [ch_ctrl_mat[:,c] for c in range(dim)]
		del ch_ctrl_mat

		self.size = size
		self.pos = position
		self.dim = dim
		self.draw_state = 0

		w, h = window.init_size
		pi_position = [(w/2) - ltr_size, -(h/2) + ltr_size]
		self.photoindicator = visual.Circle(
			win=window,
			units="pix",
			radius=ltr_size*(2/3),
			fillColor=[255,255,255],
			lineColor=[255,255,255],
			lineWidth = 1,
			opacity = 0.0,
			edges = 32,
			pos = pi_position
		)

		self._bake()

	def _bake(self):
		"""
		Creates screenshots of all stimuli states. This allows
		for faster display changes and the app can reach 60fps.
		"""

		imgs = []
		for i in range(self.dim * 2):
			self.win.clearBuffer(color=True, depth=False, stencil=False)
			self.raw_update(i)
			self.raw_draw()
			im = self.win._getFrame(buffer='back')
			imgs.append(im)

		self.win.clearBuffer(color=True, depth=False, stencil=False)
		self.raw_reset()
		self.raw_draw()
		im = self.win._getFrame(buffer='back')
		imgs.append(im)

		self.win.clearBuffer(color=True, depth=False, stencil=False)
		self.raw_calibrate()
		self.raw_draw()
		im = self.win._getFrame(buffer='back')
		imgs.append(im)

		self.baked_stim = []
		for img in imgs:
			img_stim = visual.ImageStim( win=self.win, image=img,units='pix', size=self.win.init_size)
			self.baked_stim.append(img_stim)

		self.draw_state = len(self.baked_stim) - 2 # off state

	# raw_draw == SLOW
	# draw == FAST
	# etc.
	def draw(self):
		self.baked_stim[self.draw_state].draw()

	def update(self, highlight_index):
		self.draw_state = highlight_index

	def reset(self):
		self.draw_state = len(self.baked_stim) - 2 # off state

	def calibrate(self):
		self.draw_state = len(self.baked_stim) - 1 # all on state

	def raw_draw(self):
		for l in self.ch_ctrl:
			l.draw()
		self.photoindicator.draw()

	def raw_update(self, highlight_index):
		for l in self.ch_ctrl:
			l.off()

		for ch in self.ch_ctrl_2[highlight_index]:
			ch.on()
		self.photoindicator.opacity = 1.0

	def raw_reset(self):
		for l in self.ch_ctrl: l.off()
		self.photoindicator.opacity = 0.0

	def raw_calibrate(self):
		for l in self.ch_ctrl: l.on()
		self.photoindicator.opacity = 1.0

# ==============
#  HELPER FNC
# ==============
def MsToFrames(ms, fps):
	return math.ceil(ms/(1000/fps))


# ==============
#  Main Sequence
# ==============
if __name__ == "__main__":
	gui = PsychoGUI(fullscreen=False)

	speller = Speller(size=[700,700], position=[0,0], window=gui.win)
	# lsl_info = StreamInfo('P300_Speller_Markers', 'Markers', 1, 0, 'string', 'speller_marker_stream')
	# lsl_stream = StreamOutlet(lsl_info)

	clock = core.Clock()

	avg = 0
	f_time = 0.0
	clock.reset()
	fps = 60.0
	frame_on = MsToFrames(125 ,fps)
	frame_off = MsToFrames(250,fps)
	frame_count = 0
	index_count = 0
	speller.reset()

	while True:		

		cur_time = clock.getTime()
		elapsed = (cur_time - f_time) * 1000.0
		if elapsed >= 1000.0/fps:
			f_time = cur_time
			
			# notes:
			# ~250ms 10/60*1000=166.6666
			# 125ms -> 62.5ms or 125ms  capture 800ms
			# Fz, Cz, Pz, Oz, P3, P4, PO7 and PO8
			# referenced to the right earlobe and grounded to the left mastoid
			# [1] https://www.frontiersin.org/articles/10.3389/fnhum.2019.00261/full#F1
			# [2] https://www.frontiersin.org/articles/10.3389/fnhum.2013.00732/full


			if frame_count == frame_on:
				speller.update(index_count%12)

			if frame_count == frame_off:
				speller.reset()
				frame_count = -1
				index_count += 1

			speller.draw()
			gui.win.flip()
			
			frame_count += 1
			avg = (avg + elapsed) / 2.0


		if len(event.getKeys())>0:
			break

		event.clearEvents()


	total = round(avg,2)
	print('Average Frame Duration:', total, 'ms')
	gui.win.close()
	core.quit()
	