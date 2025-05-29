# Infinova
Easy to learn and to use game engine with a lot of features. Based on Python &amp; Pygame-ce

[Русская версия](https://github.com/Faratos/Infinova/blob/main/docs/ru/overview.md)

### Infinova has support for:
- Multi-layer rendering
- Animation system
- Collisions and (in the future) fully-working physics
- Particles, effects, lightning
- Scenes and transitions between them
- Custom components
--- 
### Dependencies:
- Pygame-ce 2.5.3+
- Pillow (to work with GIF, unnecessary)
---
### Fast start:
```py
import infinova
import pygame

infinova.init(800, 600)

game = infinova.GetGame()

class Scene(infinova.Scene):
    def __init__(self):
        super().__init__("Demo")

        game.assets.CreateImage("GameObject image", 100, 100, surface=pygame.Surface((100, 100)))

        self.player = infinova.GameObject(
            infinova.RectGeometry(10, 10, 100, 100),
            "GameObject image"
        )

        self.objectsLayer = infinova.layer.ObjectsLayer("Objects")
        self.objectsLayer.AddObject(self.player)

        self.AddLayer(self.objectsLayer)

        self.SetLoopFunction(self.__loop)
    
    def __loop(self):
        self.player.geometry.position.x += 100 * game.time.GetDeltaTime()

game.AddScene(Scene())
game.SetSceneByIndex(1)

infinova.run()
```
---
### Documentation
- **Basics:**
    - Initialization
    - Scenes and layers
    - Assets system
    - Colliders, collisions
    - Components
    - Animation component
    - Time and Input
- **Advanced:**
    - Camera
    - Particle system
    - Tilemaps and tiles
    - Light
    - Transitions between scenes