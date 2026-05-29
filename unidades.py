import pygame


class Tropa:
    # aca se definen los parametros de las tropas
    def __init__(self, x, y, faccion, vida):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.vida = vida
        self.estado = "quieto"
        self.destinoX = x
        self.destinoY = y

    # aca se define el como se mueven las tropas
    def movimiento(self):
        if (self.estado == "quieto"):
            if (self.x < self.destinoX):
                self.x += 10
            elif (self.x > self.destinoX):
                self.x -= 10

            if (self.y < self.destinoY):
                self.y += 10
            elif (self.y > self.destinoY):
                self.y -= 10

    # aca se define como se dibuja una tropa graficamente
    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, (0, 255, 0), (self.x, self.y), 15)
