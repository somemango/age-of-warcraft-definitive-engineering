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
            # dano de las unidades +20%
            "efecto": lambda juego: setattr(juego, "mod_danno", 1.20),
        },
        "compilador": {
            "nombre": "Compilador",
            "costo": 500,
            "requiere": "algoritmo_eficiente",
            # +30% velocidad
            "efecto": lambda juego: setattr(juego, "mod_entrena", 1.20),
        },
        "base_de_datos": {
            "nombre": "Base de Datos",
            "costo": 1000,
            "requiere": "compilador",
            # habilita bases de datos
            "efecto": lambda juego: setattr(juego, "mod_base_datos", True),
        },
    },
    "civil": {
        "torreta_cemento": {
            "nombre": "Torreta de Cemento",
            "costo": 120,
            "requiere": None,
            # habilita la torreta de cemento
            "efecto": lambda juego: setattr(juego, "mod_torreta_cemento", True),
        },
        "reforzamiento": {
            "nombre": "Reforzamiento",
            "costo": 500,
            "requiere": "torreta_cemento",
            # hace que las unidades tengan 1.5 veces mas vida
            "efecto": lambda juego: _buff_vida_tropas(juego, 1.5),
        },
        "planificacion_urbana": {
            "nombre": "Planificacion Urbana",
            "costo": 300,
            "requiere": "reforzamiento",
            # aumenta en 1.3 veces la vida de todas las estructuras
            "efecto": lambda juego: setattr(juego, "mod_planificacion_urbana", 1.3),
        },
    },
    "industrial": {
        "mejor_mina": {
            "nombre": "Minas Mejoradas",
            "costo": 0,
            "requiere": None,
            # hace que las minas produzcan mas oro
            "efecto": lambda juego: setattr(juego, "mod_mejor_mina", 1.2),
        },
        "linea_ensamblaje": {
            "nombre": "Linea de Ensamblaje",
            "costo": 250,
            "requiere": "mejor_mina",
            # hace que las estructuras tarden menos en hacerse
            "efecto": lambda juego: setattr(juego, "mod_linea_ensamblaje", 0.8),
        },
        "manufactura": {
            "nombre": "Manufactura",
            "costo": 1100,
            "requiere": "linea_ensamblaje",
            # hace que las unidades se produzcan el doble de rapido
            "efecto": lambda juego: setattr(juego, "mod_manufactura", 2.0),
        },
    },
    "telecomunicaciones": {
        "antena_amplificadora": {
            "nombre": "Antena Amplificadora",
            "costo": 200,
            "requiere": None,
            # hace que las unidades ataquen con 3 veces mas rango
            "efecto": lambda juego: setattr(juego, "mod_antena_amplificadora", 3.0),
        },
        "banda_ancha": {
            "nombre": "Banda Ancha",
            "costo": 350,
            "requiere": "antena_amplificadora",
            # aumenta la velocidad de movimiento en las tropas x1.5
            "efecto": lambda juego: setattr(juego, "mod_banda_ancha", 1.5)
        },
        "antena_suprema": {
            "nombre": "Antena Suprema",
            "costo": 300,
            "requiere": "banda_ancha",
            # invalida la produccion de recursos del enemigo por unos segundos
            "efecto": lambda juego: setattr(juego, "timer_antena_suprema", 600),
        },
    },
}


def _buff_vida_tropas(juego, multiplicador):
    """Aplica aumento de vida a todas las tropas existentes y futuras."""
    for unidad in juego.mis_unidades:
        unidad.vida = int(unidad.vida * multiplicador)
    juego.mod_vida_tropas = multiplicador


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
