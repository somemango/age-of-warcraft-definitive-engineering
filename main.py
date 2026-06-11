import pygame
import random
import os
from juego import Juego

pygame.init()
pygame.mixer.init()

ANCHO_BASE, ALTO_BASE = 800, 600
pantalla = pygame.display.set_mode((ANCHO_BASE, ALTO_BASE))
pygame.display.set_caption("Selección de Facción de Ingeniería")
reloj = pygame.time.Clock()

facciones_disponibles = ["sistemas", "telecomunicaciones", "civil", "industrial"]
fuente_menu = pygame.font.SysFont(None, 30)
fuente_titulo = pygame.font.SysFont(None, 45)
fuente_controles = pygame.font.SysFont(None, 24)

botones = {}
ancho_btn, alto_btn = 260, 45
x_btn = (ANCHO_BASE - ancho_btn) // 2

for i, faccion in enumerate(facciones_disponibles):
    y_btn = 140 + i * (alto_btn + 12)
    botones[faccion] = pygame.Rect(x_btn, y_btn, ancho_btn, alto_btn)

volumen = 0.5
pygame.mixer.music.set_volume(volumen)

btn_vol_mas = pygame.Rect(260, 430, 50, 40)
btn_vol_menos = pygame.Rect(490, 430, 50, 40)

btn_entendido = pygame.Rect(300, 520, 200, 45)

estado = "MENU"  
juego = None
run = True
faccion_jugador_sel = None
faccion_enemigo_sel = None

mostrar_menu_desplegable = False
ancho_desp, alto_desp = 240, 290
rect_desplegable = pygame.Rect(280, 155, ancho_desp, alto_desp)

btn_desp_reiniciar = pygame.Rect(300, 175, 200, 35)
btn_desp_vol_mas = pygame.Rect(300, 225, 95, 35)
btn_desp_vol_menos = pygame.Rect(405, 225, 95, 35)
btn_desp_menu = pygame.Rect(300, 275, 200, 35)
btn_desp_salir = pygame.Rect(300, 325, 200, 35)

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
        except pygame.error:
            pass

while run:
    if estado == "MENU":
        reproducir_musica("tema menu.mp3")
    elif estado == "CONTROLES":
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
                        faccion_jugador_sel = faccion
                        faccion_enemigo_sel = random.choice(facciones_disponibles)
                        while faccion_enemigo_sel == faccion_jugador_sel:
                            faccion_enemigo_sel = random.choice(facciones_disponibles)
                        estado = "CONTROLES"
                        break
                
                if btn_vol_mas.collidepoint(mouse_pos):
                    volumen = min(1.0, volumen + 0.1)
                    pygame.mixer.music.set_volume(volumen)
                elif btn_vol_menos.collidepoint(mouse_pos):
                    volumen = max(0.0, volumen - 0.1)
                    pygame.mixer.music.set_volume(volumen)

        elif estado == "CONTROLES":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_entendido.collidepoint(event.pos):
                    juego = Juego(pantalla, faccion_jugador_sel, faccion_enemigo_sel)
                    estado = "JUGANDO"

        elif estado == "JUGANDO":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                mostrar_menu_desplegable = not mostrar_menu_desplegable
                continue

            if mostrar_menu_desplegable:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    if btn_desp_reiniciar.collidepoint(mouse_pos):
                        juego = Juego(pantalla, faccion_jugador_sel, faccion_enemigo_sel)
                        mostrar_menu_desplegable = False
                    elif btn_desp_vol_mas.collidepoint(mouse_pos):
                        volumen = min(1.0, volumen + 0.1)
                        pygame.mixer.music.set_volume(volumen)
                    elif btn_desp_vol_menos.collidepoint(mouse_pos):
                        volumen = max(0.0, volumen - 0.1)
                        pygame.mixer.music.set_volume(volumen)
                    elif btn_desp_menu.collidepoint(mouse_pos):
                        estado = "MENU"
                        mostrar_menu_desplegable = False
                        juego = None
                    elif btn_desp_salir.collidepoint(mouse_pos):
                        run = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                juego.mostrar_menu_habilidades = not juego.mostrar_menu_habilidades
                continue  

            clic_en_habilidad = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if juego.mostrar_menu_habilidades:
                    for id_hab, rect in juego.rects_habilidades.items():
                        if rect.collidepoint(event.pos):
                            if juego.habilidades.desbloquear(id_hab):
                                pass
                            clic_en_habilidad = True
                            break  

            if not clic_en_habilidad:
                juego.procesar_eventos(event)

    if estado == "MENU":
        pantalla.fill((30, 30, 50))
        txt_titulo = fuente_titulo.render("SELECCIONA TU FACCION", True, (255, 255, 255))
        pantalla.blit(txt_titulo, ((ANCHO_BASE - txt_titulo.get_width()) // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        for faccion, rect in botones.items():
            color = (60, 120, 200) if rect.collidepoint(mouse_pos) else (45, 45, 85)
            pygame.draw.rect(pantalla, color, rect, border_radius=8)
            pygame.draw.rect(pantalla, (100, 200, 255), rect, width=2, border_radius=8)
            txt_btn = fuente_menu.render(faccion.capitalize(), True, (255, 255, 255))
            pantalla.blit(txt_btn, (rect.x + (rect.width - txt_btn.get_width()) // 2,
                                            rect.y + (rect.height - txt_btn.get_height()) // 2))

        txt_vol = fuente_menu.render(f"Volumen: {int(volumen * 100)}%", True, (200, 200, 200))
        pantalla.blit(txt_vol, ((ANCHO_BASE - txt_vol.get_width()) // 2, 440))

        color_mas = (70, 140, 70) if btn_vol_mas.collidepoint(mouse_pos) else (50, 90, 50)
        pygame.draw.rect(pantalla, color_mas, btn_vol_mas, border_radius=5)
        txt_mas = fuente_menu.render("+", True, (255, 255, 255))
        pantalla.blit(txt_mas, (btn_vol_mas.x + (btn_vol_mas.width - txt_mas.get_width()) // 2,
                                        btn_vol_mas.y + (btn_vol_mas.height - txt_mas.get_height()) // 2))

        color_menos = (140, 70, 70) if btn_vol_menos.collidepoint(mouse_pos) else (90, 50, 50)
        pygame.draw.rect(pantalla, color_menos, btn_vol_menos, border_radius=5)
        txt_menos = fuente_menu.render("-", True, (255, 255, 255))
        pantalla.blit(txt_menos, (btn_vol_menos.x + (btn_vol_menos.width - txt_menos.get_width()) // 2,
                                          btn_vol_menos.y + (btn_vol_menos.height - txt_menos.get_height()) // 2))

    elif estado == "CONTROLES":
        pantalla.fill((25, 25, 40))
        txt_ctrl_titulo = fuente_titulo.render("GUIA DE CONTROLES", True, (255, 255, 255))
        pantalla.blit(txt_ctrl_titulo, ((ANCHO_BASE - txt_ctrl_titulo.get_width()) // 2, 40))

        controles_texto = [
            ("Camara:", "Mueve el cursor hacia los bordes de la pantalla para desplazarte."),
            ("Seleccion masiva:", "Manten presionado Clic Izquierdo y arrastra el cuadro sobre tus tropas."),
            ("Seleccion unica:", "Haz Clic Izquierdo simple directamente sobre una sola unidad."),
            ("Acciones (Mover/Atacar):", "Usa Clic Derecho sobre el terreno o sobre un elemento objetivo."),
            ("Construir estructuras:", "Haz Clic Derecho sobre un plano base colocado previamente."),
            ("Menu de construccion:", "Presiona la tecla B para abrirlo y desplegar opciones."),
            ("Menu de habilidades:", "Presiona la tecla H para gestionarlo."),
            ("Pausa / Desplegable:", "Presiona la tecla Z durante la partida para abrir opciones.")
        ]

        for idx, (accion, desc) in enumerate(controles_texto):
            txt_acc = fuente_controles.render(accion, True, (150, 200, 255))
            txt_desc = fuente_controles.render(desc, True, (230, 230, 230))
            y_pos = 120 + idx * 46
            pantalla.blit(txt_acc, (50, y_pos))
            pantalla.blit(txt_desc, (50, y_pos + 20))

        mouse_pos = pygame.mouse.get_pos()
        color_entendido = (60, 150, 60) if btn_entendido.collidepoint(mouse_pos) else (40, 100, 40)
        pygame.draw.rect(pantalla, color_entendido, btn_entendido, border_radius=8)
        pygame.draw.rect(pantalla, (150, 255, 150), btn_entendido, width=2, border_radius=8)
        txt_ent = fuente_menu.render("Entendido / Jugar", True, (255, 255, 255))
        pantalla.blit(txt_ent, (btn_entendido.x + (btn_entendido.width - txt_ent.get_width()) // 2,
                                        btn_entendido.y + (btn_entendido.height - txt_ent.get_height()) // 2))

    elif estado == "JUGANDO":
        juego.actualizar()
        juego.dibujar()

        if mostrar_menu_desplegable:
            s_sombra = pygame.Surface((ANCHO_BASE, ALTO_BASE), pygame.SRCALPHA)
            s_sombra.fill((0, 0, 0, 100))
            pantalla.blit(s_sombra, (0, 0))

            pygame.draw.rect(pantalla, (40, 40, 60), rect_desplegable, border_radius=10)
            pygame.draw.rect(pantalla, (120, 120, 180), rect_desplegable, width=2, border_radius=10)

            mouse_pos = pygame.mouse.get_pos()

            c_re = (70, 70, 110) if btn_desp_reiniciar.collidepoint(mouse_pos) else (50, 50, 80)
            pygame.draw.rect(pantalla, c_re, btn_desp_reiniciar, border_radius=5)
            t_re = fuente_menu.render("Reiniciar", True, (255, 255, 255))
            pantalla.blit(t_re, (btn_desp_reiniciar.x + (btn_desp_reiniciar.width - t_re.get_width()) // 2,
                                         btn_desp_reiniciar.y + (btn_desp_reiniciar.height - t_re.get_height()) // 2))

            c_v_mas = (70, 120, 70) if btn_desp_vol_mas.collidepoint(mouse_pos) else (50, 90, 50)
            pygame.draw.rect(pantalla, c_v_mas, btn_desp_vol_mas, border_radius=5)
            t_v_mas = fuente_menu.render("Vol +", True, (255, 255, 255))
            pantalla.blit(t_v_mas, (btn_desp_vol_mas.x + (btn_desp_vol_mas.width - t_v_mas.get_width()) // 2,
                                            btn_desp_vol_mas.y + (btn_desp_vol_mas.height - t_v_mas.get_height()) // 2))

            c_v_men = (120, 70, 70) if btn_desp_vol_menos.collidepoint(mouse_pos) else (90, 50, 50)
            pygame.draw.rect(pantalla, c_v_men, btn_desp_vol_menos, border_radius=5)
            t_v_men = fuente_menu.render("Vol -", True, (255, 255, 255))
            pantalla.blit(t_v_men, (btn_desp_vol_menos.x + (btn_desp_vol_menos.width - t_v_men.get_width()) // 2,
                                            btn_desp_vol_menos.y + (btn_desp_vol_menos.height - t_v_men.get_height()) // 2))

            c_me = (70, 70, 110) if btn_desp_menu.collidepoint(mouse_pos) else (50, 50, 80)
            pygame.draw.rect(pantalla, c_me, btn_desp_menu, border_radius=5)
            t_me = fuente_menu.render("Menu Principal", True, (255, 255, 255))
            pantalla.blit(t_me, (btn_desp_menu.x + (btn_desp_menu.width - t_me.get_width()) // 2,
                                         btn_desp_menu.y + (btn_desp_menu.height - t_me.get_height()) // 2))

            c_sa = (100, 40, 40) if btn_desp_salir.collidepoint(mouse_pos) else (70, 30, 30)
            pygame.draw.rect(pantalla, c_sa, btn_desp_salir, border_radius=5)
            t_sa = fuente_menu.render("Cerrar Juego", True, (255, 255, 255))
            pantalla.blit(t_sa, (btn_desp_salir.x + (btn_desp_salir.width - t_sa.get_width()) // 2,
                                         btn_desp_salir.y + (btn_desp_salir.height - t_sa.get_height()) // 2))

    pygame.display.flip()
    reloj.tick(60)

pygame.mixer.quit()
pygame.quit()