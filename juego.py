import pygame
import time
import math
import random
from unidades import Tropa, Generador, Constructor
from estructuras import Cuartel, Mina, Granja, BaseDatos, Torreta, Antena, MinaMejorada, Muro
from habilidades import ArbolHabilidades

TIPOS_EDIFICIO_BASE = {"Cuartel": Cuartel, "Mina": Mina, "Granja": Granja, "Muro": Muro}
COSTOS_EDIFICIO_BASE = {"Cuartel": 150, "Mina": 100, "Granja": 80, "Muro": 50}

EDIFICIO_EXCLUSIVO = {
    "sistemas":           ("BaseDatos",     BaseDatos,     180, "Genera +4 de oro por segundo."),
    "civil":              ("Torreta",       Torreta,       220, "Ataca de forma automatica."),
    "telecomunicaciones": ("Antena",        Antena,        160, "Ralentiza tropas enemigas."),
    "industrial":         ("MinaMejorada",  MinaMejorada,  200, "Multiplica la extraccion x3."),
}

class Juego:
    def __init__(self, pantalla, faccion_jugador, faccion_enemigo):
        self.pantalla = pantalla
        self.oro = 300
        self.oro_enemigo = 350
        self.faccion = faccion_jugador
        self.faccion_enemigo = faccion_enemigo

        self.tiempo_inicio = time.time()
        self.fase_dificultad_actual = 0  

        self.mis_unidades = []
        self.estructuras = []
        
        self.mostrar_menu_construccion = False
        self.mostrar_menu_habilidades = False
        self.mostrar_guia_manual = False
        self.pagina_guia = 0
        
        self.edificio_fantasma = None  

        self.ancho_mapa = 1600  
        self.alto_mapa = 1200   
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

        self.generador_aliado = Generador(150, 150, self.faccion, (0, 125, 0), tiempo_generacion_segundos=8, dano_unidades=10)
        self.generador_enemigo = Generador(1450, 1050, "enemigo", (255, 0, 0), tiempo_generacion_segundos=15.0, dano_unidades=5)

        cuartel_inicial_aliado = Cuartel(300, 150, self.faccion)
        cuartel_inicial_aliado.construida = True
        cuartel_inicial_aliado.progreso = 100
        cuartel_inicial_aliado._juego = self
        self.estructuras.append(cuartel_inicial_aliado)

        cuartel_inicial_enemigo = Cuartel(1300, 1050, "enemigo")
        cuartel_inicial_enemigo.construida = True
        cuartel_inicial_enemigo.progreso = 100
        cuartel_inicial_enemigo._juego = self
        self.estructuras.append(cuartel_inicial_enemigo)

        for i in range(4):
            self.mis_unidades.append(Tropa(200 + (i*25), 200, self.faccion, 100, (0, 255, 0)))
        self.mis_unidades.append(Constructor(180, 220, self.faccion))

        self.habilidades = ArbolHabilidades(self.faccion, self)

        self.ex = self.generador_enemigo.x
        self.ey = self.generador_enemigo.y
        
        for idx in range(4):
            t = Tropa(self.ex - 80 - (idx * 25), self.ey - 80, "enemigo", 100, (255, 60, 60))
            t.dano = 5
            self.mis_unidades.append(t)
        self.mis_unidades.append(Constructor(self.ex - 50, self.ey - 50, "enemigo"))

        self.plan_construccion_enemigo = [
            (Mina, -150, 0),
            (Granja, 0, -150)
        ]

        self.ia_fase = "construir_inicio"       
        self.ia_timer = 0               
        self.ia_intervalo_ataque = 600  
        self.ia_punto_rally = (self.ex - 200, self.ey - 200)  

        self.tipos_edificio = dict(TIPOS_EDIFICIO_BASE)
        self.costos_edificio = dict(COSTOS_EDIFICIO_BASE)
        self.descripciones_edificio = {
            "Cuartel": "Entrena constructores automatizados.",
            "Mina": "Genera oro (requiere 1 Tropa cerca).",
            "Granja": "Aumenta la poblacion maxima +5.",
            "Muro": "Barrera defensiva con vida alta (750)."
        }
        if self.faccion in EDIFICIO_EXCLUSIVO:
            nombre, clase, costo, desc = EDIFICIO_EXCLUSIVO[self.faccion]
            self.tipos_edificio[nombre] = clase
            self.costos_edificio[nombre] = costo
            self.descripciones_edificio[nombre] = desc

        self.fuente = pygame.font.SysFont(None, 20)
        self.fuente_grande = pygame.font.SysFont(None, 28)
        self.last_economy_tick = time.time()

    def actualizar_camara(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        velocidad_camara = 6
        if mouse_x < 20: self.camara_x -= velocidad_camara
        elif mouse_x > 780: self.camara_x += velocidad_camara
        if mouse_y < 20: self.camara_y -= velocidad_camara
        elif mouse_y > 580: self.camara_y += velocidad_camara

        self.camara_x = max(0, min(self.camara_x, self.ancho_mapa - 800))
        self.camara_y = max(0, min(self.camara_y, self.alto_mapa - 600))

    def _validar_posicion_construccion(self, mx, my):
        if abs(mx - self.generador_aliado.x) < 65 and abs(my - self.generador_aliado.y) < 65:
            return False
        if abs(mx - self.generador_enemigo.x) < 65 and abs(my - self.generador_enemigo.y) < 65:
            return False
        for est in self.estructuras:
            if abs(mx - est.x) < 50 and abs(my - est.y) < 50:
                return False
        return True

    def _gestionar_escalado_dificultad(self, minutos):
        if minutos >= 10 and self.fase_dificultad_actual < 3:
            self.fase_dificultad_actual = 3
            self.generador_enemigo.cooldown = 4.0      
            self.generador_enemigo.dano_unidades = 22  
        elif minutos >= 7 and self.fase_dificultad_actual < 2:
            self.fase_dificultad_actual = 2
            self.generador_enemigo.cooldown = 7.0      
            self.generador_enemigo.dano_unidades = 15  
        elif minutos >= 3 and self.fase_dificultad_actual < 1:
            self.fase_dificultad_actual = 1
            self.generador_enemigo.cooldown = 10.0      
            self.generador_enemigo.dano_unidades = 10  

    def actualizar(self):
        if self.mostrar_guia_manual: return
        self.actualizar_camara()

        tiempo_transcurrido = time.time() - self.tiempo_inicio
        minutos = int(tiempo_transcurrido // 60)
        self._gestionar_escalado_dificultad(minutos)

        self.generador_aliado.actualizar(self)
        self.generador_enemigo.actualizar(self)

        for unidad in self.mis_unidades:
            pos_anterior = (unidad.x, unidad.y)
            
            if isinstance(unidad, Constructor):
                unidad.actualizar(self)
            else:
                unidad.actualizar(self)
                
            for est in self.estructuras:
                if est.construida and est.__class__.__name__ == "Muro" and est.faccion != unidad.faccion:
                    if (est.x - 38 <= unidad.x <= est.x + 38) and (est.y - 38 <= unidad.y <= est.y + 38):
                        unidad.x, unidad.y = pos_anterior
                        unidad.estado = "quieto"

        for i in range(len(self.mis_unidades)):
            for j in range(i + 1, len(self.mis_unidades)):
                u1 = self.mis_unidades[i]
                u2 = self.mis_unidades[j]
                dx = u2.x - u1.x
                dy = u2.y - u1.y
                dist = math.hypot(dx, dy)
                radio_total = u1.radio + u2.radio
                if dist < radio_total and dist > 0:
                    solapamiento = radio_total - dist
                    desfase_x = (dx / dist) * (solapamiento / 2)
                    desfase_y = (dy / dist) * (solapamiento / 2)
                    u1.x -= desfase_x
                    u1.y -= desfase_y
                    u2.x += desfase_x
                    u2.y += desfase_y

        todos_los_objetivos = self.mis_unidades + self.estructuras
        if self.generador_aliado.vida > 0: todos_los_objetivos.append(self.generador_aliado)
        if self.generador_enemigo.vida > 0: todos_los_objetivos.append(self.generador_enemigo)
        
        self._actualizar_ia_enemiga(todos_los_objetivos, tiempo_transcurrido)

        for est in self.estructuras:
            est.actualizar(self)

        self.mis_unidades = [u for u in self.mis_unidades if u.vida > 0]
        self.estructuras = [e for e in self.estructuras if e.vida > 0]
        self._verificar_fin_partida()

    def procesar_eventos(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_b, pygame.K_z):
                if self.mostrar_guia_manual:
                    self.mostrar_guia_manual = False
                else:
                    self.mostrar_menu_construccion = not self.mostrar_menu_construccion
            elif event.key == pygame.K_ESCAPE:
                if self.mostrar_guia_manual:
                    self.mostrar_guia_manual = False
                else:
                    self.edificio_fantasma = None 

        if self.mostrar_guia_manual:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if 150 <= mx <= 280 and 460 <= my <= 500: 
                    self.pagina_guia = max(0, self.pagina_guia - 1)
                elif 520 <= mx <= 650 and 460 <= my <= 500: 
                    self.pagina_guia = min(2, self.pagina_guia + 1)
                elif 340 <= mx <= 460 and 460 <= my <= 500: 
                    self.mostrar_guia_manual = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            if self.mostrar_menu_construccion and mouse_pos[0] > 650 and mouse_pos[1] > 260:
                self._procesar_clic_menu(mouse_pos)
                return

            if self.edificio_fantasma:
                mundo_x = mouse_pos[0] + self.camara_x
                mundo_y = mouse_pos[1] + self.camara_y
                
                if self._validar_posicion_construccion(mundo_x, mundo_y):
                    costo = self.costos_edificio[self.edificio_fantasma]
                    if self.oro >= costo:
                        self.oro -= costo
                        ClaseEst = self.tipos_edificio[self.edificio_fantasma]
                        nuevo_plano = ClaseEst(mundo_x, mundo_y, self.faccion)
                        nuevo_plano._juego = self
                        self.estructuras.append(nuevo_plano)
                        self.edificio_fantasma = None 
                return

            self.seleccionando = True
            self.inicio_seleccion = (mouse_pos[0] + self.camara_x, mouse_pos[1] + self.camara_y)
            self.fin_seleccion = self.inicio_seleccion

        elif event.type == pygame.MOUSEMOTION:
            if self.seleccionando:
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
                    if u.faccion == self.faccion and not isinstance(u, Constructor):
                        if es_clic_simple:
                            dist = ((u.x - x_min) ** 2 + (u.y - y_min) ** 2) ** 0.5
                            u.seleccionada = (dist <= 30)
                        else:
                            u.seleccionada = (x_min <= u.x <= x_max and y_min <= u.y <= y_max)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.edificio_fantasma = None 
            mouse_x, mouse_y = event.pos
            mundo_x = mouse_x + self.camara_x
            mundo_y = mouse_y + self.camara_y

            for tropa in self.mis_unidades:
                if tropa.seleccionada and tropa.faccion == self.faccion and not isinstance(tropa, Constructor):
                    tropa.destinoX = mundo_x
                    tropa.destinoY = mundo_y
                    tropa.estado = "moviendose"

    def _procesar_clic_menu(self, pos):
        if 660 <= pos[0] <= 790 and 270 <= pos[1] <= 305:
            self.mostrar_guia_manual = True
            self.pagina_guia = 0
            self.mostrar_menu_construccion = False
            return

        menu_x, menu_y = 660, 320
        ancho_opcion, alto_opcion, separacion = 130, 44, 8
        opciones = list(self.tipos_edificio.keys())
        for i, nombre in enumerate(opciones):
            rect = pygame.Rect(menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            if rect.collidepoint(pos):
                self.edificio_fantasma = nombre
                self.mostrar_menu_construccion = False

    def _tropas_enemigas(self):
        return [u for u in self.mis_unidades if u.faccion == "enemigo" and not isinstance(u, Constructor)]

    def _tropas_aliadas(self):
        return [u for u in self.mis_unidades if u.faccion == self.faccion and not isinstance(u, Constructor)]

    def _actualizar_ia_enemiga(self, todos_los_objetivos, tiempo_transcurrido):
        tropas = self._tropas_enemigas()
        self.ia_timer += 1

        if self.ia_fase == "construir_inicio":
            if self.plan_construccion_enemigo:
                ClaseEdif, dx, dy = self.plan_construccion_enemigo[0]
                costo_edif = 100 
                
                if self.oro_enemigo >= costo_edif:
                    self.oro_enemigo -= costo_edif
                    nuevo_plano = ClaseEdif(self.ex + dx, self.ey + dy, "enemigo")
                    nuevo_plano._juego = self
                    self.estructuras.append(nuevo_plano)
                    self.plan_construccion_enemigo.pop(0)

            minas_enemigas = [e for e in self.estructuras if e.__class__.__name__ == "Mina" and e.faccion == "enemigo"]
            if minas_enemigas and tropas:
                mina_meta = minas_enemigas[0]
                t_trabajadora = tropas[0]
                if math.hypot(t_trabajadora.x - mina_meta.x, t_trabajadora.y - mina_meta.y) > 40:
                    t_trabajadora.destinoX = mina_meta.x
                    t_trabajadora.destinoY = mina_meta.y
                    t_trabajadora.estado = "moviendose"

            if tiempo_transcurrido >= 45:
                self.ia_fase = "defender"

        elif self.ia_fase == "defender":
            for t in tropas:
                intruso = None
                for a in self._tropas_aliadas():
                    if pygame.math.Vector2(a.x - self.ex, a.y - self.ey).length() < 350:
                        intruso = a
                        break
                if intruso:
                    t.destinoX = intruso.x
                    t.destinoY = intruso.y
                    t.estado = "moviendose"

            if len(tropas) >= 5 and self.ia_timer >= self.ia_intervalo_ataque:
                self.ia_timer = 0
                self.ia_fase = "reagrupar"
                ax, ay = self.generador_aliado.x, self.generador_aliado.y
                self.ia_punto_rally = (int(self.ex + (ax - self.ex) * 0.35), int(self.ey + (ay - self.ey) * 0.35))

        elif self.ia_fase == "reagrupar":
            rx, ry = self.ia_punto_rally
            listas = 0
            tropas_ataque = tropas[1:] 
            for t in tropas_ataque:
                dist = pygame.math.Vector2(t.x - rx, t.y - ry).length()
                if dist > 60:
                    t.destinoX = rx
                    t.destinoY = ry
                    t.estado = "moviendose"
                else: 
                    listas += 1
            if listas >= max(1, int(len(tropas_ataque) * 0.7)):
                self.ia_fase = "atacar"

        elif self.ia_fase == "atacar":
            if not tropas:
                self.ia_fase = "defender"
                self.ia_timer = 0
                return
            for t in tropas[1:]:
                if self.generador_aliado.vida > 0:
                    t.destinoX = self.generador_aliado.x
                    t.destinoY = self.generador_aliado.y
                    t.estado = "moviendose"

            if len(tropas) < 3:
                self.ia_fase = "defender"
                self.ia_timer = 0

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
            real_x, real_y = est.x, est.y
            est.x -= self.camara_x
            est.y -= self.camara_y
            est.dibujar(self.pantalla, self.fuente)
            est.x, est.y = real_x, real_y

        for u in self.mis_unidades:
            u.dibujar(self.pantalla, self.fuente, self.camara_x, self.camara_y)

        if self.edificio_fantasma:
            mx, my = pygame.mouse.get_pos()
            mundo_x = mx + self.camara_x
            mundo_y = my + self.camara_y
            
            es_valido = self._validar_posicion_construccion(mundo_x, mundo_y)
            color_caja = (0, 255, 0) if es_valido else (255, 0, 0) 
            
            pygame.draw.rect(self.pantalla, color_caja, (mx - 35, my - 35, 70, 70), width=3)
            relleno = pygame.Surface((70, 70), pygame.SRCALPHA)
            relleno.fill((0, 255, 0, 70) if es_valido else (255, 0, 0, 70))
            self.pantalla.blit(relleno, (mx - 35, my - 35))

        if self.seleccionando:
            x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
            y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
            ancho_abs = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
            alto_abs = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])
            pygame.draw.rect(self.pantalla, (255, 255, 255), (x_min - self.camara_x, y_min - self.camara_y, ancho_abs, alto_abs), 1)

        self._dibujar_hud()
        if self.mostrar_menu_construccion:
            self._dibujar_menu_construccion()
        
        if self.mostrar_guia_manual:
            self._dibujar_guia_interactiva()

    def _dibujar_hud(self):
        ahora = time.time()
        if ahora - self.last_economy_tick >= 2.5: 
            self.oro += 1 
            self.oro_enemigo += 1
            self.last_economy_tick = ahora

        txt_oro = self.fuente_grande.render(f"Oro: {int(self.oro)}  |  Oro Enemigo: {int(self.oro_enemigo)}", True, (255, 215, 0))
        self.pantalla.blit(txt_oro, (20, 20))

        if self.edificio_fantasma:
            txt_aviso = self.fuente.render(f"Colocando: {self.edificio_fantasma} (ESC para cancelar)", True, (255, 255, 255))
            self.pantalla.blit(txt_aviso, (20, 95))

        txt_facciones = self.fuente.render(f"{self.faccion.capitalize()} vs Enano Bot Simetrico", True, (255, 255, 255))
        self.pantalla.blit(txt_facciones, (20, 48))

        fase = getattr(self, "ia_fase", "defender")
        txt_fase = self.fuente.render(f"IA: {fase.upper()}", True, (200, 200, 200))
        self.pantalla.blit(txt_fase, (20, 68))

        tiempo_transcurrido = ahora - self.tiempo_inicio
        minutos = int(tiempo_transcurrido // 60)
        segundos = int(tiempo_transcurrido % 60)
        str_tiempo = f"{minutos:02d}:{segundos:02d}"
        
        color_reloj = [(255, 255, 255), (255, 230, 0), (255, 120, 0), (255, 0, 0)][self.fase_dificultad_actual]
        txt_tiempo = self.fuente_grande.render(str_tiempo, True, color_reloj)
        self.pantalla.blit(txt_tiempo, (800 - txt_tiempo.get_width() - 20, 20))

        fin = getattr(self, "_fin_partida", None)
        if fin:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.pantalla.blit(overlay, (0, 0))
            fuente_fin = pygame.font.SysFont(None, 72)
            txt = fuente_fin.render("¡VICTORIA!" if fin == "victoria" else "DERROTA", True, (80, 255, 120) if fin == "victoria" else (255, 80, 80))
            self.pantalla.blit(txt, ((800 - txt.get_width()) // 2, 220))

    def _dibujar_menu_construccion(self):
        rect_guia = pygame.Rect(660, 270, 130, 35)
        m_pos = pygame.mouse.get_pos()
        c_g_fondo = (40, 50, 100) if rect_guia.collidepoint(m_pos) else (25, 30, 60)
        pygame.draw.rect(self.pantalla, c_g_fondo, rect_guia, border_radius=6)
        pygame.draw.rect(self.pantalla, (100, 150, 255), rect_guia, width=1, border_radius=6)
        txt_g = self.fuente.render("Ver Guia", True, (255, 255, 255))
        self.pantalla.blit(txt_g, (rect_guia.x + (rect_guia.width - txt_g.get_width())//2, rect_guia.y + (rect_guia.height - txt_g.get_height())//2))

        menu_x, menu_y = 660, 320 
        ancho_opcion, alto_opcion, separacion = 130, 44, 8
        exclusivo_nombre = EDIFICIO_EXCLUSIVO[self.faccion][0] if self.faccion in EDIFICIO_EXCLUSIVO else None
        mouse_pos = pygame.mouse.get_pos()
        descripcion_a_mostrar = None

        for i, nombre in enumerate(list(self.tipos_edificio.keys())):
            rect = pygame.Rect(menu_x, menu_y + i * (alto_opcion + separacion), ancho_opcion, alto_opcion)
            costo = self.costos_edificio[nombre]
            puede_pagar = self.oro >= costo
            es_exclusivo = (nombre == exclusivo_nombre)

            if rect.collidepoint(mouse_pos):
                descripcion_a_mostrar = self.descripciones_edificio.get(nombre, "")

            color_fondo = (60, 40, 80) if es_exclusivo and puede_pagar else ((40, 80, 40) if puede_pagar else (80, 40, 40))
            color_borde = (200, 100, 255) if es_exclusivo else ((100, 200, 100) if puede_pagar else (200, 100, 100))

            pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=6)
            pygame.draw.rect(self.pantalla, color_borde, rect, width=1, border_radius=6)

            self.pantalla.blit(self.fuente.render(nombre, True, (230, 230, 230)), (rect.x + 6, rect.y + 5))
            self.pantalla.blit(self.fuente.render(f"{costo} oro", True, (200, 180, 80)), (rect.x + 6, rect.y + 22))

        if descripcion_a_mostrar:
            panel_rect = pygame.Rect(400, 530, 245, 55)
            pygame.draw.rect(self.pantalla, (20, 20, 30), panel_rect, border_radius=5)
            pygame.draw.rect(self.pantalla, (100, 100, 150), panel_rect, width=1, border_radius=5)
            
            palabras = descripcion_a_mostrar.split(' ')
            lineas = []
            linea_actual = ""
            for palabra in palabras:
                test_linea = linea_actual + " " + palabra if linea_actual else palabra
                if self.fuente.size(test_linea)[0] < panel_rect.width - 15:
                    linea_actual = test_linea
                else:
                    lineas.append(linea_actual)
                    linea_actual = palabra
            if linea_actual:
                lineas.append(linea_actual)

            for idx, linea in enumerate(lineas):
                txt_linea = self.fuente.render(linea, True, (240, 240, 240))
                self.pantalla.blit(txt_linea, (panel_rect.x + 8, panel_rect.y + 6 + (idx * 15)))

    def _dibujar_guia_interactiva(self):
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 230))
        self.pantalla.blit(overlay, (0, 0))

        cuadro = pygame.Rect(100, 80, 600, 440)
        pygame.draw.rect(self.pantalla, (25, 30, 45), cuadro, border_radius=10)
        pygame.draw.rect(self.pantalla, (70, 120, 230), cuadro, width=2, border_radius=10)

        fuente_titulo = pygame.font.SysFont(None, 36)
        fuente_sub = pygame.font.SysFont(None, 24)

        if self.pagina_guia == 0:
            txt_tit = fuente_titulo.render("GUIA GENERAL: OBJETIVOS", True, (100, 200, 255))
            self.pantalla.blit(txt_tit, (cuadro.x + 30, cuadro.y + 25))
            
            puntos = [
                "CONDICION DE VICTORIA:",
                "-> Debes destruir por completo la Base del enemigo ubicado en la",
                "   esquina inferior derecha del mapa.",
                "",
                "CONDICION DE DERROTA:",
                "-> El enemigo destruye tu Base principal,",
                "   o elimina por completo a tus ingenieros.",
                "",
                "UNIDADES",
                "-> Ambos bandos inician con 5 unidades en total.",
                "-> Las minas de oro NO funcionan solas: mantén una Tropa parada",
                "   justo encima de ella para que extraiga recursos de forma activa."
            ]
            for idx, p in enumerate(puntos):
                color = (255, 100, 100) if "DERROTA" in p else ((100, 255, 100) if "VICTORIA" in p else (230, 230, 230))
                self.pantalla.blit(self.fuente.render(p, True, color), (cuadro.x + 35, cuadro.y + 80 + (idx * 22)))

        elif self.pagina_guia == 1:
            txt_tit = fuente_titulo.render("GUIA GENERAL: ESTRUCTURAS", True, (100, 200, 255))
            self.pantalla.blit(txt_tit, (cuadro.x + 30, cuadro.y + 25))

            edifs = [
                ("BASE PRINCIPAL", "Genera soldados de combate regulares cobrando oro al bot enemigo."),
                ("CUARTEL", "Despliega constructores (Naranjas). Maximo 5 por bando simultaneos."),
                ("MINA DE ORO", "Genera oro constante SOLO si una tropa se encuentra encima trabajando."),
                ("GRANJA", "Expande tu infraestructura sumando +5 al limite total de poblacion."),
                ("EDIFICIOS DE FACCION (EXCLUSIVOS)", "Desbloqueables desde el arbol de habilidades con la tecla H."),
                ("   - Base de Datos (Sistemas)", "Multiplica radicalmente la generacion de oro."),
                ("   - Torreta de Cemento (Civil)", "Estructura defensiva estatica que dispara a enemigos cercanos."),
                ("   - Antena de Red (Telecom.)", "Ralentiza e intercepta la velocidad de las tropas enemigas."),
                ("   - Mina Industrial (Industrial)", "Triplica la recoleccion del oro pasivo del mapa.")
            ]
            for idx, (tit, desc) in enumerate(edifs):
                self.pantalla.blit(self.fuente.render(tit, True, (255, 215, 0)), (cuadro.x + 35, cuadro.y + 70 + (idx * 34)))
                self.pantalla.blit(self.fuente.render(desc, True, (210, 210, 210)), (cuadro.x + 35, cuadro.y + 86 + (idx * 34)))

        elif self.pagina_guia == 2:
            txt_tit = fuente_titulo.render("GUIA GENERAL: UNIDADES", True, (100, 200, 255))
            self.pantalla.blit(txt_tit, (cuadro.x + 30, cuadro.y + 25))

            tropas_info = [
                ("TROPAS ", "Soldados basicos de combate de 100 de salud base.", "Estaciónalos sobre las minas para extraer oro o mándalos al ataque."),
                ("CONSTRUCTORES (NARANJAS)", "Unidades automaticas del Cuartel con 50 de salud.", "Patrullan la base o edifican planos de estructuras libres.")
            ]
            y_off = 80
            for tit, d1, d2 in tropas_info:
                self.pantalla.blit(fuente_sub.render(tit, True, (255, 215, 0)), (cuadro.x + 35, cuadro.y + y_off))
                self.pantalla.blit(self.fuente.render(d1, True, (230, 230, 230)), (cuadro.x + 35, cuadro.y + y_off + 20))
                self.pantalla.blit(self.fuente.render(d2, True, (230, 230, 230)), (cuadro.x + 35, cuadro.y + y_off + 35))
                y_off += 75

        btn_ant = pygame.Rect(150, 460, 130, 40)
        btn_cerrar = pygame.Rect(340, 460, 120, 40)
        btn_sig = pygame.Rect(520, 460, 130, 40)

        pygame.draw.rect(self.pantalla, (45, 55, 75) if self.pagina_guia > 0 else (20, 25, 30), btn_ant, border_radius=5)
        pygame.draw.rect(self.pantalla, (180, 50, 50), btn_cerrar, border_radius=5)
        pygame.draw.rect(self.pantalla, (45, 55, 75) if self.pagina_guia < 2 else (20, 25, 30), btn_sig, border_radius=5)

        self.pantalla.blit(self.fuente.render("<< Anterior", True, (255,255,255) if self.pagina_guia > 0 else (100,100,100)), (btn_ant.x + 25, btn_ant.y + 13))
        self.pantalla.blit(self.fuente.render("Cerrar", True, (255,255,255)), (btn_cerrar.x + 40, btn_cerrar.y + 13))
        self.pantalla.blit(self.fuente.render("Siguiente >>", True, (255,255,255) if self.pagina_guia < 2 else (100,100,100)), (btn_sig.x + 25, btn_sig.y + 13))