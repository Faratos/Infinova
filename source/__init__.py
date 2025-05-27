import pygame as _sdl

from . import assets, component, entity, geometry, layer, scene, system, smoothing

from .assets import Image
from .geometry import RectGeometry
from .entity import GameObject
from .scene import Scene

from .__infinova import _getGame, _getDisplay, _getWindow
from .__infinova import init, run

def GetGame():
    return _getGame()

def GetWindow():
    return _getWindow()

def GetDisplay():
    return _getDisplay()

print("Infinova beta (0.1.0)")

_sdl.init()

del _sdl, __infinova