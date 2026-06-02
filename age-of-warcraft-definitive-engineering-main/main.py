import pygame
from juego import Juego

# Inicialización limpia de Pygame. Todo el comportamiento pesado lo maneja la clase Juego
pygame.init()
pantalla = pygame.display.set_mode((800, 600))
reloj = pygame.time.Clock()
juego = Juego(pantalla)
run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        juego.procesar_eventos(event)

    juego.actualizar()

    pantalla.fill("purple")
    juego.dibujar()
    pygame.display.flip()

    reloj.tick(60)  # Forzamos el bucle a correr a 60 FPS estables

pygame.quit()