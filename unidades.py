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
        self.dano = 10
        self.rango_ataque = 45
        self.cooldown_ataque = 60
        self.timer_ataque = 0

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

    def ejecutar_tareas(self, todas_las_unidades, juego):
        # Manejo pasivo del timer de ataque
        if self.timer_ataque > 0:
            self.timer_ataque -= 1

        # 1. ORDEN: CONSTRUIR
        if self.tarea == "construir" and self.objetivo:
            # Medimos distancia al edificio
            distancia = pygame.math.Vector2(self.x - self.objetivo.x, self.y - self.objetivo.y).length()
            if distancia <= self.radio + 35:
                self.estado = "quieto"
                self.objetivo.recibir_construccion(self.velocidad_construccion)
                if self.objetivo.construida:
                    self.tarea = None
                    self.objetivo = None
            else:
                self.destinoX = self.objetivo.x
                self.destinoY = self.objetivo.y
                self.estado = "moviendose"
                self.movimiento(todas_las_unidades, self)

        # 2. ORDEN: ATACAR
        elif self.tarea == "atacar" and self.objetivo_combate:
            if self.objetivo_combate.vida > 0:
                distancia = pygame.math.Vector2(self.x - self.objetivo_combate.x, self.y - self.objetivo_combate.y).length()
                if distancia > self.rango_ataque:
                    self.destinoX = self.objetivo_combate.x
                    self.destinoY = self.objetivo_combate.y
                    self.movimiento(todas_las_unidades, self)
                else:
                    if self.timer_ataque == 0:
                        self.objetivo_combate.vida -= self.dano
                        self.timer_ataque = self.cooldown_ataque
            else:
                self.tarea = None
                self.objetivo_combate = None
                self.estado = "quieto"

        # 3. SIN ÓRDENES ESPECIALES (Solo caminar o quedarse quieto)
        else:
            self.movimiento(todas_las_unidades, self)

    def movimiento(self, todas_las_unidades, juego):
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
                    vel_final = self.velocidad * getattr(juego, "mod_banda_ancha", 1.0)
                    vector_movimiento = direccion * vel_final
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
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)

        # Dibujamos base del soldado
        if -30 <= screen_x <= 830 and -30 <= screen_y <= 630:
            u.dibujar(self.pantalla, self.camara_x, self.camara_y)

        # Aro de selección
        if self.seleccionada and self.faccion == "sistemas":
            pygame.draw.circle(pantalla, (255, 255, 255), (screen_x, screen_y), self.radio + 3, 1)

        # Barra de vida flotante
        if self.vida < 100:
            screen_x = self.x - camara_x
            screen_y = self.y - camara_y
            ancho_barra = 26
            bx = int(screen_x) - (ancho_barra // 2)
            by = int(screen_y) - self.radio - 6

            # Fondo rojo oscuro
            pygame.draw.rect(pantalla, (100, 0, 0), (bx, by, ancho_barra, 4))
            # Vida actual en verde
            ancho_verde = int(ancho_barra * max(0, (self.vida / 100)))
            if ancho_verde > 0:
                pygame.draw.rect(pantalla, (0, 255, 0), (bx, by, ancho_verde, 4))

class Generador:
    def __init__(self, x, y, faccion, color, tiempo_generacion_segundos=3):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.color = color 
        self.cooldown = tiempo_generacion_segundos
        self.ultimo_spawn = time.time()

    def actualizar(self, lista_unidades):
        tiempo_actual = time.time()
        unidades_faccion = [u for u in lista_unidades if u.faccion == self.faccion]

        if len(unidades_faccion) < 5:
            if tiempo_actual - self.ultimo_spawn >= self.cooldown:
                color_tropa = (0, 255, 0) if self.faccion == "sistemas" else self.color
                nueva_tropa = Tropa(self.x, self.y, self.faccion, 100, color_tropa)

                if self.faccion == "enemigos":
                    nueva_tropa.destinoX = 550
                    nueva_tropa.destinoY = 400
                    nueva_tropa.estado = "moviendose"

                lista_unidades.append(nueva_tropa)
                self.ultimo_spawn = tiempo_actual

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, self.color, (self.x - 30, self.y - 30, 60, 60))