import pygame as _sdl

from . import assets, animation, entity, geometry, layer, locals, physics, scene, system, smoothing

from .assets import Image
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

print("Infinova 0.1.0-beta")

_sdl.init()

del _sdl, __infinova