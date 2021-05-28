#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 13 21:24:36 2021

@author: colinwageman
"""

import pyxdf
import matplotlib.pyplot as plt
import numpy as np

dr = '/Users/colinwageman/Desktop/School/Cogs199/Recordings/latency/'
# file = 'light_sensor-001.xdf'
file = 'light_split_02.xdf'
# file = 'aux_eeg-001.xdf'
# file = 'double-001.xdf'
# file = 'bci-001.xdf'

def onChunk(values, stamps, stream, StreamId):
#     print(StreamId)
    return values, stamps, stream

data, header = pyxdf.load_xdf(dr+file, verbose=True, on_chunk=onChunk)