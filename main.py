import pygame
import random
import os
from juego import Juego

pygame.init()
pygame.mixer.init()

pantalla = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Selección de Facción de Ingeniería")
reloj = pygame.time.Clock()

facciones_disponibles = ["sistemas", "telecomunicaciones", "civil", "industrial"]
fuente_menu = pygame.font.SysFont(None, 30)
fuente_titulo = pygame.font.SysFont(None, 45)

botones = {}
ancho_btn, alto_btn = 260, 50
x_btn = (800 - ancho_btn) // 2

for i, faccion in enumerate(facciones_disponibles):
    y_btn = 200 + i * (alto_btn + 20)
    botones[faccion] = pygame.Rect(x_btn, y_btn, ancho_btn, alto_btn)

estado = "MENU"  
juego = None
run = True

cancion_actual = None

def reproducir_musica(archivo_cancion):
    global cancion_actual
    if cancion_actual != archivo_cancion:
        try:
            ruta_script = os.path.join(os.path.dirname(__file__), archivo_cancion)
            ruta_consola = os.path.join(os.getcwd(), archivo_cancion)
            ruta_directa = archivo_cancion
            
            ruta_final = None
            if os.path.exists(ruta_script):
                ruta_final = ruta_script
            elif os.path.exists(ruta_consola):
                ruta_final = ruta_consola
            elif os.path.exists(ruta_directa):
                ruta_final = ruta_directa
                
            if ruta_final:
                pygame.mixer.music.load(ruta_final)
                pygame.mixer.music.play(-1)
                cancion_actual = archivo_cancion
            else:
                print(f"No se encontro el archivo. Intentado en:")
                print(f"1: {ruta_script}")
                print(f"2: {ruta_consola}")
        except pygame.error as e:
            print(f"No se pudo cargar el archivo de audio {archivo_cancion}: {e}")

while run:
    if estado == "MENU":
        reproducir_musica("tema menu.mp3")
    elif estado == "JUGANDO":
        reproducir_musica("tema ciclo de juego.mp3")

    eventos = pygame.event.get()
    for event in eventos:
        if event.type == pygame.QUIT:
            run = False

        if estado == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for faccion, rect in botones.items():
                    if rect.collidepoint(mouse_pos):
                        faccion_jugador = faccion
                        faccion_enemigo = random.choice(facciones_disponibles)
                        while faccion_enemigo == faccion_jugador:
                            faccion_enemigo = random.choice(facciones_disponibles)
                        
                        juego = Juego(pantalla, faccion_jugador, faccion_enemigo)
                        estado = "JUGANDO"
                        break

        elif estado == "JUGANDO":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                juego.mostrar_menu_habilidades = not juego.mostrar_menu_habilidades
                continue  

            clic_en_habilidad = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if juego.mostrar_menu_habilidades:
                    for id_hab, rect in juego.rects_habilidades.items():
                        if rect.collidepoint(event.pos):
                            if juego.habilidades.desbloquear(id_hab):
                                print(f"Habilidad '{id_hab}' comprada con éxito.")
                            clic_en_habilidad = True
                            break  

            if not clic_en_habilidad:
                juego.procesar_eventos(event)

    if estado == "MENU":
        pantalla.fill((30, 30, 50))
        txt_titulo = fuente_titulo.render("SELECCIONA TU FACCION", True, (255, 255, 255))
        pantalla.blit(txt_titulo, ((800 - txt_titulo.get_width()) // 2, 80))

        mouse_pos = pygame.mouse.get_pos()
        for faccion, rect in botones.items():
            color = (60, 120, 200) if rect.collidepoint(mouse_pos) else (45, 45, 85)
            pygame.draw.rect(pantalla, color, rect, border_radius=8)
            pygame.draw.rect(pantalla, (100, 200, 255), rect, width=2, border_radius=8)
            txt_btn = fuente_menu.render(faccion.capitalize(), True, (255, 255, 255))
            pantalla.blit(txt_btn, (rect.x + (rect.width - txt_btn.get_width()) // 2,
                                    rect.y + (rect.height - txt_btn.get_height()) // 2))

    elif estado == "JUGANDO":
        juego.actualizar()
        juego.dibujar()

    pygame.display.flip()
    reloj.tick(60)

pygame.mixer.quit()
pygame.quit()