"""
Sistema de árbol de habilidades por facción.

Uso desde Juego:
    self.habilidades = ArbolHabilidades("sistemas", self)
    self.habilidades.desbloquear("compilador")
"""


# ------------------------------------------------------------------
# Definición de los árboles
# ------------------------------------------------------------------

ARBOLES = {
    "sistemas": {
        "algoritmo_eficiente": {
            "nombre": "Algoritmo eficiente",
            "costo": 100,
            "requiere": None,
            # +20% daño a las tropas aliadas YA existentes y futuras (via mod_danno_sistemas)
            "efecto": lambda juego: _buff_danno_tropas(juego, 1.20),
        },
        "compilador": {
            "nombre": "Compilador",
            "costo": 500,
            "requiere": "algoritmo_eficiente",
            # +20% velocidad de entrenamiento
            "efecto": lambda juego: setattr(juego, "mod_entrena", 1.20),
        },
        "base_de_datos": {
            "nombre": "Base de Datos",
            "costo": 1000,
            "requiere": "compilador",
            # Desbloquea el edificio BaseDatos en el menú de construcción
            "efecto": lambda juego: juego._desbloquear_edificio_exclusivo(),
        },
    },
    "civil": {
        "torreta_cemento": {
            "nombre": "Torreta de Cemento",
            "costo": 120,
            "requiere": None,
            # Desbloquea la Torreta en el menú de construcción
            "efecto": lambda juego: juego._desbloquear_edificio_exclusivo(),
        },
        "reforzamiento": {
            "nombre": "Reforzamiento",
            "costo": 500,
            "requiere": "torreta_cemento",
            # +50% vida a tropas aliadas existentes y futuras
            "efecto": lambda juego: _buff_vida_tropas(juego, 1.5),
        },
        "planificacion_urbana": {
            "nombre": "Planificacion Urbana",
            "costo": 300,
            "requiere": "reforzamiento",
            # +30% vida a todas las estructuras (aplica multiplicador global)
            "efecto": lambda juego: setattr(juego, "mod_planificacion_urbana", 1.3),
        },
    },
    "industrial": {
        "mejor_mina": {
            "nombre": "Minas Mejoradas",
            "costo": 0,
            "requiere": None,
            # Minas producen 20% más oro
            "efecto": lambda juego: setattr(juego, "mod_mejor_mina", 1.2),
        },
        "linea_ensamblaje": {
            "nombre": "Linea de Ensamblaje",
            "costo": 250,
            "requiere": "mejor_mina",
            # Desbloquea MinaMejorada + estructuras tardan 20% menos en construirse
            "efecto": lambda juego: (_aplicar_linea_ensamblaje(juego)),
        },
        "manufactura": {
            "nombre": "Manufactura",
            "costo": 1100,
            "requiere": "linea_ensamblaje",
            # Unidades se producen el doble de rápido
            "efecto": lambda juego: setattr(juego, "mod_manufactura", 2.0),
        },
    },
    "telecomunicaciones": {
        "antena_amplificadora": {
            "nombre": "Antena Amplificadora",
            "costo": 200,
            "requiere": None,
            # Triplica el rango de ataque de tropas aliadas
            "efecto": lambda juego: _buff_rango_tropas(juego, 3.0),
        },
        "banda_ancha": {
            "nombre": "Banda Ancha",
            "costo": 350,
            "requiere": "antena_amplificadora",
            # +50% velocidad de movimiento a tropas aliadas
            "efecto": lambda juego: _buff_velocidad_tropas(juego, 1.5),
        },
        "antena_suprema": {
            "nombre": "Antena Suprema",
            "costo": 300,
            "requiere": "banda_ancha",
            # Desbloquea Antena + pausa producción enemiga por 10 segundos (600 frames)
            "efecto": lambda juego: (_aplicar_antena_suprema(juego)),
        },
    },
}


def _buff_vida_tropas(juego, multiplicador):
    """Aplica aumento de vida SOLO a tropas aliadas existentes y guarda el mod para las futuras."""
    for unidad in juego.mis_unidades:
        if unidad.faccion == juego.faccion:
            unidad.vida = int(unidad.vida * multiplicador)
    juego.mod_vida_tropas = multiplicador


def _buff_danno_tropas(juego, multiplicador):
    """Aplica aumento de daño SOLO a tropas aliadas existentes y guarda el mod para las futuras."""
    for unidad in juego.mis_unidades:
        if unidad.faccion == juego.faccion:
            unidad.dano = int(unidad.dano * multiplicador)
    juego.mod_danno = multiplicador


def _buff_rango_tropas(juego, multiplicador):
    """Amplía el rango de ataque SOLO a tropas aliadas existentes y guarda el mod para las futuras."""
    for unidad in juego.mis_unidades:
        if unidad.faccion == juego.faccion:
            unidad.rango_ataque = int(unidad.rango_ataque * multiplicador)
    juego.mod_antena_amplificadora = multiplicador


def _buff_velocidad_tropas(juego, multiplicador):
    """Aumenta la velocidad de movimiento SOLO a tropas aliadas existentes y guarda el mod."""
    for unidad in juego.mis_unidades:
        if unidad.faccion == juego.faccion:
            unidad.velocidad = unidad.velocidad * multiplicador
    juego.mod_banda_ancha = multiplicador


def _aplicar_linea_ensamblaje(juego):
    """Activa el modificador de construcción más rápida y desbloquea la MinaMejorada."""
    juego.mod_linea_ensamblaje = 0.8
    juego._desbloquear_edificio_exclusivo()


def _aplicar_antena_suprema(juego):
    """Desbloquea la Antena y activa el timer de bloqueo de producción enemiga."""
    juego._desbloquear_edificio_exclusivo()
    juego.timer_antena_suprema = 600


# ------------------------------------------------------------------
# Clase ArbolHabilidades
# ------------------------------------------------------------------

class ArbolHabilidades:
    def __init__(self, faccion, juego):
        self.faccion = faccion
        self.juego = juego
        self.arbol = ARBOLES.get(faccion, {})
        self.desbloqueadas = set()

    def puede_desbloquear(self, id_hab):
        """Devuelve True si el jugador cumple los requisitos."""
        if id_hab not in self.arbol:
            return False
        if id_hab in self.desbloqueadas:
            return False
        datos = self.arbol[id_hab]
        if datos["requiere"] and datos["requiere"] not in self.desbloqueadas:
            return False
        if self.juego.oro < datos["costo"]:
            return False
        return True

    def desbloquear(self, id_hab):
        """Intenta desbloquear una habilidad. Devuelve True si tuvo éxito."""
        if not self.puede_desbloquear(id_hab):
            return False
        datos = self.arbol[id_hab]
        self.juego.oro -= datos["costo"]
        self.desbloqueadas.add(id_hab)
        if datos["efecto"]:
            datos["efecto"](self.juego)
        return True

    def habilidades_disponibles(self):
        """Lista de ids que el jugador puede desbloquear ahora."""
        return [h for h in self.arbol if self.puede_desbloquear(h)]

    def estado(self):
        """Devuelve un dict con el estado de cada habilidad para dibujar la UI."""
        resultado = {}
        for id_hab, datos in self.arbol.items():
            if id_hab in self.desbloqueadas:
                estado = "activa"
            elif self.puede_desbloquear(id_hab):
                estado = "disponible"
            else:
                estado = "bloqueada"
            resultado[id_hab] = {**datos, "estado": estado}
        return resultado
