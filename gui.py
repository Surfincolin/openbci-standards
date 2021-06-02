# gui.py

from psychopy import visual, core, event, colors
import math
import numpy as np
from random import shuffle
from pylsl import StreamInfo, StreamOutlet, local_clock
# from enum import Enum

class PsychoGUI:
	def __init__(self, fullscreen=False):
		# mon = monitors.Monitor('DELL U2718Q')
		# window_size = [1280, 720]
		window_size = [1680, 1050]

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


class RunTime():
	# in ms
	SHORT_WAIT = 2000.0
	MED_WAIT = 3000.0
	LONG_WAIT = 5000.0
	# stimuli duration 125ms ~8 frames (133.33ms) at 60Hz
	STIM = 133.33
	# inter-stimuli interval
	ISI = 133.33
	# inter-trial interval
	ITI = 500.0


class SpellerController:
	def __init__(self, speller, lsl_outlet=None):
		self.speller = speller
		self.lsl_outlet = lsl_outlet
		self.queue = ActionQueue()
		self.status = 'No Prompt'
		self.last_draw = None

		self.prompt = visual.TextBox(
			window = self.speller.win,
			text = self.status,
			font_size = 24,
			color_space='rgb',
			font_color=[-1,-1,-1],
			background_color=[1,1,1],
			border_color=[1,1,1],
			border_stroke_width=10,
			size=(min(self.speller.win.size[0],1280), 120),
			pos=(0.0,0),
			units='pix'
			)
	#pos=(0.0,self.speller.win.size[1]/2-30),

	def CreateSequence(self, action_list):
		for action, duration, draw in action_list:
			n_frames = MsToFrames(duration)
			self.queue.add((action, draw))
			for i in range(n_frames-1):
				self.queue.add((self.DummyAction, draw))
			
	def DummyAction(self):
		pass

	def RunFrame(self):
		if self.queue.size() > 0:
			action, draw = self.queue.get()
			self.last_draw = draw
			action()
			draw()
		else:
			self.last_draw()

	def mark_and_update(self, index):
		marker = list([str(index)])
		self.speller.update(index)
		if self.lsl_outlet is not None:
			self.lsl_outlet.push_sample(marker);
    

	def TrialActionList(self):
		order = list(range(self.speller.dim * 2))
		shuffle(order)
		action_list = []
		for val in order:
			action = lambda v=val: self.mark_and_update(v)
			duration = RunTime.STIM
			action_list.append((action, duration, self.speller.draw))
			action = self.speller.reset
			duration = RunTime.ISI
			action_list.append((action, duration, self.speller.draw))

		action = self.speller.reset
		duration = RunTime.ITI
		action_list.append((action, duration, self.speller.draw))

		return action_list

	def update_status_prompt(self, status):
		self.status = status
		self.prompt.setText(self.status)
		if self.lsl_outlet is not None:
			marker = list([status])
			self.lsl_outlet.push_sample(marker);

	def draw_prompt_overlay(self):
		self.speller.draw()
		self.prompt.draw()

	def get_status_prompt_action(self, duration):
		return (self.DummyAction, duration, self.draw_prompt_overlay)


class ActionQueue:
	def __init__(self):
		self.queue = []

	def add(self, item):
		self.queue.append(item)

	def get(self):
		if len(self.queue) < 1:
			return None
		return self.queue.pop(0)

	def size(self):
		return len(self.queue)

# ==============
#  HELPER FNC
# ==============
def MsToFrames(ms, fps = 60.0):
	return math.ceil(ms/(1000.0/fps))


# ==============
#  Main Sequence
# ==============
if __name__ == "__main__":
	gui = PsychoGUI(fullscreen=True)

	prompt = visual.TextBox(
		window = gui.win,
		text = 'Welcome to a Cyton P300 Speller',
		font_size = 24,
		color_space='rgb',
		font_color=[-1,-1,-1],
		background_color=[1,1,1],
		border_color=[1,1,1],
		border_stroke_width=10,
		grid_horz_justification='center', 
		size=(min(gui.win.size[0],1280), 120),
		pos=(0.0,gui.win.size[1]/2-60),
		units='pix'
		)

	timer = core.Clock()
	timer.add(4)
	
	while timer.getTime() < 0:
		prompt.draw()
		gui.win.flip()

	print('__ Initiating Speller __')
	speller = Speller(size=[700,700], position=[0,0], window=gui.win)
	lsl_info = StreamInfo('P300_Speller_Markers', 'Markers', 1, 0, 'string', 'speller_marker_stream')
	lsl_stream = StreamOutlet(lsl_info)

	gui.win.fullscr = False
	while True:
		if len(event.getKeys())>0:
			break

	event.clearEvents()
	gui.win.fullscr = True

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

	prompt = ['SPELLER', 'WORLD']

	print('__ Creating Sequence __')
	controller = SpellerController(speller=speller, lsl_outlet=lsl_stream)
	
	controller.update_status_prompt(prompt[0])

	controller.CreateSequence([
		(speller.reset, RunTime.SHORT_WAIT, speller.draw),
		(speller.calibrate, RunTime.ITI, speller.draw),
		(speller.reset, RunTime.ITI, speller.draw),
		(speller.calibrate, RunTime.ITI, speller.draw),
		(speller.reset, RunTime.MED_WAIT, speller.draw)
	])

	trails_per_letter = 10

	for i in range(len(prompt[0])):
		status = prompt[0][:i] + '[' + prompt[0][i] + ']' + prompt[0][i+1:]
		prompt_action = controller.get_status_prompt_action(RunTime.MED_WAIT)
		new_p_action = lambda input_str=status: controller.update_status_prompt(input_str)

		controller.CreateSequence([
			(speller.reset, RunTime.SHORT_WAIT, speller.draw),
			(new_p_action, prompt_action[1], prompt_action[2]),
			(speller.reset, RunTime.MED_WAIT, speller.draw)
		])

		for i in range(trails_per_letter):
			tal = controller.TrialActionList()
			controller.CreateSequence(tal)



	print('__ Begin __')
	while True:		

		cur_time = clock.getTime()
		elapsed = (cur_time - f_time) * 1000.0
		if elapsed >= 1000.0/fps:
			f_time = cur_time
		

			controller.RunFrame()

			gui.win.flip()
			
			frame_count += 1
			avg = (avg + elapsed) / 2.0


		if len(event.getKeys())>0:
			break

		event.clearEvents()

	# print('__ End __')
	total = round(avg,2)
	print('Average Frame Duration:', total, 'ms')
	gui.win.close()
	core.quit()
	
# notes:
# ~250ms 10/60*1000=166.6666
# 125ms -> 62.5ms or 125ms  capture 800ms
# 10-10 standard
# Fz, Cz, Pz, Oz, P3, P4, PO7 and PO8
# Fz, Cz, Pz, CP1, CP2
# referenced to the right earlobe and grounded to the left mastoid
# [1] https://www.frontiersin.org/articles/10.3389/fnhum.2019.00261/full#F1
# [2] https://www.frontiersin.org/articles/10.3389/fnhum.2013.00732/full

# 10-10 image
# https://commons.wikimedia.org/wiki/File:EEG_10-10_system_with_additional_information.svg