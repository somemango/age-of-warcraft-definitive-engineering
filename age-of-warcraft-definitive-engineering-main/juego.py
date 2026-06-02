import pygame
from unidades import Tropa, Generador

class Juego:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.oro = 100
        self.mis_unidades = []  # Lista global única para procesar la física y colisiones de todos a la vez

        # Tracking del destino global para meter en vereda a las unidades aliadas que vayan naciendo después
        self.ultimo_destino_x = 100
        self.ultimo_destino_y = 100
        self.estado_actual_ordenado = "quieto"

        # Variables para gestionar el cuadro de selección con el clic izquierdo
        self.seleccionando = False
        self.inicio_seleccion = (0, 0)
        self.fin_seleccion = (0, 0)

        # El generador aliado se mantiene con su color verde oscuro (0, 125, 0)
        self.generador_aliado = Generador(100, 100, "sistemas", (0, 125, 0), tiempo_generacion_segundos=3)
        self.generador_enemigo = Generador(700, 500, "enemigos", (255, 0, 0), tiempo_generacion_segundos=3)
        
        # Unidad inicial del bando aliado (verde brillante)
        self.mis_unidades.append(Tropa(150, 150, "sistemas", 100, (0, 255, 0)))

    # Captura las interacciones del teclado y el mouse
    def procesar_eventos(self, event):
        # Clic derecho: Mueve a las unidades elegidas
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos
            
            self.ultimo_destino_x = mouse_x
            self.ultimo_destino_y = mouse_y
            self.estado_actual_ordenado = "moviendose"

            for unidad in self.mis_unidades:
                # Ahora solo le damos la orden de marcha si es de nuestra facción Y está seleccionada
                if unidad.faccion == "sistemas" and unidad.seleccionada:
                    unidad.destinoX = mouse_x
                    unidad.destinoY = mouse_y
                    unidad.estado = "moviendose"

        # Captura el inicio del cuadro al pisar el clic izquierdo
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.seleccionando = True
            self.inicio_seleccion = event.pos
            self.fin_seleccion = event.pos

        # Actualiza la esquina del cuadro mientras arrastras el mouse
        elif event.type == pygame.MOUSEMOTION and self.seleccionando:
            self.fin_seleccion = event.pos

        # Al soltar el clic izquierdo, calculamos el área definitiva y seleccionamos tropas
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.seleccionando:
                self.seleccionando = False
                self.fin_seleccion = event.pos
                self.evaluar_seleccion_multiple()

    # Método matemático para verificar qué unidades cayeron dentro del cuadro
    def evaluar_seleccion_multiple(self):
        x_min = min(self.inicio_seleccion[0], self.fin_seleccion[0])
        x_max = max(self.inicio_seleccion[0], self.fin_seleccion[0])
        y_min = min(self.inicio_seleccion[1], self.fin_seleccion[1])
        y_max = max(self.inicio_seleccion[1], self.fin_seleccion[1])

        # Recorremos la lista y marcamos/desmarcamos según las coordenadas del rectángulo
        for unidad in self.mis_unidades:
            if unidad.faccion == "sistemas":  # Solo seleccionamos las nuestras, las rojas se ignoran
                if x_min <= unidad.x <= x_max and y_min <= unidad.y <= y_max:
                    unidad.seleccionada = True
                else:
                    unidad.seleccionada = False

    # Actualización lógica del estado del juego frame a frame
    def actualizar(self):
        self.generador_aliado.actualizar(self.mis_unidades)
        self.generador_enemigo.actualizar(self.mis_unidades)

        for unidad in self.mis_unidades:
            # Si nace una unidad aliada seleccionada y el grupo se movía, hereda las coordenadas globales de destino
            if unidad.faccion == "sistemas" and unidad.seleccionada:
                if self.estado_actual_ordenado == "moviendose" and unidad.destinoX != self.ultimo_destino_x:
                    unidad.destinoX = self.ultimo_destino_x
                    unidad.destinoY = self.ultimo_destino_y
                    unidad.estado = "moviendose"
            
            unidad.movimiento(self.mis_unidades)

    # Dibuja los componentes en la pantalla (las estructuras van primero en el fondo)
    def dibujar(self):
        self.generador_aliado.dibujar(self.pantalla)
        self.generador_enemigo.dibujar(self.pantalla)
        
        for unidad in self.mis_unidades:
            unidad.dibujar(self.pantalla)

        # Si el usuario está arrastrando el mouse, renderizamos el cuadro verde de selección
        if self.seleccionando:
            x = min(self.inicio_seleccion[0], self.fin_seleccion[0])
            y = min(self.inicio_seleccion[1], self.fin_seleccion[1])
            ancho = abs(self.fin_seleccion[0] - self.inicio_seleccion[0])
            alto = abs(self.fin_seleccion[1] - self.inicio_seleccion[1])
            
            rectangulo = pygame.Rect(x, y, ancho, alto)
            pygame.draw.rect(self.pantalla, (0, 255, 0), rectangulo, 1)  # Rectángulo verde sin relleno de 1 píxel de borde