import pygame
import time
from unidades import Tropa, Generador
from estructuras import Cuartel, Mina, Granja, BaseDatos, Torreta, Antena, MinaMejorada
from habilidades import ArbolHabilidades

TIPOS_EDIFICIO_BASE = {"Cuartel": Cuartel, "Mina": Mina, "Granja": Granja}
COSTOS_EDIFICIO_BASE = {"Cuartel": 150, "Mina": 100, "Granja": 80}

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

        # ⏱️ CONTROL DE TIEMPO Y ESCALADO
        self.tiempo_inicio = time.time()
        self.fase_dificultad_actual = 0  

        self.mis_unidades = []
        self.estructuras = []
        
        # 🛠️ CORRECCIÓN: Declaramos las variables del menú de habilidades que pide main.py
        self.mostrar_menu_construccion = False
        self.mostrar_menu_habilidades = False
        self.rects_habilidades = {}

        self.ancho_mapa = 2400  
        self.alto_mapa = 1800   
        self.camara_x = 0       
        self.camara_y = 0       

        self.fondo_visual = pygame.Surface((self.ancho_mapa, self.alto_mapa))
        self.fondo_visual.fill((34, 139, 34)) 
        
        for x in range(0, self.ancho_mapa, 100):
            pygame.draw.line(self.fondo_visual, (45, 150, 45), (x, 0), (x, self.alto_mapa), 2)
        for y in range(0, self.alto_mapa, 100):
            pygame.draw.line(self.fondo_visual, (45, 150, 45), (0, y), (self.ancho_mapa, y), 2)

        self.ultimo_destino_x = 100
        self.ultimo_destino_y = 100
        self.seleccionando = False
        self.inicio_seleccion = (0, 0)
        self.fin_seleccion = (0, 0)

        # Configuración Generador Aliado
        self.generador_aliado = Generador(100, 100, self.faccion, (0, 125, 0), tiempo_generacion_segundos=3, dano_unidades=10)
        
        # 🔴 GENERADOR ENEMIGO: Al principio genera lento (cada 6 segundos) y hace 5 de daño
        self.generador_enemigo = Generador(2200, 1600, "enemigo", (255, 0, 0), tiempo_generacion_segundos=6.0, dano_unidades=5)

        self.mis_unidades.append(Tropa(150, 150, self.faccion, 100, (0, 255, 0)))
        self.habilidades = ArbolHabilidades(self.faccion, self)

        # Construcciones Iniciales Enemigas
        ex = self.generador_enemigo.x
        ey = self.generador_enemigo.y

        def _base(clase, dx, dy):
            est = clase(ex + dx, ey + dy, "enemigo")
            est.progreso = 100
            est.construida = True
            est.al_construirse()
            self.estructuras.append(est)

        _base(Cuartel, -120, 0)       
        _base(Cuartel,  120, 0)       
        _base(Mina,       0, 120)     
        _base(Granja,  -120, 120)     

        if self.faccion_enemigo in EDIFICIO_EXCLUSIVO:
            _, ClaseExcl, _, _ = EDIFICIO_EXCLUSIVO[self.faccion_enemigo]
            _base(ClaseExcl, 120, 120)

        # Guardia Inicial Enemiga
        for dx, dy in [(-60, -60), (0, -80), (60, -60)]:
            t = Tropa(ex + dx, ey + dy, "enemigo", 100, (255, 60, 60))
            t.dano = 5
            self.mis_unidades.append(t)

        self.ia_fase = "defender"       
        self.ia_timer = 0               
        self.ia_intervalo_ataque = 600  
        self.ia_punto_rally = (ex - 200, ey - 200)  

        self.tipos_edificio = dict(TIPOS_EDIFICIO_BASE)
        self.costos_edificio = dict(COSTOS_EDIFICIO_BASE)
        self.descripciones_edificio = {
            "Cuartel": "Entrena tropas",
            "Mina": "Genera oro",
            "Granja": "+5 límite tropas",
        }
        # Los edificios exclusivos que requieren habilidad se desbloquean
        # a través del árbol. Solo los que NO requieren habilidad se agregan aquí.
        # Ver _desbloquear_edificio_exclusivo() que lo llaman los efectos de habilidad.
        EXCLUSIVOS_SIN_HABILIDAD = {}  # ninguno arranca desbloqueado por defecto
        # (reservado para futura configuración por facción)

        self.fuente = pygame.font.SysFont(None, 20)
        self.fuente_grande = pygame.font.SysFont(None, 28)

        # valores por defecto de las habilidades
        self.mod_danno = 1.0
        self.mod_entrena = 1.0
        self.mod_vida_tropas = 1.0
        self.mod_planificacion_urbana = 1.0
        self.mod_mejor_mina = 1.0
        self.mod_linea_ensamblaje = 1.0
        self.mod_manufactura = 1.0
        self.mod_antena_amplificadora = 1.0
        self.mod_banda_ancha = 1.0
        self.timer_antena_suprema = 0
        self.mod_base_datos = False
        self.mod_torreta_cemento = False

    def _desbloquear_edificio_exclusivo(self):
        """Agrega el edificio exclusivo de la facción al menú de construcción.
        Solo se llama desde los efectos de habilidad que lo requieren."""
        if self.faccion in EDIFICIO_EXCLUSIVO:
            nombre, clase, costo, desc = EDIFICIO_EXCLUSIVO[self.faccion]
            if nombre not in self.tipos_edificio:
                self.tipos_edificio[nombre] = clase
                self.costos_edificio[nombre] = costo
                self.descripciones_edificio[nombre] = desc

    def actualizar_camara(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        velocidad_camara = 6
        if mouse_x < 20: self.camara_x -= velocidad_camara
        elif mouse_x > 780: self.camara_x += velocidad_camara
        if mouse_y < 20: self.camara_y -= velocidad_camara
        elif mouse_y > 580: self.camara_y += velocidad_camara

        self.camara_x = max(0, min(self.camara_x, self.ancho_mapa - 800))
        self.camara_y = max(0, min(self.camara_y, self.alto_mapa - 600))

    def _gestionar_escalado_dificultad(self, minutos):
        """Ajusta dinámicamente la velocidad de spawn y el daño enemigo basado en el tiempo."""
        if minutos >= 15 and self.fase_dificultad_actual < 3:
            self.fase_dificultad_actual = 3
            self.generador_enemigo.cooldown = 1.5      
            self.generador_enemigo.dano_unidades = 22  
        elif minutos >= 10 and self.fase_dificultad_actual < 2:
            self.fase_dificultad_actual = 2
            self.generador_enemigo.cooldown = 2.5      
            self.generador_enemigo.dano_unidades = 15  
        elif minutos >= 5 and self.fase_dificultad_actual < 1:
            self.fase_dificultad_actual = 1
            self.generador_enemigo.cooldown = 4.0      
            self.generador_enemigo.dano_unidades = 10  

    def actualizar(self):
        self.actualizar_camara()

        tiempo_transcurrido = time.time() - self.tiempo_inicio
        minutos = int(tiempo_transcurrido // 60)
        self._gestionar_escalado_dificultad(minutos)

        self.generador_aliado.actualizar(self.mis_unidades, self)
        self.generador_enemigo.actualizar(self.mis_unidades, self)

        objetivos_para_aliados  = self.mis_unidades + [self.generador_enemigo]
        objetivos_para_enemigos = self.mis_unidades + [self.generador_aliado]

        for unidad in self.mis_unidades:
            if unidad.faccion == self.faccion:
                unidad.ejecutar_tareas(objetivos_para_aliados)
            else:
                self._mover_tropa_enemiga(unidad, objetivos_para_enemigos)

        todos_los_objetivos = self.mis_unidades + [self.generador_aliado, self.generador_enemigo]
        self._actualizar_ia_enemiga(todos_los_objetivos)

        for est in self.estructuras:
            est.actualizar(self)

        self.mis_unidades = [u for u in self.mis_unidades if u.vida > 0]
        self._verificar_fin_partida()

    def procesar_eventos(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.mostrar_menu_construccion = not self.mostrar_menu_construccion

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] > 650 and event.pos[1] > 400:
                self._procesar_clic_menu(event.pos)
                return
            self.seleccionando = True
            self.inicio_seleccion = (event.pos[0] + self.camara_x, event.pos[1] + self.camara_y)
            self.fin_seleccion = self.inicio_seleccion

        elif event.type == pygame.MOUSEMOTION and self.seleccionando:
            self.fin_seleccion = (event.pos[0] + self.camara_x, event.pos[1] + self.camara_y)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.seleccionando:
                self.seleccionando = False
                x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
                x_max = max(self.inicio_seleccion[0], self.fin_seleccion[0])
                y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
                y_max = max(self.inicio_seleccion[1], self.fin_seleccion[1])
                es_clic_simple = (x_max - x_min < 5) and (y_max - y_min < 5)

                for u in self.mis_unidades:
                    if u.faccion == self.faccion:
                        if es_clic_simple:
                            dist = ((u.x - x_min) ** 2 + (u.y - y_min) ** 2) ** 0.5
                            u.seleccionada = (dist <= u.radio)
                        else:
                            u.seleccionada = (x_min <= u.x <= x_max and y_min <= u.y <= y_max)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos
            mundo_x = mouse_x + self.camara_x
            mundo_y = mouse_y + self.camara_y
            self.ultimo_destino_x = mundo_x
            self.ultimo_destino_y = mundo_y

            objetivo_enemigo = None
            objetivo_estructura = None

            if self.generador_enemigo.vida > 0:
                dist_gen = pygame.math.Vector2(mundo_x - self.generador_enemigo.x, mundo_y - self.generador_enemigo.y).length()
                if dist_gen <= self.generador_enemigo.radio:
                    objetivo_enemigo = self.generador_enemigo

            if not objetivo_enemigo:
                for unidad in self.mis_unidades:
                    if unidad.faccion == "enemigo" and unidad.vida > 0:
                        distancia = pygame.math.Vector2(mundo_x - unidad.x, mundo_y - unidad.y).length()
                        if distancia <= unidad.radio:
                            objetivo_enemigo = unidad
                            break

            if not objetivo_enemigo:
                for est in self.estructuras:
                    if est.x - 25 <= mundo_x <= est.x + 25 and est.y - 25 <= mundo_y <= est.y + 25:
                        if not est.construida:
                            objetivo_estructura = est
                            break

            for tropa in self.mis_unidades:
                if tropa.seleccionada and tropa.faccion == self.faccion:
                    if objetivo_enemigo:
                        tropa.tarea = "atacar"
                        tropa.objetivo_combate = objetivo_enemigo
                        tropa.objetivo = None 
                    elif objetivo_estructura:
                        tropa.tarea = "construir"
                        tropa.objetivo = objetivo_estructura
                        tropa.objetivo_combate = None
                    else:
                        tropa.tarea = None
                        tropa.objetivo = None
                        tropa.objetivo_combate = None
                        tropa.destinoX = mundo_x
                        tropa.destinoY = mundo_y
                        tropa.estado = "moviendose"

    def _procesar_clic_menu(self, pos):
        menu_x, menu_y = 660, 410
        ancho_opcion, alto_opcion, separacion = 120, 40, 10
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
                    for u in self.mis_unidades:
                        if u.seleccionada and u.faccion == self.faccion:
                            u.objetivo = nueva_est
                            u.tarea = "construir"
                            u.destinoX = nueva_est.x
                            u.destinoY = nueva_est.y
                            u.estado = "moviendose"

    def _tropas_enemigas(self):
        return [u for u in self.mis_unidades if u.faccion == "enemigo"]

    def _tropas_aliadas(self):
        return [u for u in self.mis_unidades if u.faccion == self.faccion]

    def _actualizar_ia_enemiga(self, todos_los_objetivos):
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
                self.ia_punto_rally = (int(ex + (ax - ex) * 0.35), int(ey + (ay - ey) * 0.35))

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
                else: listas += 1
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
                    objetivo = t.buscar_enemigo_mas_cercano(todos_los_objetivos)
                    if objetivo:
                        t.tarea = "atacar"
                        t.objetivo_combate = objetivo
                    else:
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
        if self.ia_fase != "atacar":
            unidad.ejecutar_tareas(todos_los_objetivos)

    def _verificar_fin_partida(self):
        if not hasattr(self, "_fin_partida"): self._fin_partida = None
        if self._fin_partida: return
        if self.generador_enemigo.vida <= 0: self._fin_partida = "victoria"
        elif self.generador_aliado.vida <= 0: self._fin_partida = "derrota"

    def dibujar(self):
        self.pantalla.blit(self.fondo_visual, (-self.camara_x, -self.camara_y))
        self.generador_aliado.dibujar(self.pantalla, self.fuente, self.camara_x, self.camara_y)
        self.generador_enemigo.dibujar(self.pantalla, self.fuente, self.camara_x, self.camara_y)

        for est in self.estructuras:
            coord_real_x, coord_real_y = est.x, est.y
            est.x -= self.camara_x
            est.y -= self.camara_y
            est.dibujar(self.pantalla, self.fuente)
            est.x, est.y = coord_real_x, coord_real_y

        for u in self.mis_unidades:
            u.dibujar(self.pantalla, self.camara_x, self.camara_y)

        if self.seleccionando:
            x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
            y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
            ancho_abs = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
            alto_abs = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])
            pygame.draw.rect(self.pantalla, (255, 255, 255), (x_min - self.camara_x, y_min - self.camara_y, ancho_abs, alto_abs), 1)

        self._dibujar_hud()
        if self.mostrar_menu_construccion:
            self._dibujar_menu_construccion()
            
        # 🛠️ CORRECCIÓN: Renderizar árbol si está activo para evitar comportamientos fantasma
        if self.mostrar_menu_habilidades:
            self._dibujar_arbol_habilidades()

    def _dibujar_arbol_habilidades(self):
        """Dibuja el árbol de habilidades interactivo de la facción del jugador."""
        PANEL_X, PANEL_Y = 100, 80
        PANEL_W, PANEL_H = 600, 460
        CARD_W, CARD_H = 170, 70
        COLS = 3
        PAD_X, PAD_Y = 20, 20
        START_X = PANEL_X + PAD_X
        START_Y = PANEL_Y + 54

        # Fondo semitransparente
        overlay = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        overlay.fill((20, 20, 45, 220))
        self.pantalla.blit(overlay, (PANEL_X, PANEL_Y))
        pygame.draw.rect(self.pantalla, (100, 100, 200),
                         (PANEL_X, PANEL_Y, PANEL_W, PANEL_H), 2, border_radius=8)

        # Título
        txt_titulo = self.fuente_grande.render(
            f"ÁRBOL DE HABILIDADES — {self.faccion.upper()}  [H para cerrar]",
            True, (200, 200, 255))
        self.pantalla.blit(txt_titulo, (PANEL_X + 10, PANEL_Y + 10))

        estado_habs = self.habilidades.estado()
        self.rects_habilidades = {}

        COLORES = {
            "activa":      {"fondo": (30, 80, 30),  "borde": (80, 220, 80),  "texto": (150, 255, 150)},
            "disponible":  {"fondo": (50, 50, 100), "borde": (120, 120, 255),"texto": (200, 200, 255)},
            "bloqueada":   {"fondo": (40, 40, 40),  "borde": (80, 80, 80),   "texto": (110, 110, 110)},
        }

        for i, (id_hab, datos) in enumerate(estado_habs.items()):
            col = i % COLS
            fila = i // COLS
            cx = START_X + col * (CARD_W + 10)
            cy = START_Y + fila * (CARD_H + 10)
            rect = pygame.Rect(cx, cy, CARD_W, CARD_H)
            self.rects_habilidades[id_hab] = rect

            est = datos["estado"]
            col_est = COLORES[est]

            pygame.draw.rect(self.pantalla, col_est["fondo"], rect, border_radius=6)
            pygame.draw.rect(self.pantalla, col_est["borde"], rect, 2, border_radius=6)

            # Nombre
            txt_nom = self.fuente.render(datos["nombre"], True, col_est["texto"])
            self.pantalla.blit(txt_nom, (cx + 6, cy + 6))

            # Costo
            costo_str = f"Costo: {datos['costo']} oro" if datos["costo"] > 0 else "Costo: GRATIS"
            txt_cos = self.fuente.render(costo_str, True, (200, 180, 80))
            self.pantalla.blit(txt_cos, (cx + 6, cy + 24))

            # Requisito
            req = datos.get("requiere")
            if req:
                req_nombre = estado_habs[req]["nombre"] if req in estado_habs else req
                txt_req = self.fuente.render(f"Req: {req_nombre}", True, (160, 130, 80))
                self.pantalla.blit(txt_req, (cx + 6, cy + 41))

            # Estado badge
            badge = {"activa": "✓ ACTIVA", "disponible": "Clic para comprar",
                     "bloqueada": "🔒 Bloqueada"}[est]
            txt_badge = self.fuente.render(badge, True, col_est["borde"])
            self.pantalla.blit(txt_badge, (cx + 6, cy + 54))

    def _dibujar_hud(self):
        txt_oro = self.fuente_grande.render(f"Oro: {int(self.oro)}", True, (255, 215, 0))
        self.pantalla.blit(txt_oro, (20, 20))

        txt_facciones = self.fuente.render(f"{self.faccion.capitalize()} vs Enano Bot", True, (255, 255, 255))
        self.pantalla.blit(txt_facciones, (20, 48))

        fase = getattr(self, "ia_fase", "defender")
        txt_fase = self.fuente.render(f"IA: {fase.upper()}", True, (200, 200, 200))
        self.pantalla.blit(txt_fase, (20, 68))

        if fase == "defender":
            progreso = min(1.0, self.ia_timer / max(1, self.ia_intervalo_ataque))
            pygame.draw.rect(self.pantalla, (60, 30, 30), (20, 84, 140, 6), border_radius=3)
            pygame.draw.rect(self.pantalla, (200, 60, 60), (20, 84, int(140 * progreso), 6), border_radius=3)

        # 🕒 RELOJ HUD
        tiempo_transcurrido = time.time() - self.tiempo_inicio
        minutos = int(tiempo_transcurrido // 60)
        segundos = int(tiempo_transcurrido % 60)
        str_tiempo = f"{minutos:02d}:{segundos:02d}"
        
        colores_alerta = [(255, 255, 255), (255, 230, 0), (255, 120, 0), (255, 0, 0)]
        color_reloj = colores_alerta[self.fase_dificultad_actual]

        txt_tiempo = self.fuente_grande.render(str_tiempo, True, color_reloj)
        txt_alerta = self.fuente.render(f"Peligro: Nivel {self.fase_dificultad_actual}", True, color_reloj)
        
        self.pantalla.blit(txt_tiempo, (800 - txt_tiempo.get_width() - 20, 20))
        self.pantalla.blit(txt_alerta, (800 - txt_alerta.get_width() - 20, 45))

        fin = getattr(self, "_fin_partida", None)
        if fin:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.pantalla.blit(overlay, (0, 0))
            fuente_fin = pygame.font.SysFont(None, 72)
            txt = fuente_fin.render("¡VICTORIA!" if fin == "victoria" else "DERROTA", True, (80, 255, 120) if fin == "victoria" else (255, 80, 80))
            self.pantalla.blit(txt, ((800 - txt.get_width()) // 2, 220))

    def _dibujar_menu_construccion(self):
        menu_x, menu_y = 660, 380
        ancho_opcion, alto_opcion, separacion = 130, 44, 8
        exclusivo_nombre = EDIFICIO_EXCLUSIVO[self.faccion][0] if self.faccion in EDIFICIO_EXCLUSIVO else None

        for i, nombre in enumerate(list(self.tipos_edificio.keys())):
            rect = pygame.Rect(menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            costo = self.costos_edificio[nombre]
            desc = self.descripciones_edificio.get(nombre, "")
            puede_pagar = self.oro >= costo
            es_exclusivo = (nombre == exclusivo_nombre)

            color_fondo = (60, 40, 80) if es_exclusivo and puede_pagar else ((40, 80, 40) if puede_pagar else (80, 40, 40))
            color_borde = (200, 100, 255) if es_exclusivo else ((100, 200, 100) if puede_pagar else (200, 100, 100))

            pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=6)
            pygame.draw.rect(self.pantalla, color_borde, rect, width=1, border_radius=6)

            if es_exclusivo:
                tag = self.fuente.render("★ EXCLUSIVO", True, (200, 140, 255))
                self.pantalla.blit(tag, (rect.x + 4, rect.y + 1))
                self.pantalla.blit(self.fuente.render(nombre, True, (230, 200, 255)), (rect.x + 4, rect.y + 13))
                self.pantalla.blit(self.fuente.render(f"{costo}o {desc}", True, (200, 180, 80)), (rect.x + 4, rect.y + 27))
            else:
                self.pantalla.blit(self.fuente.render(nombre, True, (230, 230, 230)), (rect.x + 6, rect.y + 5))
                self.pantalla.blit(self.fuente.render(f"{costo} oro {desc}", True, (200, 180, 80)), (rect.x + 6, rect.y + 22))