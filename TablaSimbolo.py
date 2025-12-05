class TablaSimbolos:
    def __init__(self, padre=None):
        # Cada tabla puede tener una tabla "padre" (por ejemplo, una tabla local dentro de un método)
        self.simbolos = {}
        self.padre = padre

    def insertar(self, nombre, tipo, categoria, parametros=None):
        if nombre in self.simbolos:
            raise Exception(f"Error semántico: '{nombre}' ya declarado en este ámbito.")
        self.simbolos[nombre] = {
            "tipo": tipo,
            "categoria": categoria,
            "parametros": parametros or []
        }

    def existe(self, nombre):
        """Verifica si un símbolo ya existe en la tabla actual o alguna superior."""
        if nombre in self.simbolos:
            return True
        elif self.padre:
            return self.padre.existe(nombre)
        return False

    def obtener(self, nombre):
        """Obtiene el símbolo desde la tabla actual o una superior."""
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        elif self.padre:
            return self.padre.obtener(nombre)
        else:
            raise Exception(f"Error semántico: '{nombre}' no declarado.")
