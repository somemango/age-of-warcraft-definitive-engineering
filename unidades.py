import pygame
import time

class Tropa:
    def __init__(self, x, y, faccion, vida, color):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.vida = vida
        self.color = color
        self.estado = "quieto"
        self.destinoX = x
        self.destinoY = y
        self.velocidad = 2
        self.radio = 15  
        self.distancia_separacion = 45
        self.seleccionada = False

        # Tareas y combate (Prioridades del RTS)
        self.tarea = None               # None | "construir" | "atacar"
        self.objetivo = None            # Referencia a estructura
        self.objetivo_combate = None    # Referencia a enemigo
        self.velocidad_construccion = 2  
        self.dano = 10 if faccion != "enemigo" else 5  # Reducido daño inicial enemigo de 10 a 5
        self.rango_ataque = 45
        self.cooldown_ataque = 60
        self.timer_ataque = 0
        self.rango_vision = 200         # Distancia para detectar enemigos automáticamente

    def buscar_enemigo_mas_cercano(self, todas_las_unidades):
        enemigo_mas_cercano = None
        distancia_minima = float('inf')
        pos_actual = pygame.math.Vector2(self.x, self.y)

        for otra in todas_las_unidades:
            if otra.faccion != self.faccion and otra.vida > 0:
                pos_otra = pygame.math.Vector2(otra.x, otra.y)
                distancia = (pos_actual - pos_otra).length()
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    enemigo_mas_cercano = otra

        return enemigo_mas_cercano

    def ejecutar_tareas(self, todas_las_unidades):
        # Manejo pasivo del timer de ataque
        if self.timer_ataque > 0:
            self.timer_ataque -= 1

        # 1. ORDEN: CONSTRUIR
        if self.tarea == "construir" and self.objetivo:
            distancia = pygame.math.Vector2(self.x - self.objetivo.x, self.y - self.objetivo.y).length()
            if distancia <= self.radio + 35:
                self.estado = "quieto"
                self.objetivo.recibir_construccion(self.velocidad_construccion, juego=None)
                if self.objetivo.construida:
                    self.tarea = None
                    self.objetivo = None
            else:
                self.destinoX = self.objetivo.x
                self.destinoY = self.objetivo.y
                self.estado = "moviendose"
                self.movimiento(todas_las_unidades)

        # 2. ORDEN: ATACAR
        elif self.tarea == "atacar" and self.objetivo_combate:
            if self.objetivo_combate.vida > 0:
                distancia = pygame.math.Vector2(self.x - self.objetivo_combate.x, self.y - self.objetivo_combate.y).length()
                if distancia > self.rango_ataque:
                    self.destinoX = self.objetivo_combate.x
                    self.destinoY = self.objetivo_combate.y
                    self.estado = "moviendose"
                    self.movimiento(todas_las_unidades)
                else:
                    if self.timer_ataque == 0:
                        reduccion = getattr(self.objetivo_combate, "dano_reduccion", 0)
                        dano_real = max(1, self.dano - reduccion)
                        self.objetivo_combate.vida -= dano_real
                        self.timer_ataque = self.cooldown_ataque
            else:
                # Objetivo muerto: limpiar y retornar pasivo
                self.tarea = None
                self.objetivo_combate = None
                self.estado = "quieto"

        # 3. SIN ÓRDENES ESPECIALES / ESCANEO AUTOMÁTICO DE ENEMIGOS cercanos
        else:
            enemigo = self.buscar_enemigo_mas_cercano(todas_las_unidades)
            if enemigo:
                dist_enemigo = pygame.math.Vector2(self.x - enemigo.x, self.y - enemigo.y).length()
                if dist_enemigo <= self.rango_vision:
                    self.tarea = "atacar"
                    self.objetivo_combate = enemigo
            
            self.movimiento(todas_las_unidades)

    def movimiento(self, todas_las_unidades):
        posicion_actual = pygame.math.Vector2(self.x, self.y)
        fuerza_separacion = pygame.math.Vector2(0, 0)

        for otra in todas_las_unidades:
            if otra is not self:
                pos_otra = pygame.math.Vector2(otra.x, otra.y)
                direccion_escape = posicion_actual - pos_otra
                distancia = direccion_escape.length()
                if distancia < self.distancia_separacion and distancia > 0:
                    direccion_escape.normalize_ip()
                    fuerza_separacion += direccion_escape * (self.distancia_separacion - distancia) * 0.15

        if self.estado == "moviendose":
            destino = pygame.math.Vector2(self.destinoX, self.destinoY)
            direccion = destino - posicion_actual
            distancia_destino = direccion.length()

            if distancia_destino <= self.velocidad and fuerza_separacion.length() == 0:
                self.x = self.destinoX
                self.y = self.destinoY
                self.estado = "quieto"
            else:
                if distancia_destino > 0:
                    direccion.normalize_ip()
                    vector_movimiento = direccion * self.velocidad
                else:
                    vector_movimiento = pygame.math.Vector2(0, 0)

                vector_final = vector_movimiento + fuerza_separacion
                if vector_final.length() > self.velocidad:
                    vector_final.normalize_ip()
                    vector_final *= self.velocidad

                self.x += vector_final.x
                self.y += vector_final.y
        else:
            if fuerza_separacion.length() > 0:
                if fuerza_separacion.length() > self.velocidad:
                    fuerza_separacion.normalize_ip()
                    fuerza_separacion *= self.velocidad
                self.x += fuerza_separacion.x
                self.y += fuerza_separacion.y

    def dibujar(self, pantalla, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        if not (-self.radio - 10 <= sx <= 830 + self.radio and
                -self.radio - 10 <= sy <= 630 + self.radio):
            return

        pygame.draw.circle(pantalla, self.color, (sx, sy), self.radio)
        r, g, b = self.color
        borde = (max(0, r - 70), max(0, g - 70), max(0, b - 70))
        pygame.draw.circle(pantalla, borde, (sx, sy), self.radio, 2)
        pygame.draw.circle(pantalla, (255, 255, 255), (sx, sy - 3), 4)
        pygame.draw.circle(pantalla, borde, (sx, sy - 3), 4, 1)

        if self.seleccionada:
            pygame.draw.circle(pantalla, (255, 255, 255), (sx, sy), self.radio + 4, 2)

        bw = self.radio * 2
        bh = 4
        bx = sx - self.radio
        by = sy - self.radio - 8
        porcentaje = max(0.0, self.vida / 100)
        color_vida = (int(220 * (1 - porcentaje)), int(200 * porcentaje), 30)

        pygame.draw.rect(pantalla, (40, 10, 10), (bx, by, bw, bh), border_radius=2)
        if porcentaje > 0:
            pygame.draw.rect(pantalla, color_vida, (bx, by, int(bw * porcentaje), bh), border_radius=2)
        pygame.draw.rect(pantalla, (160, 160, 160), (bx, by, bw, bh), width=1, border_radius=2)


class Generador:
    VIDA_MAX = 500
    RADIO = 35          
    SPAWN_OFFSET = 80   

    def __init__(self, x, y, faccion, color, tiempo_generacion_segundos=3, dano_unidades=10):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.color = color
        self.cooldown = tiempo_generacion_segundos  
        self.ultimo_spawn = time.time()
        self.vida = self.VIDA_MAX
        self.radio = self.RADIO         
        self.dano_unidades = dano_unidades # Guardamos el daño con el que nacerán sus unidades

    def _punto_spawn(self):
        import math, random
        angulo = random.uniform(0, math.pi * 2)
        return (
            self.x + math.cos(angulo) * self.SPAWN_OFFSET,
            self.y + math.sin(angulo) * self.SPAWN_OFFSET,
        )

    def actualizar(self, lista_unidades, juego=None):
        if self.vida <= 0:
            return

        # Antena Suprema: bloquea la producción del generador enemigo
        if juego is not None and self.faccion != juego.faccion:
            if getattr(juego, "timer_antena_suprema", 0) > 0:
                juego.timer_antena_suprema -= 1
                return  # producción enemiga bloqueada este frame

        tiempo_actual = time.time()
        unidades_faccion = [u for u in lista_unidades if u.faccion == self.faccion]

        if len(unidades_faccion) < 8:
            if tiempo_actual - self.ultimo_spawn >= self.cooldown:
                sx, sy = self._punto_spawn()
                nueva_tropa = Tropa(sx, sy, self.faccion, 100, self.color)
                nueva_tropa.dano = self.dano_unidades

                # Aplicar mods de habilidades a tropas aliadas recién generadas
                if juego is not None and self.faccion == juego.faccion:
                    nueva_tropa.dano = int(nueva_tropa.dano * getattr(juego, "mod_danno", 1.0))
                    nueva_tropa.vida = int(nueva_tropa.vida * getattr(juego, "mod_vida_tropas", 1.0))
                    nueva_tropa.velocidad *= getattr(juego, "mod_banda_ancha", 1.0)
                    nueva_tropa.rango_ataque = int(
                        nueva_tropa.rango_ataque * getattr(juego, "mod_antena_amplificadora", 1.0))

                nueva_tropa.destinoX = sx
                nueva_tropa.destinoY = sy
                lista_unidades.append(nueva_tropa)
                self.ultimo_spawn = tiempo_actual

    def dibujar(self, pantalla, fuente=None, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        if self.vida <= 0:
            pygame.draw.rect(pantalla, (60, 60, 60), (sx - 30, sy - 30, 60, 60), border_radius=4)
            return

        pygame.draw.rect(pantalla, self.color, (sx - 30, sy - 30, 60, 60), border_radius=6)
        r, g, b = self.color
        borde = (min(255, r + 80), min(255, g + 80), min(255, b + 80))
        pygame.draw.rect(pantalla, borde, (sx - 30, sy - 30, 60, 60), width=2, border_radius=6)

        pygame.draw.line(pantalla, borde, (sx, sy - 18), (sx, sy + 18), 3)
        pygame.draw.line(pantalla, borde, (sx - 18, sy), (sx + 18, sy), 3)

        bw = 60
        bx = sx - bw // 2
        by = sy - 42
        porcentaje = max(0.0, self.vida / self.VIDA_MAX)
        color_vida = (int(220 * (1 - porcentaje)), int(200 * porcentaje), 40)
        pygame.draw.rect(pantalla, (50, 20, 20), (bx, by, bw, 7), border_radius=3)
        if porcentaje > 0:
            pygame.draw.rect(pantalla, color_vida, (bx, by, int(bw * porcentaje), 7), border_radius=3)
        pygame.draw.rect(pantalla, (180, 180, 180), (bx, by, bw, 7), width=1, border_radius=3)

        if fuente:
            txt = fuente.render(f"{int(self.vida)}/{self.VIDA_MAX}", True, (220, 220, 220))
            pantalla.blit(txt, (sx - txt.get_width() // 2, by - 14))