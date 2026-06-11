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
    "sistemas":           ("BaseDatos",     BaseDatos,     180, "Oro+, entrena rápido"),
    "civil":              ("Torreta",       Torreta,       220, "Dispara a enemigos"),
    "telecomunicaciones": ("Antena",        Antena,        160, "Ralentiza enemigos"),
    "industrial":         ("MinaMejorada",  MinaMejorada,  200, "Oro ×3, armadura"),
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

        # ------------------------------------------------------------------
        # BASE INICIAL DEL ENEMIGO (ya construidas desde el inicio)
        # ------------------------------------------------------------------
        ex = self.generador_enemigo.x
        ey = self.generador_enemigo.y

        def _base(clase, dx, dy):
            est = clase(ex + dx, ey + dy, self.faccion_enemigo)
            est.progreso = 100
            est.construida = True
            est.al_construirse()
            self.estructuras.append(est)
            return est

        _base(Cuartel, -120, 0)       # Cuartel a la izquierda del generador
        _base(Cuartel,  120, 0)       # Segundo cuartel a la derecha
        _base(Mina,       0, 120)     # Mina debajo
        _base(Granja,  -120, 120)     # Granja diagonal

        # Estructura exclusiva de la facción enemiga (también pre-construida)
        if self.faccion_enemigo in EDIFICIO_EXCLUSIVO:
            _, ClaseExcl, _, _ = EDIFICIO_EXCLUSIVO[self.faccion_enemigo]
            _base(ClaseExcl, 120, 120)

        # Unidades iniciales enemigas (pequeña guardia)
        for dx, dy in [(-60, -60), (0, -80), (60, -60)]:
            t = Tropa(ex + dx, ey + dy, self.faccion_enemigo, 100, (255, 60, 60))
            self.mis_unidades.append(t)

        # ------------------------------------------------------------------
        # ESTADO DE LA IA ENEMIGA
        # ------------------------------------------------------------------
        self.ia_fase = "defender"       # "defender" | "atacar" | "reagrupar"
        self.ia_timer = 0               # Contador de frames
        self.ia_intervalo_ataque = 600  # Lanza oleada cada 10 seg (60fps×10)
        self.ia_punto_rally = (ex - 200, ey - 200)  # Punto de reunión antes de atacar

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

            # 1a. Chequear si hicimos clic sobre el generador enemigo
            if self.generador_enemigo.vida > 0:
                dist_gen = pygame.math.Vector2(mundo_x - self.generador_enemigo.x,
                                               mundo_y - self.generador_enemigo.y).length()
                if dist_gen <= self.generador_enemigo.radio:
                    objetivo_enemigo = self.generador_enemigo

            # 1b. Chequear si hicimos clic sobre una tropa enemiga
            if not objetivo_enemigo:
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
        menu_y = 410
        ancho_opcion = 120
        alto_opcion = 40
        separacion = 10

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
                else:
                    print("No tienes suficiente oro.")

    def actualizar(self):
        self.actualizar_camara()

        self.generador_aliado.actualizar(self.mis_unidades)
        self.generador_enemigo.actualizar(self.mis_unidades)

        # Listas de objetivos separadas para evitar que cada bando ataque su propia base
        objetivos_para_aliados  = self.mis_unidades + [self.generador_enemigo]
        objetivos_para_enemigos = self.mis_unidades + [self.generador_aliado]

        # Lógica de unidades
        for unidad in self.mis_unidades:
            if unidad.faccion == self.faccion:
                unidad.ejecutar_tareas(objetivos_para_aliados)
            else:
                self._mover_tropa_enemiga(unidad, objetivos_para_enemigos)

        # IA del bot (toma decisiones de alto nivel)
        todos_los_objetivos = self.mis_unidades + [self.generador_aliado, self.generador_enemigo]
        self._actualizar_ia_enemiga(todos_los_objetivos)

        for est in self.estructuras:
            est.actualizar(self)

        self.mis_unidades = [u for u in self.mis_unidades if u.vida > 0]

        # Verificar condición de derrota / victoria
        self._verificar_fin_partida()

    # ------------------------------------------------------------------
    # IA ENEMIGA
    # ------------------------------------------------------------------

    def _tropas_enemigas(self):
        return [u for u in self.mis_unidades if u.faccion == self.faccion_enemigo]

    def _tropas_aliadas(self):
        return [u for u in self.mis_unidades if u.faccion == self.faccion]

    def _actualizar_ia_enemiga(self, todos_los_objetivos):
        """Máquina de estados sencilla: defender → reagrupar → atacar → defender."""
        tropas = self._tropas_enemigas()
        aliadas = self._tropas_aliadas()
        self.ia_timer += 1

        ex, ey = self.generador_enemigo.x, self.generador_enemigo.y

        if self.ia_fase == "defender":
            for t in tropas:
                if t.objetivo_combate is None or t.objetivo_combate.vida <= 0:
                    t.objetivo_combate = None
                    intruso = None
                    for a in aliadas:
                        if pygame.math.Vector2(a.x - ex, a.y - ey).length() < 350:
                            intruso = a
                            break
                    if intruso:
                        t.tarea = "atacar"
                        t.objetivo_combate = intruso
                    else:
                        import math
                        idx = tropas.index(t)
                        angulo = (self.ia_timer * 0.01 + idx * (2 * math.pi / max(1, len(tropas))))
                        px = ex + math.cos(angulo) * 120
                        py = ey + math.sin(angulo) * 120
                        if pygame.math.Vector2(t.x - px, t.y - py).length() > 30:
                            t.destinoX = px
                            t.destinoY = py
                            t.estado = "moviendose"
                            t.tarea = None

            if len(tropas) >= 4 and self.ia_timer >= self.ia_intervalo_ataque:
                self.ia_timer = 0
                self.ia_fase = "reagrupar"
                ax, ay = self.generador_aliado.x, self.generador_aliado.y
                self.ia_punto_rally = (
                    int(ex + (ax - ex) * 0.35),
                    int(ey + (ay - ey) * 0.35),
                )

        elif self.ia_fase == "reagrupar":
            rx, ry = self.ia_punto_rally
            listas = 0
            for t in tropas:
                t.tarea = None
                t.objetivo_combate = None
                dist = pygame.math.Vector2(t.x - rx, t.y - ry).length()
                if dist > 60:
                    t.destinoX = rx
                    t.destinoY = ry
                    t.estado = "moviendose"
                else:
                    listas += 1
            if listas >= max(1, int(len(tropas) * 0.7)):
                self.ia_fase = "atacar"

        elif self.ia_fase == "atacar":
            if not tropas:
                self.ia_fase = "defender"
                self.ia_timer = 0
                return

            for t in tropas:
                if t.objetivo_combate is None or t.objetivo_combate.vida <= 0:
                    t.objetivo_combate = None
                    # Buscar tropa aliada primero
                    objetivo = t.buscar_enemigo_mas_cercano(todos_los_objetivos)
                    if objetivo:
                        t.tarea = "atacar"
                        t.objetivo_combate = objetivo
                    else:
                        # Sin tropas visibles: atacar el generador aliado directamente
                        if self.generador_aliado.vida > 0:
                            t.tarea = "atacar"
                            t.objetivo_combate = self.generador_aliado
                        else:
                            t.destinoX = self.generador_aliado.x
                            t.destinoY = self.generador_aliado.y
                            t.estado = "moviendose"
                            t.tarea = None

                t.ejecutar_tareas(todos_los_objetivos)

            if len(tropas) < 2:
                self.ia_fase = "defender"
                self.ia_timer = 0

    def _mover_tropa_enemiga(self, unidad, todos_los_objetivos):
        """Delega el movimiento a ejecutar_tareas, excepto en fase atacar
        (que ya lo maneja _actualizar_ia_enemiga directamente)."""
        if self.ia_fase != "atacar":
            unidad.ejecutar_tareas(todos_los_objetivos)

    def _verificar_fin_partida(self):
        """Muestra mensaje de victoria o derrota cuando cae un generador."""
        if not hasattr(self, "_fin_partida"):
            self._fin_partida = None

        if self._fin_partida:
            return

        if self.generador_enemigo.vida <= 0:
            self._fin_partida = "victoria"
        elif self.generador_aliado.vida <= 0:
            self._fin_partida = "derrota"

    def dibujar(self):
        # 🎥 1. Pintamos nuestro césped gigante desplazado según el movimiento de la cámara
        self.pantalla.blit(self.fondo_visual, (-self.camara_x, -self.camara_y))

        # 2. Dibujamos los generadores (cuarteles centrales) con barra de vida
        self.generador_aliado.dibujar(self.pantalla, self.fuente, self.camara_x, self.camara_y)
        self.generador_enemigo.dibujar(self.pantalla, self.fuente, self.camara_x, self.camara_y)

        # 3. Dibujamos estructuras aplicando la cámara de forma segura
        for est in self.estructuras:
            coord_real_x, coord_real_y = est.x, est.y
            # Las movemos temporalmente a posición de pantalla para usar su propio dibujo interno
            est.x -= self.camara_x
            est.y -= self.camara_y
            est.dibujar(self.pantalla, self.fuente)
            # Restauramos sus coordenadas reales para no alterar la lógica matemática
            est.x, est.y = coord_real_x, coord_real_y

        # 4. Dibujamos las unidades con su propio método (cuerpo + barra de vida + selección)
        for u in self.mis_unidades:
            u.dibujar(self.pantalla, self.camara_x, self.camara_y)

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
                texto_costo = self.fuente.render(f"{costo}o  {desc}", True, (200, 180, 80))
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

        # Indicador de fase de la IA enemiga
        colores_fase = {
            "defender":   (100, 180, 100),
            "reagrupar":  (220, 180,  40),
            "atacar":     (220,  60,  60),
        }
        etiquetas_fase = {
            "defender":  "Enemigo: esperando",
            "reagrupar": "Enemigo: reagrupando...",
            "atacar":    "Enemigo: ¡ATACANDO!",
        }
        fase = getattr(self, "ia_fase", "defender")
        color_fase = colores_fase.get(fase, (200, 200, 200))
        txt_fase = self.fuente.render(etiquetas_fase.get(fase, ""), True, color_fase)
        self.pantalla.blit(txt_fase, (20, 68))

        # Barra de cuenta atrás del próximo ataque (solo en fase defender)
        if fase == "defender":
            intervalo = max(1, self.ia_intervalo_ataque)
            progreso = min(1.0, self.ia_timer / intervalo)
            bx, by, bw, bh = 20, 84, 140, 6
            pygame.draw.rect(self.pantalla, (60, 30, 30), (bx, by, bw, bh), border_radius=3)
            pygame.draw.rect(self.pantalla, (200, 60, 60),
                             (bx, by, int(bw * progreso), bh), border_radius=3)

        # Overlay de fin de partida
        fin = getattr(self, "_fin_partida", None)
        if fin:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.pantalla.blit(overlay, (0, 0))

            fuente_fin = pygame.font.SysFont(None, 72)
            if fin == "victoria":
                txt = fuente_fin.render("¡VICTORIA!", True, (80, 255, 120))
            else:
                txt = fuente_fin.render("DERROTA", True, (255, 80, 80))
            self.pantalla.blit(txt, ((800 - txt.get_width()) // 2, 220))

            sub = self.fuente_grande.render("Cierra la ventana para salir", True, (200, 200, 200))
            self.pantalla.blit(sub, ((800 - sub.get_width()) // 2, 310))