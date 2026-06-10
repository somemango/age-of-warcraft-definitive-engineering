import pygame

from juego import Juego

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

    juego.dibujar()
    pygame.display.flip()

    reloj.tick(60)

pygame.quit()
