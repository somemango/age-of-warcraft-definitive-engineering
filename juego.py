import pygame

from unidades import Tropa


class Juego:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.oro = 100
        self.mis_unidades = []
        self.unidades_enemigas = []

        self.mis_unidades.append(Tropa(100, 100, "sistemas", 100))

    def procesar_eventos(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos

            for unidad in self.mis_unidades:
                unidad.destinoX = mouse_x
                unidad.destinoY = mouse_y

    def actualizar(self):
        for unidad in self.mis_unidades:
            unidad.movimiento()

    def dibujar(self):
        for unidad in self.mis_unidades:
            unidad.dibujar(self.pantalla)
