import pygame

from unidades import Tropa


class Juego:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.oro = 100
        self.mis_unidades = []
        self.unidades_enemigas = []

        # variables para la seleccion de varias tropas
        self.seleccionando = False
        self.inicio_seleccion = (0, 0)
        self.fin_seleccion = (0, 0)

        self.mis_unidades.append(Tropa(100, 100, "sistemas", 100))
        self.mis_unidades.append(Tropa(200, 200, "sistemas", 100))

    def procesar_eventos(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos

            for unidad in self.mis_unidades:
                unidad.destinoX = mouse_x
                unidad.destinoY = mouse_y
                unidad.estado = "moviendose"

        # esto es para cuando se pisa el click izquierdo
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for unidad in self.mis_unidades:
                unidad.destinoX = unidad.x
                unidad.destinoY = unidad.y
            self.seleccionando = True
            self.inicio_seleccion = event.pos
            self.fin_seleccion = event.pos

        # esto es para mientras vas arrastrando el mouse (actualizar)
        elif event.type == pygame.MOUSEMOTION and self.seleccionando:
            self.fin_seleccion = event.pos

        # aca se suelta el click y selecciona unidades
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.seleccionando:
                self.seleccionando = False
                self.fin_seleccion = event.pos
                
                # vemos cuales tropas se seleccionaron con la fucnion de abajo
                self.evaluar_seleccion_multiple()

    def evaluar_seleccion_multiple(self):
        # no tengo idea, lo vi en internet :(
        x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
        x_max = max(self.inicio_seleccion[0], self.fin_seleccion[0])
        y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
        y_max = max(self.inicio_seleccion[1], self.fin_seleccion[1])

        # revisamos tropa a tropa si estan en el rango con la cosa rara de arriba
        for unidad in self.mis_unidades:
            if x_min <= unidad.x <= x_max and y_min <= unidad.y <= y_max:
                unidad.seleccionada = True
            else:
                unidad.seleccionada = False

    def actualizar(self):
        for unidad in self.mis_unidades:
            unidad.movimiento()

    def dibujar(self):
        for unidad in self.mis_unidades:
            unidad.dibujar(self.pantalla)

            if self.seleccionando:
                x = min(self.inicio_seleccion[0], self.fin_seleccion[0])
                y = min(self.inicio_seleccion[1], self.fin_seleccion[1])
                ancho = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
                alto = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])
                
                # con esto se dibuja um rectangulo sin relleno para el area de seleccion
                rectangulo = pygame.Rect(x, y, ancho, alto)
                pygame.draw.rect(self.pantalla, (0, 255, 0), rectangulo, 1)
