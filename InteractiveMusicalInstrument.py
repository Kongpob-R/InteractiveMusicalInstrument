import pygame
from pygame.locals import *
import matplotlib
matplotlib.use("Agg")

import matplotlib.backends.backend_agg as agg


import pylab

from scipy.fft import fft

import math
import numpy

pygame.init()

display_width = 1366
display_height = 720
bits = 16
pygame.mixer.pre_init(44100, -bits, 2)

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

clock = pygame.time.Clock()
running = True
configMode = False
lastGameTicks = 0
pianoKeys = pygame.image.load('./src/piano/keys.png')
keyEvents = [pygame.K_q,pygame.K_w,pygame.K_e,pygame.K_r,pygame.K_t,pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_f,pygame.K_g,pygame.K_z,pygame.K_x,pygame.K_c,pygame.K_v,pygame.K_b]
keyPosXs = [30,85,140,195,250,30,85,140,195,250,30,85,140,195,250]
keyPosYs = [400,400,400,400,400,455,455,455,455,455,510,510,510,510,510]
keyTexts = ['Q','W','E','R','T','A','S','D','F','G','Z','X','C','V','B']

class KeyBinding:
    def __init__(self, bindingMap):
        self.defaultSlotPos = [['Q',30,400],['W',85,400],['E',140,400],['R',195,400],['T',250,400],['A',30,455],['S',85,455],['D',140,455],['F',195,455],['G',250,455],['Z',30,510],['X',85,510],['C',140,510],['V',195,510],['B',250,510]]
        self.notesSlotPos = [['C3',900,50],['D3',900,100],['E3',900,150],['F3',900,200],['G3',900,250],['A3',900,300],['B3',900,350],[],['C4',1000,50],['D4',1000,100],['E4',1000,150],['F4',1000,200],['G4',900,250],['A4',1000,300],['B4',1000,350]]
        self.bindingMap = bindingMap
        self.newSlotPos = self.defaultSlotPos

    def get_dict(self):
        self.bindingMap = {}
        for i, value in zip(range(len(self.newSlotPos)), self.newSlotPos):
            if self.newSlotPos != 0:
                self.bindingMap[value[0]] = i
        return self.bindingMap

    def reset(self):
        self.newSlotPos = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    def default(self):
        self.newSlotPos = self.defaultSlotPos

keyBinding = KeyBinding({'Q':0,'W':1,'E':2,'R':3,'T':4,'A':5,'S':6,'D':7,'F':8,'G':9,'Z':10,'X':11,'C':12,'V':13,'B':14})
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
                f = middleC[channel]
                y = int(math.sin(2 * math.pi * f * x / display_width / 50) * 50)
                sumY += y

            plotPoints.append([x, sumY + (display_height/4)])
        pygame.draw.lines(gameDisplay, [0, 0, 0], False, plotPoints, 2)
            
def drawFrequencySpectrum(channelPlay):
    fig = pylab.figure(figsize=[13, 4], # Inches
                dpi=100,        # 100 dots per inch, so the resulting buffer is 400x400 pixels
                )
    ax = fig.gca()
    N = display_width
    # sample spacing
    T = 1.0 / 800.0
    x = numpy.linspace(0.0, N*T, N)
    y = 0
    if len(channelPlay) > 0:
        for channel in channelPlay: 
            f = middleC[channel]
            y += numpy.sin(f * 2.0*numpy.pi*x)
    else:
        y += numpy.sin(0.1 * 2.0*numpy.pi*x) * 0
    yf = fft(y)
    xf = numpy.linspace(0.0, 1.0/(2.0*T), N//2)
    ax.plot(xf, 2.0/N * numpy.abs(yf[0:N//2]))
    
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    size = canvas.get_width_height()
    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_rgb()

    surf = pygame.image.fromstring(raw_data, size, "RGB")
    gameDisplay.blit(surf, (0,0))


def drawRectButton(x, y, w, h, text, state, r = 2):
    if state == 'idle':
        color = pygame.Color('lightgrey')
    elif state == 'hover':
        color = pygame.Color('grey')
    else:
        color = pygame.Color('lightgreen')
    pygame.draw.rect(gameDisplay, color, pygame.Rect((x, y), (w, h)), border_radius = r)
    smallText = pygame.font.Font("freesansbold.ttf",20)
    textSurf, textRect = text_objects(text, smallText)
    textRect.center = ( (x+(w/2)), (y+(h/2)) )
    gameDisplay.blit(textSurf, textRect)

def visualizeModeButton(currentMode, mouse, click, cooldown = 500):
    global lastGameTicks
    visualizeModes = ['Time Domain', 'Frequency Domain', 'Color Full']
    x = 30
    y = 565
    w = 270
    h = 50
    if (x+w > mouse[0] > x and y+h > mouse[1] > y and click):
        drawRectButton(x, y, w, h, visualizeModes[currentMode], "active")
        if pygame.time.get_ticks() - lastGameTicks >= cooldown:
            lastGameTicks = pygame.time.get_ticks()
            currentMode += 1
            if currentMode > 1:
                currentMode = 0
    elif (x+w > mouse[0] > x and y+h > mouse[1] > y and not click):
        drawRectButton(x, y, w, h, visualizeModes[currentMode], 'hover')
    else:
        drawRectButton(x, y, w, h, visualizeModes[currentMode], 'idle')
    return currentMode
    
def bindingModeButton(bindingMode, mouse, click, cooldown = 500):
    global lastGameTicks
    global bindingMap
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
                bindingMap = keyBinding.get_dict()

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
        elif (done['x']+done['w'] > mouse[0] > done['x'] and done['y']+done['h'] > mouse[1] > done['y'] and not click):
            drawRectButton(done['x'], done['y'], done['w'], done['h'], done['text'], 'hover')
        else:
            drawRectButton(done['x'], done['y'], done['w'], done['h'], done['text'], 'idle')
    
        if (reset['x']+reset['w'] > mouse[0] > reset['x'] and reset['y']+reset['h'] > mouse[1] > reset['y'] and click):
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()

        elif (reset['x']+reset['w'] > mouse[0] > reset['x'] and reset['y']+reset['h'] > mouse[1] > reset['y'] and not click):
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], 'hover')
        else:
            drawRectButton(reset['x'], reset['y'], reset['w'], reset['h'], reset['text'], 'idle')

        if (default['x']+default['w'] > mouse[0] > default['x'] and default['y']+default['h'] > mouse[1] > default['y'] and click):
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], "active")
            if pygame.time.get_ticks() - lastGameTicks >= cooldown:
                lastGameTicks = pygame.time.get_ticks()
                
        elif (default['x']+default['w'] > mouse[0] > default['x'] and default['y']+default['h'] > mouse[1] > default['y'] and not click):
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], 'hover')
        else:
            drawRectButton(default['x'], default['y'], default['w'], default['h'], default['text'], 'idle')

    return bindingMode
w = 50
h = 50

keyPressed = []
channelPlay = []
currentMode = 0
bindingMode = False
bindingMap = keyBinding.get_dict()
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
        
            print(channelPlay)
            if bindingMap[keyText] in channelPlay:
                print(bindingMap[keyText])
                pureSines[bindingMap[keyText]].play()
            else:
                pureSines[bindingMap[keyText]].stop()
        
        currentMode = visualizeModeButton(currentMode, mouse, click)
        if currentMode == 0:
            drawSineVisualization(channelPlay)
        elif currentMode == 1:
            drawFrequencySpectrum(channelPlay)
    else:
        
        pass

    
    pygame.display.update()
    clock.tick(60)
pygame.quit()
quit()

