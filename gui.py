from psychopy import visual, core, event
import time
import math
import numpy as np

class PsychoGUI:
	def __init__(self, fullscreen=False):
		# mon = monitors.Monitor('DELL U2718Q')
		self.win = visual.Window(
			screen=0,
			pos=[20,20],
			size=[1280, 720],
			monitor='testMonitor',
			units='deg',
			fullscr=fullscreen,
			color=[-1, -1, -1],
			gammaErrorPolicy='ignore'
		);

	def get_win(self):
		return self.win

class Letter:
	def __init__(self, letter, size, position, window):
		self.letter = letter
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

		self.ch_ctrl = []
		ch_ctrl_mat = []
		count = 0
		ltr_size = 60
		w_adj = size[0]-ltr_size
		h_adj = size[1]-ltr_size
		h_spacing = w_adj/(dim-1)
		v_spacing = h_adj/(dim-1)
		placement = [-w_adj/2 + position[0], h_adj/2 + position[1]]
		for row in character_grid:
			r_container = []
			for ch in row:
				l = Letter(letter=ch, size=[60,60], position=placement, window=window)
				self.ch_ctrl.append(l)
				r_container.append(l)
				placement = [placement[0] + h_spacing, placement[1]]

			ch_ctrl_mat.append(r_container)
			placement = [-size[0]/2 + position[0], placement[1] - v_spacing]

		# create a list of row and columns for simple indexing 0-12
		ch_ctrl_mat = np.array(ch_ctrl_mat)
		self.ch_ctrl_2 = [ch_ctrl_mat[r,:] for r in range(dim)] + [ch_ctrl_mat[:,c] for c in range(dim)]
		del ch_ctrl_mat

		self.size = size
		self.pos = position

	def create(self):
		pass

	def draw(self):
		for l in self.ch_ctrl:
			l.draw()

	def update(self, highlight_index):
		for l in self.ch_ctrl:
			l.off()

		# self.ch_ctrl[highlight_index].on()
		for ch in self.ch_ctrl_2[highlight_index]:
			ch.on()

	def reset(self):
		for l in self.ch_ctrl:
			l.off()

if __name__ == "__main__":
	gui = PsychoGUI()

	speller = Speller(size=[700,700], position=[0,0], window=gui.win)

	clock = core.Clock()
	opacity = 1.0
	clock.add(5)
	# overlay.opacity = 0.5
	# sin_time = math.sin(clock.getTime())
	# print(sin_time)
	frame_count = 0
	index_count = 0
	speller.update(index_count%12)
	while True:
		# grating.setPhase(0.05, '+')
		# grating.draw()
		# fixation.draw()
		# t = clock.getTime()
		# sin_time = (math.sin(t) + 1.0) /2.0
		# overlay.opacity = sin_time
		# a_text.draw()
		# overlay.draw()
		# ~250ms
		if frame_count == 7:
			index_count += 1
			speller.update(index_count%12)
			frame_count = 0

		frame_count += 1
		speller.draw()
		gui.win.flip()



		# a_text.updateOpacity(opacity)

		if len(event.getKeys())>0:
			break

		event.clearEvents()

	sin_time = math.sin(clock.getTime())
	print(sin_time)
	gui.win.close()
	core.quit()
	