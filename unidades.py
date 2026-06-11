import pygame
import time
import math
import random

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

        self.tarea = None               
        self.objetivo = None            
        self.objetivo_combate = None    
        self.velocidad_construccion = 2  
        self.dano = 10 if faccion != "enemigo" else 5  
        self.rango_ataque = 45
        self.cooldown_ataque = 60
        self.timer_ataque = 0
        self.rango_vision = 200         

    def buscar_enemigo_mas_cercano(self, todas_las_unidades):
        enemigo_mas_cercano = None
        distancia_minima = float('inf')
        pos_actual = pygame.math.Vector2(self.x, self.y)

        for otra in todas_las_unidades:
            if otra.faccion != self.faccion and otra.vida > 0:
                pos_otra = pygame.math.Vector2(otra.x, otra.y)
                dist = pos_actual.distance_to(pos_otra)
                if dist < distancia_minima:
                    distancia_minima = dist
                    enemigo_mas_cercano = otra
        return enemigo_mas_cercano

    def atacar(self, objetivo):
        if self.timer_ataque <= 0:
            objetivo.vida -= self.dano
            self.timer_ataque = self.cooldown_ataque
        else:
            self.timer_ataque -= 1

    def actualizar(self, juego):
        if self.vida <= 0: return

        if self.timer_ataque > 0:
            self.timer_ataque -= 1

        if self.estado == "moviendose":
            pos_actual = pygame.math.Vector2(self.x, self.y)
            pos_destino = pygame.math.Vector2(self.destinoX, self.destinoY)
            dist = pos_actual.distance_to(pos_destino)

            if dist > 5:
                dir_hacia = (pos_destino - pos_actual).normalize()
                self.x += dir_hacia.x * self.velocidad
                self.y += dir_hacia.y * self.velocidad
            else:
                self.estado = "quieto"

        elif self.estado == "quieto":
            alrededor = juego.mis_unidades + juego.estructuras
            if self.generador_enemigo_vivo(juego):
                alrededor.append(juego.generador_enemigo)
            if juego.generador_aliado.vida > 0:
                alrededor.append(juego.generador_aliado)

            enemigo = self.buscar_enemigo_mas_cercano(alrededor)
            if enemigo:
                pos_actual = pygame.math.Vector2(self.x, self.y)
                pos_enemigo = pygame.math.Vector2(enemigo.x, enemigo.y)
                dist_e = pos_actual.distance_to(pos_enemigo)

                if dist_e <= self.rango_vision:
                    if dist_e <= self.rango_ataque:
                        self.atacar(enemigo)
                    else:
                        dir_hacia = (pos_enemigo - pos_actual).normalize()
                        self.x += dir_hacia.x * self.velocidad
                        self.y += dir_hacia.y * self.velocidad

    def generador_enemigo_vivo(self, juego):
        return hasattr(juego, 'generador_enemigo') and juego.generador_enemigo.vida > 0

    def dibujar(self, pantalla, fuente=None, cam_x=0, cam_y=0):
        if self.vida <= 0: return
        pos_x = int(self.x - cam_x)
        pos_y = int(self.y - cam_y)
        pygame.draw.circle(pantalla, self.color, (pos_x, pos_y), self.radio)
        if self.seleccionada:
            pygame.draw.circle(pantalla, (255, 255, 255), (pos_x, pos_y), self.radio + 3, 1)

class Obrero(Tropa):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, vida=60, color=(255, 255, 0))
        self.velocidad = 2.5
        self.radio = 10

    def actualizar(self, estructuras_juego):
        pass

    def dibujar(self, pantalla, fuente=None, cam_x=0, cam_y=0):
        if self.vida <= 0: return
        pos_x = int(self.x - cam_x)
        pos_y = int(self.y - cam_y)
        pygame.draw.circle(pantalla, self.color, (pos_x, pos_y), self.radio)
        if self.seleccionada:
            pygame.draw.circle(pantalla, (255, 255, 255), (pos_x, pos_y), self.radio + 2, 1)

class Constructor(Tropa):
    def __init__(self, x, y, faccion):
        color = (230, 130, 40) if faccion != "enemigo" else (160, 90, 40)
        super().__init__(x, y, faccion, vida=50, color=color)
        self.radio = 12
        self.velocidad = 2.2
        self.dano = 0
        self._tiempo_ultimo_patrullaje = 0
        self._cooldown_patrullaje = random.uniform(3.0, 6.0)

    def actualizar(self, juego):
        if self.vida <= 0: return

        if self.tarea == "construir" and self.objetivo:
            if self.objetivo.vida <= 0 or self.objetivo.construida:
                self.tarea = None
                self.objetivo = None
                self.estado = "quieto"
            else:
                dist = math.hypot(self.objetivo.x - self.x, self.objetivo.y - self.y)
                if dist > 55:
                    dx = self.objetivo.x - self.x
                    dy = self.objetivo.y - self.y
                    self.x += (dx / dist) * self.velocidad
                    self.y += (dy / dist) * self.velocidad
                    self.estado = "moviendose"
                else:
                    self.estado = "quieto"
                    self.objetivo.recibir_construccion(self.velocidad_construccion)
            return

        if self.tarea is None or self.objetivo is None:
            planos_propios = [e for e in juego.estructuras if e.faccion == self.faccion and not e.construida]
            if planos_propios:
                self.tarea = "construir"
                self.objetivo = planos_propios[0]
            else:
                base = juego.generador_aliado if self.faccion == juego.faccion else juego.generador_enemigo
                if self.estado == "moviendose":
                    dist_destino = math.hypot(self.destinoX - self.x, self.destinoY - self.y)
                    if dist_destino > 5:
                        dx = self.destinoX - self.x
                        dy = self.destinoY - self.y
                        self.x += (dx / dist_destino) * self.velocidad
                        self.y += (dy / dist_destino) * self.velocidad
                    else:
                        self.estado = "quieto"
                        self._tiempo_ultimo_patrullaje = time.time()
                        self._cooldown_patrullaje = random.uniform(3.0, 6.0)
                else:
                    if time.time() - self._tiempo_ultimo_patrullaje >= self._cooldown_patrullaje:
                        self.destinoX = base.x + random.randint(-150, 150)
                        self.destinoY = base.y + random.randint(-150, 150)
                        self.destinoX = max(10, min(juego.ancho_mapa - 10, self.destinoX))
                        self.destinoY = max(10, min(juego.alto_mapa - 10, self.destinoY))
                        self.estado = "moviendose"

    def dibujar(self, pantalla, fuente=None, cam_x=0, cam_y=0):
        if self.vida <= 0: return
        pos_x = int(self.x - cam_x)
        pos_y = int(self.y - cam_y)
        pygame.draw.circle(pantalla, self.color, (pos_x, pos_y), self.radio)
        pygame.draw.circle(pantalla, (255, 255, 255), (pos_x, pos_y), self.radio - 4, 1)

class Generador:
    def __init__(self, x, y, faccion, color, tiempo_generacion_segundos=6, dano_unidades=10):
        self.x, self.y = x, y
        self.faccion, self.color = faccion, color
        self.cooldown = tiempo_generacion_segundos
        self.ultimo_spawn = time.time()
        self.vida_maxima = 2000
        self.vida = self.vida_maxima
        self.dano_unidades = dano_unidades

    def actualizar(self, juego_instancia):
        if self.vida <= 0: return
        tiempo_actual = time.time()
        
        if tiempo_actual - self.ultimo_spawn >= self.cooldown:
            costo_tropa = 75
            
            if self.faccion == "enemigo":
                if juego_instancia.oro_enemigo >= costo_tropa:
                    juego_instancia.oro_enemigo -= costo_tropa
                    nueva_tropa = Tropa(self.x + random.randint(-40, 40), self.y - 50, "enemigo", 100, self.color)
                    nueva_tropa.dano = self.dano_unidades
                    juego_instancia.mis_unidades.append(nueva_tropa)
                    self.ultimo_spawn = tiempo_actual
            else:
                nueva_tropa = Tropa(self.x + random.randint(-40, 40), self.y + 50, self.faccion, 100, self.color)
                nueva_tropa.dano = self.dano_unidades
                juego_instancia.mis_unidades.append(nueva_tropa)
                self.ultimo_spawn = tiempo_actual

    def dibujar(self, pantalla, fuente=None, cam_x=0, cam_y=0):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        if self.vida <= 0:
            pygame.draw.rect(pantalla, (60, 60, 60), (sx - 30, sy - 30, 60, 60), border_radius=4)
            return
        pygame.draw.rect(pantalla, self.color, (sx - 30, sy - 30, 60, 60), border_radius=6)
        bw, bx, by = 60, sx - 30, sy - 42
        pygame.draw.rect(pantalla, (40, 40, 40), (bx, by, bw, 5))
        pygame.draw.rect(pantalla, (220, 50, 50), (bx, by, int(bw * (self.vida / self.vida_maxima)), 5))