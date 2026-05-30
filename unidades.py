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
        self.velocidad = 0.5

    # aca se define el como se mueven las tropas
    def movimiento(self):
        if (self.estado == "moviendose"):
            print(f"Estado: {self.estado} | Pos actual: ({self.x}, {self.y}) | Destino: ({self.destinoX}, {self.destinoY})")
            # vectores necesarios para el calculo
            posicion_actual = pygame.math.Vector2(self.x, self.y)
            destino = pygame.math.Vector2(self.destinoX, self.destinoY)

            # calculo del vector distancia y direccion
            direccion = destino - posicion_actual
            distancia = direccion.length()  # aplica pitagoras automaticamente

            print(f"distancia al objetivo: {distancia}")

            if (distancia <= self.velocidad):
                self.x = self.destinoX
                self.y = self.destinoY
                self.estado = "quieto"
            else:
                if (distancia > 0):
                    direccion.normalize_ip()  # normaliza el vector direccion
                    vector = direccion * self.velocidad

                    # se aplica el movimiento frame por frame
                    self.x += vector.x
                    self.y += vector.y
                else:
                    print("distancia menor o igual a 0")

    # aca se define como se dibuja una tropa graficamente
    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, (0, 255, 0), (int(self.x), int(self.y)), 15)
