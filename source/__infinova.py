from random import randint
import pygame as pg
from . import smoothing
from typing import overload
import math
import json
import sys
import os

pillowImported = True
try:
    from PIL import Image as pillowImage
except ImportError:
    pillowImported = False

"""

Infinova 0.1.0-beta by Faratos
Using Pygame-ce 2.5.3 and Python 3.13.2

"""

pg.init()


def valuesNearlyEqual(a: float, b: float, distance: float = 0.001):
    return abs(a - b) < distance

def vectorsNearlyEqual(a: pg.Vector2, b: pg.Vector2, distance: float = 0.005):
    return a.distance_squared_to(b) < distance**2


def quit():
    pg.quit()
    sys.exit()


EVENT_TIMER_ACTIVE = pg.event.custom_type()


SHAPE_BOX = 3
SHAPE_CIRCLE = 4
SHAPE_CAPSULE = 5


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
    def ThrowMissingError(className: str, function: str, object: str, action: str = "remove"):
        ErrorHandler.Throw("MissingError", className, function, None, f"You cannot {action} a {object} that isn't added to \"{className}\" instance")

    @staticmethod
    def ThrowExistenceError(className: str, function: str, object: str):
        ErrorHandler.Throw("ExistenceError", className, function, None, f"Tried to add a {object} that was already used")

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

    def CropToGeometry(self, geometry):
        if geometry.shapeType == SHAPE_BOX:
            self.__original = pg.transform.scale(self.__original, (geometry.width, geometry.height)).convert_alpha()

        if geometry.shapeType == SHAPE_CIRCLE:
            self.__original = pg.transform.scale(self.__original, (geometry.radius * 2, geometry.radius * 2))
            mask = pg.Surface((geometry.radius * 2, geometry.radius * 2)).convert_alpha()
            mask.fill((255, 255, 255, 255))
            pg.draw.circle(mask, (0, 0, 0, 0), (geometry.radius, geometry.radius), geometry.radius)
            self.__original.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_SUB)

        if geometry.shapeType == SHAPE_CAPSULE:
            self.__original = pg.transform.scale(self.__original, (geometry.radius * 2, geometry.radius * 2 + geometry.height))
            mask = pg.Surface((geometry.radius * 2, geometry.radius * 2)).convert_alpha()
            mask.fill((255, 255, 255, 255))
            pg.draw.rect(mask, (0, 0, 0, 0), (0, 0, self.radius * 2, self.height + self.radius * 2), border_radius=self.radius)
            self.__original.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_SUB)

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
        self.current = pg.transform.rotate(self.current, -self.__rotation)

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

    def Fill(self, color):
        self.__original.fill(color)
        self.UpdateSurface()

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


def TransformVector(vector: pg.Vector2, position: pg.Vector2, sin: float, cos: float):
    return pg.Vector2(cos * vector.x - sin * vector.y + position.x,
                      sin * vector.x + cos * vector.y + position.y)

class AABB:
    def __init__(self, min: pg.Vector2, max: pg.Vector2):
        self.min = pg.Vector2(min)
        self.max = pg.Vector2(max)

        self.width = max.x - min.x
        self.height = max.y - min.y

class Geometry:
    @overload
    def __init__(self, x: float, y: float, radius: float): ...

    @overload
    def __init__(self, x: float, y: float, radius: float, height: float): ...

    @overload
    def __init__(self, x: float, y: float, size: pg.Vector2 | tuple[int, int]): 
        """Box geometry""" 
        ...

    def __init__(self, *args):
        self.__shapeType = None
        self.__radius = 0
        self.__width = 0
        self.__height = 0

        if len(args) == 4:
            self.__shapeType = SHAPE_CAPSULE
            self.__radius = args[2]
            self.__height = args[3]
        elif isinstance(args[2], (int, float)):
            self.__shapeType = SHAPE_CIRCLE
            self.__radius = args[2]
        elif isinstance(args[2], (tuple, pg.Vector2)):
            self.__shapeType = SHAPE_BOX
            self.__width, self.__height = tuple(args[2])
        else:
            ErrorHandler.Throw("TypeError", "Geometry", "__init__", None, "Unknown realization")
        
        self.__position = pg.Vector2(args[0], args[1])
        self.__angle = 0

        self.__transformUpdateRequired = True
        self.__aabbUpdateRequired = True
        self.__anchorsUpdateRequired = True

        self.vertices: list[pg.Vector2] = []
        self.__aabb: AABB = None

        self.anchors: list[pg.Vector2] = []
        self.__transformedAnchors: list[pg.Vector2] = []

        if self.__shapeType == SHAPE_BOX:
            self.vertices = self._createBoxVertices(self.__width, self.__height)

        if self.__shapeType == SHAPE_CAPSULE:
            self.vertices = self.__createCapsuleVertices(self.__height)

        self.__transformedVertices: list[pg.Vector2] = [pg.Vector2() for _ in range(len(self.vertices))]

        self.cannotCollideWith = []

    @property
    def shapeType(self):
        return self.__shapeType

    @property
    def radius(self):
        if self.shapeType in [SHAPE_CIRCLE, SHAPE_CAPSULE]:
            return self.__radius
        
        ErrorHandler.Throw("InvalidProperty", "Geometry", None, "radius", "You cannot get the \"radius\" property of \"Box\" Geometry")

    @property
    def width(self):
        if self.shapeType == SHAPE_BOX:
            return self.__width
        
        ErrorHandler.Throw("InvalidProperty", "Geometry", None, "width", "You cannot get the \"radius\" property of \"Circle\" or \"Capsule\" Geometry")
    
    @property
    def height(self):
        if self.shapeType in [SHAPE_BOX, SHAPE_CAPSULE]:
            return self.__height + self.__radius * 2
        
        ErrorHandler.Throw("InvalidProperty", "Geometry", None, "height", "You cannot get the \"height\" property of \"Circle\" Geometry")

    # @classmethod
    # def Box(cls, x: float, y: float, width: float, height: float):
    #     return cls(x, y, 0, width, height, SHAPE_BOX)
    
    # @classmethod
    # def Circle(cls, x: float, y: float, radius: float):
    #     return cls(x, y, radius, 0, 0, SHAPE_CIRCLE)

    # @classmethod
    # def Capsule(cls, x: float, y: float, height: float, radius: float):
    #     return cls(x, y, radius, 0, height - radius * 2, SHAPE_CAPSULE)

    def Update(self):
        self.__transformUpdateRequired = True
        self.__aabbUpdateRequired = True
        self.__anchorsUpdateRequired = True

    def _createBoxVertices(self, width: int, height: int):
        left =  -width / 2
        right = left + width
        top = -height / 2
        bottom = top + height
        
        return [pg.Vector2(left, top),
                pg.Vector2(right, top),
                pg.Vector2(right, bottom),
                pg.Vector2(left, bottom)]
    
    def __createCapsuleVertices(self, height: int):
        top = -height / 2
        bottom = top + height
        
        return [pg.Vector2(0, top),
                pg.Vector2(0, bottom)]
    
    def Move(self, value: pg.Vector2 | tuple[int, int]):
        if not (value[0] == 0 and value[1] == 0):
            self.__position += pg.Vector2(value)
            self.__transformUpdateRequired = True
            self.__aabbUpdateRequired = True

    @property
    def position(self):
        return pg.Vector2(self.__position)
    
    def SetPosition(self, value: tuple | pg.Vector2):
        if not (value[0] == self.__position[0] and value[1] == self.__position[1]):
            self.__position = pg.Vector2(value[0], value[1])
            self.__transformUpdateRequired = True
            self.__aabbUpdateRequired = True

    @property
    def angle(self):
        return math.degrees(self.__angle)
    
    @property
    def angleRadians(self):
        return self.__angle

    def Rotate(self, value: int):
        self.RotateRadians(math.radians(value))

    def RotateRadians(self, value: int):
        if value != 0:
            self.__angle += value
            self.__transformUpdateRequired = True
            self.__aabbUpdateRequired = True

    def SetAngle(self, value: int):
        self.SetAngleRadians(math.radians(value))

    def SetAngleRadians(self, value: int):
        radiansValue = value
        if radiansValue != self.__angle:
            self.__angle = radiansValue
            self.__transformUpdateRequired = True
            self.__aabbUpdateRequired = True

    def ScaleBy(self, value: float):
        if self.shapeType == SHAPE_BOX:
            for vertex in self.vertices:
                vertex.scale_to_length(vertex.length() * value)
            self.__width *= value
            self.__height *= value

        elif self.shapeType == SHAPE_CIRCLE:
            self.__radius *= value

        elif self.shapeType == SHAPE_CAPSULE:
            for vertex in self.vertices:
                vertex.scale_to_length(vertex.length() * value)
            self.__radius *= value

    def GetAABB(self):
        if self.__aabbUpdateRequired:
            min = pg.Vector2(1e+20, 1e+20)
            max = pg.Vector2(-1e+20, -1e+20)

            if self.shapeType == SHAPE_CIRCLE:
                min.x = self.__position.x - self.radius
                min.y = self.__position.y - self.radius

                max.x = self.__position.x + self.radius
                max.y = self.__position.y + self.radius

            else:
                vertices = self.GetTransformedVertices()

                for i in range(len(vertices)):
                    vert = vertices[i]

                    if vert.x < min.x: min.x = vert.x  # noqa: E701
                    if vert.x > max.x: max.x = vert.x  # noqa: E701
                    if vert.y < min.y: min.y = vert.y  # noqa: E701
                    if vert.y > max.y: max.y = vert.y  # noqa: E701

                if self.shapeType == SHAPE_CAPSULE:
                    min -= pg.Vector2(self.radius, self.radius)
                    max += pg.Vector2(self.radius, self.radius)

            self.__aabb = AABB(min, max)

            self.__aabbUpdateRequired = False
        
        return self.__aabb

    def GetTransformedVertices(self):
        if self.__transformUpdateRequired:
            sin = math.sin(self.__angle)
            cos = math.cos(self.__angle)

            for i in range(len(self.vertices)):
                vector = self.vertices[i]
                self.__transformedVertices[i] = TransformVector(vector, self.__position, sin, cos)

            self.__transformUpdateRequired = False
        
        return self.__transformedVertices
    
    def AddAnchor(self, anchor: pg.Vector2 | tuple):
        self.anchors.append(pg.Vector2(anchor))
        self.__transformedAnchors.append(pg.Vector2())
        self.__anchorsUpdateRequired = True
    
    def GetAnchor(self, index: int):
        if self.__anchorsUpdateRequired:
            sin = math.sin(self.__angle)
            cos = math.cos(self.__angle)

            for i in range(len(self.anchors)):
                self.__transformedAnchors[i] = TransformVector(self.anchors[i], self.__position, sin, cos)

            self.__anchorsUpdateRequired = False
        
        if index < 0 or index >= len(self.__transformedAnchors):
            return None

        return self.__transformedAnchors[index]

    def DrawOnScreen(self, screen: pg.Surface, color: str | pg.Color | tuple[int, int, int], width: int, cameraPosition: pg.Vector2):
        camPos = cameraPosition
        position = self.__position - camPos

        if self.shapeType == SHAPE_CIRCLE:
            pg.draw.circle(screen, color, position, self.radius, width)

        if self.shapeType == SHAPE_BOX:
            vertices = [i - camPos for i in self.GetTransformedVertices()]
            pg.draw.polygon(screen, color, vertices, width)

        if self.shapeType == SHAPE_CAPSULE:
            radius = self.radius
            height = self.height

            heightLine = pg.Vector2(0, height / 2)
            heightLine.rotate_rad_ip(self.__angle)
            pg.draw.circle(screen, color, position + heightLine, radius, width)
            pg.draw.circle(screen, color, position - heightLine, radius, width)

            radiusLine = pg.Vector2(radius, 0)
            radiusLine.rotate_rad_ip(self.__angle)
            vertices = [i - camPos for i in self.GetTransformedVertices()]
            pg.draw.line(screen, color, vertices[0] + radiusLine, vertices[1] + radiusLine, width)
            pg.draw.line(screen, color, vertices[0] - radiusLine, vertices[1] - radiusLine, width)

    def __str__(self):
        return f"Geometry(pos: {self.__position}, angle: {self.__angle}, size:[{self.width}, {self.height}])"
    
    def __repr__(self):
        return self.__str__()

class collisions:
    @staticmethod
    def CollideRectPoint(rect: pg.Rect, point: pg.Vector2):
        return (point.x > rect.x and point.y > rect.y and 
                point.x < rect.x + rect.w and point.y < rect.y + rect.h)

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
    def __projectVertices(vertices: list[pg.Vector2], axis: pg.Vector2):
        min = 1.7976931348623157e+308
        max = -1.7976931348623157e+308

        for i in range(len(vertices)):
            vert = vertices[i]
            projection = vert.dot(axis)

            if projection < min:
                min = projection

            if projection > max:
                max = projection

        return min, max
    
    @staticmethod
    def __projectCircle(center: pg.Vector2, radius: float, axis: pg.Vector2):
        direction = axis.normalize()
        directionAndRadius = direction * radius

        point1 = center + directionAndRadius
        point2 = center - directionAndRadius

        min = point1.dot(axis)
        max = point2.dot(axis)

        if min > max:
            min, max = max, min

        return min, max
    
    @staticmethod
    def __projectCapsule(radius: float, axis: pg.Vector2, vertices: list[pg.Vector2]):
        direction = axis.normalize()
        directionAndRadius = direction * radius

        min = 1.7976931348623157e+308
        max = -1.7976931348623157e+308

        for i in range(len(vertices)):
            vert = vertices[i]
            projection1 = (vert - directionAndRadius).dot(axis)
            projection2 = (vert + directionAndRadius).dot(axis)

            projection = projection1 if projection1 < projection2 else projection2
            if projection < min:
                min = projection

            projection = projection1 if projection1 > projection2 else projection2
            if projection > max:
                max = projection

        if min > max:
            min, max = max, min

        return min, max

    @staticmethod
    def __closestPointOnPolygon(circleCenter: pg.Vector2, vertices: list[pg.Vector2]):
        result = 0
        minDist = 1.7976931348623157e+308

        for i in range(len(vertices)):
            vector = vertices[i]
            distance = vector.distance_squared_to(circleCenter)
            if (distance < minDist):
                minDist = distance
                result = i

        return result
    
    @staticmethod
    def __closestPointOnPolygonToCapsule(verticesA: pg.Vector2, verticesB: list[pg.Vector2]):
        result = 0
        minDist = 1.7976931348623157e+308
        bestPoint = None

        for i in range(len(verticesB)):
            vector = verticesB[i]
            point, distance = collisions.PointSegmentDistanceSquared(vector, verticesA[0], verticesA[1])
            if (distance < minDist):
                minDist = distance
                bestPoint = point
                result = i

        return result, bestPoint

    @staticmethod
    def PointSegmentDistanceSquared(point: pg.Vector2, a: pg.Vector2, b: pg.Vector2):
        ab = b - a
        ap = point - a

        proj = ap.dot(ab)
        abLenSqr = ab.length_squared()
        d = proj / abLenSqr

        if d <= 0: 
            closestPoint = a
        elif d >= 1: 
            closestPoint = b
        else: 
            closestPoint = a + ab * d

        distanceSquared = point.distance_squared_to(closestPoint)

        return closestPoint, distanceSquared
    
    @staticmethod
    def PointLineDistanceSquared(point: pg.Vector2, a: pg.Vector2, b: pg.Vector2):
        ab = b - a
        ap = point - a

        proj = ap.dot(ab)
        abLenSqr = ab.length_squared()
        d = proj / abLenSqr

        closestPoint = a + ab * d

        distanceSquared = point.distance_squared_to(closestPoint)

        return closestPoint, distanceSquared

    @staticmethod
    def FindContactPoints(first: Geometry, second: Geometry):
        if (first.shapeType == SHAPE_CIRCLE and second.shapeType == SHAPE_CAPSULE) or (second.shapeType == SHAPE_CIRCLE and first.shapeType == SHAPE_CAPSULE):
            circle, capsule = (first, second) if first.shapeType == SHAPE_CIRCLE else (second, first)

            vertices = capsule.GetTransformedVertices()

            closestPoint, distance = collisions.PointSegmentDistanceSquared(circle.position, vertices[0], vertices[1])

            direction = circle.position - closestPoint

            return closestPoint + direction.normalize() * capsule.radius, None, 1
        
        if (first.shapeType == SHAPE_CAPSULE and second.shapeType == SHAPE_BOX) or (second.shapeType == SHAPE_CAPSULE and first.shapeType == SHAPE_BOX):
            capsule, box = (first, second) if first.shapeType == SHAPE_CAPSULE else (second, first)
            verticesA = box.GetTransformedVertices()
            verticesB = capsule.GetTransformedVertices()

            contact1 = pg.Vector2()
            contact2 = pg.Vector2()
            contactCount = 0

            minDist = 1.0e+10
            for i in range(len(verticesA)):
                vert = verticesA[i]

                closestPoint, distance = collisions.PointSegmentDistanceSquared(vert, verticesB[0], verticesB[1])

                if valuesNearlyEqual(distance, minDist) and not vectorsNearlyEqual(closestPoint, contact1):
                    contact2 = closestPoint
                    contactCount = 2

                if distance < minDist:
                    minDist = distance
                    contact1 = vert
                    contactCount = 1

            for i in range(len(verticesB)):
                point = verticesB[i]

                for j in range(len(verticesA)):
                    closestPoint, distance = collisions.PointSegmentDistanceSquared(point, verticesA[j], verticesA[(j + 1) % len(verticesA)])
                    
                    if valuesNearlyEqual(distance, minDist) and not vectorsNearlyEqual(closestPoint, contact1):
                        contact2 = closestPoint
                        contactCount = 2

                    if distance < minDist:
                        minDist = distance
                        contact1 = closestPoint
                        contactCount = 1

            return contact1, contact2, contactCount

        if first.shapeType == SHAPE_CIRCLE and second.shapeType == SHAPE_CIRCLE:
            return first.position + (second.position - first.position).normalize() * first.radius, None, 1
        
        if first.shapeType == SHAPE_BOX and second.shapeType == SHAPE_BOX:
            contact1 = pg.Vector2()
            contact2 = pg.Vector2()
            contactCount = 0

            verticesA = first.GetTransformedVertices()
            verticesB = second.GetTransformedVertices()

            minDist = 1.0e+10

            for i in range(len(verticesA)):
                point = verticesA[i]

                for j in range(len(verticesB)):
                    vertA = verticesB[j]
                    vertB = verticesB[(j + 1) % len(verticesB)]

                    closestPoint, distance = collisions.PointSegmentDistanceSquared(point, vertA, vertB)

                    if valuesNearlyEqual(distance, minDist) and not vectorsNearlyEqual(closestPoint, contact1):
                        contact2 = closestPoint
                        contactCount = 2

                    if distance < minDist:
                        minDist = distance
                        contactCount = 1
                        contact1 = closestPoint

            for i in range(len(verticesB)):
                point = verticesB[i]

                for j in range(len(verticesA)):
                    vertA = verticesA[j]
                    vertB = verticesA[(j + 1) % len(verticesA)]

                    closestPoint, distance = collisions.PointSegmentDistanceSquared(point, vertA, vertB)

                    if valuesNearlyEqual(distance, minDist) and not vectorsNearlyEqual(closestPoint, contact1):
                        contact2 = closestPoint
                        contactCount = 2

                    if distance < minDist:
                        minDist = distance
                        contactCount = 1
                        contact1 = closestPoint

            return contact1, contact2, contactCount
        
        if (first.shapeType == SHAPE_CIRCLE and second.shapeType == SHAPE_BOX) or (second.shapeType == SHAPE_CIRCLE and first.shapeType == SHAPE_BOX):
            circle, box = (first, second) if first.shapeType == SHAPE_CIRCLE else (second, first)
            vertices = box.GetTransformedVertices()

            point = pg.Vector2()

            minDist = 1.0e+10
            for i in range(len(vertices)):
                vertA = vertices[i]
                vertB = vertices[(i + 1) % len(vertices)]

                contact, distance = collisions.PointSegmentDistanceSquared(circle.position, vertA, vertB)

                if distance < minDist:
                    minDist = distance
                    point = contact

            return point, None, 1
        
        return None, None, 0

    @staticmethod
    def IntersectCircles(firstPosition: pg.Vector2, firstRadius: float, secondPosition: pg.Vector2, secondRadius: int):
        isCollided, normal, depth = False, pg.Vector2(), 0

        distance = firstPosition.distance_to(secondPosition)
        radius = firstRadius + secondRadius
        if distance >= radius:
            return False, pg.Vector2(), 0
        
        normal = (secondPosition - firstPosition)
        normal.xy = (0, 1) if normal.xy == (0, 0) else normal.normalize()
        depth = radius - distance
        isCollided = True

        return isCollided, normal, depth

    @staticmethod
    def IntersectPolygons(verticesA: list[pg.Vector2], positionA: pg.Vector2, verticesB: list[pg.Vector2], positionB: pg.Vector2):
        isCollided, normal, depth = False, pg.Vector2(), 0

        depth = 1.7976931348623157e+308
        for i in range(len(verticesA)):
            vertA = verticesA[i]
            vertB = verticesA[(i + 1) % len(verticesA)]

            edge = vertB - vertA
            axis = pg.Vector2(-edge.y, edge.x)
            axis.normalize_ip()

            minA, maxA = collisions.__projectVertices(verticesA, axis)
            minB, maxB = collisions.__projectVertices(verticesB, axis)

            if minA >= maxB or minB >= maxA:
                return False, pg.Vector2(), 0
            
            axisDepth = min(maxB - minA, maxA - minB)

            if axisDepth < depth:
                depth = axisDepth
                normal = axis
            
        for i in range(len(verticesB)):
            vertA = verticesB[i]
            vertB = verticesB[(i + 1) % len(verticesB)]

            edge = vertB - vertA
            axis = pg.Vector2(-edge.y, edge.x)
            axis.normalize_ip()

            minA, maxA = collisions.__projectVertices(verticesA, axis)
            minB, maxB = collisions.__projectVertices(verticesB, axis)

            if minA >= maxB or minB >= maxA:
                return False, pg.Vector2(), 0
            
            axisDepth = min(maxB - minA, maxA - minB)

            if axisDepth < depth:
                depth = axisDepth
                normal = axis
            
        isCollided = True

        direction = positionB - positionA

        if (direction.dot(normal) < 0):
            normal = -normal

        return isCollided, normal, depth

    @staticmethod
    def IntersectPolygonCircle(vertices: list[pg.Vector2], polygonPosition: pg.Vector2, radius: float, circlePosition: pg.Vector2, isFirstABox: bool):
        isCollided, normal, depth = False, pg.Vector2(), 0

        depth = 1.7976931348623157e+308

        axis = pg.Vector2()

        for i in range(len(vertices)):
            vertA = vertices[i]
            vertB = vertices[(i + 1) % len(vertices)]

            edge = vertB - vertA
            axis = pg.Vector2(-edge.y, edge.x)
            axis.normalize_ip()

            minA, maxA = collisions.__projectVertices(vertices, axis)
            minB, maxB = collisions.__projectCircle(circlePosition, radius, axis)

            if minA >= maxB or minB >= maxA:
                return False, pg.Vector2(), 0
            
            axisDepth = min(maxB - minA, maxA - minB)

            if axisDepth < depth:
                depth = axisDepth
                normal = axis

        point = vertices[collisions.__closestPointOnPolygon(circlePosition, vertices)]

        axis = point - circlePosition
        axis.normalize_ip()

        minA, maxA = collisions.__projectVertices(vertices, axis)
        minB, maxB = collisions.__projectCircle(circlePosition, radius, axis)

        if minA >= maxB or minB >= maxA:
            return False, pg.Vector2(), 0
        
        axisDepth = min(maxB - minA, maxA - minB)

        if axisDepth < depth:
            depth = axisDepth
            normal = axis

        isCollided = True

        direction = polygonPosition - circlePosition

        if (isFirstABox and direction.dot(normal) > 0) or (not isFirstABox and direction.dot(normal) < 0):
            normal = -normal
    
        return isCollided, normal, depth
    
    @staticmethod
    def IntersectPolygonCapsule(verticesA: list[pg.Vector2], polygonPosition: pg.Vector2, verticesB: list[pg.Vector2], radius: float, height: float, circlePosition: pg.Vector2, isFirstABox: bool):
        isCollided, normal, depth = False, pg.Vector2(), 1.7976931348623157e+308

        for i in range(len(verticesA)):
            vertA = verticesA[i]
            vertB = verticesA[(i + 1) % len(verticesA)]

            edge = vertB - vertA
            axis = pg.Vector2(-edge.y, edge.x)
            axis.normalize_ip()

            minA, maxA = collisions.__projectVertices(verticesA, axis)
            minB, maxB = collisions.__projectCapsule(radius, axis, verticesB)

            if minA >= maxB or minB >= maxA:
                return False, pg.Vector2(), 0
            
            axisDepth = min(maxB - minA, maxA - minB)

            if axisDepth < depth:
                depth = axisDepth
                normal = axis

        idx, bestPoint = collisions.__closestPointOnPolygonToCapsule(verticesB, verticesA) 
        point = verticesA[idx]

        axis = point - circlePosition
        axis.normalize_ip()

        minA, maxA = collisions.__projectVertices(verticesA, axis)
        minB, maxB = collisions.__projectCapsule(radius, axis, verticesB)

        if minA >= maxB or minB >= maxA:
            return False, pg.Vector2(), 0
        
        axisDepth = min(maxB - minA, maxA - minB)

        if axisDepth < depth:
            depth = axisDepth
            normal = axis

        isCollided = True

        direction = polygonPosition - bestPoint

        if (isFirstABox and direction.dot(normal) > 0) or (not isFirstABox and direction.dot(normal) < 0):
            normal = -normal
    
        return isCollided, normal, depth

    @staticmethod
    def IntersectCapsuleCircle(capsuleRadius: float, capsuleVertices: float, circlePosition: pg.Vector2, circleRadius: float):
        isCollided, normal, depth = False, pg.Vector2(), 0

        bestPoint, distance = collisions.PointSegmentDistanceSquared(circlePosition, capsuleVertices[0], capsuleVertices[1])
        radius = capsuleRadius + circleRadius

        distance = math.sqrt(distance)
        
        if distance > radius:
            return isCollided, normal, depth

        normal = (circlePosition - bestPoint)

        normal.xy = (0, 1) if normal.xy == (0, 0) else normal.normalize()
        depth = radius - distance
        isCollided = True

        return isCollided, normal, depth
        
    @staticmethod
    def IntersectGeometries(first: Geometry, second: Geometry):
        isCollided, normal, depth = False, pg.Vector2(), 0

        if second in first.cannotCollideWith or first in second.cannotCollideWith:
            return isCollided, normal, depth
        
        if (first.shapeType == SHAPE_CIRCLE and second.shapeType == SHAPE_CIRCLE):
            isCollided, normal, depth = collisions.IntersectCircles(first.position, first.radius, second.position, second.radius)
        
        elif (first.shapeType == SHAPE_BOX and second.shapeType == SHAPE_BOX):
            isCollided, normal, depth = collisions.IntersectPolygons(first.GetTransformedVertices(), first.position, second.GetTransformedVertices(), second.position)
            
        elif ((first.shapeType == SHAPE_BOX and second.shapeType == SHAPE_CIRCLE) or (second.shapeType == SHAPE_BOX and first.shapeType == SHAPE_CIRCLE)):
            polygon = second if second.shapeType == SHAPE_BOX else first
            circle = first if first.shapeType == SHAPE_CIRCLE else second

            isCollided, normal, depth = collisions.IntersectPolygonCircle(polygon.GetTransformedVertices(), polygon.position, circle.radius, circle.position, first.shapeType == SHAPE_BOX)

        elif ((first.shapeType == SHAPE_CAPSULE and second.shapeType == SHAPE_CIRCLE) or (second.shapeType == SHAPE_CAPSULE and first.shapeType == SHAPE_CIRCLE)):
            capsule = second if second.shapeType == SHAPE_CAPSULE else first
            circle = first if first.shapeType == SHAPE_CIRCLE else second

            isCollided, normal, depth = collisions.IntersectCapsuleCircle(capsule.radius, capsule.GetTransformedVertices(), circle.position, circle.radius) #, first.shapeType == SHAPE_BOX

        elif ((first.shapeType == SHAPE_CAPSULE and second.shapeType == SHAPE_BOX) or (second.shapeType == SHAPE_CAPSULE and first.shapeType == SHAPE_BOX)):
            polygon = second if second.shapeType == SHAPE_BOX else first
            capsule = first if first.shapeType == SHAPE_CAPSULE else second

            isCollided, normal, depth = collisions.IntersectPolygonCapsule(polygon.GetTransformedVertices(), polygon.position, capsule.GetTransformedVertices(), capsule.radius, capsule.height, capsule.position, first.shapeType == SHAPE_BOX)

        return isCollided, normal, depth
    
    @staticmethod
    def CollideGeometries(first: Geometry, second: Geometry):
        isCollided, _, _ = collisions.IntersectGeometries(first, second)

        return isCollided

    @staticmethod
    def CollideAABB(first: AABB, second: AABB):
        if (first.max.x <= second.min.x or second.max.x <= first.min.x or
            first.max.y <= second.min.y or second.max.y <= first.min.y):
            return False
        
        return True

    @staticmethod
    def CollidePoint(geometry: Geometry, point: pg.Vector2):
        if geometry.shapeType == SHAPE_CIRCLE:
            return geometry.position.distance_squared_to(point) < geometry.radius**2
        
        elif geometry.shapeType == SHAPE_CAPSULE:
            vertices = geometry.GetTransformedVertices()
            return collisions.PointSegmentDistanceSquared(point, vertices[0], vertices[1])[1] < geometry.radius**2
        
        elif geometry.shapeType == SHAPE_BOX:
            vertices = geometry.GetTransformedVertices()
            
            collision = False

            next = 0
            for current in range(len(vertices)):

                next = current + 1
                if next >= len(vertices): 
                    next = 0

                currentPoint = vertices[current]
                nextPoint = vertices[next]

                if (((currentPoint.y >= point.y and nextPoint.y < point.y) or (currentPoint.y < point.y and nextPoint.y >= point.y)) and 
                        (point.x < (nextPoint.x - currentPoint.x) * (point.y - currentPoint.y) / (nextPoint.y - currentPoint.y) + currentPoint.x)):
                    collision = not collision
            
            return collision
    
        return False


class Component:
    def __init__(self, type: str):
        self.__type = type
        self._object: GameObject = None
    
    def Init(self):
        pass

    def Update(self):
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


class PhysicsMaterial:
    def __init__(self, density: float = 1, restitution: float = 0, staticFriction: float = 0.5, dynamicFriction: float = 0.3, airFriction: float = 0.002):
        self.density = density
        self.restitution = pg.math.clamp(restitution, 0, 2)
        self.staticFriction = pg.math.clamp(staticFriction, 0, 1)
        self.dynamicFriction = pg.math.clamp(dynamicFriction, 0, 1)
        self.airFriction = pg.math.clamp(airFriction, 0, 1)

    def Copy(self):
        return PhysicsMaterial(self.density, self.restitution, self.staticFriction, self.dynamicFriction)

class Rigidbody(Component):
    def __init__(self, material: PhysicsMaterial, isStatic: bool = False, freezeRotation: bool = False):
        super().__init__("object")
        self.__shape: Geometry = None

        self.mass = 0
        self.invMass = 0
        self.area = 0
        self.inertia = 0
        self.invInertia = 0
        self.material = material

        self.__freezedRotations = freezeRotation
        self.__isStatic = isStatic
        
        self.linearVelocity = pg.Vector2()
        self.angularVelocity = 0

        self.force = pg.Vector2()
        self.torque = 0

        # self.cannotCollideWith: list[Rigidbody] = []

    @property
    def shape(self):
        if not self.__shape:
            ErrorHandler.Throw("PropertyError", "RigidbodyPhysics", None, "shape", "The \"shape\" property was used before component was added to a \"GameObject\" instance")

        return self.__shape
    
    def IsStatic(self):
        return self.__isStatic
    
    def SetStatic(self, value):
        self.__isStatic = value
        self.invInertia = 0
        self.invMass = 0
        if not self.__isStatic:
            if not self.__freezedRotations:
                self.invInertia = 1 / self.inertia
            self.invMass = 1 / self.mass

    def FreezeRotations(self):
        self.__freezedRotations = True
        self.invInertia = 0
        
    def UnfreezeRotations(self):
        self.__freezedRotations = False
        if not self.__isStatic:
            self.invInertia = 1 / self.inertia

    def Init(self):
        super().Init()
        self.__shape = self._object.geometry

        if self.shape.shapeType == SHAPE_CAPSULE:
            self.area = self.shape.radius ** 2 * math.pi + self.shape.height * self.shape.radius * 2
            self.mass = (self.area / 37.93**2 / 10000) * self.material.density
            self.inertia = 0.5 * self.mass * self.shape.radius**2 + (1 / 12) * self.mass * ((self.shape.radius * 2)**2 + self.shape.height**2)

        elif self.shape.shapeType == SHAPE_CIRCLE:
            self.area = self.shape.radius ** 2 * math.pi
            self.mass = (self.area / 37.93**2 / 10000) * self.material.density
            self.inertia = 0.5 * self.mass * self.shape.radius**2

        elif self.shape.shapeType == SHAPE_BOX:
            self.area = self.shape.width * self.shape.height
            self.mass = (self.area / 37.93**2 / 10000) * self.material.density
            self.inertia = (1 / 12) * self.mass * (self.shape.width**2 + self.shape.height**2)

        if not self.__isStatic:
            if not self.__freezedRotations:
                self.invInertia = 1 / self.inertia
            self.invMass = 1 / self.mass

    def Update(self, dt: float):
        if not self.__isStatic and self._object._layer:
            self.linearVelocity += self._object._layer._gravity * dt

        acceleration = self.force / self.mass

        self.linearVelocity += acceleration * dt
        self.angularVelocity += self.torque / self.inertia * dt
        
        self.linearVelocity *= 1 - self.material.airFriction
        self.angularVelocity *= 1 - self.material.airFriction

        self.shape.Move(self.linearVelocity * dt)
        self.shape.RotateRadians(self.angularVelocity * dt)

        self.force.xy = (0, 0)
        self.torque = 0

        if self._object.image:
            self._object.image.rotation = self.shape.angle
        self.shape.Update()

    def ApplyForce(self, value: pg.Vector2 | tuple):
        self.force += pg.Vector2(value)

    def ApplyForceAtPoint(self, value: pg.Vector2 | tuple, point: pg.Vector2, torqueFactor: float = 1):
        self.ApplyForceAtLocalPoint(pg.Vector2(value), point - self.position, torqueFactor)

    def ApplyForceAtLocalPoint(self, value: pg.Vector2 | tuple, point: pg.Vector2, torqueFactor: float = 1):
        if point is not None and value is not None:
            self.force += pg.Vector2(value)
            self.torque += point.cross(value) * torqueFactor

    def ApplyForceAtAnchor(self, value: pg.Vector2, anchorIndex: int, torqueFactor: float = 1):
        self.ApplyForceAtPoint(value, self.GetAnchor(anchorIndex), torqueFactor)

    def ApplyAngularForce(self, value: float):
        self.angularVelocity += value


components = [Animator, Rigidbody]


class GameObject(object):
    __gameObjectCount = 0

    def __init__(self, geometry: Geometry, imageName: str = None, **kwargs):
        global game
        self.__game = game
        self.image: Image = self.__game.assets.GetImage(imageName) if imageName else None
        self.geometry: Geometry = geometry

        self._layer: ObjectsLayer = None

        self.__components: dict[str, Component] = {}

        self.__id = GameObject.__gameObjectCount
        self.__destroyed = False

        GameObject.__gameObjectCount += 1

        for name, value in kwargs.items():
            match(name):
                case "components":
                    if not isinstance(value, list):
                        ErrorHandler.Throw("TypeError", "GameObject", "__init__", "components", "Invalid \"components\" argument type. It must be a list")
                    for component in value:
                        self.AddComponent(component)

                case "createImage":
                    if value:
                        if not self.image:
                            self.__createImage()
                        self.image.Fill("black")

                case "fillImage":
                    if not self.image:
                        self.__createImage()
                    self.image.Fill(value)

                case "scale":
                    if not isinstance(value, (int, float)):
                        ErrorHandler.Throw("TypeError", "GameObject", "__init__", "scale", "Invalid \"scale\" argument type. It must be an integer or float")
                    if self.image:
                        self.image.ScaleBy(value)
                    self.geometry.ScaleBy(value)

                case "angle":
                    if not isinstance(value, (int, float)):
                        ErrorHandler.Throw("TypeError", "GameObject", "__init__", "angle", "Invalid \"angle\" argument type. It must be an integer or float")
                    if self.image:
                        self.image.rotation = value
                    self.geometry.SetAngle(value)

                case "cropImage":
                    if value and self.image:
                        self.image.CropToGeometry(self.geometry)

                case "layer":
                    if not issubclass(type(value), ObjectsLayer):
                        ErrorHandler.Throw("TypeError", "GameObject", "__init__", "layer", "\"layer\" argument must inherit from \"ObjectsLayer\"")

                    value.AddObject(self)


    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, value):
        ErrorHandler.Throw("PropertyError", "GameObject", None, "id", "You cannot set the \"id\" property of \"GameObject\" instance")

    def __createImage(self):
        geometryAABB = self.geometry.GetAABB()
        self.image = self.__game.assets.CreateImage(f"GameObject {self.__id}", geometryAABB.width, geometryAABB.height)      

    def Update(self):
        for component in self.__components.values():
            component.Update(self.__game.time.GetDeltaTime())

    def AddComponent(self, component: Component):
        if issubclass(type(component), Component):
            if self.HasComponent(type(Component)):
                ErrorHandler.ThrowExistenceError("GameObject", "AddComponent", "component")

            self.__components[type(component).__name__] = component
            component._object = self
            component.Init()
            return
        
        ErrorHandler.Throw("TypeError", "GameObject", "AddComponent", None, "Invalid component type")

    @overload
    def RemoveComponent(self, component: Component): ... 

    @overload
    def RemoveComponent(self, componentType): ...

    def RemoveComponent(self, arg: type | Component): 
        componentType = arg if isinstance(arg, type) else type(arg)
        if self.HasComponent(componentType):
            return self.__components.pop(componentType.__name__)
        
        ErrorHandler.ThrowMissingError("GameObject", "RemoveComponent", "component")

    def GetComponent(self, componentType: type):
        if self.HasComponent(componentType):
            return self.__components[componentType.__name__]
        
        ErrorHandler.ThrowMissingError("GameObject", "GetComponent", "component", "get")
            
    def HasComponent(self, componentType: type):
        return componentType.__name__ in self.__components.keys()
    
    def Rotate(self, angle):
        self.image.rotation += angle
        self.geometry.Rotate(angle)

    def Destroy(self):
        if self._layer:
            self._layer.RemoveObject(self)
        self.__destroyed = True
        del self

    def IsDestroyed(self):
        return self.__destroyed

    def __str__(self):
        return f"GameObject(pos: {self.geometry.position.xy})"
    
    def __repr__(self):
        return str(self)


class CollisionManifold:
    def __init__(self, bodyA: GameObject, bodyB: GameObject, normal: pg.Vector2, depth: int, contacts: tuple):
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.normal = normal
        self.depth = depth
        self.contact1 = contacts[0]
        self.contact2 = contacts[1]
        self.contactCount = contacts[2]

class CollisionsResolver:
    @staticmethod
    def __ResolveCollisionsBasic(contact: CollisionManifold):
        first: Rigidbody = contact.bodyA.GetComponent(Rigidbody)
        second: Rigidbody = contact.bodyB.GetComponent(Rigidbody)
        normal = contact.normal

        relativeVelocity = second.linearVelocity - first.linearVelocity

        if relativeVelocity.dot(normal) > 0:
            return

        e = min(first.material.restitution, second.material.restitution)
        
        j = (-(1 + e) * relativeVelocity.dot(normal)) / (first.invMass + second.invMass)

        impulse = j * normal

        first.linearVelocity -= impulse * first.invMass
        second.linearVelocity += impulse * second.invMass

    @staticmethod
    def __ResolveCollisionsWithRotation(contact: CollisionManifold):
        first = contact.bodyA.GetComponent(Rigidbody)
        second = contact.bodyB.GetComponent(Rigidbody)
        normal = contact.normal

        contact1: pg.Vector2 = contact.contact1
        contact2: pg.Vector2 = contact.contact2
        contactCount = contact.contactCount

        e = min(first.material.restitution, second.material.restitution)

        contactList = [contact1, contact2]
        impulses: list[pg.Vector2] = []
        raList: list[pg.Vector2] = []
        rbList: list[pg.Vector2] = []

        for i in range(contactCount):
            ra = contactList[i] - first._object.geometry.position
            rb = contactList[i] - second._object.geometry.position

            raList.append(ra)
            rbList.append(rb)
            
            raPerp = pg.Vector2(-ra.y, ra.x)
            rbPerp = pg.Vector2(-rb.y, rb.x)

            angularLinearVelocityA = raPerp * first.angularVelocity
            angularLinearVelocityB = rbPerp * second.angularVelocity

            relativeVelocity = ((second.linearVelocity + angularLinearVelocityB) - 
                                (first.linearVelocity + angularLinearVelocityA))

            contactVelocityMag = relativeVelocity.dot(normal)

            if contactVelocityMag > 0:
                continue

            raPerpDotN = raPerp.dot(normal)
            rbPerpDotN = rbPerp.dot(normal)

            denom = (first.invMass + second.invMass + 
                        raPerpDotN**2 * first.invInertia + 
                        rbPerpDotN**2 * second.invInertia)

            j = -(1 + e) * contactVelocityMag
            j /= denom
            j /= contactCount

            impulse = j * normal
            impulses.append(impulse)

        for i in range(len(impulses)):
            impulse = impulses[i]

            first.linearVelocity += -impulse * first.invMass
            first.angularVelocity += -raList[i].cross(impulse) * first.invInertia

            second.linearVelocity += impulse * second.invMass
            second.angularVelocity += rbList[i].cross(impulse) * second.invInertia

    @staticmethod
    def __ResolveCollisionsWithRotationAndFriction(contact: CollisionManifold):
        first = contact.bodyA.GetComponent(Rigidbody)
        second = contact.bodyB.GetComponent(Rigidbody)
        normal = contact.normal

        contact1: pg.Vector2 = contact.contact1
        contact2: pg.Vector2 = contact.contact2
        contactCount = contact.contactCount

        e = min(first.material.restitution, second.material.restitution)

        staticFriction = (first.material.staticFriction + second.material.staticFriction) / 2
        dynamicFriction = (first.material.dynamicFriction + second.material.dynamicFriction) / 2

        contactList = [contact1, contact2]
        impulses: list[pg.Vector2] = []
        raList: list[pg.Vector2] = []
        rbList: list[pg.Vector2] = []
        jList: list[int] = []

        for i in range(contactCount):
            ra = contactList[i] - first._object.geometry.position
            rb = contactList[i] - second._object.geometry.position

            raList.append(ra)
            rbList.append(rb)
            
            raPerp = pg.Vector2(-ra.y, ra.x)
            rbPerp = pg.Vector2(-rb.y, rb.x)

            angularLinearVelocityA = raPerp * first.angularVelocity
            angularLinearVelocityB = rbPerp * second.angularVelocity

            relativeVelocity = ((second.linearVelocity + angularLinearVelocityB) - 
                                (first.linearVelocity + angularLinearVelocityA))

            contactVelocityMag = relativeVelocity.dot(normal)

            if contactVelocityMag > 0:
                continue

            raPerpDotN = raPerp.dot(normal)
            rbPerpDotN = rbPerp.dot(normal)

            denom = (first.invMass + second.invMass + 
                        raPerpDotN**2 * first.invInertia + 
                        rbPerpDotN**2 * second.invInertia)

            j = -(1 + e) * contactVelocityMag
            j /= denom
            j /= contactCount

            jList.append(j)

            impulse = j * normal
            impulses.append(impulse)

        for i in range(len(impulses)):
            impulse = impulses[i]

            first.linearVelocity += -impulse * first.invMass
            first.angularVelocity += -raList[i].cross(impulse) * first.invInertia

            second.linearVelocity += impulse * second.invMass
            second.angularVelocity += rbList[i].cross(impulse) * second.invInertia

        frictionImpulses = []

        for i in range(contactCount):
            ra = contactList[i] - first._object.geometry.position
            rb = contactList[i] - second._object.geometry.position

            raList[i] = ra
            rbList[i] = rb
            
            raPerp = pg.Vector2(-ra.y, ra.x)
            rbPerp = pg.Vector2(-rb.y, rb.x)

            angularLinearVelocityA = raPerp * first.angularVelocity
            angularLinearVelocityB = rbPerp * second.angularVelocity

            relativeVelocity = ((second.linearVelocity + angularLinearVelocityB) - 
                                (first.linearVelocity + angularLinearVelocityA))

            tangent = relativeVelocity - relativeVelocity.dot(normal) * normal

            if (vectorsNearlyEqual(tangent, pg.Vector2())):
                continue

            tangent.normalize_ip()

            raPerpDotT = raPerp.dot(tangent)
            rbPerpDotT = rbPerp.dot(tangent)

            denom = (first.invMass + second.invMass + 
                        raPerpDotT**2 * first.invInertia + 
                        rbPerpDotT**2 * second.invInertia)

            jt = -relativeVelocity.dot(tangent)
            jt /= denom
            jt /= contactCount

            impulse = pg.Vector2()

            if i < len(jList):
                if abs(jt) <= jList[i] * staticFriction:
                    impulse = jt * tangent
                else:
                    impulse = -jList[i] * tangent * dynamicFriction

                frictionImpulses.append(impulse)

        for i in range(len(frictionImpulses)):
            impulse = frictionImpulses[i]

            first.linearVelocity += -impulse * first.invMass
            first.angularVelocity += -raList[i].cross(impulse) * first.invInertia

            second.linearVelocity += impulse * second.invMass
            second.angularVelocity += rbList[i].cross(impulse) * second.invInertia

    @staticmethod
    def SeparateBodies(first: GameObject, second: GameObject, mtv: pg.Vector2):
        if first.GetComponent(Rigidbody).IsStatic():
            second.geometry.Move(mtv)
        elif second.GetComponent(Rigidbody).IsStatic():
            first.geometry.Move(-mtv)
        else:
            first.geometry.Move(-mtv / 2)
            second.geometry.Move(mtv / 2)

    @staticmethod
    def BroadPhase(bodies: list[GameObject], dt: float, contactPairs: list[tuple[int, int]]):
        for i in range(len(bodies)):
            mainBody = bodies[i]
            mainBody.Update()
            mainBody.GetComponent(Rigidbody).Update(dt)

            mainAABB = mainBody.geometry.GetAABB()
            mainBodyComponent = mainBody.GetComponent(Rigidbody)

            if i < len(bodies) - 1:
                for j in range(i + 1, len(bodies)):
                    otherBody = bodies[j]
                    otherAABB = otherBody.geometry.GetAABB()

                    if (mainBodyComponent.IsStatic() and otherBody.GetComponent(Rigidbody).IsStatic()) or not collisions.CollideAABB(mainAABB, otherAABB):
                        continue

                    contactPairs.append((i, j))

    @staticmethod   
    def NarrowPhase(bodies: list[GameObject], contactPairs: list[tuple[int, int]], resolvingCollisionMethod: int = 2):
        for pair in contactPairs:
            mainBody = bodies[pair[0]]
            otherBody = bodies[pair[1]]

            isCollided, normal, depth = collisions.IntersectGeometries(mainBody.geometry, otherBody.geometry)
                
            if isCollided:
                CollisionsResolver.SeparateBodies(mainBody, otherBody, normal * depth)
                CollisionsResolver.__ResolveCollisionsWithRotationAndFriction(CollisionManifold(mainBody, otherBody, normal, depth, collisions.FindContactPoints(mainBody.geometry, otherBody.geometry)))


class Joint:
    def __init__(self, bodyA: GameObject, bodyB: GameObject, anchorAIndex: int, anchorBIndex: int):
        self.objectA = bodyA
        self.objectB = bodyB
        self.bodyA: Rigidbody = self.objectA.GetComponent(Rigidbody)
        self.bodyB: Rigidbody = self.objectB.GetComponent(Rigidbody)
        self.anchorAIndex = anchorAIndex
        self.anchorBIndex = anchorBIndex
        self._layer = None

    def Update(self, dt: float): 
        pass

class ForceJoint(Joint):
    def __init__(self, bodyA: GameObject, bodyB: GameObject, anchorAIndex: int, anchorBIndex: int, strength: float):
        super().__init__(bodyA, bodyB, anchorAIndex, anchorBIndex)

        self.strength = strength

    def Update(self, dt: float):
        a = self.objectA.geometry.GetAnchor(self.anchorAIndex)
        b = self.objectB.geometry.GetAnchor(self.anchorBIndex)
        direction = (b - a).normalize() * self.strength * 0.1
        
        if not self.bodyA.IsStatic():
            self.bodyA.ApplyForceAtPoint(direction, b, 1)
        if not self.bodyB.IsStatic():
            self.bodyB.ApplyForceAtPoint(-direction, a, 1)

class SpringJoint(Joint):
    def __init__(self, bodyA: Rigidbody, bodyB: Rigidbody, anchorAIndex: int, anchorBIndex: int, restLength: float, springConstant: float):
        super().__init__(bodyA, bodyB, anchorAIndex, anchorBIndex)
        self.springConstant = springConstant
        self.restLength = restLength

    def Update(self, dt: float):
        anchorAPos = self.objectA.geometry.GetAnchor(self.anchorAIndex)
        anchorBPos = self.objectB.geometry.GetAnchor(self.anchorBIndex)

        direction = anchorBPos - anchorAPos
        distance = direction.length()
        restDistance = distance - self.restLength
        forceMagnitude = restDistance * self.restLength * self.springConstant * 0.001

        force = direction.normalize() * forceMagnitude
        if not self.bodyA.IsStatic():
            self.bodyA.ApplyForceAtPoint(force / 2, anchorAPos)

        if not self.bodyB.IsStatic():                                
            self.bodyB.ApplyForceAtPoint(-force / 2, anchorBPos)


# def ResolveCollisionHingeJoint(contact: CollisionManifold, penetrationPoint: pg.Vector2):
#     penetrationToCentroidA = penetrationPoint - contact.bodyA.position
#     penetrationToCentroidB = penetrationPoint - contact.bodyB.position
        
#     angularVelocityPenetrationCentroidA = pg.Vector2(-contact.bodyA.angularVelocity * penetrationToCentroidA.y, contact.bodyA.angularVelocity * penetrationToCentroidA.x)
#     angularVelocityPenetrationCentroidB = pg.Vector2(-contact.bodyB.angularVelocity * penetrationToCentroidB.y, contact.bodyB.angularVelocity * penetrationToCentroidB.x)

#     relativeVelocityA = contact.bodyA.linearVelocity + angularVelocityPenetrationCentroidA
#     relativeVelocityB = contact.bodyB.linearVelocity + angularVelocityPenetrationCentroidB
                        
#     relativeVel = relativeVelocityB - relativeVelocityA
#     velocityInNormal = relativeVel.dot(contact.normal)	

#     if velocityInNormal > 0: return
    
#     e = min(contact.bodyA.material.restitution, contact.bodyB.material.restitution)	
#     pToCentroidCrossNormalA = penetrationToCentroidA.cross(contact.normal)
#     pToCentroidCrossNormalB = penetrationToCentroidB.cross(contact.normal)
    
#     invMassSum = contact.bodyA.invMass + contact.bodyB.invMass

#     bodyAInvInertia = contact.bodyA.invInertia
#     bodyBInvInertia = contact.bodyB.invInertia
#     crossNSum  = pToCentroidCrossNormalA * pToCentroidCrossNormalA * bodyAInvInertia + pToCentroidCrossNormalB * pToCentroidCrossNormalB * bodyBInvInertia

#     j = -(1 + e ) * velocityInNormal
#     j /= (invMassSum + crossNSum)

#     impulseVector = contact.normal * j
    
#     contact.bodyA.linearVelocity -= impulseVector * contact.bodyA.invMass
#     contact.bodyB.linearVelocity -= impulseVector * contact.bodyB.invMass	
#     contact.bodyA.angularVelocity += -pToCentroidCrossNormalA * j * bodyAInvInertia		
#     contact.bodyB.angularVelocity += pToCentroidCrossNormalB * j * bodyBInvInertia	

#     # Frictional impulse
#     velocityInNormalDirection = contact.normal * relativeVel.dot(contact.normal)
#     tangent = velocityInNormalDirection - relativeVel
#     tangent *= -1
#     minFriction = min(contact.bodyA.material.dynamicFriction, contact.bodyB.material.dynamicFriction)
#     if(tangent.x > 0.00001 or tangent.y > 0.00001):
#         tangent.normalize_ip()
    
#     pToCentroidCrossTangentA = penetrationToCentroidA.cross(tangent)
#     pToCentroidCrossTangentB = penetrationToCentroidB.cross(tangent)

#     crossSumTangent = pToCentroidCrossTangentA * pToCentroidCrossTangentA * bodyAInvInertia + pToCentroidCrossTangentB * pToCentroidCrossTangentB * bodyBInvInertia
#     frictionalImpulse = -(1 + e ) * relativeVel.dot(tangent) * minFriction
#     frictionalImpulse /= (invMassSum + crossSumTangent)
#     if frictionalImpulse > j:
#         frictionalImpulse = j

#     frictionalImpulseVector = tangent * frictionalImpulse
    
#     contact.bodyA.linearVelocity -= frictionalImpulseVector * contact.bodyA.invMass
#     contact.bodyB.linearVelocity -= frictionalImpulseVector * contact.bodyB.invMass	
    
#     contact.bodyA.angularVelocity += -pToCentroidCrossTangentA * frictionalImpulse * bodyAInvInertia		
#     contact.bodyB.angularVelocity += pToCentroidCrossTangentB * frictionalImpulse * bodyBInvInertia
	

class HingeJoint(Joint):
    def __init__(self, bodyA: GameObject, bodyB: GameObject, anchorAIndex: int, anchorBIndex: int, length: float = -1, strength: float = 5):
        super().__init__(bodyA, bodyB, anchorAIndex, anchorBIndex)

        self.objectA.geometry.cannotCollideWith.append(self.objectB.geometry)

        anchorA = self.objectA.geometry.GetAnchor(self.anchorAIndex)
        anchorB = self.objectB.geometry.GetAnchor(self.anchorBIndex)

        self.materialA = self.bodyA.material
        self.materialB = self.bodyB.material

        self.initialLength = (anchorA - anchorB).length() if length < 0 else length

        self.relativeAngle = self.objectA.geometry.angle - self.objectA.geometry.angle

        self.strength = pg.math.clamp(strength, 0, 100000)

    def Update(self, dt: float):
        anchorA = self.objectA.geometry.GetAnchor(self.anchorAIndex)
        anchorB = self.objectB.geometry.GetAnchor(self.anchorBIndex)

        direction = anchorB - anchorA
        distance = direction.length()
        if distance < 0.001:
            return

        normal = direction.normalize()

        contact = CollisionManifold(self.bodyB, self.bodyA, normal, self.initialLength - distance, (None, None, 0))
        CollisionsResolver.SeparateBodies(self.bodyA, self.bodyB, contact.normal * contact.depth * 0.5)

        if not self.bodyA.IsStatic():
            self.bodyA.ApplyForceAtAnchor(-contact.normal * contact.depth * self.strength, self.anchorAIndex)
            
        if not self.bodyB.IsStatic():
            self.bodyB.ApplyForceAtAnchor(contact.normal * contact.depth * self.strength, self.anchorBIndex)


class FixedJointWIP(HingeJoint):
    def __init__(self, bodyA: Rigidbody, bodyB: Rigidbody, anchorAIndex: int, anchorBIndex: int, strength: float = 5, angularStrength: float = 5):
        super().__init__(bodyA, bodyB, anchorAIndex, anchorBIndex, 0, strength)

        self.angularStrength = angularStrength

    def Update(self, dt: float):
        super().Update(dt)

        if not self.bodyB.IsStatic():
            self.bodyB.angularVelocity += (self.relativeAngle - (self.bodyB.angle - self.bodyA.angle)) * self.angularStrength
        if not self.bodyA.IsStatic():
            self.bodyA.angularVelocity += (self.relativeAngle - (self.bodyA.angle - self.bodyB.angle)) * self.angularStrength


class ImageGroup:
    def __init__(self, name: str):
        self.__name = name
        self.__objects: dict[str, Image] = {}

    @property
    def name(self):
        return self.__name
    
    def Count(self):
        return len(self.__objects)

    def AddImage(self, image: Image):
        if issubclass(type(image), Image):
            self.__objects[image.name] = image
            return
        ErrorHandler.Throw("TypeError", "ImageGroup", "AddImage", None, "Invalid image type")

    @overload
    def RemoveImage(self, name: str): ...

    @overload
    def RemoveImage(self, image: Image): ...

    def RemoveImage(self, arg: str | Image):
        name = arg if isinstance(arg, str) else arg.name
        if name in self.__objects.keys():
            self.__objects.pop(name)

        ErrorHandler.ThrowMissingError("ImageGroup", "RemoveImage", "image")

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
        self.__imageGroups: dict[str, ImageGroup] = {"All": ImageGroup("All")}

    def CreateImageGroup(self, name: str):
        if self.GetImageGroup(name): 
            ErrorHandler.ThrowExistanceError
        self.__imageGroups[name] = ImageGroup(name)

    def GetImageGroup(self, name: str):
        if name in self.__imageGroups.keys():
            return self.__imageGroups[name]

    def RemoveImageGroup(self, name: str):
        if name == "All": 
            return
        
        if name in self.__imageGroups.keys():
            self.RemoveAllImagesFromGroup(name)
            return self.__imageGroups.pop(name)

    def LoadImage(self, fileName: str, imageName: str = None, group: str = None):
        surface = pg.image.load(fileName)
        return self.CreateImage(imageName if imageName else fileName, 
                                 surface.get_width(), 
                                 surface.get_height(), 
                                 group,
                                 surface.convert_alpha())

    def CreateImage(self, name: str, width: int, height: int, groupName: str = None, surface: pg.Surface = None):
        image = Image(name, width, height, surface)
        self.__imageGroups["All"].AddImage(image)
        if (group := self.GetImageGroup(groupName)) is not None:
            group.AddImage(image)
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
        if not image:
            return
        
        for group in self.__imageGroups:
            if image in group.objects:
                group.RemoveObject(image)
                
        return image
                    
    def RemoveAllImagesFromGroup(self, name: str):
        group = self.GetImageGroup(name)
        for image in group.objects:
            if image in self.__imageGroups[0]:
               self.__imageGroups[0].RemoveImage(image) 
        
        group.objects.clear()

class Camera:
    def __init__(self, size: pg.Vector2 | tuple, renderSurface: pg.Surface):
        self.__position = pg.Vector2(0, 0)
        self.__zoom = 1
        self.__rotation = 0
        self.renderSurface = renderSurface
        self._size = pg.Vector2(size)
        self.__surface = pg.Surface(size, pg.SRCALPHA)

        self.updateRequired = False

    def TransformPointToWorld(self, point: pg.Vector2):
        newPoint = pg.Vector2(point) - pg.Vector2(self.renderSurface.size) / 2
        sin = math.sin(math.radians(self.__rotation))
        cos = math.cos(math.radians(self.__rotation))
        return TransformVector(newPoint, pg.Vector2(), sin, cos) / self.__zoom + self.__position# 

    def TransformPointToScreen(self, point: pg.Vector2):
        newPoint = pg.Vector2(point)# 
        sin = math.sin(math.radians(-self.__rotation))
        cos = math.cos(math.radians(-self.__rotation))
        return TransformVector(newPoint, pg.Vector2(), sin, cos) * self.__zoom - self.__position + pg.Vector2(self.renderSurface.size) / 2

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
        if not valuesNearlyEqual(self.__rotation, value):
            self.__rotation = value % 360
            self.updateRequired = True

    def SetSize(self, value: pg.Vector2 | tuple):
        if self._size != value:
            self._size = pg.Vector2(value)
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
        return self.__position + self._size / 2
    
    @center.setter
    def center(self, value: pg.Vector2 | tuple):
        if isinstance(value, (tuple, pg.Vector2)):
            self.__position = value + self._size / 2

    def LookAt(self, point: pg.Vector2 | tuple, smoothness: float = 1):
        self.position += (pg.Vector2(point) - (self.center)) / smoothness

    def __getRotatedSurfaceSize(self):
        if self.__rotation in [0, 180]:
            return self._size
        if self.__rotation in [90, 270]:
            return pg.Vector2(self._size.y, self._size.x)
        
        vertices = Geometry._createBoxVertices(None, *tuple(self._size))
        screenVertices = [vertices[(i + 1) % 4].copy() + self._size for i in range(4)]

        sin = math.sin(math.radians(self.__rotation))
        cos = math.cos(math.radians(self.__rotation))
        for vertex in vertices:
            vertex.xy = TransformVector(vertex, self._size, sin, cos)
        
        startPoint = int((self.__rotation // 90 + 2) % 4)

        for i in range(4):
            vertex1, vertex2 = vertices[i], vertices[(i + 1) % 4]
            boxPoint = screenVertices[(startPoint + i) % 4]
            cp, _ = collisions.PointLineDistanceSquared(boxPoint, vertex1, vertex2)
            
            vertex1 -= (cp - boxPoint)
            vertex2 -= (cp - boxPoint)

        width = vertices[0].distance_to(vertices[1])
        height = vertices[1].distance_to(vertices[2])

        return pg.Vector2(width, height)

    def GetTransformedSurface(self):
        if self.updateRequired:
            rotatedSize = self.__getRotatedSurfaceSize()
            zoomedSize = rotatedSize / self.__zoom
            self.__surface = pg.Surface(zoomedSize, pg.SRCALPHA)
            self.updateRequired = False

        return self.__surface
    
    def _getOffset(self):
        # surface = self.GetTransformedSurface()
        return pg.Vector2()#(pg.Vector2(self.renderSurface.size) / 2 - pg.Vector2(surface.size) / 2) if self.renderSurface.size != surface.size else pg.Vector2(0, 0)

    def Update(self):
        surface = self.GetTransformedSurface()
        
        surface = pg.transform.rotozoom(surface, self.__rotation, self.__zoom)

        self.renderSurface.blit(surface, pg.Vector2(self.renderSurface.size) / 2 - pg.Vector2(surface.size) / 2)


class Layer:
    __layersCount = 0

    def __init__(self, name: str):
        self.name = name

        self.active = True

        self.renderWithZoomAndRotation = True

        self.__id = Layer.__layersCount
        Layer.__layersCount += 1

        self.zIndex = self.__id

        self._scene = None

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, value):
        ErrorHandler.Throw("PropertyError", "Layer", None, "id", "You cannot set the \"id\" property of \"Layer\" instance")

    def DoesObjectFitInScreen(self, objectPosition: pg.Vector2, objectSize: tuple[int, int], screenSize: tuple[int, int]):
        return (objectPosition[0] >= -objectSize[0] and 
                objectPosition[0] <= screenSize[0] and 
                objectPosition[1] >= -objectSize[1] and
                objectPosition[1] <= screenSize[1])

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2):
        pass

# Objects and game objects are synonymns
class ObjectsLayer(Layer):
    def __init__(self, name: str):
        super().__init__(name)        
        self.__gameObjects: list[GameObject] = []

    def ObjectsCount(self):
        return len(self.__gameObjects)

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2):
        for gameObject in self.__gameObjects:
            gameObject.Update()

            if not gameObject.image:
                continue

            imageSurface = gameObject.image.GetSurface()
            position = gameObject.geometry.position - cameraPosition + gameObject.image.offset - pg.Vector2(imageSurface.size) / 2 + pg.Vector2(surface.size) / 2

            if self.DoesObjectFitInScreen(position, imageSurface.size, surface.size):
                surface.blit(imageSurface, position)

    def AddObject(self, gameObject: GameObject):
        if gameObject.IsDestroyed():
            ErrorHandler.Throw("ObjectDestroyedError", "ObjectsLayer", "AddObject", "gameObject", "You cannot use a destroyed \"GameObject\" instance")
        if gameObject.HasComponent(Rigidbody):
            ErrorHandler.Throw("InvalidObject", "ObjectsLayer", "AddObject", "gameObject", "You cannot link \"GameObject\" instance which has a \"Rigidbody\" component to \"ObjectsLayer\" ")

        self.__gameObjects.append(gameObject)
        gameObject._layer = self

    def GetObjectByIndex(self, index: int):
        if index >= 0 and index < len(self.__gameObjects):
            return self.__gameObjects[index]

    def RemoveObject(self, gameObject: GameObject):
        if gameObject in self.__gameObjects:
            self.__gameObjects.remove(gameObject)


class PhysicsLayer(ObjectsLayer):
    def __init__(self, name: str):
        super().__init__(name)        
        global game
        self.__game = game
        self.__gameObjects: list[GameObject] = []

        self._gravity = pg.Vector2(0, 200)

        self.__physicsIterations = 4

        self.__joints = []

        self.__showHitboxes = False
        self.__hitboxColor = "red"
        self.__hitboxWidth = 1

    def AddJoint(self, joint: Joint):
        if joint in self.__joints or joint._layer:
            ErrorHandler.Throw("ExistenceError", "PhysicsLayer", "AddJoint", None, "Tried to add a joint that was already added")
        
        joint._layer = self
        self.__joints.append(joint)

    def RemoveJoint(self, joint: Joint):
        if joint in self.__joints:
            self.__joints.remove(joint)
            return

        ErrorHandler.ThrowMissingError("PhysicsLayer", "RemoveJoint", "joint")
        
    def RemoveJointByIndex(self, index: int):
        if index >= 0 and index < len(self.__joints):
            return self.__joints.pop(index)

    def SetGravity(self, value: tuple | pg.Vector2):
        self._gravity = pg.Vector2(value)

    def SetPhysicsIterations(self, value: int):
        self.__physicsIterations = pg.math.clamp(value, 1, 128)

    def ShowHitboxes(self, color: str | pg.Color | tuple[int, int, int] = "red", width = 1):
        self.__showHitboxes = True
        self.__hitboxColor = color
        self.__hitboxWidth = pg.math.clamp(width, 0, 100)

    def HideHitboxes(self):
        self.__showHitboxes = False

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2):
        contactPairs = []
        dt = self.__game.time.GetDeltaTime() / self.__physicsIterations
        for _ in range(self.__physicsIterations):
            contactPairs.clear()

            CollisionsResolver.BroadPhase(self.__gameObjects, dt, contactPairs)
            CollisionsResolver.NarrowPhase(self.__gameObjects, contactPairs)

            for joint in self.__joints:
                joint.Update(dt)

        for gameObject in self.__gameObjects:
            if not gameObject.image:
                continue

            imageSurface = gameObject.image.GetSurface()
            position = gameObject.geometry.position - cameraPosition + gameObject.image.offset - pg.Vector2(imageSurface.size) / 2 + pg.Vector2(surface.size) / 2

            if self.DoesObjectFitInScreen(position, imageSurface.size, surface.size):
                surface.blit(imageSurface, position)
                if self.__showHitboxes:
                    gameObject.geometry.DrawOnScreen(surface, self.__hitboxColor, self.__hitboxWidth, cameraPosition)

    def AddObject(self, gameObject: GameObject):
        if gameObject.IsDestroyed():
            ErrorHandler.Throw("ObjectDestroyedError", "ObjectsLayer", "AddObject", "gameObject", "You cannot use a destroyed \"GameObject\" instance")
        self.__gameObjects.append(gameObject)
        gameObject._layer = self


class Light:
    def __init__(self, position: pg.Vector2 | tuple, radius: float, brightness: float, intensity: float, color: str | pg.Color | tuple[int, int, int] = "white"):

        self.position = pg.Vector2(position)

        self._radius = radius
        self.__brightness = pg.math.clamp(brightness, 0, 1)
        self.__intensity = pg.math.clamp(intensity, 0, 1)
        self.__color = color

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

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2):
        darkSurface = pg.Surface(surface.size, pg.SRCALPHA)
        darkSurface.fill(self.color)

        for light in self.__lights:
            darkSurface.blit(light._surface, light.position - pg.Vector2(light._radius, light._radius) - cameraPosition + pg.Vector2(surface.size) / 2, special_flags=pg.BLEND_RGBA_ADD)

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

            position = particle.position - cameraPosition - offset + pg.Vector2(surface.size) / 2

            if self.DoesObjectFitInScreen(position, particle._currentSurface.size, surface.size):
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
        super().__init__(Geometry.Box(position[0], position[1], size, size), tileType.imageName)

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

    def Render(self, surface: pg.Surface, cameraPosition: pg.Vector2):
        for tile in self.tiles:
            tile.Update()

            imageSurface = tile.image.GetSurface()
            position = tile.geometry.position - cameraPosition + tile.GetImageOffset() + pg.Vector2(surface.size) / 2

            if self.DoesObjectFitInScreen(position, imageSurface.size, surface.size):
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
        global display
        self.name = name
        self.__layers: dict[int, Layer] = {}
        self.start = lambda: None
        self.loop = lambda: None
        self.end = lambda: None

        if display is None:
            ErrorHandler.Throw("EngineInitialization", "Scene", None, None, "Infinova has to be initialized before creating a \"Scene\"")

        self._screenSurface = pg.Surface(display.size, pg.SRCALPHA).convert_alpha()
        self.camera = Camera(self._screenSurface.size, self._screenSurface)
        self._fillColor = "white"

    def AddLayer(self, layer: Layer):
        if layer._scene:
            ErrorHandler.ThrowExistenceError("Scene", "AddLayer", "layer")

        self.__layers[layer.id] = layer
        layer._scene = self

    @overload
    def RemoveLayer(self, layer: Layer): ...

    @overload
    def RemoveLayer(self, id: int): ...

    def RemoveLayer(self, arg: int | Layer):
        if issubclass(type(arg), Layer):
            if arg.id in self.__layers.keys():
                self.__layers.pop(arg.id)
                return
        elif issubclass(type(arg), int):
            if arg in self.__layers.keys():
                self.__layers.pop(arg)
                return
        
        ErrorHandler.ThrowMissingError("Scene", "RemoveLayer", "layer")

    def SetFillColor(self, colorValue: str | tuple[int, int, int] | pg.Color):
        self._fillColor = colorValue

    def _render(self):
        self._screenSurface.fill(self._fillColor)
        self.camera.updateRequired = True
        cameraSurface = self.camera.GetTransformedSurface()
        cameraSurface.fill(self._fillColor)
        layersWithoutZoomAndRotation = []
        layers = sorted(self.__layers.values(), key=lambda layer: layer.zIndex)
        for layer in layers:
            if not layer.active:
                continue

            if layer.renderWithZoomAndRotation:
                layer.Render(cameraSurface, self.camera.position)
                continue

            layersWithoutZoomAndRotation.append(layer)

        self.camera.Update()

        for layer in layersWithoutZoomAndRotation:
            layer.Render(self._screenSurface, self.camera.position)

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


class Timer:
    def __init__(self, name: str, interval: float, startFrom: float = 0, repeats: int = -1):
        self.name = name
        self.__interval = interval
        self.__startFrom = startFrom
        self._repeats = repeats
        self.__time = 0

    def Update(self, dt: float):
        self.__time += dt
        if self.__startFrom != 0:
            if self.__time >= self.__startFrom:
                self.__startFrom = 0
                self.__time = 0
            return
        
        if self.__time >= self.__interval:
            pg.event.post(pg.Event(EVENT_TIMER_ACTIVE, {"timer": self}))
            self.__time = 0
            self._repeats -= 1

        if self._repeats < -1:
            self._repeats = -1

    def __str__(self):
        return f"Timer(name: {self.name}, interval: {self.__interval})"
    
    def __repr__(self):
        return str(self)

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
        self.__timers: list[Timer] = []

    def SetFPS(self, value: int):
        self.__FPS = value
        self.__dt = 1000 / value
    
    def GetCurrentFPS(self):
        return self.__currentFPS
    
    def GetDeltaTime(self):
        return self.__dt
    
    def CreateTimer(self, name: str, interval: int, startFrom: int = 0, repeats: int = -1):
        self.__timers.append(Timer(name, interval, startFrom, repeats))

    def Update(self):
        self.__clock.tick(self.__FPS)
        self.__currentFPS = round(self.__clock.get_fps(), 2)
        self.__dt = round(1 / (self.__currentFPS if self.__currentFPS else self.__FPS), 5)

        i = 0
        while i < len(self.__timers):
            self.__timers[i].Update(self.__dt)
            if self.__timers[i]._repeats == 0:
                self.__timers.pop(i)
                i -= 1
            
            i += 1

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

    @overload
    def RemoveScene(self, scene: Scene): ...

    @overload
    def RemoveScene(self, index: int): ...

    @overload
    def RemoveScene(self, name: str): ...

    def RemoveScene(self, arg: str | int | Scene):
        if isinstance(arg, int):
            if arg >= 0 and arg < len(self.scenes) and len(self.scenes) > 1:
                self.scenes.pop(arg)
                self.__currentScene = pg.math.clamp(self.__currentScene, 0, len(self.scenes) - 1)
                return
        else:
            scene = self.GetSceneByName(arg) if isinstance(arg, str) else arg
            if len(self.scenes) > 1 and scene is not None and scene in self.scenes:
                self.scenes.remove(scene)
                self.__currentScene = pg.math.clamp(self.__currentScene, 0, len(self.scenes) - 1)
                return
            
        ErrorHandler.ThrowMissingError("Game", "RemoveScene", "scene")

    @overload
    def GetScene(self, index: int): ...
        
    @overload
    def GetScene(self, name: str): ...
            
    def GetScene(self, arg: str | int):
        if isinstance(arg, int):
            if arg >= 0 and arg < len(self.scenes):
                return self.scenes[arg]
        elif isinstance(arg, str):
            for scene in self.scenes:
                if scene.name == arg:
                    return scene
                
        ErrorHandler.ThrowMissingError("Game", "GetScene", "scene", "get")

    def __eventsUpdate(self):
        global display, window
        self.events = pg.event.get()
        mouseWheel = 0
        keysDown = []
        keysUp = []
        for event in self.events:
            if event.type == pg.QUIT:
                window.destroy()
                quit()

            if event.type == pg.WINDOWSIZECHANGED:
                display = window.get_surface()
                self.winSize.xy = display.size
                self._screen = pg.Surface(self.winSize, pg.SRCALPHA).convert_alpha()
                for scene in self.scenes:
                    scene._screenSurface = pg.Surface(display.size, pg.SRCALPHA).convert_alpha()
                    scene.camera.renderSurface = scene._screenSurface
                    scene.camera._size = pg.Vector2(scene._screenSurface.size)

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
        window.minimum_size = (50, 50)
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