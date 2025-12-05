class TablaSimbolos:
    def __init__(self, size=50):
        self.tabla = {}
        self.size = size

    def _hash(self, nombre):
        """Calcula índice hash para un identificador"""
        return hash(nombre) % self.size

    def insertar(self, nombre, atributos):
        """Agrega un nuevo símbolo"""
        if self.existe(nombre):
            print(f"[Error semántico] '{nombre}' ya está declarado.")
            return False
        self.tabla[nombre] = atributos
        print(f"[Info] Símbolo '{nombre}' insertado correctamente: {atributos}")
        return True

    def agregar(self, nombre, atributos):
        """Alias de insertar"""
        return self.insertar(nombre, atributos)

    def existe(self, nombre):
        """Verifica si el símbolo ya existe"""
        return nombre in self.tabla

    def obtener(self, nombre):
        """Devuelve los atributos de un símbolo"""
        if nombre in self.tabla:
            print(f"[Info] Se obtuvo '{nombre}': {self.tabla[nombre]}")
            return self.tabla[nombre]
        print(f"[Aviso] Variable '{nombre}' no encontrada.")
        return None

    def actualizar(self, nombre, nuevo_valor):
        """Actualiza valor o atributo de una variable"""
        if nombre in self.tabla:
            self.tabla[nombre].update(nuevo_valor)
            print(f"[Info] Variable '{nombre}' actualizada: {self.tabla[nombre]}")
            return True
        else:
            print(f"[Error] Variable '{nombre}' no declarada.")
            return False

    def __repr__(self):
        """Para imprimir la tabla de manera legible"""
        salida = "\n--- Tabla de Símbolos ---\n"
        for nombre, attrs in self.tabla.items():
            salida += f"{nombre}: {attrs}\n"
        return salida
