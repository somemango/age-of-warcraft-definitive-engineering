import pygame
import random
from juego import Juego

pygame.init()
pantalla = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Selección de Facción de Ingeniería")
reloj = pygame.time.Clock()

# --- Configuración del Menú ---
facciones_disponibles = ["sistemas", "telecomunicaciones", "civil", "industrial"]
fuente_menu = pygame.font.SysFont(None, 30)
fuente_titulo = pygame.font.SysFont(None, 45)

# Crear rectángulos para los botones
botones = {}
ancho_btn, alto_btn = 260, 50
x_btn = (800 - ancho_btn) // 2

for i, faccion in enumerate(facciones_disponibles):
    y_btn = 200 + i * (alto_btn + 20)
    botones[faccion] = pygame.Rect(x_btn, y_btn, ancho_btn, alto_btn)

# --- Variables de Estado del Flujo Principal ---
estado = "MENU"  # Valores posibles: "MENU" o "JUGANDO"
juego = None
run = True

# --- Bucle Principal en main.py ---
# --- Bucle Principal en main.py ---
while run:
    eventos = pygame.event.get()
    for event in eventos:
        if event.type == pygame.QUIT:
            run = False

        # =========================================================================
        # 🖥️ ESTADO: MENÚ DE INICIO
        # =========================================================================
        if estado == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for faccion, rect in botones.items():
                    if rect.collidepoint(mouse_pos):
                        faccion_jugador = faccion
                        # El enemigo elige una facción aleatoria distinta
                        faccion_enemigo = random.choice(facciones_disponibles)
                        while faccion_enemigo == faccion_jugador:
                            faccion_enemigo = random.choice(facciones_disponibles)
                        
                        # Inicializamos la partida con total seguridad
                        juego = Juego(pantalla, faccion_jugador, faccion_enemigo)
                        estado = "JUGANDO"
                        break

        # =========================================================================
        # ⚔️ ESTADO: EN PARTIDA (JUGANDO)
        # =========================================================================
        elif estado == "JUGANDO":
            # 1. Teclado: Abrir/Cerrar menú de habilidades con la 'H'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                juego.mostrar_menu_habilidades = not juego.mostrar_menu_habilidades
                continue  # Pasamos al siguiente evento

            # 2. Interceptamos clics izquierdos si el menú de habilidades está abierto
            clic_en_habilidad = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if juego.mostrar_menu_habilidades:
                    for id_hab, rect in juego.rects_habilidades.items():
                        if rect.collidepoint(event.pos):
                            if juego.habilidades.desbloquear(id_hab):
                                print(f"Habilidad '{id_hab}' comprada con éxito.")
                            clic_en_habilidad = True
                            break  # Rompemos el ciclo de botones de habilidades

            # 3. Si NO fue un clic en el menú de habilidades, se lo enviamos al juego normal
            # Aquí entran la selección de unidades, movimiento con clic derecho, scroll, etc.
            if not clic_en_habilidad:
                juego.procesar_eventos(event)

    # --- Actualización y renderizado según el estado ---
    if estado == "MENU":
        pantalla.fill((30, 30, 50))

        # Título
        txt_titulo = fuente_titulo.render("SELECCIONA TU FACCION", True, (255, 255, 255))
        pantalla.blit(txt_titulo, ((800 - txt_titulo.get_width()) // 2, 80))

        # Botones
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

pygame.quit()