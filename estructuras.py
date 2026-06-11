import pygame


class Estructura:
    """Clase base para todas las estructuras del mapa."""

    COLOR_BARRA = (80, 180, 80)
    COLOR_BARRA_FONDO = (60, 60, 60)
    COLOR_EDIFICIO = (150, 150, 200)

    def __init__(self, x, y, faccion, costo):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.costo = costo
        self.progreso = 0       # 0 a 100
        self.construida = False
        self.nivel = 1

    def recibir_construccion(self, cantidad):
        """Suma progreso de construcción. Aplica mod_linea_ensamblaje si corresponde."""
        juego = getattr(self, "_juego", None)
        mod = 1.0
        if juego is not None and self.faccion == juego.faccion:
            mod = 1.0 / getattr(juego, "mod_linea_ensamblaje", 1.0)
        self.progreso = min(100, self.progreso + cantidad * mod)
        if self.progreso >= 100:
            self.construida = True
            self.al_construirse()

    def al_construirse(self):
        """Llamado una sola vez cuando la construcción termina. Subclases lo pueden sobrescribir."""
        pass

    def actualizar(self, juego):
        """Lógica por frame una vez construida. Guarda referencia al juego y subclases lo sobrescriben."""
        self._juego = juego  # disponible para recibir_construccion

    def dibujar(self, pantalla, fuente):
        # Cuerpo del edificio
        color = self.COLOR_EDIFICIO if self.construida else (100, 100, 140)
        pygame.draw.rect(pantalla, color, (self.x - 25,
                         self.y - 25, 50, 50), border_radius=4)
        pygame.draw.rect(pantalla, (200, 200, 255), (self.x -
                         25, self.y - 25, 50, 50), width=1, border_radius=4)

        # Etiqueta
        nombre = self.__class__.__name__
        txt = fuente.render(nombre, True, (220, 220, 255))
        pantalla.blit(txt, (self.x - txt.get_width() // 2, self.y - 44))

        # Barra de construcción (solo mientras no está terminada)
        if not self.construida:
            barra_x = self.x - 25
            barra_y = self.y + 30
            pygame.draw.rect(pantalla, self.COLOR_BARRA_FONDO,
                             (barra_x, barra_y, 50, 6), border_radius=3)
            ancho_progreso = int(50 * self.progreso / 100)
            pygame.draw.rect(pantalla, self.COLOR_BARRA, (barra_x,
                             barra_y, ancho_progreso, 6), border_radius=3)


# ----------------------------------------------------------------------
# Subclases
# ----------------------------------------------------------------------

class Cuartel(Estructura):
    """Produce tropas con una cola de entrenamiento."""

    COLOR_EDIFICIO = (80, 100, 180)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=150)
        self.cola = []                  # lista de nombres de tropa a entrenar
        self.timer_entrenamiento = 0    # frames transcurridos
        self.tiempo_entrenamiento = 300  # frames por tropa (5 seg a 60fps)

    def encolar_tropa(self, tipo="basica"):
        self.cola.append(tipo)

    def actualizar(self, juego):
        if not self.construida or not self.cola:
            return

        # mod_entrena: velocidad base de entrenamiento (Compilador/BaseDatos)
        # mod_manufactura: duplica la velocidad de entrenamiento (Manufactura industrial)
        mod_entrena = getattr(juego, "mod_entrena", 1.0)
        mod_manufactura = getattr(juego, "mod_manufactura", 1.0)
        self.timer_entrenamiento += mod_entrena * mod_manufactura

        if self.timer_entrenamiento >= self.tiempo_entrenamiento:
            self.timer_entrenamiento = 0
            self.cola.pop(0)
            from unidades import Tropa
            color = (0, 200, 80) if self.faccion != "enemigo" else (255, 60, 60)
            nueva = Tropa(self.x + 40, self.y, self.faccion, 100, color)

            # Solo aplicar mods de habilidades a tropas de la facción del jugador
            if self.faccion == juego.faccion:
                nueva.dano = int(nueva.dano * getattr(juego, "mod_danno", 1.0))
                nueva.vida = int(nueva.vida * getattr(juego, "mod_vida_tropas", 1.0))
                nueva.velocidad *= getattr(juego, "mod_banda_ancha", 1.0)
                nueva.rango_ataque = int(
                    nueva.rango_ataque * getattr(juego, "mod_antena_amplificadora", 1.0))

            juego.mis_unidades.append(nueva)


class Mina(Estructura):
    """Genera oro por frame cuando hay recolectores asignados."""

    COLOR_EDIFICIO = (180, 150, 60)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=100)
        self.oro_por_frame = 0.05

    def actualizar(self, juego):
        if not self.construida:
            return
        mod = getattr(juego, "mod_mejor_mina", 1.0)
        juego.oro += self.oro_por_frame * mod


class Granja(Estructura):
    """Aumenta el límite de tropas y genera comida."""

    COLOR_EDIFICIO = (80, 160, 80)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=80)
        self.limite_extra = 5
        self._bonus_aplicado = False

    def al_construirse(self):
        self._bonus_aplicado = False    # se aplica en el primer actualizar

    def actualizar(self, juego):
        if not self.construida:
            return
        if not self._bonus_aplicado:
            juego.limite_tropas = getattr(
                juego, "limite_tropas", 10) + self.limite_extra
            self._bonus_aplicado = True


# ----------------------------------------------------------------------
# Estructuras exclusivas por facción
# ----------------------------------------------------------------------

class BaseDatos(Estructura):
    """[SISTEMAS] Genera oro pasivamente y aplica buff de velocidad de entrenamiento
    a todos los cuarteles aliados mientras esté activa."""

    COLOR_EDIFICIO = (60, 120, 200)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=180)
        self.oro_por_frame = 0.08           # Más rentable que la Mina básica
        self.buff_entrena = 1.3             # +30 % velocidad de entrenamiento
        self._buff_aplicado = False

    def al_construirse(self):
        self._buff_aplicado = False

    def actualizar(self, juego):
        if not self.construida:
            return

        # Genera oro pasivo
        mod = getattr(juego, "mod_oro", 1.0)
        juego.oro += self.oro_por_frame * mod

        # Aplica buff de entrenamiento una sola vez
        if not self._buff_aplicado:
            juego.mod_entrena = max(getattr(juego, "mod_entrena", 1.0), self.buff_entrena)
            self._buff_aplicado = True

    def dibujar(self, pantalla, fuente):
        super().dibujar(pantalla, fuente)
        if self.construida:
            # Icono: dos cilindros pequeños (representan discos de BD)
            cx, cy = self.x, self.y
            for i, dy in enumerate([-7, 5]):
                pygame.draw.ellipse(pantalla, (100, 180, 255), (cx - 12, cy + dy - 4, 24, 8))
                pygame.draw.ellipse(pantalla, (160, 220, 255), (cx - 12, cy + dy - 4, 24, 8), 1)


class Torreta(Estructura):
    """[CIVIL] Dispara automáticamente al enemigo más cercano dentro de su rango."""

    COLOR_EDIFICIO = (160, 80, 60)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=220)
        self.rango = 150
        self.dano = 15
        self.cooldown = 90              # Frames entre disparos (1.5 seg)
        self.timer = 0
        self.objetivo = None
        self._angulo = 0                # Para animar el cañón

    def actualizar(self, juego):
        if not self.construida:
            return

        if self.timer > 0:
            self.timer -= 1

        # Buscar enemigo más cercano dentro del rango
        self.objetivo = None
        distancia_min = self.rango
        for unidad in juego.mis_unidades:
            if unidad.faccion != self.faccion and unidad.vida > 0:
                dist = pygame.math.Vector2(
                    self.x - unidad.x, self.y - unidad.y).length()
                if dist < distancia_min:
                    distancia_min = dist
                    self.objetivo = unidad

        # Disparar
        if self.objetivo and self.timer == 0:
            self.objetivo.vida -= self.dano
            self.timer = self.cooldown

    def dibujar(self, pantalla, fuente):
        super().dibujar(pantalla, fuente)
        if self.construida:
            # Base circular de la torreta
            pygame.draw.circle(pantalla, (120, 60, 40), (self.x, self.y), 14)
            pygame.draw.circle(pantalla, (200, 100, 80), (self.x, self.y), 14, 2)

            # Cañón apuntando al objetivo (o hacia arriba si no hay)
            if self.objetivo:
                dx = self.objetivo.x - self.x
                dy = self.objetivo.y - self.y
                vec = pygame.math.Vector2(dx, dy)
                if vec.length() > 0:
                    vec.normalize_ip()
                    vec *= 18
            else:
                vec = pygame.math.Vector2(0, -18)

            pygame.draw.line(pantalla, (220, 220, 220),
                             (self.x, self.y),
                             (int(self.x + vec.x), int(self.y + vec.y)), 4)

            # Círculo de rango (tenue)
            rango_surf = pygame.Surface((self.rango * 2, self.rango * 2), pygame.SRCALPHA)
            pygame.draw.circle(rango_surf, (255, 80, 60, 25),
                               (self.rango, self.rango), self.rango)
            pygame.draw.circle(rango_surf, (255, 80, 60, 60),
                               (self.rango, self.rango), self.rango, 1)
            pantalla.blit(rango_surf, (self.x - self.rango, self.y - self.rango))

            # Flash de disparo
            if self.timer > self.cooldown - 5 and self.objetivo:
                pygame.draw.line(pantalla, (255, 220, 80),
                                 (self.x, self.y),
                                 (self.objetivo.x, self.objetivo.y), 2)


class Antena(Estructura):
    """[TELECOMUNICACIONES] Amplía el campo de visión aliado y genera un pulso
    periódico que ralentiza a los enemigos cercanos."""

    COLOR_EDIFICIO = (80, 180, 160)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=160)
        self.rango_pulso = 120
        self.ralentizacion = 0.5        # Multiplicador de velocidad (50 % más lento)
        self.intervalo_pulso = 300      # Frames entre pulsos (5 seg)
        self.timer_pulso = 0
        self._pulso_visual = 0          # Para animar el pulso

    def actualizar(self, juego):
        if not self.construida:
            return

        self.timer_pulso += 1
        if self._pulso_visual > 0:
            self._pulso_visual -= 4

        if self.timer_pulso >= self.intervalo_pulso:
            self.timer_pulso = 0
            self._pulso_visual = self.rango_pulso  # Activa animación

            # Ralentizar enemigos cercanos temporalmente
            for unidad in juego.mis_unidades:
                if unidad.faccion != self.faccion:
                    dist = pygame.math.Vector2(
                        self.x - unidad.x, self.y - unidad.y).length()
                    if dist <= self.rango_pulso:
                        unidad.velocidad = max(
                            0.5, unidad.velocidad * self.ralentizacion)

    def dibujar(self, pantalla, fuente):
        super().dibujar(pantalla, fuente)
        if self.construida:
            # Palo vertical de la antena
            pygame.draw.line(pantalla, (160, 230, 210),
                             (self.x, self.y + 12), (self.x, self.y - 20), 3)
            # Brazos laterales en V
            pygame.draw.line(pantalla, (160, 230, 210),
                             (self.x, self.y - 8), (self.x - 14, self.y - 20), 2)
            pygame.draw.line(pantalla, (160, 230, 210),
                             (self.x, self.y - 8), (self.x + 14, self.y - 20), 2)
            # Punto parpadeante en la punta
            color_punto = (80, 255, 200) if (self.timer_pulso // 30) % 2 == 0 else (40, 120, 100)
            pygame.draw.circle(pantalla, color_punto, (self.x, self.y - 20), 3)

            # Onda del pulso visual
            if self._pulso_visual > 0:
                alpha = int(180 * (self._pulso_visual / self.rango_pulso))
                radio_actual = self.rango_pulso - self._pulso_visual
                pulso_surf = pygame.Surface(
                    (self.rango_pulso * 2, self.rango_pulso * 2), pygame.SRCALPHA)
                pygame.draw.circle(pulso_surf, (80, 255, 200, alpha),
                                   (self.rango_pulso, self.rango_pulso), radio_actual, 2)
                pantalla.blit(pulso_surf, (self.x - self.rango_pulso, self.y - self.rango_pulso))


class MinaMejorada(Estructura):
    """[INDUSTRIAL] Genera oro a alta velocidad y además produce un bono de armadura
    a las tropas aliadas cercanas."""

    COLOR_EDIFICIO = (200, 140, 40)

    def __init__(self, x, y, faccion):
        super().__init__(x, y, faccion, costo=200)
        self.oro_por_frame = 0.15           # Triple que la Mina básica
        self.rango_armadura = 100
        self.bonus_armadura = 5             # Reduce el daño recibido
        self._armadura_aplicada = set()     # IDs de unidades ya buffeadas
        self._particulas = []               # Mini partículas de chispa visual

    def actualizar(self, juego):
        if not self.construida:
            return

        # Generar oro (beneficiada por Minas Mejoradas si es la facción industrial)
        mod = getattr(juego, "mod_mejor_mina", 1.0)
        juego.oro += self.oro_por_frame * mod

        # Aplicar armadura a tropas aliadas cercanas (solo una vez por unidad)
        for unidad in juego.mis_unidades:
            if unidad.faccion == self.faccion and id(unidad) not in self._armadura_aplicada:
                dist = pygame.math.Vector2(
                    self.x - unidad.x, self.y - unidad.y).length()
                if dist <= self.rango_armadura:
                    unidad.dano_reduccion = getattr(unidad, "dano_reduccion", 0) + self.bonus_armadura
                    self._armadura_aplicada.add(id(unidad))

        # Limpiar IDs de unidades muertas para no acumular memoria
        ids_vivos = {id(u) for u in juego.mis_unidades}
        self._armadura_aplicada &= ids_vivos

        # Generar partículas de chispa ocasionalmente
        import random
        if random.random() < 0.15:
            import math
            angulo = random.uniform(0, math.pi * 2)
            self._particulas.append({
                "x": self.x + random.randint(-10, 10),
                "y": self.y + random.randint(-10, 10),
                "vx": math.cos(angulo) * random.uniform(0.5, 2),
                "vy": math.sin(angulo) * random.uniform(0.5, 2) - 1.5,
                "vida": random.randint(15, 30),
            })

        # Actualizar partículas
        for p in self._particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
        self._particulas = [p for p in self._particulas if p["vida"] > 0]

    def dibujar(self, pantalla, fuente):
        super().dibujar(pantalla, fuente)
        if self.construida:
            # Engranaje central simplificado (hexágono)
            import math
            cx, cy, r = self.x, self.y, 10
            puntos = [
                (cx + r * math.cos(math.radians(60 * i - 30)),
                 cy + r * math.sin(math.radians(60 * i - 30)))
                for i in range(6)
            ]
            pygame.draw.polygon(pantalla, (255, 180, 40), puntos)
            pygame.draw.polygon(pantalla, (255, 220, 100), puntos, 2)
            pygame.draw.circle(pantalla, (60, 40, 20), (cx, cy), 4)

            # Dibujar partículas de chispa
            for p in self._particulas:
                alpha = int(255 * (p["vida"] / 30))
                color = (255, min(255, 150 + alpha // 2), 0)
                pygame.draw.circle(pantalla, color, (int(p["x"]), int(p["y"])), 2)
