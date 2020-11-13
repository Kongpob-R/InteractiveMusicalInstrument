import pygame
from pygame.locals import *
import matplotlib
import struct
import copy
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg


import pylab

from scipy.fft import fft

import math
import numpy

import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if ('Stereo Mix' in dev['name'] and dev['hostApi'] == 0):
        dev_index = dev['index'];
        print('dev_index', dev_index)
# stream object to get data from microphone
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    input=True,
    output=True,
    input_device_index = dev_index,
    frames_per_buffer=2048
)

pygame.init()

display_width = 1366
display_height = 720
bits = 16
pygame.mixer.pre_init(44100, -bits, 16)

gameDisplay = pygame.display.set_mode((display_width,display_height))
pygame.display.set_caption('Interactive Musical instrument')

def generatePureSine(frequency):
    duration = 1          # in seconds
    #freqency for the left speaker
    frequency_l = frequency
    #frequency for the right speaker
    frequency_r = frequency

    sample_rate = 44100

    n_samples = int(round(duration*sample_rate))

    #setup our numpy array to handle 16 bit ints, which is what we set our mixer to expect with "bits" up above
    buf = numpy.zeros((n_samples, 2), dtype = numpy.int16)
    max_sample = 2**(bits - 1) - 1

    for s in range(n_samples):
        t = float(s)/sample_rate    # time in seconds
        #grab the x-coordinate of the sine wave at a given time, while constraining the sample to what our mixer is set to with "bits"
        buf[s][0] = int(round(max_sample*math.sin(2*math.pi*frequency_l*t)))        # left
        buf[s][1] = int(round(max_sample*0.5*math.sin(2*math.pi*frequency_r*t)))    # right

    sound = pygame.sndarray.make_sound(buf)
    #play once, then loop forever
    return sound

def text_objects(text, font):
    textSurface = font.render(text, True, black)
    return textSurface, textSurface.get_rect()
 
def message_display(text):
    largeText = pygame.font.Font('freesansbold.ttf',115)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = ((display_width/2),(display_height/2))
    gameDisplay.blit(TextSurf, TextRect)
 
    pygame.display.update()
 
    time.sleep(2)
 
    game_loop()

black = (0,0,0)
white = (255,255,255)
w = 50
h = 50

class Key:
    def __init__(self, text, currentPos):
        self.text = text
        self.currentPos = currentPos

class ActionSlot:
    def __init__(self, actionIndex, text, originalPos, offset = False):
        self.actionIndex = actionIndex
        self.text = text
        self.originalPos = originalPos
        self.offset = offset

class Mapper:
    def __init__(self, action, key):
        self.action = action
        self.key = key

clock = pygame.time.Clock()
running = True
configMode = False
lastGameTicks = 0
keyEvents = [pygame.K_q,pygame.K_w,pygame.K_e,pygame.K_r,pygame.K_t,pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_f,pygame.K_g,pygame.K_z,pygame.K_x,pygame.K_c,pygame.K_v,pygame.K_b]
keyPosXs = [30,85,140,195,250,30,85,140,195,250,30,85,140,195,250]
keyPosYs = [400,400,400,400,400,455,455,455,455,455,510,510,510,510,510]
keyTexts = ['Q','W','E','R','T','A','S','D','F','G','Z','X','C','V','B']
notesSlotPos = [['C3',900,50],['D3',900,100],['E3',900,150],['F3',900,200],['G3',900,250],['A3',900,300],['B3',900,350],['Silent', 900, 500],['C4',1000,50],['D4',1000,100],['E4',1000,150],['F4',1000,200],['G4',1000,250],['A4',1000,300],['B4',1000,350]]
drumSlotPos = [['kick', 600, 300], ['snare', 400, 200], ['tomH', 300, 100], ['tomL', 400, 100], ['tomM', 500, 100]]
map = []
resetMap = []
for posX, posY, keyText in zip(keyPosXs, keyPosYs, keyTexts):
    map.append(Mapper(ActionSlot(False, keyText, [posX, posY]), False))
    resetMap.append(Mapper(ActionSlot(False, keyText, [posX, posY]), (Key(keyText, [posX, posY]))))
# load pure sine notes
for keyText, i, noteSlot in zip(keyTexts, range(15), notesSlotPos):
    map.append(Mapper(ActionSlot(i, noteSlot[0], [noteSlot[1], noteSlot[2]], True), (Key(keyText, [noteSlot[1], noteSlot[2]]))))
    resetMap.append(Mapper(ActionSlot(i, noteSlot[0], [noteSlot[1], noteSlot[2]], True), False))

for drum, i in zip(drumSlotPos, range(15,20)):
    map.append(Mapper(ActionSlot(i, drum[0], [drum[1], drum[2]], True), False))
    resetMap.append(Mapper(ActionSlot(i, drum[0], [drum[1], drum[2]], True), False))
    
defaultMap = copy.deepcopy(map)


def convertMap(map):
    convertMap = {}
    for pair in map:
        if pair.key != False:
            convertMap[pair.key.text] = pair.action.actionIndex
    return convertMap

bindingMap = convertMap(map)

def findNear(mouseX, mouseY, selected):
    global map
    posiblePos = []
    dist = 99999
    for i, pair in zip(range(len(map)), map):
        if pair.key is False:
            if selected.text == pair.action.text:
                posiblePos.append([pair.action.originalPos[0], pair.action.originalPos[1], i])
            elif pair.action.offset is True:
                posiblePos.append([pair.action.originalPos[0], pair.action.originalPos[1], i])
    for pos in posiblePos:
        newDist = math.sqrt((pos[0]+(w/2)-mouseX)**2 + (pos[1]+(w/2)-mouseY)**2)
        if newDist < dist:
            dist = newDist
            outX = pos[0]
            outY = pos[1]
            outPair = pos[2]
    map[outPair].key = selected
    map[outPair].key.currentPos[0] = outX
    map[outPair].key.currentPos[1] = outY

# load drum .wav
drum = list(range(15))
for waveFile in [['drum_heavy_kick.wav'], ['drum_snare_hard.wav'], ['drum_tom_hi_hard.wav'], ['drum_tom_lo_hard.wav'], ['drum_tom_mid_hard.wav']]:
    drum.append(pygame.mixer.Sound('./sounds/' + waveFile[0]))

middleC = [261.63, 293.66, 329.63, 349.23, 392.63, 440, 493.88, 0, 220, 246.94, 130.81, 146.83, 164.83, 174.61, 196]
pureSines = []
for frequency in middleC:
    pureSines.append(generatePureSine(frequency))
    
def drawSineVisualization(channelPlay):
    if len(channelPlay) > 0:
        plotPoints = []
        for x in range(0, display_width):
            sumY = 0
            for channel in channelPlay:
                if channel < 15:
                    f = middleC[channel]
                    y = int(math.sin(2 * math.pi * f * x / display_width / 50) * 50)
                    sumY += y

            plotPoints.append([x, sumY + (display_height/4)])
        pygame.draw.lines(gameDisplay, [0, 0, 0], False, plotPoints, 2)

class AudioWaveform:
    def __init__(self):
        self.fig = plt.figure(figsize=[13, 4])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('AUDIO WAVEFORM')
        self.ax.set_xlabel('samples')
        self.ax.set_ylabel('volume')
        self.ax.set_ylim(0, 255)
        self.ax.set_xlim(0, 2 * 2048)
        self.canvas = agg.FigureCanvasAgg(self.fig)
        x = numpy.arange(0, 2 * 2048, 2)
        self.line, = self.ax.plot(x, numpy.random.rand(2048), '-', lw=2)
    
    def plot(self):
        chunk = 2048
        data = stream.read(chunk)
        data_int = struct.unpack(str(2*chunk) + 'B', data)
        data_np = numpy.array(data_int, dtype='b')[::2] + 128
        self.line.set_ydata(data_np)
        self.canvas.draw()
        self.canvas.flush_events()
        renderer = self.canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = self.canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        gameDisplay.blit(surf, (0, 0))

class AudioSpectrumform:
    def __init__(self):
        RATE = 44100
        self.fig = plt.figure(figsize=[13, 4])
        self.canvas = agg.FigureCanvasAgg(self.fig)
        self.ax2 = self.fig.add_subplot(111)
        self.ax1 = self.fig.add_subplot(222)
        x = numpy.arange(0, 2 * 2048, 2)       # samples (waveform)
        xf = numpy.linspace(0, RATE, 2048)     # frequencies (spectrum)
        self.line, = self.ax1.plot(x, numpy.random.rand(2048), '-', lw=2)
        self.line_fft, = self.ax2.semilogx(xf, numpy.random.rand(2048), '-', lw=2)
        self.ax1.set_title('AUDIO WAVEFORM')
        self.ax1.set_xlabel('samples')
        self.ax1.set_ylabel('volume')
        self.ax1.set_ylim(0, 255)
        self.ax1.set_xlim(0, 2 * 2048)
        self.ax2.set_xlim(20, RATE / 2)

    def plot(self):
        chunk = 2048
        data = stream.read(chunk)
        data_int = struct.unpack(str(2*chunk) + 'B', data)
        data_np = numpy.array(data_int, dtype='b')[::2] + 128
        self.line.set_ydata(data_np)
        yf = fft(data_int)
        self.line_fft.set_ydata(numpy.abs(yf[0:chunk])  / (128 * chunk))
        self.canvas.draw()
        self.canvas.flush_events()
        renderer = self.canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = self.canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        gameDisplay.blit(surf, (0, 0))

    

def drawRectButton(x, y, w, h, text, state, r = 2, offset = False):
    if state == 'idle':
        color = pygame.Color('lightgrey')
    elif state == 'hover':
        color = pygame.Color('grey')
    else:
        color = pygame.Color('lightgreen')
    pygame.draw.rect(gameDisplay, color, pygame.Rect((x, y), (w, h)), border_radius = r)
    smallText = pygame.font.Font("freesansbold.ttf",20)
    textSurf, textRect = text_objects(text, smallText)
    if offset:
        textRect.center = ( (x-(w/2)), (y+(h/2)) )
    else:
        textRect.center = ( (x+(w/2)), (y+(h/2)) )
    gameDisplay.blit(textSurf, textRect)

def visualizeModeButton(currentMode, mouse, click, cooldown = 500):
    global lastGameTicks
    visualizeModes = ['Waveform(Simulation)', 'Waveform(LineOut)', 'Spectrum(LineOut)']
    x = 30
    y = 565
    w = 270
    h = 50
    if (x+w > mouse[0] > x and y+h > mouse[1] > y and click):
        drawRectButton(x, y, w, h, visualizeModes[currentMode], "active")
        if pygame.time.get_ticks() - lastGameTicks >= cooldown:
            lastGameTicks = pygame.time.get_ticks()
            currentMode += 1
            if currentMode > 2:
                currentMode = 0
    elif (x+w > mouse[0] > x and y+h > mouse[1] > y and not click):
        drawRectButton(x, y, w, h, visualizeModes[currentMode], 'hover')
    else:
        drawRectButton(x, y, w, h, visualizeModes[currentMode], 'idle')
    return currentMode
    
def bindingModeButton(bindingMode, mouse, click, cooldown = 500):
    global lastGameTicks
    global bindingMap
    global map
    global defaultMap
    global resetMap
    bind = {'x':30, 'y':620, 'w':270, 'h':50, 'text':'Keys binding'}
    reset = {'x':30, 'y':620, 'w':85, 'h':50, 'text':'Reset'}
    default = {'x':120, 'y':620, 'w':85, 'h':50, 'text':'Default'}
    done = {'x':210, 'y':620, 'w':85, 'h':50, 'text':'Done'}
    if not bindingMode:
        if (bind['x']+bind['w'] > mouse[0] > bind['x'] and bind['y']+bind['h'] > mouse[1] > bind['y'] and click):
            drawRectButton(bind['x'], bind['y'], bind['w'], bind['h'], bind['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()
                bindingMode = not bindingMode

        elif (bind['x']+bind['w'] > mouse[0] > bind['x'] and bind['y']+bind['h'] > mouse[1] > bind['y'] and not click):
            drawRectButton(bind['x'], bind['y'], bind['w'], bind['h'], bind['text'], 'hover')
        else:
            drawRectButton(bind['x'], bind['y'], bind['w'], bind['h'], bind['text'], 'idle')
    else:
        if (done['x']+done['w'] > mouse[0] > done['x'] and done['y']+done['h'] > mouse[1] > done['y'] and click):
            drawRectButton(done['x'], done['y'], done['w'], done['h'], done['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()
                bindingMode = not bindingMode
                bindingMap = convertMap(map)
        elif (done['x']+done['w'] > mouse[0] > done['x'] and done['y']+done['h'] > mouse[1] > done['y'] and not click):
            drawRectButton(done['x'], done['y'], done['w'], done['h'], done['text'], 'hover')
        else:
            drawRectButton(done['x'], done['y'], done['w'], done['h'], done['text'], 'idle')
    
        if (reset['x']+reset['w'] > mouse[0] > reset['x'] and reset['y']+reset['h'] > mouse[1] > reset['y'] and click):
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()
                map = copy.deepcopy(resetMap)
                bindingMap = convertMap(resetMap)

        elif (reset['x']+reset['w'] > mouse[0] > reset['x'] and reset['y']+reset['h'] > mouse[1] > reset['y'] and not click):
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], 'hover')
        else:
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], 'idle')

        if (default['x']+default['w'] > mouse[0] > default['x'] and default['y']+default['h'] > mouse[1] > default['y'] and click):
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()
                map = copy.deepcopy(defaultMap)
                bindingMap = convertMap(defaultMap)
                
        elif (default['x']+default['w'] > mouse[0] > default['x'] and default['y']+default['h'] > mouse[1] > default['y'] and not click):
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], 'hover')
        else:
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], 'idle')

    return bindingMode

keyPressed = []
channelPlay = []
currentMode = 0
bindingMode = False
channel = pygame.mixer.Channel
audioWaveform = AudioWaveform()
audioSpectrumform = AudioSpectrumform()
floatingKey = False
cooldown = 500
while running:
    gameDisplay.fill(white)
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed(num_buttons = 3)[0]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            for keyEvent in keyEvents:
                if event.key == keyEvent:
                    keyPressed.append(keyEvent)
        elif event.type == pygame.KEYUP:
            for keyEvent in keyEvents:
                if event.key == keyEvent:
                    keyPressed.remove(keyEvent)

    bindingMode = bindingModeButton(bindingMode, mouse, click)
    if not bindingMode:
        for posX, posY, keyText, keyEvent in zip(keyPosXs, keyPosYs, keyTexts, keyEvents):
            if (posX+w > mouse[0] > posX and posY+h > mouse[1] > posY and click) or keyEvent in keyPressed:
                drawRectButton(posX, posY, w, h, keyText, 'active')
                if bindingMap[keyText] not in channelPlay:
                    channelPlay.append(bindingMap[keyText])
            elif (posX+w > mouse[0] > posX and posY+h > mouse[1] > posY and not click):
                drawRectButton(posX, posY, w, h, keyText, 'hover')
                if bindingMap[keyText] in channelPlay:
                    channelPlay.remove(bindingMap[keyText])
            else:
                drawRectButton(posX, posY, w, h, keyText, 'idle')
                if bindingMap[keyText] in channelPlay:
                    channelPlay.remove(bindingMap[keyText])
        
            # print(channelPlay)
            if bindingMap[keyText] in channelPlay:
                # print(bindingMap[keyText])
                if bindingMap[keyText] < 15:
                    pureSines[bindingMap[keyText]].play()
                else:
                    if pygame.time.get_ticks() - lastGameTicks >= 200:
                        lastGameTicks = pygame.time.get_ticks()
                        drum[bindingMap[keyText]].play()
            else:
                if bindingMap[keyText] < 15:
                    pureSines[bindingMap[keyText]].stop()
        
        currentMode = visualizeModeButton(currentMode, mouse, click)
        if currentMode == 0:
            drawSineVisualization(channelPlay)
        elif currentMode == 1:
            audioWaveform.plot()
        elif currentMode == 2:
            audioSpectrumform.plot()

    else:
        for pair in map:
            drawRectButton(pair.action.originalPos[0], pair.action.originalPos[1], w, h, pair.action.text, 'idle', offset = pair.action.offset)

        for pair in map:
            if pair.key != False:
                if (pair.key.currentPos[0]+w > mouse[0] > pair.key.currentPos[0] and pair.key.currentPos[1]+h > mouse[1] > pair.key.currentPos[1] and click):
                    if floatingKey == False:
                        floatingKey = pair.key
                        pair.key = False
                else:
                    drawRectButton(pair.key.currentPos[0], pair.key.currentPos[1], w, h, pair.key.text, 'active')

        if floatingKey != False:
            floatingKey.currentPos[0] = mouse[0]-(w/2)
            floatingKey.currentPos[1] = mouse[1]-(h/2)
            drawRectButton(floatingKey.currentPos[0], floatingKey.currentPos[1], w, h, floatingKey.text, 'active')
            if click:
                if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                    lastGameTicks = pygame.time.get_ticks()
                    findNear(mouse[0], mouse[1], floatingKey)
                    floatingKey = False

            
    
    pygame.display.update()
    clock.tick(60)
pygame.quit()
quit()

