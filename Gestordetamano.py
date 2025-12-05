class Gestordetamano:
    def tamano(self, tipo):
        if tipo == 'number':
            return 4
        elif tipo == 'decimal':
            return 4
        elif tipo == 'bool':
            return 1
        elif tipo == 'text':
            return None  # tamaño variable
        else:
            return 0