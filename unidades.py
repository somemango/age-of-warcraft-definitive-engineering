import pygame
import time  # Controlamos el tiempo de spawn de manera independiente a los FPS de pygame


class Tropa:
    # Constructor de la tropa con el color de facción y las variables de espacio físico
    def __init__(self, x, y, faccion, vida, color):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.vida = vida
        # Guarda el color (verde para aliados, rojo para enemigos)
        self.color = color
        self.estado = "quieto"
        self.destinoX = x
        self.destinoY = y
        self.velocidad = 2
        self.radio = 15  # El tamaño del círculo, nos sirve para el render y colisiones
        # Espacio personal mínimo para que no se encimen las unidades
        self.distancia_separacion = 45
        # Atributo para controlar si la unidad fue atrapada por el cuadro de selección
        self.seleccionada = False
        # Nuevos atributos para tareas
        self.tarea = None               # None | "construir" | "recolectar"
        self.objetivo = None            # referencia a la Estructura destino
        self.velocidad_construccion = 2  # puntos de progreso por frame al llegar
        # atributos para el ataque de las unidades
        self.dano = 10
        self.rango_ataque = 45
        self.cooldown_ataque = 60
        self.timer_ataque = 0
        self.objetivo_combate = None

    def buscar_enemigo_mas_cercano(self, todas_las_unidades):
        enemigo_mas_cercano = None
        distancia_minima = float('inf')
        pos_actual = pygame.math.Vector2(self.x, self.y)

        for otra in todas_las_unidades:
            # si es de otra faccion y tiene vida:
            if otra.faccion != self.faccion and otra.vida > 0:
                pos_otra = pygame.math.Vector2(otra.x, otra.y)
                distancia = (pos_actual - pos_otra).length()
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    enemigo_mas_cercano = otra

        return enemigo_mas_cercano

    def atacar(self, todas_las_unidades):
        # manejo del temporizador de ataque (cooldown)
        if self.timer_ataque > 0:
            self.timer_ataque -= 1

        # si no tiene objetivo manual o el objetivo ya murio, vuelve a estar quieto
        if self.objetivo_combate is None or self.objetivo_combate.vida <= 0:
            self.objetivo_combate = None
            self.estado = "quieto"
            return

        # calcular distancias vectoriales hacia el objetivo asignado
        pos_actual = pygame.math.Vector2(self.x, self.y)
        pos_enemigo = pygame.math.Vector2(self.objetivo_combate.x, self.objetivo_combate.y)
        direccion = pos_enemigo - pos_actual
        distancia = direccion.length()

        # si esta lejos lo persigue
        if distancia > self.rango_ataque:
            self.destinoX = self.objetivo_combate.x
            self.destinoY = self.objetivo_combate.y
            # forzamos que se traslade hacia alla
            self.estado = "moviendose" 
        else:
            # si esta en rango se detiene a atacar y empieza el cooldown
            if self.timer_ataque == 0:
                self.objetivo_combate.vida -= self.dano
                self.timer_ataque = self.cooldown_ataque
                print(f"¡Golpe manual! Vida del enemigo: {self.objetivo_combate.vida}")

    # Algoritmo de Flocking/Separación básica para que avancen en grupo respetando su distancia

    def movimiento(self, todas_las_unidades):
        posicion_actual = pygame.math.Vector2(self.x, self.y)
        fuerza_separacion = pygame.math.Vector2(0, 0)

        # Chequeamos la distancia con las demás unidades del mapa para evitar colisiones
        for otra in todas_las_unidades:
            if otra is not self:
                pos_otra = pygame.math.Vector2(otra.x, otra.y)
                direccion_escape = posicion_actual - pos_otra
                distancia = direccion_escape.length()

                # Si están muy pegadas, generamos un vector de empuje hacia el lado opuesto
                if distancia < self.distancia_separacion and distancia > 0:
                    direccion_escape.normalize_ip()
                    fuerza_separacion += direccion_escape * \
                        (self.distancia_separacion - distancia) * 0.15

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

                # Sumamos el movimiento hacia el objetivo con el empuje de separación
                vector_final = vector_movimiento + fuerza_separacion
                if vector_final.length() > self.velocidad:
                    vector_final.normalize_ip()
                    vector_final *= self.velocidad

                self.x += vector_final.x
                self.y += vector_final.y
        else:
            # Si la unidad está quieta pero otra la empuja al llegar, se mueve un poco para dar espacio
            if fuerza_separacion.length() > 0:
                if fuerza_separacion.length() > self.velocidad:
                    fuerza_separacion.normalize_ip()
                    fuerza_separacion *= self.velocidad
                self.x += fuerza_separacion.x
                self.y += fuerza_separacion.y

    # Renderizado de la unidad
    def dibujar(self, pantalla):
        # Dibujamos el círculo base de la tropa
        pygame.draw.circle(pantalla, self.color,
                           (int(self.x), int(self.y)), self.radio)

        # Aro verde oscuro (0, 100, 0) y delgado para las unidades seleccionadas
        if self.seleccionada and self.faccion == "sistemas":
            pygame.draw.circle(pantalla, (0, 100, 0), (int(
                self.x), int(self.y)), self.radio + 3, 1)

        # barra de vida
        if self.vida < 100:
            ancho_barra = 20
            bx = int(self.x) - ancho_barra // 2
            by = int(self.y) - self.radio - 6

            # Fondo rojo oscuro
            pygame.draw.rect(pantalla, (100, 0, 0), (bx, by, ancho_barra, 4))

            # Barra verde que se encoge con la vida actual
            ancho_verde = int(ancho_barra * (self.vida / 100))
            if ancho_verde > 0:
                pygame.draw.rect(pantalla, (0, 255, 0), (bx, by, ancho_verde, 4))

# Estructuras fijas del mapa que generan reclutas automáticamente
class Generador:
    def __init__(self, x, y, faccion, color, tiempo_generacion_segundos=3):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.color = color  # Este color ahora se queda exclusivo para pintar el edificio
        self.cooldown = tiempo_generacion_segundos
        self.ultimo_spawn = time.time()

    # Controla el reloj del cooldown y clava el límite de población en 5 tropas vivas por bando
    def actualizar(self, lista_unidades):
        tiempo_actual = time.time()
        unidades_faccion = [
            u for u in lista_unidades if u.faccion == self.faccion]

        if len(unidades_faccion) < 5:
            if tiempo_actual - self.ultimo_spawn >= self.cooldown:
                # MODIFICADO: Separamos el color de la unidad del color de la base.
                # Si somos "sistemas", forzamos que la tropa nazca verde chillón (0, 255, 0) aunque el cuadrado sea oscuro.
                color_tropa = (
                    0, 255, 0) if self.faccion == "sistemas" else self.color

                nueva_tropa = Tropa(
                    self.x, self.y, self.faccion, 100, color_tropa)

                # Si es la base enemiga, mandamos a los rojos a marchar a un punto cercano para que salgan del spawn
                if self.faccion == "enemigos":
                    nueva_tropa.destinoX = 550
                    nueva_tropa.destinoY = 400
                    nueva_tropa.estado = "moviendose"

                lista_unidades.append(nueva_tropa)
                self.ultimo_spawn = tiempo_actual

    # Dibuja la estructura como un cuadrado de 60x60
    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, self.color,
                         (self.x - 30, self.y - 30, 60, 60))
