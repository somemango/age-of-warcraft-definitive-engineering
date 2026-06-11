import pygame
import time
import random
import math

class Estructura:
    COLOR_BARRA = (80, 180, 80)
    COLOR_BARRA_FONDO = (60, 60, 60)
    COLOR_EDIFICIO = (150, 150, 200)

    def __init__(self, x, y, faccion, costo):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.costo = costo
        self.progreso = 0       
        self.construida = False
        self.nivel = 1
        self.vida_maxima = 500  
        self.vida = self.vida_maxima
        self.radio = 45

    def recibir_construccion(self, cantidad):
        juego = getattr(self, "_juego", None)
        mod = 1.0
        if juego is not None and self.faccion == juego.faccion:
            mod = 1.0 / getattr(juego, "mod_linea_ensamblaje", 1.0)
        self.progreso = min(100, self.progreso + cantidad * mod)
        if self.progreso >= 100:
            self.construida = True
            self.al_construirse()

    def al_construirse(self):
        pass

    def actualizar(self, juego):
        pass

    def dibujar(self, pantalla, fuente):
        color_render = self.COLOR_EDIFICIO if self.construida else (110, 110, 150)
        if self.faccion == "enemigo":
            color_render = (180, 70, 70) if self.construida else (130, 60, 60)

        pygame.draw.rect(pantalla, color_render, (self.x - 35, self.y - 35, 70, 70), border_radius=5)
        pygame.draw.rect(pantalla, (255, 255, 255), (self.x - 35, self.y - 35, 70, 70), width=1, border_radius=5)

        nombre = self.__class__.__name__[:4].upper()
        txt = fuente.render(nombre, True, (240, 240, 240))
        pantalla.blit(txt, (self.x - txt.get_width() // 2, self.y - txt.get_height() // 2))

        if not self.construida:
            pygame.draw.rect(pantalla, self.COLOR_BARRA_FONDO, (self.x - 35, self.y - 48, 70, 6))
            pygame.draw.rect(pantalla, (240, 200, 40), (self.x - 35, self.y - 48, int(70 * (self.progreso / 100.0)), 6))
        elif self.vida < self.vida_maxima:
            pygame.draw.rect(pantalla, self.COLOR_BARRA_FONDO, (self.x - 35, self.y - 48, 70, 6))
            pygame.draw.rect(pantalla, (230, 40, 40), (self.x - 35, self.y - 48, int(70 * (self.vida / self.vida_maxima)), 6))

class Cuartel(Estructura):
    def __init__(self, x, y, faccion): 
        super().__init__(x, y, faccion, 150)
        self.ultimo_spawn = time.time()
        self.cooldown_spawn = 12.0 

    def actualizar(self, juego):
        if not self.construida: return
        
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_spawn >= self.cooldown_spawn:
            from unidades import Constructor
            
            cantidad_constructores = sum(1 for u in juego.mis_unidades if isinstance(u, Constructor) and u.faccion == self.faccion)
            
            if cantidad_constructores < 5:
                desfase_x = random.randint(-30, 30)
                desfase_y = 50 if self.faccion != "enemigo" else -50
                nuevo_constructor = Constructor(self.x + desfase_x, self.y + desfase_y, self.faccion)
                juego.mis_unidades.append(nuevo_constructor)
                
            self.ultimo_spawn = tiempo_actual

class Mina(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 100)
        self._last_tick = time.time()

    def actualizar(self, juego):
        if not self.construida: return
        ahora = time.time()
        if ahora - self._last_tick >= 1.0:
            val = 2.0 * getattr(juego, "mod_mina_oro", 1.0)
            if self.faccion == juego.faccion:
                juego.oro += val
            else:
                juego.oro_enemigo = getattr(juego, "oro_enemigo", 0) + val
            self._last_tick = ahora

class Granja(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 80)

    def al_construirse(self):
        juego = getattr(self, "_juego", None)
        if juego and self.faccion == juego.faccion:
            juego.max_poblacion = getattr(juego, "max_poblacion", 10) + 5

class BaseDatos(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 180)
        self._last_tick = time.time()

    def actualizar(self, juego):
        if not self.construida: return
        ahora = time.time()
        if ahora - self._last_tick >= 1.0:
            if self.faccion == juego.faccion:
                juego.oro += 4.0
            self._last_tick = ahora

class Torreta(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 220)
        self.rango = 180
        self.dano = 15
        self.cooldown = 45
        self.timer = 0

    def actualizar(self, juego):
        if not self.construida: return
        if self.timer > 0:
            self.timer -= 1
            return

        alrededor = juego.mis_unidades
        objetivo = None
        for u in alrededor:
            if u.faccion != self.faccion and u.vida > 0:
                if math.hypot(u.x - self.x, u.y - self.y) <= self.rango:
                    objetivo = u
                    break

        if objetivo:
            objetivo.vida -= self.dano
            self.timer = self.cooldown

class Antena(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 160)
        self.rango = 220

    def actualizar(self, juego):
        if not self.construida: return
        for u in juego.mis_unidades:
            if u.faccion != self.faccion and u.vida > 0:
                if math.hypot(u.x - self.x, u.y - self.y) <= self.rango:
                    u.velocidad = 1.0
                else:
                    u.velocidad = 2.0

class MinaMejorada(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 200)
        self._last_tick = time.time()

    def actualizar(self, juego):
        if not self.construida: return
        ahora = time.time()
        if ahora - self._last_tick >= 1.0:
            if self.faccion == juego.faccion:
                juego.oro += 6.0
            self._last_tick = ahora

class Muro(Estructura):
    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, 50)
        # 🧱 Vida aumentada 1.5x respecto al estándar (500 * 1.5 = 750)
        self.vida_maxima = 750
        self.vida = self.vida_maxima