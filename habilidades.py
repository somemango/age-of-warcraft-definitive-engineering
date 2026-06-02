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
            "costo": 0,
            "requiere": None,
            "efecto": None,         # nodo raíz, solo desbloquea ramas
        },
        "compilador": {
            "nombre": "Compilador optimizado",
            "costo": 200,
            "requiere": "algoritmo_eficiente",
            # +30% velocidad
            "efecto": lambda juego: setattr(juego, "mod_entrena", 1.43),
        },
        "red_distribuida": {
            "nombre": "Red distribuida",
            "costo": 300,
            "requiere": "algoritmo_eficiente",
            # +50% oro
            "efecto": lambda juego: setattr(juego, "mod_oro", 1.5),
        },
    },
    "hardware": {
        "overclock": {
            "nombre": "Overclock",
            "costo": 0,
            "requiere": None,
            "efecto": None,
        },
        "refrigeracion": {
            "nombre": "Refrigeración líquida",
            "costo": 200,
            "requiere": "overclock",
            "efecto": lambda juego: _buff_vida_tropas(juego, 1.2),
        },
        "multiprocesador": {
            "nombre": "Multiprocesador",
            "costo": 300,
            "requiere": "overclock",
            "efecto": lambda juego: setattr(juego, "tropas_por_cola", 2),
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

        # Desbloquear nodo raíz automáticamente
        for id_hab, datos in self.arbol.items():
            if datos["requiere"] is None:
                self.desbloqueadas.add(id_hab)

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
