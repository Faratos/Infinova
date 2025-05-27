import pygame as pg
import math

pg.init()

"""
Support functions for smooth animations
"""

def linear(x: float):
    return x

def cubicBezier(x1, y1, x2, y2):
    def function(t):
        if t <= 0:
            return 0.0
        if t >= 1:
            return 1.0
        
        s = t
        epsilon = 1e-6
        
        for _ in range(8):
            x = 3 * (1 - s)**2 * s * x1 + 3 * (1 - s) * s**2 * x2 + s**3

            dx = 3 * (1 - s) * (1 - 3 * s) * x1 + 3 * (2 * s - 3 * s**2) * x2 + 3 * s**2
            
            if abs(dx) < epsilon:
                break
                
            xDiff = x - t
            s -= xDiff / dx
            
            if abs(xDiff) < epsilon:
                break
        
        return 3 * (1 - s)**2 * s * y1 + 3 * (1 - s) * s**2 * y2 + s**3
    
    return function

def easeOutCubic(x: float):
    return 1 - math.pow(1 - x, 3)

def easeInOutCubic(x: float):
    return 4 * x ** 3 if x < 0.5 else 1 - math.pow(-2 * x + 2, 3) / 2

def easeInCubic(x: float):
    return x ** 3

def easeInOutBack(x: float):
    c1 = 1.70158
    c2 = c1 * 1.525

    return (math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2 if x < 0.5 else (math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2

def easeInOutQuint(x: float):
    return 16 * x ** 5 if x < 0.5 else 1 - math.pow(-2 * x + 2, 5) / 2

def easeOutElastic(x: float):
    return 0 if x == 0 else 1 if x == 1 else (math.pow(2, -10 * x) * math.sin((x * 10 - 0.75) * ((2 * math.pi) / 3)) + 1)

def easeOutBounce(x: float):
    n1 = 7.5625
    d1 = 2.75

    if (x < 1 / d1):
        return n1 * x ** 2
    elif (x < 2 / d1):
        x -= 1.5 / d1
        return n1 * x ** 2 + 0.75
    elif (x < 2.5 / d1):
        x -= 2.25 / d1
        return n1 * x ** 2 + 0.9375
    else:
        x -= 2.625 / d1
        return n1 * x ** 2 + 0.984375

class Value:
    def __init__(self, values: list[int], time: float = 0.5, function = easeInOutCubic):
        self.List = list(values)
        self.TransitionTime = time if time > 0.01 else 0.01
        self.EasingFunction = function

    def __str__(self):
        return f"Value({self.List}, {self.TransitionTime}, {self.EasingFunction.__name__})"

    def Copy(self):
        return Value(self.List, self.TransitionTime, self.EasingFunction)
    
class Transition:
    def __init__(self):
        self.__values: list[Value] = []

        self.Looping = False
        self.Round = False

        self.__currentValue: Value = None
        self.__currentValueIndex = 0

        self.__isInProcess = False
        self.__process = 0
        self.__processValuesFrom: Value = None
        self.__processValuesTo: Value = None
        self.__processTransitionTime = 0.5

    def GetValue(self):
        return self.__currentValue
    
    def AddValue(self, value: Value):
        if not isinstance(value, Value):
            return False
        
        for i in value.List:
            if not isinstance(i, (int, float)):
                return False
            
        self.__values.append(value)

        return True
    
    def SetTransitionTime(self, time: float, replace: float = None):
        for value in self.__values:
            if replace is None:
                value.TransitionTime = time
            elif value.TransitionTime == replace:
                value.TransitionTime = time

    def SetEasingFunction(self, function):
        for value in self.__values:
            value.EasingFunction = function
    
    def __incCurrentValueIndex(self):
        self.__currentValueIndex += 1

        if self.__currentValueIndex >= len(self.__values):
            self.__currentValueIndex = 0

    def ToNextValue(self):
        if len(self.__values) > 1:
            self.SetValueFromTo(self.__values[self.__currentValueIndex],
                                self.__values[(self.__currentValueIndex + 1) if self.__currentValueIndex < len(self.__values) - 1 else 0])
            
            self.__incCurrentValueIndex()

    def SetValueFromTo(self, valueFrom: Value, valueTo: Value):
        self.__processTransitionTime = valueTo.TransitionTime
        self.__processValuesTo = valueTo

        if not self.__isInProcess:
            self.__processValuesFrom = valueFrom
        else:
            self.__processValuesFrom = self.__currentValue
            
            self.__process = 0

        self.__isInProcess = True

    def GetSavedValue(self, index: int):
        return self.__values[index].Copy() if index < len(self.__values) else None
    
    def IsInProcess(self):
        return self.__isInProcess

    def Update(self, delta: float):
        if self.__isInProcess:
            self.__process += delta

            if self.__process / self.__processTransitionTime > 1:
                self.__process = 1 * self.__processTransitionTime

            first: list[int] = self.__processValuesFrom.List
            second: list[int] = self.__processValuesTo.List

            easing = self.__processValuesTo.EasingFunction

            self.__currentValue = self.__processValuesFrom.Copy()
            if len(first) < len(second):
                for i in range(len(first), len(second)):
                    self.__currentValue.List.append(second[i])

            less = len(second) if len(second) < len(first) else len(first)

            for index in range(less):
                self.__currentValue.List[index] = (first[index] + (second[index] - first[index]) * easing(self.__process / self.__processTransitionTime))

        if self.__process / self.__processTransitionTime == 1:
            self.__isInProcess = False
            self.__process = 0

            if self.Looping:
                self.ToNextValue()

        if not self.__currentValue and self.__values:
            self.__currentValue = self.__values[0]

        if self.Round:
            self.__currentValue.List = list(map(round, self.__currentValue.List))

class Updater:
    def __init__(self):
        pass