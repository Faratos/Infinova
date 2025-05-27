import source
import pygame

source.init(800, 600, "Infinova Demo", "3.14", "Demo!")

game = source.GetGame()

class DemoScene(source.Scene):
    def __init__(self):
        super().__init__("Demo")

        # Here You can create any objects or other stuff

        game.assets.CreateImage("GameObject image", 100, 100, surface=pygame.Surface((100, 100)))

        self.player = source.GameObject( # Creating a Game object with 100x100 rect and previously created image
            source.RectGeometry(10, 10, 100, 100),
            "GameObject image"
        )

        self.objectsLayer = source.layer.ObjectsLayer("Objects")
        self.objectsLayer.AddObject(self.player)

        self.AddLayer(self.objectsLayer)

        self.SetLoopFunction(self.__loop)

    def __loop(self):
        # And here You can write logic of your objects. For example, Player control
        
        dt = game.time.GetDeltaTime()

        axisX = game.input.GetAxis("H")
        axisY = game.input.GetAxis("V")
        
        movingVector = pygame.Vector2(axisX, axisY) # Some math to make player always move at the same speed
        if movingVector.length_squared() != 0:
            movingVector.normalize_ip()

        self.player.geometry.position += movingVector * 312 * dt # moving by 312 px every second

game.AddScene(DemoScene()) # Loading our Demo scene to game
game.SetSceneByIndex(1)

source.run()