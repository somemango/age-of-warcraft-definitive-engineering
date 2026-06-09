import pygame
from unidades import Tropa, Generador
from estructuras import Cuartel, Mina, Granja
from habilidades import ArbolHabilidades

TIPOS_EDIFICIO = {
    "Cuartel": Cuartel,
    "Mina": Mina,
    "Granja": Granja,
}

COSTOS_EDIFICIO = {
    "Cuartel": 150,
    "Mina": 100,
    "Granja": 80,
}


class Juego:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.oro = 300
        self.faccion = "sistemas"

        self.mis_unidades = []
        self.estructuras = []

        # Tracking del destino global
        self.ultimo_destino_x = 100
        self.ultimo_destino_y = 100
        self.estado_actual_ordenado = "quieto"

        # Variables para el cuadro de selección
        self.seleccionando = False
        self.inicio_seleccion = (0, 0)
        self.fin_seleccion = (0, 0)

        # Generadores
        self.generador_aliado = Generador(
            100, 100, "sistemas", (0, 125, 0), tiempo_generacion_segundos=3)
        self.generador_enemigo = Generador(
            700, 500, "enemigos", (255, 0, 0), tiempo_generacion_segundos=3)

        # Unidad inicial
        self.mis_unidades.append(Tropa(150, 150, "sistemas", 100, (0, 255, 0)))

        # Estado del menú de construcción
        self.menu_activo = False
        self.opciones_menu = list(TIPOS_EDIFICIO.keys())
        self.edificio_seleccionado = None
        self.preview_pos = (0, 0)

        # Árbol de habilidades
        self.habilidades = ArbolHabilidades(self.faccion, self)

        # Fuentes
        self.fuente = pygame.font.SysFont(None, 22)
        self.fuente_grande = pygame.font.SysFont(None, 28)

    # ------------------------------------------------------------------
    # EVENTOS
    # ------------------------------------------------------------------

    def procesar_eventos(self, event):
        # Abrir/cerrar menú con B
        if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
            if not self.edificio_seleccionado:
                self.menu_activo = not self.menu_activo

        # Cancelar con ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.edificio_seleccionado:
                self.edificio_seleccionado = None
            else:
                self.menu_activo = False

        # Actualizar posición del preview
        if event.type == pygame.MOUSEMOTION:
            self.preview_pos = event.pos
            if self.seleccionando:
                self.fin_seleccion = event.pos

        # Clic izquierdo
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_activo and not self.edificio_seleccionado:
                self._click_menu(event.pos)
            elif self.edificio_seleccionado:
                self._colocar_edificio(event.pos)
            else:
                # Inicio del cuadro de selección
                self.seleccionando = True
                self.inicio_seleccion = event.pos
                self.fin_seleccion = event.pos

        # Soltar clic izquierdo: cerrar cuadro de selección
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.seleccionando:
                self.seleccionando = False
                self.fin_seleccion = event.pos
                self.evaluar_seleccion_multiple()

        # Clic derecho: mover tropas seleccionadas (solo si no hay menú activo)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if not self.menu_activo and not self.edificio_seleccionado:
                mouse_x, mouse_y = event.pos
                self.ultimo_destino_x = mouse_x
                self.ultimo_destino_y = mouse_y
                self.estado_actual_ordenado = "moviendose"

                for unidad in self.mis_unidades:
                    if unidad.faccion == "sistemas" and unidad.seleccionada:
                        unidad.destinoX = mouse_x
                        unidad.destinoY = mouse_y
                        unidad.estado = "moviendose"
                        unidad.tarea = None
                        unidad.objetivo = None

                mouse_x, mouse_y = event.pos
                pos_clic = pygame.math.Vector2(mouse_x, mouse_y)

                # 1. detectar si el jugador le hizo clic a un enemigo
                enemigo_clicado = None
                for unidad in self.mis_unidades:
                    if unidad.faccion == "enemigos":  # si es del bando contrario
                        pos_enemigo = pygame.math.Vector2(unidad.x, unidad.y)
                        # si el clic cayo dentro del radio del círculo del enemigo
                        if (pos_clic - pos_enemigo).length() <= unidad.radio:
                            enemigo_clicado = unidad
                            break

                # 2. repartir la orden a las unidades seleccionadas
                for unidad in self.mis_unidades:
                    if unidad.faccion == "sistemas" and unidad.seleccionada:
                        if enemigo_clicado is not None:
                            # ORDEN MANUAL DE ATAQUE
                            unidad.objetivo_combate = enemigo_clicado
                            unidad.estado = "atacando"
                        else:
                            # ORDEN DE MOVIMIENTO NORMAL
                            unidad.destinoX = mouse_x
                            unidad.destinoY = mouse_y
                            unidad.estado = "moviendose"
                            unidad.objetivo_combate = None # olvida el objetivo anterior si se le ordena caminar

    def _click_menu(self, pos):
        mx, my = pos
        menu_x, menu_y = 10, 40
        ancho_opcion, alto_opcion = 130, 36
        separacion = 8

        for i, nombre in enumerate(self.opciones_menu):
            rect = pygame.Rect(
                menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            if rect.collidepoint(mx, my):
                if self.oro >= COSTOS_EDIFICIO[nombre]:
                    self.edificio_seleccionado = nombre
                    self.menu_activo = False
                break

    def _colocar_edificio(self, pos):
        nombre = self.edificio_seleccionado
        costo = COSTOS_EDIFICIO[nombre]
        if self.oro < costo:
            return

        self.oro -= costo
        nueva = TIPOS_EDIFICIO[nombre](pos[0], pos[1], self.faccion)
        self.estructuras.append(nueva)

        # Manda las tropas seleccionadas a construir
        for unidad in self.mis_unidades:
            if unidad.faccion == "sistemas" and unidad.seleccionada:
                unidad.tarea = "construir"
                unidad.objetivo = nueva
                unidad.destinoX = pos[0]
                unidad.destinoY = pos[1]
                unidad.estado = "moviendose"

        self.edificio_seleccionado = None

    def evaluar_seleccion_multiple(self):
        x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
        x_max = max(self.inicio_seleccion[0], self.fin_seleccion[0])
        y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
        y_max = max(self.inicio_seleccion[1], self.fin_seleccion[1])

        for unidad in self.mis_unidades:
            if unidad.faccion == "sistemas":
                if x_min <= unidad.x <= x_max and y_min <= unidad.y <= y_max:
                    unidad.seleccionada = True
                else:
                    unidad.seleccionada = False

    # ------------------------------------------------------------------
    # ACTUALIZAR
    # ------------------------------------------------------------------

    def actualizar(self):
        self.generador_aliado.actualizar(self.mis_unidades)
        self.generador_enemigo.actualizar(self.mis_unidades)

        # Filtro para mantener vivas solo a las unidades con salud
        self.mis_unidades = [u for u in self.mis_unidades if u.vida > 0]

        for unidad in self.mis_unidades:
            # Si le ordenaste moverse colectivamente
            if unidad.faccion == "sistemas" and unidad.seleccionada:
                if self.estado_actual_ordenado == "moviendose" and unidad.destinoX != self.ultimo_destino_x:
                    unidad.destinoX = self.ultimo_destino_x
                    unidad.destinoY = self.ultimo_destino_y
                    unidad.estado = "moviendose"

            # 🛡️ IA DE AUTODEFENSA (Solo si está quieta y tú no le has dado órdenes manuales)
            if unidad.estado == "quieto" and unidad.objetivo_combate is None:
                enemigo_cercano = unidad.buscar_enemigo_mas_cercano(self.mis_unidades)
                if enemigo_cercano:
                    pos_u = pygame.math.Vector2(unidad.x, unidad.y)
                    pos_e = pygame.math.Vector2(enemigo_cercano.x, enemigo_cercano.y)
                    # Si el enemigo invade su espacio (100 píxeles), se defiende solo
                    if (pos_u - pos_e).length() < 100:
                        unidad.objetivo_combate = enemigo_cercano
                        unidad.estado = "atacando"

            if unidad.objetivo_combate is not None:
                unidad.atacar(self.mis_unidades)

            # Actualizaciones físicas por frame
            unidad.movimiento(self.mis_unidades)
            self._actualizar_tarea(unidad)

        # Corregido: "estructura" en español para que coincida con el for
        for estructura in self.estructuras:
            estructura.actualizar(self)

    def _actualizar_tarea(self, unidad):
        if unidad.estado != "quieto" or unidad.tarea is None:
            return

        if unidad.tarea == "construir" and unidad.objetivo:
            estructura = unidad.objetivo
            if not estructura.construida:
                estructura.recibir_construccion(unidad.velocidad_construccion)
            else:
                unidad.tarea = None
                unidad.objetivo = None

    # ------------------------------------------------------------------
    # DIBUJAR
    # ------------------------------------------------------------------

    def dibujar(self):
        # Generadores (fondo)
        self.generador_aliado.dibujar(self.pantalla)
        self.generador_enemigo.dibujar(self.pantalla)

        # Estructuras construidas/en construcción
        for estructura in self.estructuras:
            estructura.dibujar(self.pantalla, self.fuente)

        # Unidades
        for unidad in self.mis_unidades:
            # Dibujamos el círculo base de la tropa
            unidad.dibujar(self.pantalla)

        # Cuadro de selección
        if self.seleccionando:
            x = min(self.inicio_seleccion[0], self.fin_seleccion[0])
            y = min(self.inicio_seleccion[1], self.fin_seleccion[1])
            ancho = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
            alto = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])
            pygame.draw.rect(self.pantalla, (0, 255, 0),
                             pygame.Rect(x, y, ancho, alto), 1)

        # Preview del edificio a colocar
        if self.edificio_seleccionado:
            self._dibujar_preview()

        # Menú de construcción
        if self.menu_activo:
            self._dibujar_menu()

        # HUD
        self._dibujar_hud()

    def _dibujar_preview(self):
        px, py = self.preview_pos
        superficie = pygame.Surface((60, 60), pygame.SRCALPHA)
        superficie.fill((255, 255, 255, 60))
        pygame.draw.rect(superficie, (200, 200, 255, 120), (0, 0, 60, 60), 2)
        self.pantalla.blit(superficie, (px - 30, py - 30))
        texto = self.fuente.render(
            self.edificio_seleccionado, True, (220, 220, 255))
        self.pantalla.blit(texto, (px - texto.get_width() // 2, py - 50))

    def _dibujar_menu(self):
        menu_x, menu_y = 10, 40
        ancho_opcion, alto_opcion = 130, 36
        separacion = 8

        alto_total = len(self.opciones_menu) * (alto_opcion + separacion) + 36
        fondo = pygame.Surface((150, alto_total), pygame.SRCALPHA)
        fondo.fill((20, 20, 40, 200))
        self.pantalla.blit(fondo, (menu_x - 5, menu_y - 5))

        titulo = self.fuente_grande.render(
            "Construir (B)", True, (200, 200, 255))
        self.pantalla.blit(titulo, (menu_x, menu_y - 28))

        for i, nombre in enumerate(self.opciones_menu):
            rect = pygame.Rect(
                menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            costo = COSTOS_EDIFICIO[nombre]
            puede_pagar = self.oro >= costo
            color_fondo = (40, 80, 40) if puede_pagar else (80, 40, 40)
            color_borde = (100, 200, 100) if puede_pagar else (200, 100, 100)

            pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=6)
            pygame.draw.rect(self.pantalla, color_borde,
                             rect, width=1, border_radius=6)

            texto_nombre = self.fuente.render(nombre, True, (230, 230, 230))
            texto_costo = self.fuente.render(
                f"{costo} oro", True, (200, 180, 80))
            self.pantalla.blit(texto_nombre, (rect.x + 8, rect.y + 5))
            self.pantalla.blit(texto_costo, (rect.x + 8, rect.y + 20))

    def _dibujar_hud(self):
        txt_oro = self.fuente_grande.render(
            f"Oro: {int(self.oro)}", True, (255, 215, 0))
        self.pantalla.blit(
            txt_oro, (self.pantalla.get_width() - txt_oro.get_width() - 10, 10))

        instrucciones = [
            "B - menu construccion",
            "Clic der - mover seleccionadas",
            "ESC - cancelar",
        ]
        for j, linea in enumerate(instrucciones):
            txt = self.fuente.render(linea, True, (180, 180, 180))
            self.pantalla.blit(
                txt, (self.pantalla.get_width() - txt.get_width() - 10, 40 + j * 20))
