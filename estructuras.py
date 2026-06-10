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
        """Suma progreso de construcción. Acepta modificadores externos."""
        self.progreso = min(100, self.progreso + cantidad)
        if self.progreso >= 100:
            self.construida = True
            self.al_construirse()

    def al_construirse(self):
        """Llamado una sola vez cuando la construcción termina. Subclases lo pueden sobrescribir."""
        pass

    def actualizar(self, juego):
        """Lógica por frame una vez construida. Subclases lo sobrescriben."""
        pass

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

        # Aplica modificador de habilidad si existe
        mod = getattr(juego, "mod_entrena", 1.0)
        self.timer_entrenamiento += mod

        if self.timer_entrenamiento >= self.tiempo_entrenamiento:
            self.timer_entrenamiento = 0
            self.cola.pop(0)
            # Genera la tropa cerca del cuartel
            from unidades import Tropa
            nueva = Tropa(self.x + 40, self.y, self.faccion, 100, (0, 255, 0))
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
        # Aplica modificador de habilidad si existe
        mod = getattr(juego, "mod_oro", 1.0)
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
