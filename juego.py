import pygame
from unidades import Tropa, Generador
from estructuras import Cuartel, Mina, Granja, BaseDatos, Torreta, Antena, MinaMejorada
from habilidades import ArbolHabilidades

# Estructuras disponibles para todas las facciones
TIPOS_EDIFICIO_BASE = {
    "Cuartel": Cuartel,
    "Mina": Mina,
    "Granja": Granja,
}

COSTOS_EDIFICIO_BASE = {
    "Cuartel": 150,
    "Mina": 100,
    "Granja": 80,
}

# Estructura exclusiva por facción: faccion → (nombre_clave, clase, costo, descripcion)
EDIFICIO_EXCLUSIVO = {
    "sistemas":           ("BaseDatos",     BaseDatos,     180, ""),
    "civil":              ("Torreta",       Torreta,       220, ""),
    "telecomunicaciones": ("Antena",        Antena,        160, ""),
    "industrial":         ("MinaMejorada",  MinaMejorada,  200, ""),
}


class Juego:
    def __init__(self, pantalla, faccion_jugador, faccion_enemigo):
        self.pantalla = pantalla
        self.oro = 300
        self.faccion = faccion_jugador
        self.faccion_enemigo = faccion_enemigo

        self.mis_unidades = []
        self.estructuras = []
        self.mostrar_menu_construccion = False

        # =========================================================================
        # 🎥 CONFIGURACIÓN DE CÁMARA Y MAPA GIGANTE PROVISIONAL
        # =========================================================================
        self.ancho_mapa = 2400  # Tu mapa ahora mide 2400 píxeles de ancho
        self.alto_mapa = 1800   # Tu mapa ahora mide 1800 píxeles de alto
        self.camara_x = 0       # Posición horizontal de la cámara
        self.camara_y = 0       # Posición vertical de la cámara

        # Creamos una superficie verde gigante en memoria como fondo provisional
        self.fondo_visual = pygame.Surface((self.ancho_mapa, self.alto_mapa))
        self.fondo_visual.fill((34, 139, 34)) # Verde pasto
        
        # Dibujamos una cuadrícula cada 100 píxeles para notar el movimiento del scroll
        for x in range(0, self.ancho_mapa, 100):
            pygame.draw.line(self.fondo_visual, (45, 150, 45), (x, 0), (x, self.alto_mapa), 2)
        for y in range(0, self.alto_mapa, 100):
            pygame.draw.line(self.fondo_visual, (45, 150, 45), (0, y), (self.ancho_mapa, y), 2)
        # =========================================================================

        # Tracking del destino global
        self.ultimo_destino_x = 100
        self.ultimo_destino_y = 100
        self.estado_actual_ordenado = "quieto"

        # Variables para el cuadro de selección
        self.seleccionando = False
        self.inicio_seleccion = (0, 0)
        self.fin_seleccion = (0, 0)

        # Generadores configurados dinámicamente con las facciones elegidas
        self.generador_aliado = Generador(
            100, 100, self.faccion, (0, 125, 0), tiempo_generacion_segundos=3)
        self.generador_enemigo = Generador(
            2200, 1600, self.faccion_enemigo, (255, 0, 0), tiempo_generacion_segundos=3)

        # Unidad inicial usando la facción del jugador
        self.mis_unidades.append(
            Tropa(150, 150, self.faccion, 100, (0, 255, 0)))

        # Inicializar árbol de habilidades
        self.habilidades = ArbolHabilidades(self.faccion, self)

        # Construir catálogo de edificios: base + exclusivo de la facción
        self.tipos_edificio = dict(TIPOS_EDIFICIO_BASE)
        self.costos_edificio = dict(COSTOS_EDIFICIO_BASE)
        self.descripciones_edificio = {
            "Cuartel": "Entrena tropas",
            "Mina": "Genera oro",
            "Granja": "+5 límite tropas",
        }
        if self.faccion in EDIFICIO_EXCLUSIVO:
            nombre, clase, costo, desc = EDIFICIO_EXCLUSIVO[self.faccion]
            self.tipos_edificio[nombre] = clase
            self.costos_edificio[nombre] = costo
            self.descripciones_edificio[nombre] = desc

        # Fuentes
        self.fuente = pygame.font.SysFont(None, 20)
        self.fuente_grande = pygame.font.SysFont(None, 28)

    def actualizar_camara(self):
        """Mueve la cámara de forma automática si el mouse toca los bordes de la pantalla."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        velocidad_camara = 6

        # Desplazamiento horizontal (borde izquierdo o derecho)
        if mouse_x < 20:
            self.camara_x -= velocidad_camara
        elif mouse_x > 780:  # 800 de pantalla - 20 de margen
            self.camara_x += velocidad_camara

        # Desplazamiento vertical (borde superior o inferior)
        if mouse_y < 20:
            self.camara_y -= velocidad_camara
        elif mouse_y > 580:  # 600 de pantalla - 20 de margen
            self.camara_y += velocidad_camara

        # Limitamos la cámara para que nunca muestre el vacío fuera del mapa gigante
        self.camara_x = max(0, min(self.camara_x, self.ancho_mapa - 800))
        self.camara_y = max(0, min(self.camara_y, self.alto_mapa - 600))

    def procesar_eventos(self, event):
        # 🆕 1. Detectar si se presiona la tecla 'B' para abrir/cerrar el menú
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.mostrar_menu_construccion = not self.mostrar_menu_construccion

        # --- CLIC IZQUIERDO: SELECCIÓN ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Si el clic es en la interfaz del menú, no arrastramos el cuadro de selección
            if event.pos[0] > 650 and event.pos[1] > 400:
                self._procesar_clic_menu(event.pos)
                return

            self.seleccionando = True
            # Convertimos la posición de la pantalla a coordenadas reales del mapa gigante
            self.inicio_seleccion = (event.pos[0] + self.camara_x, event.pos[1] + self.camara_y)
            self.fin_seleccion = self.inicio_seleccion

        elif event.type == pygame.MOUSEMOTION and self.seleccionando:
            # Guardamos la posición del arrastre en coordenadas reales
            self.fin_seleccion = (event.pos[0] + self.camara_x, event.pos[1] + self.camara_y)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.seleccionando:
                self.seleccionando = False

                x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
                x_max = max(self.inicio_seleccion[0], self.fin_seleccion[0])
                y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
                y_max = max(self.inicio_seleccion[1], self.fin_seleccion[1])

                # Si el arrastre es milimétrico, se procesa como un clic simple
                es_clic_simple = (x_max - x_min < 5) and (y_max - y_min < 5)

                for u in self.mis_unidades:
                    if u.faccion == self.faccion:
                        if es_clic_simple:
                            # Clic simple: medimos distancia con el radio de la unidad
                            dist = ((u.x - x_min) ** 2 + (u.y - y_min) ** 2) ** 0.5
                            u.seleccionada = (dist <= u.radio)
                        else:
                            # Selección por cuadro en el mapa gigante
                            u.seleccionada = (x_min <= u.x <= x_max and y_min <= u.y <= y_max)

        # --- CLIC DERECHO: ACCIONES Y MOVIMIENTO ---
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos
            mundo_x = mouse_x + self.camara_x
            mundo_y = mouse_y + self.camara_y
            self.ultimo_destino_x = mundo_x
            self.ultimo_destino_y = mundo_y

            objetivo_enemigo = None
            objetivo_estructura = None

            # 1. Chequear si hicimos clic sobre un enemigo
            for unidad in self.mis_unidades:
                if unidad.faccion == self.faccion_enemigo and unidad.vida > 0:
                    distancia = pygame.math.Vector2(mundo_x - unidad.x, mundo_y - unidad.y).length()
                    if distancia <= unidad.radio:
                        objetivo_enemigo = unidad
                        break

            # 2. Chequear si hicimos clic sobre una estructura sin terminar
            if not objetivo_enemigo:
                for est in self.estructuras:
                    # Chequeo de colisión simple (ajusta según tu lógica)
                    if est.x - 25 <= mundo_x <= est.x + 25 and est.y - 25 <= mundo_y <= est.y + 25:
                        if not est.construida:
                            objetivo_estructura = est
                            break

            # 3. Mandar la orden a todas las unidades aliadas seleccionadas
            for tropa in self.mis_unidades:
                if tropa.seleccionada and tropa.faccion == self.faccion:
                    if objetivo_enemigo:
                        # ¡A la guerra!
                        tropa.tarea = "atacar"
                        tropa.objetivo_combate = objetivo_enemigo
                        tropa.objetivo = None # Borrar orden de construcción si la tenía
                    elif objetivo_estructura:
                        # ¡A trabajar!
                        tropa.tarea = "construir"
                        tropa.objetivo = objetivo_estructura
                        tropa.objetivo_combate = None
                    else:
                        # Simplemente caminar
                        tropa.tarea = None
                        tropa.objetivo = None
                        tropa.objetivo_combate = None
                        tropa.destinoX = mundo_x
                        tropa.destinoY = mundo_y
                        tropa.estado = "moviendose"

    def _procesar_clic_menu(self, pos):
        menu_x = 660
        menu_y = 380
        ancho_opcion = 130
        alto_opcion = 44
        separacion = 8

        opciones = list(self.tipos_edificio.keys())
        for i, nombre in enumerate(opciones):
            rect = pygame.Rect(menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            if rect.collidepoint(pos):
                costo = self.costos_edificio[nombre]
                if self.oro >= costo:
                    self.oro -= costo
                    ClaseEstructura = self.tipos_edificio[nombre]

                    nueva_est = ClaseEstructura(self.ultimo_destino_x, self.ultimo_destino_y, self.faccion)
                    self.estructuras.append(nueva_est)
                    print(f"Comprado {nombre}. Oro restante: {self.oro}")

                    for u in self.mis_unidades:
                        if u.seleccionada and u.faccion == self.faccion:
                            u.objetivo = nueva_est
                            u.tarea = "construir"
                            u.destinoX = nueva_est.x
                            u.destinoY = nueva_est.y
                            u.estado = "moviendose"
                    break
                else:
                    print("No tienes suficiente oro.")

    def actualizar(self):
        # ⚔️ Lógica de combate y movimiento corregida
        # 🎥 Movemos la cámara
        self.actualizar_camara()

        self.generador_aliado.actualizar(self.mis_unidades)
        self.generador_enemigo.actualizar(self.mis_unidades)

        # ⚔️ Lógica maestra
        for unidad in self.mis_unidades:
            if unidad.faccion == self.faccion:
                # Tus tropas solo hacen lo que tú les ordenes
                unidad.ejecutar_tareas(self.mis_unidades)
            else:
                # Los enemigos tienen IA automática: buscan y atacan
                enemigo = unidad.buscar_enemigo_mas_cercano(self.mis_unidades)
                if enemigo:
                    unidad.tarea = "atacar"
                    unidad.objetivo_combate = enemigo
                    unidad.ejecutar_tareas(self.mis_unidades)

        for est in self.estructuras:
            est.actualizar(self)

        self.mis_unidades = [u for u in self.mis_unidades if u.vida > 0]

    def dibujar(self):
        # 🎥 1. Pintamos nuestro césped gigante desplazado según el movimiento de la cámara
        self.pantalla.blit(self.fondo_visual, (-self.camara_x, -self.camara_y))

        # 2. Dibujamos las bases (generadores) restando la posición de la cámara
        pygame.draw.rect(self.pantalla, self.generador_aliado.color,
                         (self.generador_aliado.x - 20 - self.camara_x, self.generador_aliado.y - 20 - self.camara_y, 40, 40))
        pygame.draw.rect(self.pantalla, self.generador_enemigo.color,
                         (self.generador_enemigo.x - 20 - self.camara_x, self.generador_enemigo.y - 20 - self.camara_y, 40, 40))

        # 3. Dibujamos estructuras aplicando la cámara de forma segura
        for est in self.estructuras:
            coord_real_x, coord_real_y = est.x, est.y
            # Las movemos temporalmente a posición de pantalla para usar su propio dibujo interno
            est.x -= self.camara_x
            est.y -= self.camara_y
            est.dibujar(self.pantalla, self.fuente)
            # Restauramos sus coordenadas reales para no alterar la lógica matemática
            est.x, est.y = coord_real_x, coord_real_y

        # 4. Dibujamos las unidades restándoles la posición de la cámara
        for u in self.mis_unidades:
            screen_x = int(u.x - self.camara_x)
            screen_y = int(u.y - self.camara_y)

            # Optimización básica: solo dibujamos si se encuentran visibles dentro de la ventana
            if -30 <= screen_x <= 830 and -30 <= screen_y <= 630:
                pygame.draw.circle(self.pantalla, u.color, (screen_x, screen_y), u.radio)

                # Dibujamos el anillo circular blanco si la unidad está seleccionada
                if u.seleccionada and u.faccion == self.faccion:
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (screen_x, screen_y), u.radio + 2, 1)

        # 5. Dibujamos el cuadro blanco de arrastre visual (si el jugador está seleccionando)
        if self.seleccionando:
            # 1. Encontrar la esquina superior izquierda real de la selección
            x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
            y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])

            # 2. Calcular el ancho y alto asegurándote de que sean positivos
            ancho_abs = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
            alto_abs = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])

            # 3. Si estás aplicando la cámara para dibujarlo en el mapa (coordenadas del mundo):
            visual_x = x_min - self.camara_x
            visual_y = y_min - self.camara_y
            visual_w = ancho_abs
            visual_h = alto_abs

            visual_x = x_min - self.camara_x
            visual_y = y_min - self.camara_y
            visual_w = ancho_abs
            visual_h = alto_abs

            pygame.draw.rect(self.pantalla, (255, 255, 255), (visual_x, visual_y, visual_w, visual_h), 1)

        # 6. INTERFAZ ESTÁTICA: El HUD y el menú de construcción se quedan fijos en la pantalla
        self._dibujar_hud()

        # 🆕 Solo se dibuja si el jugador presionó la 'B'
        if self.mostrar_menu_construccion:
            self._dibujar_menu_construccion()

    def _dibujar_menu_construccion(self):
        menu_x = 660
        menu_y = 380
        ancho_opcion = 130
        alto_opcion = 44
        separacion = 8

        # Nombre de la estructura exclusiva de esta facción (si la hay)
        exclusivo_nombre = None
        if self.faccion in EDIFICIO_EXCLUSIVO:
            exclusivo_nombre = EDIFICIO_EXCLUSIVO[self.faccion][0]

        opciones = list(self.tipos_edificio.keys())
        for i, nombre in enumerate(opciones):
            rect = pygame.Rect(menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            costo = self.costos_edificio[nombre]
            desc = self.descripciones_edificio.get(nombre, "")
            puede_pagar = self.oro >= costo
            es_exclusivo = (nombre == exclusivo_nombre)

            # Color especial para la estructura de facción
            if es_exclusivo:
                color_fondo = (60, 40, 80) if puede_pagar else (80, 40, 40)
                color_borde = (200, 100, 255) if puede_pagar else (200, 100, 100)
            else:
                color_fondo = (40, 80, 40) if puede_pagar else (80, 40, 40)
                color_borde = (100, 200, 100) if puede_pagar else (200, 100, 100)

            pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=6)
            pygame.draw.rect(self.pantalla, color_borde, rect, width=1, border_radius=6)

            # Etiqueta "EXCLUSIVO" en pequeño
            if es_exclusivo:
                tag = self.fuente.render("★ EXCLUSIVO", True, (200, 140, 255))
                self.pantalla.blit(tag, (rect.x + 4, rect.y + 1))
                texto_nombre = self.fuente.render(nombre, True, (230, 200, 255))
                texto_costo = self.fuente.render(f"{costo} oro  {desc}", True, (200, 180, 80))
                self.pantalla.blit(texto_nombre, (rect.x + 4, rect.y + 13))
                self.pantalla.blit(texto_costo, (rect.x + 4, rect.y + 27))
            else:
                texto_nombre = self.fuente.render(nombre, True, (230, 230, 230))
                texto_costo = self.fuente.render(f"{costo} oro  {desc}", True, (200, 180, 80))
                self.pantalla.blit(texto_nombre, (rect.x + 6, rect.y + 5))
                self.pantalla.blit(texto_costo, (rect.x + 6, rect.y + 22))

    def _dibujar_hud(self):
        txt_oro = self.fuente_grande.render(f"Oro: {int(self.oro)}", True, (255, 215, 0))
        self.pantalla.blit(txt_oro, (20, 20))

        txt_facciones = self.fuente.render(
            f"{self.faccion.capitalize()} vs {self.faccion_enemigo.capitalize()}", True, (255, 255, 255))
        self.pantalla.blit(txt_facciones, (20, 48))
