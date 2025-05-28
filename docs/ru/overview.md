# Infinova
Простой в изучении и использовании игровой движок с большим количеством фишек. Основан на Python &amp; Pygame-ce

### В Infinova есть поддержка:
- Многослойного рендеринга
- Системы анимаций
- Проверки столкновений и (в будущем) полноценной физики
- Частиц, эффектов, освещения
- Сцен и переходов между ними
- Компонентной архитектуры
--- 
### Зависимости:
- Pygame-ce 2.5.3+
- Pillow (для работы с GIF, необязательно)
---
### Быстрый старт:
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
### Документация
- **Основы:**
    - Инициализация
    - Сцены и слои
    - Система ресурсов
    - Коллайдеры, касания
    - Компоненты
    - Компонент анимации
    - Время и Ввод
- **Продвинутые системы:**
    - Работа с камерой
    - Система частиц
    - Тайлмапы и тайлы
    - Свет
    - Переходы между сценами
    