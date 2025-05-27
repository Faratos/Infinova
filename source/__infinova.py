from random import randint
import pygame as pg
import math
import json
import sys
import os

smoothingImported = True
try:
    import smoothing
except ImportError:
    smoothingImported = False

pillowImported = True
try:
    from PIL import Image as pillowImage
except ImportError:
    pillowImported = False

"""

Infinova 1.0 by Faratos
Using Pygame-ce 2.5.3 and Python 3.13.2

"""

pg.init()


def quit():
    pg.quit()
    sys.exit()


class ErrorHandler:
    @staticmethod
    def __basicMessage(name: str, className: str, function: str, variable: str, message: str, firstLine: str):
        fileName = os.path.abspath(sys.argv[0])
        fileLine = f"File \"{fileName}\""
        print(f"\n{f"_/ {firstLine}! \\_":_^{str(len(fileLine))}}")
        print(fileLine)
        if className:
            print(f"   ~ Class \"{className}\"")
        if function:
            print(f"   ~ Function \"{function}\"")
        if variable:
            print(f"   ~ Variable \"{variable}\"")
        print(f"{name}: {message}\n")

    @staticmethod
    def Throw(name: str, className: str, function: str, variable: str, message: str):
        ErrorHandler.__basicMessage(name, className, function, variable, message, "Error occured")
        quit()

    @staticmethod
    def Warn(name: str, className: str, function: str, variable: str, message: str):
        ErrorHandler.__basicMessage(name, className, function, variable, message, "Warning")

class Image:
    def __init__(self, name: str, width: int, height: int, surface: pg.Surface = None):
        self.name = name
        self.__original = (surface if surface else pg.Surface((width, height), pg.SRCALPHA)).convert_alpha()
        self.current = self.__original.copy()
        self.offset = pg.Vector2()
        self.__rotation = 0
        self.__size = (width, height)
        self.__opacity = 1
        self.__flipX = False
        self.__flipY = False
        self.__surfaceUpdateRequired = False
    
    @property
    def size(self):
        return self.__size
    
    @property
    def rotation(self):
        return self.__rotation
    
    @size.setter
    def size(self, value: tuple[int, int]):
        self.__size = tuple(pg.Vector2(value))
        self.UpdateSurface()
    
    @rotation.setter
    def rotation(self, value: float):
        self.__rotation = value
        self.UpdateSurface()

    @property
    def opacity(self):
        return self.__opacity

    @opacity.setter
    def opacity(self, value: float):
        self.__opacity = pg.math.clamp(value, 0, 1)
        self.UpdateSurface()
    
    def ScaleBy(self, amount: float):
        self.__size = (self.__size[0] * amount, self.__size[1] * amount)
        self.UpdateSurface()
    
    @property
    def originalSurface(self):
        return self.__original.copy()
    
    @originalSurface.setter
    def originalSurface(self, surface: pg.Surface):
        self.__original = surface.convert_alpha()
        self.UpdateSurface()
    
    def UpdateSurface(self):
        self.__surfaceUpdateRequired = True

    def Flip(self, flipX: bool, flipY: bool):
        if not self.__flipX == flipX or not self.__flipY == flipY:
            self.__flipX = flipX
            self.__flipY = flipY
            self.UpdateSurface()

    def GetFlipState(self):
        return (self.__flipX, self.__flipY)

    def GetSurface(self):
        if not self.__surfaceUpdateRequired:
            return self.current
        
        self.current = pg.transform.flip(self.__original, self.__flipX, self.__flipY)
        self.current = pg.transform.scale(self.current, self.__size)
        self.current = pg.transform.rotate(self.current, self.__rotation)

        self.current.set_alpha(round(self.__opacity * 255))

        self.__surfaceUpdateRequired = False

        return self.current
    
    def Copy(self):
        copy = Image(self.name, self.__original.width, self.__original.height, self.__original)
        copy.offset = self.offset.copy()
        return copy

    # def DrawOn(self, surface: pg.Surface, position: pg.Vector2, camera):
    #     if camera:
    #         surface.blit(pg.transform.scale_by(self.GetSurface(), camera.zoom), (position + self.offset - camera.position) * camera.zoom)
    #         return
        
    #     surface.blit(self.current, position + self.offset)

    def DrawRect(self, color, rect, width: int = -1, borderRadius: int = -1):
        pg.draw.rect(self.__original, color, rect, width, borderRadius)
        self.UpdateSurface()

    def DrawCircle(self, color, center, radius: int, width: int = -1):
        pg.draw.circle(self.__original, color, center, radius, width)
        self.UpdateSurface()

    def __str__(self):
        return f"Image({self.name}, {self.__size})"
    
    def __repr__(self):
        return str(self)


class Geometry:
    def __init__(self, type: str, x: int, y: int, width: int, height: int):
        self.__type = type
        self.position = pg.Vector2(x, y)
        self.size = pg.Vector2(width, height)

    @property
    def type(self):
        return self.__type
    
    @property
    def center(self):
        return self.position + self.size / 2
    
    @center.setter
    def center(self, value: pg.Vector2):
        self.position = pg.Vector2(value) - self.size / 2


class RectGeometry(Geometry):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__("rect", x, y, width, height)

"""
static inline int
pgCollision_RectCircle(double rx, double ry, double rw, double rh,
                       pgCircleBase *circle)
{
    const double cx = circle->x, cy = circle->y;
    const double r_bottom = ry + rh, r_right = rx + rw;

    const double test_x = (cx < rx) ? rx : ((cx > r_right) ? r_right : cx);
    const double test_y = (cy < ry) ? ry : ((cy > r_bottom) ? r_bottom : cy);

    return pgCollision_CirclePoint(circle, test_x, test_y);
}
"""


class collisions:
    @staticmethod
    def CollideRectPoint(rectPosition: pg.Vector2, rectSize: pg.Vector2, point: pg.Vector2):
        return (point.x > rectPosition.x and point.y > rectPosition.y and 
                point.x < rectPosition.x + rectSize.x and point.y < rectPosition.y + rectSize.y)

    @staticmethod
    def CollideCirclePoint(circlePosition: pg.Vector2, radius: int, point: pg.Vector2): 
        return (circlePosition.x - point.x) ** 2 + (circlePosition.y - point.y) ** 2 <= radius ** 2

    @staticmethod
    def CollideRects(firstPosition: pg.Vector2, firstSize: pg.Vector2, secondPosition: pg.Vector2, secondSize: pg.Vector2):
        return (min(firstPosition.x, firstPosition.x + firstSize.x) < max(secondPosition.x, secondPosition.x + secondSize.x) and
                min(firstPosition.y, firstPosition.y + firstSize.y) < max(secondPosition.y, secondPosition.y + secondSize.y) and
                max(firstPosition.x, firstPosition.x + firstSize.x) > min(secondPosition.x, secondPosition.x + secondSize.x) and
                max(firstPosition.y, firstPosition.y + firstSize.y) > min(secondPosition.y, secondPosition.y + secondSize.y))

    @staticmethod
    def CollideRectCircle(firstPosition: pg.Vector2, firstSize: pg.Vector2, secondPosition: pg.Vector2, secondRadius: int):
        rectBottom = firstPosition.y + firstSize.y
        rectRight = firstPosition.x + firstSize.x

        testX = firstPosition.x if (secondPosition.x < firstPosition.x) else (rectRight if (secondPosition.x > rectRight) else secondPosition.x)
        testY = firstPosition.y if (secondPosition.y < firstPosition.y) else (rectBottom if (secondPosition.y > rectBottom) else secondPosition.y)

        return collisions.CollideCirclePoint(secondPosition, secondRadius, pg.Vector2(testX, testY))

    @staticmethod
    def CollideCircles(firstPosition: pg.Vector2, firstRadius: int, secondPosition: pg.Vector2, secondRadius: int):
        return (firstPosition.x - secondPosition.x) ** 2 + (firstPosition.y - secondPosition.y) ** 2 <= (firstRadius + secondRadius) ** 2

    @staticmethod
    def CollideGeometries(first: Geometry, second: Geometry):
        if first.type not in ["rect", "circle"] or second.type not in ["rect", "circle"]:
            return None

        if first.type == "rect" and second.type == "rect":
            return collisions.CollideRects(first.position, first.size, second.position, second.size)
        elif first.type == "circle" and second.type == "circle":
            return collisions.CollideCircles(first.position, first.radius, second.position, second.radius)
        
        rect = first
        circle = second
        if (first.type == "circle"):
            rect = second
            circle = first

        return collisions.CollideRectCircle(rect.position, rect.size, circle.position, circle.radius)
    
    def CollidePoint(geometry: Geometry, point: pg.Vector2):
        if geometry.type not in ["rect", "circle"]:
            return None
        
        if geometry.type == "rect" :
            return collisions.CollideRectPoint(geometry.position, geometry.size, point)
        elif geometry.type == "circle":
            return collisions.CollideCirclePoint(geometry.position, geometry.radius, point)


class Component:
    def __init__(self, type: str):
        self.__type = type
        self._object: GameObject = None

    def Update():
        pass

    @property
    def type(self):
        return self.__type


class Frame:
    def __init__(self, image: Image, duration: int):
        self.image: Image = image.Copy()
        self.duration = duration # milliseconds

    def Copy(self):
        return Frame(self.image.Copy(), self.duration)

class Animation:
    def __init__(self, name: str, frames: list[Frame]):
        self.name = name
        self.frames = frames
        self.__playing = True
        self.__looped = True
        self.__step = 1
        self.__currentFrame = 0
        self.__timerToNextFrame = 0
    
    def Copy(self):
        return Animation(self.name, [frame.Copy() for frame in self.frames])

    @classmethod
    def FromOneFrame(self, name: str, filePath: str, scaleFrameBy: float = 1):
        surface = pg.transform.scale_by(pg.image.load(filePath), scaleFrameBy).convert_alpha()
        return Animation(name, [Frame(Image("Frame", surface.get_width(), surface.get_height(), surface), 1)])

    @classmethod
    def FromGIF(cls, filePath: str, name: str, framesDuration: int, scaleFramesBy: float = 1):
        if not pillowImported:
            ErrorHandler.Throw("ImportError", "Animation", "FromGIF", None, "You have to install \"Pillow\" before using \"Animation.FromGIF\"")

        img = pillowImage.open(filePath)

        frames = []

        try:
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.convert("RGBA")
                
                data = frame.tobytes()
                size = frame.size
                
                frames.append(Frame(Image(f"Frame {i}", size[0] * scaleFramesBy, size[1] * scaleFramesBy, pg.transform.scale_by(pg.image.frombytes(data, size, "RGBA"), scaleFramesBy)), framesDuration))
        except EOFError:
            pass

        return cls(name, frames)

    def Update(self, surface: pg.Surface, flip: dict, dt: float):
        if self.__playing:
            surface = self.__getNextFrame(surface, flip, dt)

            if (self.__currentFrame >= len(self.frames) or self.__currentFrame < 0) and not self.__looped:
                self.Stop()
            
        return surface
    
    def __getNextFrame(self, surface: pg.Surface, flip: dict, dt: float):
        self.__timerToNextFrame += dt

        if self.__currentFrame >= len(self.frames):
            self.__currentFrame = 0
        
        if self.__currentFrame < 0:
                self.__currentFrame = len(self.frames) - 1

        frame = self.frames[self.__currentFrame]
        surface = pg.transform.flip(frame.image.current, flip["X"], flip["Y"])

        if (self.__timerToNextFrame * 1000) >= frame.duration:
            self.__currentFrame += self.__step
            self.__timerToNextFrame = 0

        return surface
    
    def Play(self, looped=True, reversed=False):
        self.__playing = True
        self.__looped = looped
        self.__step = 1
        if reversed:
            self.__step = -1 if reversed else 1
            self.__currentFrame = len(self.frames) - 1

    def IsPlaying(self):
        return self.__playing
    
    def IsLooped(self):
        return self.__looped
    
    def IsReversed(self):
        return self.__step == -1

    def Stop(self):
        self.__playing = self.__looped = False
        self.__timerToNextFrame = 0
        self.__currentFrame = 0

class Animator(Component):
    def __init__(self):
        super().__init__("object")
        self.__animations: list[Animation] = []
        self.__currentAnimation = 0
        self._flip = {"X": False, "Y": False}

    @property
    def currentAnimationIndex(self):
        return self.__currentAnimation

    def Update(self, dt: float):
        if self.HasAnimations():
            self._object.image.current = self.GetCurrentAnimation().Update(self._object.image.current, self._flip, dt)
    
    def GetCurrentAnimation(self):
        if len(self.__animations):
            return self.__animations[self.__currentAnimation]
        
    def HasAnimations(self):
        return bool(len(self.__animations))

    def SetFlipX(self, value: bool):
        self._flip["X"] = value

    def SetFlipY(self, value: bool):
        self._flip["Y"] = value
    
    def PlayAnimation(self, index: int, looped=True, reversed=False):
        if index >= 0 and index < len(self.__animations):
            if self.__currentAnimation != index:
                self.__animations[self.__currentAnimation].Stop()

            self.__currentAnimation = index
            self.__animations[self.__currentAnimation].Play(looped, reversed)
        
    def PlayAnimationByName(self, name: str, looped=True, reversed=False):
        for index, animation in enumerate(self.__animations):
            if animation.name == name:
                self.PlayAnimation(index, looped, reversed)
                return

    def StopCurrentAnimation(self):
        self.__animations[self.__currentAnimation].Stop()

    def StopAnimationByIndex(self, index: int):
        if index >= 0 and index < len(self.__animations):
            self.__animations[index].Stop()

    def StopAnimationByName(self, name: str):
        for index, animation in enumerate(self.__animations):
            if animation.name == name:
                self.StopAnimationByIndex(index)
                return

    def AddAnimation(self, animation: Animation):
        self.__animations.append(animation)

    def RemoveAnimation(self, animationName: str):
        for index, animation in enumerate(self.__animations):
            if animation.name == animationName:
                self.__animations.pop(index)
                break


components = [Animator]


class GameObject(object):
    __gameObjectCount = 0

    def __init__(self, geometry: Geometry, imageName: str = None, imageGroupName: str = None):
        global game
        self.__game = game
        self.image: Image = self.__game.assets.GetImage(imageName, imageGroupName) if imageName else None
        if not self.image:
            self.image = self.__game.assets.CreateImage("GameObject", geometry.size.x, geometry.size.y, imageGroupName)
        self.geometry: Geometry = geometry

        self._layer: ObjectsLayer = None

        self.__components: list[Component] = []

        GameObject.__gameObjectCount += 1

        self.__id = GameObject.__gameObjectCount
        self.__destroyed = False

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, value):
        ErrorHandler.Throw("PropertyError", "GameObject", None, "id", "You cannot set the \"id\" property of \"GameObject\" instance")

    def Update(self):
        for component in self.__components:
            component.Update(self.__game.time.GetDeltaTime())

    def AddComponent(self, component: Component):
        if issubclass(type(component), Component):
            self.__components.append(component)
            component._object = self
            return True
        
        ErrorHandler.Throw("TypeError", "GameObject", "AddComponent", None, "Component type is invalid")

    def RemoveComponent(self, component: Component):
        if component in self.__components:
            self.__components.remove(component)
            return True

    def RemoveComponentByIndex(self, index: int):
        if index > 0 and index < len(self.__components):
            self.__components.pop(index)
            return True

    def RemoveComponentByType(self, type: object):
        component = self.GetComponent(type)
        if component:
            self.__components.remove(component)
            return True
        return False
            
    def GetComponent(self, componentType: type):
        for comp in self.__components:
            if type(comp).__name__ == componentType.__name__:
                for compont in components:
                    if isinstance(comp, compont): 
                        comp: object[compont]
                return comp
            
    def Destroy(self):
        if self._layer:
            self._layer.RemoveObject(self)
        self.__destroyed = True
        del self

    def IsDestroyed(self):
        return self.__destroyed

    def __str__(self):
        return f"GameObject(pos: {self.geometry.position.xy}, size: {self.geometry.size.xy})"
    
    def __repr__(self):
        return str(self)


class AssetGroup:
    def __init__(self, name: str, objectType: type):
        self.name = name
        self.__objectType = objectType
        self.objects = []

    def AddObject(self, object):
        if type(object).__name__ == self.__objectType.__name__:
            self.objects.append(object)

    def RemoveObject(self, object):
        if object in self.objects:
            self.objects.remove(object)

class ImageGroup(AssetGroup):
    def __init__(self, name: str):
        super().__init__(name, Image)
        self.objects: list[Image]

    def __str__(self):
        return f"ImageGroup({self.name})"
    
    def __repr__(self):
        return str(self)

class Assets:
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __init__(self):
        self.__imageGroups: list[ImageGroup] = [ImageGroup("All")]

    def CreateImageGroup(self, name: str):
        if self.GetImageGroup(name): 
            return
        self.__imageGroups.append(ImageGroup(name))

    def GetImageGroup(self, name: str):
        for group in self.__imageGroups:
            if group.name == name:
                return group

    def RemoveImageGroup(self, name: str):
        if name == "All": 
            return
        group = self.GetImageGroup(name)
        if group:
            self.__imageGroups.remove(group)
            return group

    def LoadImage(self, fileName: str, imageName: str, group: str = None):
        surface = pg.image.load(fileName)
        image = self.CreateImage(imageName, surface.get_width(), surface.get_height(), group)
        image.originalSurface = surface.convert_alpha()
        return image

    def CreateImage(self, name: str, width: int, height: int, groupName: str=None, surface: pg.Surface = None):
        image = Image(name, width, height, surface)
        self.__imageGroups[0].AddObject(image)
        if (group := self.GetImageGroup(groupName)) is not None:
            group.AddObject(image)
        return image
    
    def ClearGroup(self, name: str):
        if (group := self.GetImageGroup(name)) is not None:
            group.objects.clear()

    def GetImage(self, name: str, groupName: str = None):
        if not groupName or (group := self.GetImageGroup(groupName)) is not None:
            group = self.__imageGroups[0]
            
        for image in group.objects:
            if image.name == name:
                return image
            
    def RemoveImage(self, name: str):
        image = self.GetImage(name)
        if image:
            for group in self.__imageGroups:
                if image in group.objects:
                    for img in group.objects:
                        if img == image:
                            group.RemoveObject(image)
                            return
                    
    def RemoveAllImagesFromGroup(self, name: str):
        group = self.GetImageGroup(name)
        for group2 in self.__imageGroups:
            if group == group2:
                continue
            for img in group2.objects:
                if img in group.objects:
                    group2.RemoveObject(img)
                    return
        
        group.objects.clear()

class Camera:
    def __init__(self, size: pg.Vector2 | tuple, renderSurface: pg.Surface):
        self.__position = pg.Vector2(0, 0)
        self.__zoom = 1
        self.__rotation = 0
        self.renderSurface = renderSurface
        self.__size = pg.Vector2(size)
        self.__surface = pg.Surface(size, pg.SRCALPHA)

        self.updateRequired = False

    def TransformPoint(self, point: pg.Vector2):
        return point / self.__zoom + self.__position + self._getOffset()

    @property
    def zoom(self):
        return self.__zoom

    @zoom.setter
    def zoom(self, value: float):
        if self.__zoom != value:
            self.__zoom = pg.math.clamp(round(value, 2), 0.1, 5)
            self.updateRequired = True

    @property
    def rotation(self):
        return self.__rotation

    @rotation.setter
    def rotation(self, value: float):
        if abs(self.__rotation - value) > 0.001:
            self.__rotation = value
            self.updateRequired = True

    def SetSize(self, value: pg.Vector2 | tuple):
        if self.__size != value:
            self.__size = pg.Vector2(value)
            self.updateRequired = True

    def Move(self, value: pg.Vector2 | tuple):
        self.position += pg.Vector2(value)

    @property
    def position(self):
        return self.__position.copy()
    
    @position.setter
    def position(self, value: pg.Vector2 | tuple):
        if isinstance(value, (tuple, pg.Vector2)):
            self.__position = pg.Vector2(value)

    @property
    def center(self):
        return self.__position + self.__size / 2
    
    @center.setter
    def center(self, value: pg.Vector2 | tuple):
        if isinstance(value, (tuple, pg.Vector2)):
            self.__position = value + self.__size / 2

    def LookAt(self, point: pg.Vector2 | tuple, smoothness: float = 1):
        self.position += (pg.Vector2(point) - (self.center)) / smoothness

    def GetTransformedSurface(self):
        if self.updateRequired:
            self.__surface = pg.Surface(self.__size / self.__zoom, pg.SRCALPHA)
            self.updateRequired = False

        return self.__surface
    
    def _getOffset(self):
        surface = self.GetTransformedSurface()
        return (pg.Vector2(self.renderSurface.size) / 2 - pg.Vector2(surface.size) / 2) if self.renderSurface.size != surface.size else pg.Vector2(0, 0)

    def Update(self):
        surface = self.GetTransformedSurface()
        if self.renderSurface.size != surface.size:
            surface = pg.transform.scale(self.__surface, self.renderSurface.size)

        self.renderSurface.blit(surface, (0, 0))


class Layer:
    __layersCount = 0

    def __init__(self, name: str):
        self.name = name

        self.active = True

        self.renderWithZoom = True

        self.__id = Layer.__layersCount
        Layer.__layersCount += 1

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, value):
        ErrorHandler.Throw("PropertyError", "Layer", None, "id", "You cannot set the \"id\" property of \"Layer\" instance")

    def CheckIsOnTheScreen(self, objectPosition: pg.Vector2, objectSize: tuple[int, int], screenSize: tuple[int, int]):
        return (objectPosition[0] >= -objectSize[0] and 
                objectPosition[0] <= screenSize[0] and 
                objectPosition[1] >= -objectSize[1] and
                objectPosition[1] <= screenSize[1])

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2, offset: pg.Vector2):
        pass

# Objects and game objects are synonymns
class ObjectsLayer(Layer):
    def __init__(self, name: str):
        super().__init__(name)        
        self.__gameObjects: list[GameObject] = []

    def ObjectsCount(self):
        return len(self.__gameObjects)

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2, offset: pg.Vector2):
        for gameObject in self.__gameObjects:
            gameObject.Update()

            imageSurface = gameObject.image.GetSurface()
            position = gameObject.geometry.position - cameraPosition - offset + gameObject.image.offset + (gameObject.geometry.size - pg.Vector2(imageSurface.size)) / 2

            if self.CheckIsOnTheScreen(position, imageSurface.size, surface.size):
                surface.blit(imageSurface, position)

    def AddObject(self, gameObject: GameObject):
        if gameObject.IsDestroyed():
            ErrorHandler.Throw("ObjectDestroyed", "ObjectsLayer", "AddObject", "gameObject", "You cannot use a destroyed game object")
        self.__gameObjects.append(gameObject)
        gameObject._layer = self

    def GetObjectByIndex(self, index: int):
        if index >= 0 and index < len(self.__gameObjects):
            return self.__gameObjects[index]

    def RemoveObject(self, gameObject: GameObject):
        if gameObject in self.__gameObjects:
            self.__gameObjects.remove(gameObject)


class Light:
    def __init__(self, position: pg.Vector2 | tuple, radius: float, brightness: float, intensity: float, color: str | pg.Color | tuple[int, int, int] = "white"):

        self.position = pg.Vector2(position)

        self._radius = radius
        self.__brightness = pg.math.clamp(brightness, 0, 1)
        self.__intensity = pg.math.clamp(intensity, 0, 1)
        self.__color = color

        if not smoothingImported:
            ErrorHandler.Warn("ImportWarning", "Light", None, None, "You have to install \"Smoothing\". Otherwise \"intensity\" property of \"Light\" won't do anything")
            self.__intensity = -1

        self._surface = pg.Surface((radius*2, radius*2)).convert_alpha()

        self.__updateSurface()

    @property
    def radius(self): return self._radius
    
    @radius.setter
    def radius(self, value: float):
        self._radius = value
        self.__updateSurface()

    @property
    def brightness(self): return self.__brightness
    
    @brightness.setter
    def brightness(self, value: float):
        self.__brightness = pg.math.clamp(value, 0, 1)
        self.__updateSurface()

    @property
    def intensity(self): return self.__intensity
    
    @intensity.setter
    def intensity(self, value: float):
        self.__intensity = pg.math.clamp(value, 0, 1)
        self.__updateSurface()

    @property
    def color(self): return pg.Color(self.__color)
    
    @color.setter
    def color(self, value: str | pg.Color | tuple[int, int, int]):
        self.__color = pg.Color(value)
        self.__updateSurface()

    def __updateSurface(self): # lightness in between 1 and 255
        self._surface.fill((0, 0, 0))
        if self.__brightness <= 0.0035:
            return
        
        easingFunction = None
        if self.__intensity == -1:
            easingFunction = lambda x: x  # noqa: E731
        else:
            angle = self.__intensity * 90
            factor = 0.5 # radius of a circle on which points are lying
            
            cos1 = round(math.cos(math.radians(angle)) * factor, 3)
            sin1 = round(math.sin(math.radians(angle)) * factor, 3)

            easingFunction = smoothing.cubicBezier(cos1, sin1, cos1 + factor, sin1 + factor)

        brightness = round(255 * self.__brightness)

        for i in range(brightness, 1, -1):
            color = pg.math.clamp(round(easingFunction(((brightness + 1) - i) / brightness) * brightness), 0, 255)
            pg.draw.circle(self._surface, (color, color, color), (self._radius, self._radius), self._radius * i / brightness)

        self._surface.fill(self.__color, special_flags=pg.BLEND_RGB_MULT)


class Darkness(Layer):
    def __init__(self, name, color: str | pg.Color | tuple[int, int, int]):
        super().__init__(name)

        self.color = color

        self.__lights: list[Light] = []

    # @property
    # def color(self):
    #     return pg.Color(self.__color)

    # @color.setter
    # def color(self, value: str | pg.Color | tuple[int, int, int]):
    #     self.__color = pg.Color(value)

    def AddLight(self, light: Light):
        self.__lights.append(light)
    
    def RemoveLight(self, light: Light):
        if light in self.__lights:
            self.__lights.remove(light)

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2, offset: pg.Vector2):
        darkSurface = pg.Surface(surface.size, pg.SRCALPHA)
        darkSurface.fill(self.color)

        for light in self.__lights:
            darkSurface.blit(light._surface, light.position - pg.Vector2(light._radius, light._radius) - cameraPosition - offset, special_flags=pg.BLEND_RGBA_ADD)

        surface.blit(darkSurface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)


class ParticleTemplate:
    def __init__(self, scale: float, # factor (for example, if size = 2, surface.size will be 2x)
                       surface: pg.Surface, colors: list[tuple[int, int, int]], 
                       scaleVelocity: int = None, colorVelocity: tuple[int, int, int] | list[list[tuple[int, int, int], float]] = None, # list[list[color, % of lifetime, interpolation function (linear by default)]
                       startVelocity: pg.Vector2 | tuple[float, str] = pg.Vector2(), constantVelocity: pg.Vector2 | tuple[float, str] = pg.Vector2()): # vector or [factor, "fromCenter" - "toCenter" or "fromPosition" - "toPosition"] #(strength, shape center)
                    
        
        self.scale = scale
        self.surface = surface
        self.colors = colors

        self.scaleVelocity = scaleVelocity
        self.colorVelocity = colorVelocity
        self.startVelocity = startVelocity
        self.constantVelocity = constantVelocity

class Particle:
    def __init__(self, lifetime: float, position: pg.Vector2, template: ParticleTemplate, shape):
        if not smoothingImported:
            ErrorHandler.Throw("ImportError", "Particle", None, None, "You have to install \"Smoothing\" before using a \"Particle\"")

        self.__lifetime = lifetime
        
        self.template: ParticleTemplate = template

        self.__scale = template.scale
        self.position = position.copy()

        self.color = template.colors[randint(0, len(template.colors) - 1)]
        self.__originalSurface = template.surface
        self._currentSurface = template.surface.copy()
        self._currentSurface.fill(self.color, special_flags=pg.BLEND_RGBA_ADD)

        vector = self.template.startVelocity.copy()
        if isinstance(self.template.startVelocity, list):
            vector = self.position - (shape.center if self.template.startVelocity[1].endswith("Center") else shape.position)
            if vector.length() > 0:
                vector = vector.normalize() * self.template.startVelocity[0]
            if self.template.startVelocity[1].startswith("from"):
                vector *= -1

        self.linearVelocity = vector

        vector = self.template.constantVelocity
        if isinstance(self.template.constantVelocity, list):
            vector = self.position - (shape.center if self.template.constantVelocity[1].endswith("Center") else shape.position)
            if vector.length() > 0:
                vector = vector.normalize() * self.template.constantVelocity[0]
            if self.template.constantVelocity[1].startswith("from"):
                vector *= -1

        self.constantVelocity = vector

        self.scaleVelocity = 0
        if self.template.scaleVelocity is not None:
            self.scaleVelocity = (self.template.scaleVelocity - self.__size) / self.lifetime

        self.colorVelocity = smoothing.Transition()
        if self.template.colorVelocity is not None:
            self.colorVelocity.AddValue(smoothing.Value(list(self.color), 1))
            if isinstance(self.template.colorVelocity[0], int):
                self.colorVelocity.AddValue(smoothing.Value(list(self.template.colorVelocity), self.lifetime, smoothing.linear))
            else:
                for color in self.template.colorVelocity:
                    value = color[0]
                    time = self.lifetime * color[1] / 100 if len(color) > 1 else self.lifetime
                    func = color[2] if len(color) > 2 else smoothing.linear
                    self.colorVelocity.AddValue(smoothing.Value(list(value), time, func))

            self.colorVelocity.ToNextValue()

    @property
    def lifetime(self):
        return self.__lifetime

    def Update(self, dt: float):
        self.__lifetime = round(self.__lifetime - dt, 3)

        self.linearVelocity += self.constantVelocity * dt
        self.position += self.linearVelocity * dt

        self.colorVelocity.Update(dt)

        if self.template.scaleVelocity is not None and self.lifetime:
            self.scaleVelocity = (self.template.scaleVelocity - self.__scale) * dt / self.__lifetime
            self.__scale = round(pg.math.clamp(self.__scale + self.scaleVelocity, 0.001, 100), 3)

            self._currentSurface = pg.transform.smoothscale_by(self.__originalSurface, self.__scale)
            self._currentSurface.fill(self.color, special_flags=pg.BLEND_RGBA_ADD)

        if self.template.colorVelocity is not None:
            if not self.colorVelocity.IsInProcess():
                self.colorVelocity.ToNextValue()

            self.color = self.colorVelocity.GetValue().List
            if self.template.sizeVelocity is not None:
                self._currentSurface = self.__originalSurface.copy()
                self._currentSurface.fill(self.color, special_flags=pg.BLEND_RGBA_ADD)

class EmitterShape:
    def __init__(self, position: pg.Vector2 | tuple[int, int]):
        self.position = pg.Vector2(position)

    @property
    def center(self):
        return self.position
    
    @center.setter
    def center(self, value: pg.Vector2):
        self.position = pg.Vector2(value)

    def GetRandomPointInArea(self):
        return pg.Vector2(self.position)

class EmitterRect(EmitterShape):                                                   # for example, if fraction = 100 and random from 0 to 1, you can get 0.74
    def __init__(self, position: pg.Vector2 | tuple[int, int], size: pg.Vector2 | tuple[int, int], fraction: int = 1): # например, если fraction = 100 и разброс от 0 до 1, вы можете получить 0.74
        super().__init__(position)
        self.size = pg.Vector2(size)
        self.fraction = fraction

    @property
    def center(self):
        return self.position + self.size / 2
    
    @center.setter
    def center(self, value: pg.Vector2):
        self.position = pg.Vector2(value - self.size / 2)

    def GetRandomPointInArea(self):
        return pg.Vector2(self.position.x + randint(0, int(self.size.x * self.fraction)) / self.fraction,
                          self.position.y + randint(0, int(self.size.y * self.fraction)) / self.fraction)
    
class EmitterCircle(EmitterShape):
    def __init__(self, position: pg.Vector2 | tuple[int, int], radius: float, fraction: int = 1):
        super().__init__(position)
        self.radius = radius
        self.fraction = fraction

    def GetRandomPointInArea(self):
        return self.center + pg.Vector2(1, 0).rotate(randint(0, 359)) * randint(0, int(self.radius * self.fraction)) / self.fraction

class EmitterLine(EmitterShape):
    def __init__(self, startPosition: pg.Vector2, endPosition: pg.Vector2, width: int, fraction: int = 1):
        super().__init__(startPosition)
        self.__direction = pg.Vector2(endPosition) - self.position
        self.__directionNormalized = self.__direction.normalize()
        self.__length = self.__direction.length()
        self.__directionTurnedRight = self.__directionNormalized.rotate(90)
        self.width = width
        self.fraction = fraction

    @property
    def endPosition(self):
        return self.position + self.__direction
    
    # Do not use it much
    @endPosition.setter
    def endPosition(self, value: pg.Vector2):
        self.__direction = pg.Vector2(value) - self.position
        self.__directionNormalized = self.__direction.normalize()
        self.__length = self.__direction.length()
        self.__directionTurnedRight = self.__directionNormalized.rotate(90)

    @property
    def center(self):
        return self.position + self.__direction / 2
    
    @center.setter
    def center(self, value: pg.Vector2):
        self.position = pg.Vector2(value - self.__direction / 2)

    def GetRandomPointInArea(self):
        return (self.position + self.__directionNormalized * randint(0, int(self.__length * self.fraction)) / self.fraction +
                self.__directionTurnedRight * randint(int(-self.width / 2 * self.fraction), int(self.width / 2 * self.fraction)) / self.fraction)

class ParticleSystem(Layer):
    def __init__(self, name, shapes: dict[str, EmitterShape]): # shapes = {name: shape}
        super().__init__(name)

        self.shapes = shapes

        self.particleTemplates: dict[str, ParticleTemplate] = {}

        self.__particles: list[Particle] = []

        self.__game = game

    def AddShape(self, name: str, shape: EmitterShape):
        if name not in self.shapes.keys():
            self.shapes[name] = shape

    def AddTemplate(self, name: str, template: ParticleTemplate):
        self.particleTemplates[name] = template

    def EmitCustomShape(self, templateName: str, lifetime: float, shape: EmitterShape, count: int = 1):
        if templateName in self.particleTemplates.keys():
            for _ in range(count):
                position = shape.GetRandomPointInArea()
                particle = Particle(lifetime, position, self.particleTemplates[templateName], shape)
                self.__particles.append(particle)

    def Emit(self, templateName: str, shapeName: int, lifetime: float, count: int = 1):
        if len(self.shapes) <= 0 or shapeName not in self.shapes.keys():
            print(len(self.shapes) <= 0, shapeName, self.shapes.keys())
            return None
        
        self.EmitCustomShape(templateName, lifetime, self.shapes[shapeName], count)

    def Render(self, surface, cameraPosition, offset):
        dt = self.__game.time.GetDeltaTime() if self.__game else 0.016
        idx = 0
        while idx < len(self.__particles):
            particle = self.__particles[idx]

            particle.Update(dt)

            if particle.lifetime <= 0:
                self.__particles.pop(idx)

                continue

            position = particle.position - cameraPosition - offset

            if self.CheckIsOnTheScreen(position, particle._currentSurface.size, surface.size):
                surface.blit(particle._currentSurface, position - pg.Vector2(particle._currentSurface.size) / 2)

            idx += 1


class TileType:
    def __init__(self, id: str, imageName: str, imageOffset: tuple[int, int] | pg.Vector2 = (0, 0), cuf = None):
        self.ID = id
        self.imageName = imageName
        self.imageOffset = imageOffset
        self.cuf = cuf # custom update function

"""
# dict

{
    "tile_size": 32,
    "tile_types": {"a": {"image_name": "ground.png", "custom_update_function": None}},
    "tiles": [{"ID": 1, "position": [0, 0], "properties": {}}]
}

"""

class Tile(GameObject):
    def __init__(self, position: tuple, size: float, tileType: TileType):
        super().__init__(RectGeometry(position[0], position[1], size, size), tileType.imageName)

        self.__tileType = tileType
        self.properties = {}

    def Update(self):
        super().Update()

        if self.__tileType.cuf:
            self.__tileType.cuf(self)
        
    def GetImageOffset(self):
        return pg.Vector2(self.__tileType.imageOffset)

class Tilemap(Layer):
    def __init__(self, name, tileSize: float, tileTypes: list[TileType]):
        super().__init__(name)
        
        self.__tileSize = tileSize
        self.__tileTypes = {type.ID: type for type in tileTypes}
        self.tiles: list[Tile] = []

    def __getitem__(self, key):
        return self.tiles[key]

    @property
    def tileSize(self):
        return self.__tileSize

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2, offset: pg.Vector2):
        for tile in self.tiles:
            tile.Update()

            imageSurface = tile.image.GetSurface()
            position = tile.geometry.position - cameraPosition - offset + tile.GetImageOffset()

            if self.CheckIsOnTheScreen(position, imageSurface.size, surface.size):
                surface.blit(imageSurface, position)

    def LoadTilesFromTileList(self, tiles: list[dict]):
        for tile in tiles:
            if tile["ID"] in self.__tileTypes.keys():
                self.tiles.append(Tile(pg.Vector2(tile["position"]) * self.__tileSize, self.__tileSize, self.__tileTypes[tile["ID"]]))

    def LoadTilesFromStringList(self, tiles: list[str], startWithPosition: pg.Vector2 = pg.Vector2(0, 0)):
        for y, string in enumerate(tiles):
            for x, ID in enumerate(string):
                if ID in self.__tileTypes.keys():
                    self.tiles.append(Tile(startWithPosition + pg.Vector2(x, y) * self.__tileSize, 
                                             self.__tileSize, self.__tileTypes[ID]))

    @classmethod
    def FromDictionary(cls, name: str, dict: dict, tileListType: type = Tile):
        types = [TileType(tileType["ID"], tileType["image_name"], pg.Vector2(), tileType["custom_update_function"]) for tileType in dict["data"]["types"] if tileType["is_tile"]]

        tilemap = cls(name, dict["data"]["tile_size"], types)
        if tileListType.__name__ == Tile.__name__:
            tilemap.LoadTilesFromTileList(dict["tiles"])
        elif tileListType.__name__ == str.__name__:
            tilemap.LoadTilesFromStringList(dict["tiles"])
        else:
            return None

        return tilemap
    
    @classmethod
    def FromFile(cls, name: str, fileName: str):
        data = ""
        with open(fileName, "r") as file:
            data = file.read()

        dict = json.loads(data)

        return Tilemap.FromDictionary(name, dict)


class Scene:
    def __init__(self, name: str):
        global game
        self.name = name
        self.__layers: dict[int, Layer] = {}
        self.start = lambda: None
        self.loop = lambda: None
        self.end = lambda: None

        if game is None:
            ErrorHandler.Throw("EngineInitialization", "Scene", None, None, "Infinova has to be initialized before creating a Scene")

        self.__game = game
        self._screenSurface = pg.Surface(self.__game._screen.size, pg.SRCALPHA).convert_alpha()
        self.camera = Camera(self._screenSurface.size, self._screenSurface)
        self._fillColor = "white"

    def AddLayer(self, layer: Layer):
        self.__layers[layer.id] = layer

    def RemoveLayer(self, layer: Layer):
        if layer.id in self.__layers.keys():
            self.__layers.pop(layer.id)
            return
        
        ErrorHandler.Throw("MissingElementError", "Scene", "RemoveLayer", None, "You can't remove a layer if it hasn't been added")

    def RemoveLayerByID(self, id: int):
        if id in self.__layers.keys():
            self.__layers.pop(id)
            return
        
        ErrorHandler.Throw("MissingElementError", "Scene", "RemoveLayerByID", None, "You can't remove a layer if it hasn't been added")

    def SetFillColor(self, colorValue: str | tuple[int, int, int] | pg.Color):
        self._fillColor = colorValue

    def _render(self):
        self._screenSurface.fill(self._fillColor)
        self.camera.updateRequired = True
        cameraSurface = self.camera.GetTransformedSurface()
        cameraSurface.fill(self._fillColor)
        offset = self.camera._getOffset()
        layersWithoutZoom = []
        layers = sorted(self.__layers.items())
        for id, layer in layers:
            if not layer.active:
                continue

            if layer.renderWithZoom:
                layer.Render(cameraSurface, self.camera.position, offset)
                continue

            layersWithoutZoom.append(layer)

        self.camera.Update()

        for layer in layersWithoutZoom:
            layer.Render(self._screenSurface, self.camera.position, offset)

    def SetStartFunction(self, function):
        self.start = function

    def SetLoopFunction(self, function):
        self.loop = function

    def SetEndFunction(self, function):
        self.end = function
        

class SceneTransition:
    def __init__(self, frames: list[Frame], updateSceneBOnFrame: int = -1, stopUpdateSceneAOnFrame: int = -1): # -1 means half of frames
        global game
        self.__game = game

        self.__frames = frames

        self.__startUpdateSceneBOn = updateSceneBOnFrame if updateSceneBOnFrame != -1 else len(self.__frames) // 2
        self.__stopUpdateSceneAOn = stopUpdateSceneAOnFrame if stopUpdateSceneAOnFrame != -1 else len(self.__frames) // 2

        self.__sceneA: Scene = None
        self.__sceneB: Scene = None

        self.__running = False
        self.__timer = 0
        self.__currentFrame = 0
        self.__nextSceneIndex = 0

        self._surface = pg.Surface(self.__game._screen.size, pg.SRCALPHA).convert_alpha()
        self.__surfaceSceneA = pg.Surface(self.__game._screen.size, pg.SRCALPHA).convert_alpha()
        self.__surfaceSceneB = pg.Surface(self.__game._screen.size, pg.SRCALPHA).convert_alpha()

    @classmethod
    def FromGIF(cls, filePath: str, framesDuration: int, updateSceneBOnFrame: int = -1, stopUpdateSceneAOnFrame: int = -1):
        global game
        if not game:
            ErrorHandler.Throw("EngineInitialization", "SceneTransition", "FromGIF", None, "Infinova has to be initialized before using a \"SceneTransition\"")

        if not pillowImported:
            ErrorHandler.Throw("ImportError", "SceneTransition", "FromGIF", None, "You have to install \"Pillow\" before using \"SceneTransition.FromGIF\"")

        img = pillowImage.open(filePath)

        frames = []

        try:
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.convert("RGBA")
                
                data = frame.tobytes()
                size = frame.size
                
                frames.append(Frame(Image(f"Frame {i}", game._screen.width, game._screen.height, pg.image.frombytes(data, size, "RGBA")), framesDuration))
        except EOFError:
            pass

        return cls(frames, updateSceneBOnFrame, stopUpdateSceneAOnFrame)
        

    def Between(self, sceneA, sceneB, nextSceneIndex):
        self.__sceneA = sceneA
        self.__sceneB = sceneB

        self.__nextSceneIndex = nextSceneIndex

        self.__running = True

    def Update(self):
        if not self.__running:
            return False
        
        self.__timer += self.__game.time.GetDeltaTime()

        if self.__timer * 1000 >= self.__frames[self.__currentFrame].duration:
            self.__currentFrame += 1
            self.__timer = 0

        if self.__currentFrame >= len(self.__frames):
            self.__running = False
            self.__currentFrame = 0
            self.__timer = 0
            return True
        
        if self.__currentFrame > 1 and self.__currentFrame >= self.__startUpdateSceneBOn:
            self.__sceneB.loop()
            if self.__currentFrame == self.__startUpdateSceneBOn:
                self.__game.SetSceneByIndex(self.__nextSceneIndex)
        
        if self.__currentFrame > 1 and self.__currentFrame < self.__stopUpdateSceneAOn:
            self.__sceneA.loop()

        frame = self.__frames[self.__currentFrame]

        frameSurfaceA = pg.transform.scale(frame.image.GetSurface(), self._surface.size).convert_alpha()
        frameSurfaceB = frameSurfaceA.copy().convert_alpha()

        arrayA = pg.PixelArray(frameSurfaceA)
        arrayA.replace((255, 0, 255, 255), (255, 255, 255, 255), 0.999)
        arrayA.replace((0, 255, 0, 255), (0, 0, 0, 0), 0)
        arrayA.close()
        del arrayA

        arrayB = pg.PixelArray(frameSurfaceB)
        arrayB.replace((255, 255, 0, 255), (255, 255, 255, 255), 0.999)
        arrayB.replace((0, 0, 255, 255), (0, 0, 0, 0), 0)
        arrayB.close()
        del arrayB

        self.__sceneA._render()
        self.__surfaceSceneA.blit(self.__sceneA._screenSurface, (0, 0))
        self.__surfaceSceneA.blit(frameSurfaceA, (0, 0), special_flags=pg.BLEND_RGBA_SUB)
        self._surface.blit(self.__surfaceSceneA)

        self.__sceneB._render()
        self.__surfaceSceneB.blit(self.__sceneB._screenSurface, (0, 0))
        self.__surfaceSceneB.blit(frameSurfaceB, (0, 0), special_flags=pg.BLEND_RGBA_SUB)
        self._surface.blit(self.__surfaceSceneB)

        transitionSurface = pg.transform.scale(frame.image.GetSurface(), self._surface.size).convert_alpha()
        arrayTransition = pg.PixelArray(transitionSurface)
        arrayTransition.replace((0, 0, 255, 255), (0, 0, 0, 0))
        arrayTransition.replace((0, 255, 0, 255), (0, 0, 0, 0))
        arrayTransition.close()
        del arrayTransition
        self._surface.blit(transitionSurface, (0, 0))


class Time:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __init__(self):
        self.__dt = 0.016
        self.__FPS = 60
        self.__currentFPS = 60
        self.__clock = pg.time.Clock()

    def SetFPS(self, value: int):
        self.__FPS = value
        self.__dt = 1000 / value
    
    def GetCurrentFPS(self):
        return self.__currentFPS
    
    def GetDeltaTime(self):
        return self.__dt

    def Update(self):
        self.__clock.tick(self.__FPS)
        self.__currentFPS = round(self.__clock.get_fps(), 2)
        self.__dt = round(1 / (self.__currentFPS if self.__currentFPS else self.__FPS), 5)


class Input:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance
    
    def __init__(self):
        global game
        self.__game = game

        self.__keys = []
        self.__keysDown = []
        self.__keysUp = []

        self.__mouse = []
        self.__mouseDown = []
        self.__mouseUp = []

        self.__mouseWheel = 0

        self.Axes = {
            "H": {-1: [pg.K_a, pg.K_LEFT], 1: [pg.K_d, pg.K_RIGHT]},
            "V": {-1: [pg.K_w, pg.K_UP, pg.K_SPACE], 1: [pg.K_s, pg.K_DOWN]}
        }

    def Update(self, wheel: int, keysDown, keysUp):
        self.__keysDown = keysDown
        self.__keysUp = keysUp

        self.__keys = pg.key.get_pressed()

        self.__mouseDown = pg.mouse.get_just_pressed()
        self.__mouse = pg.mouse.get_pressed()
        self.__mouseUp = pg.mouse.get_just_released()

        self.__mouseWheel = wheel

    def GetAxis(self, axis: str):
        if axis == "Mouse":
            return pg.Vector2(pg.mouse.get_rel()) / self.__game.GetCurrentCamera().zoom
        
        if axis in self.Axes.keys():
            first = 0
            for key in self.Axes[axis][-1]:
                if self.__keys[key]:
                    first = 1
                    break
        
            second = 0
            for key in self.Axes[axis][1]:
                if self.__keys[key]:
                    second = 1
                    break

            if (first and second) or (not first and not second):
                return 0
            
            return -1 if first else 1
        
        return 0

    def GetKeyDown(self, key: int): return int(key in self.__keysDown)
    def GetKey(self, key: int): return int(self.__keys[key])
    def GetKeyUp(self, key: int): return int(key in self.__keysUp)

    def GetMouseButtonDown(self, button: int): return int(self.__mouseDown[button - 1])
    def GetMouseButton(self, button: int): return int(self.__mouse[button - 1] ) 
    def GetMouseButtonUp(self, button: int): return int(self.__mouseUp[button - 1])
    def GetMouseWheel(self): return self.__mouseWheel

    def GetLocalMousePos(self, globalMousePos: pg.Vector2 = None): # Use in UI and things, that don't transform by camera
        camera = self.__game.GetCurrentCamera()
        return (pg.Vector2(pg.mouse.get_pos()) if not globalMousePos else
                (globalMousePos - camera._getOffset()) / camera.zoom - camera.position)
    
    def GetGlobalMousePos(self):
        camera = self.__game.GetCurrentCamera()
        return pg.Vector2(pg.mouse.get_pos()) / camera.zoom + camera.position + camera._getOffset()
    
    def IsMouseOnScreen(self):
        mousePos = pg.Vector2(pg.mouse.get_pos())

        return mousePos.x >= 0 and mousePos.x <= window.width and mousePos.y >= 0 and mousePos.y <= window.height
    

class Game:
    __instance = None

    def __new__(cls, projectName: str, version: str, screenW: int, screenH: int):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance
    
    def __init__(self, projectName: str, version: str, screenW: int, screenH: int):
        global game
        game = self

        self.winSize = pg.Vector2(screenW, screenH)
        self._screen = pg.Surface(self.winSize, pg.SRCALPHA).convert_alpha()

        self.scenes: list[Scene] = []
        self.__currentScene = 0

        self.events: list[pg.Event] = []

        self.assets = Assets()
        self.time = Time()
        self.input = Input()
        self.__transitions: list[SceneTransition] = []
        self.__runningTransition = None

        self.projectName = projectName
        self.version = version

    def GetCurrentCamera(self) -> Camera:
        return self.scenes[self.__currentScene].camera

    def AddScene(self, scene: Scene):
        if scene not in self.scenes:
            self.scenes.append(scene)

    def SetScene(self, scene: Scene, transition: SceneTransition = None):
        if scene and scene in self.scenes:
            self.SetSceneByIndex(self.scenes.index(scene), transition)

    def SetSceneByIndex(self, index: int, transition: SceneTransition = None):
        if index >= 0 and index < len(self.scenes):
            if not transition:
                self.__currentScene = index
                self.scenes[self.__currentScene].start()
            elif not self.__runningTransition:
                transition.Between(self.scenes[self.__currentScene], self.scenes[index], index)
                self.__runningTransition = transition

    def SetSceneByName(self, name: str, transition: SceneTransition = None):
        scene = self.GetSceneByName(name)
        self.SetScene(scene, transition)

    def RemoveScene(self, scene: Scene):
        if scene in self.scenes and len(self.scenes) > 1:
            self.scenes.remove(scene)

        self.__currentScene = pg.math.clamp(self.__currentScene, 0, len(self.scenes) - 1)

    def RemoveSceneByIndex(self, index: int):
        if index >= 0 and index < len(self.scenes) and len(self.scenes) > 1:
            self.scenes.pop(index)

        self.__currentScene = pg.math.clamp(self.__currentScene, 0, len(self.scenes) - 1)

    def RemoveSceneByName(self, name: str):
        if (scene := self.GetSceneByName(name)) is not None and len(self.scenes) > 1:
            self.scenes.remove(scene)

        self.__currentScene = pg.math.clamp(self.__currentScene, 0, len(self.scenes) - 1)

    def GetSceneByIndex(self, index: int):
        if index >= 0 and index < len(self.scenes):
            return self.scenes[index]
        
    def GetSceneByName(self, name: str):
        for scene in self.scenes:
            if scene.name == name:
                return scene

    def __eventsUpdate(self):
        self.events = pg.event.get()
        mouseWheel = 0
        keysDown = []
        keysUp = []
        for event in self.events:
            if event.type == pg.QUIT:
                window.destroy()
                quit()

            if event.type == pg.WINDOWSIZECHANGED:
                print(event)

            if event.type == pg.KEYDOWN and event.key not in keysDown:
                keysDown.append(event.key)

            if event.type == pg.KEYUP and event.key not in keysUp:
                keysUp.append(event.key)

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 4:
                    mouseWheel = -1
                elif event.button == 5:
                    mouseWheel = 1

        self.input.Update(mouseWheel, keysDown, keysUp)

    def Run(self):
        global display

        self.scenes[self.__currentScene].start()
        while True:
            self.__eventsUpdate()

            self._screen.fill((0, 0, 0, 0))

            if not self.__runningTransition:
                self.scenes[self.__currentScene]._render()
                self.scenes[self.__currentScene].loop()

                self._screen.blit(self.scenes[self.__currentScene]._screenSurface, (0, 0))

                display.fill(self.scenes[self.__currentScene]._fillColor)
            else:
                stopped = self.__runningTransition.Update()
                self._screen.blit(self.__runningTransition._surface, (0, 0))
                if stopped:
                    self.__runningTransition = None

                display.fill("black")

            display.blit(self._screen, (0, 0))

            window.flip()
            self.time.Update()
    
    def Init(self):
        pass

global game
game: Game = None

global window
window: pg.Window = None

global display
display: pg.Surface = None

def _getGame():
    return game

def _getWindow():
    return window

def _getDisplay():
    return display

def init(screenW: int, screenH: int, projectName: str="Infinova Game", version: str="1.0", caption: str = "Infinova Game", gameClass = Game, **windowParameters):
    global game, window, display
    try:
        window = pg.Window(caption, (screenW, screenH), **windowParameters)#pg.display.set_mode((screenW, screenH), specialFlags)
        display = window.get_surface()
        
        game = gameClass(projectName, version, screenW, screenH)
        game.AddScene(Scene("Untitled"))

        game.Init()

        print(f"Initialization: success\nProject \"{projectName}\" - {version}")

    except Exception as exception: 
        print(f"Initialization: fail\n{exception.__class__.__name__}: {", ".join(exception.args)}")
        quit()


def run():
    global game

    game.Run()