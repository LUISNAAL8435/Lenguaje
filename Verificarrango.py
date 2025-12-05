class Verificarrango:
    def __init__(self, analizador=None):
        # Guardamos el analizador para usar su método error
        self.analizador = analizador
    def verificar(self, tipo, valor, linea=None, colum=None):
        """
        Verifica si un valor pertenece al rango permitido según su tipo.
        Retorna True si es válido, o lanza un error si no lo es.
        """

        if tipo == 'number':
            # number = 4 bytes (32 bits)
            if isinstance(valor, str) and valor.isdigit():
                    valor = int(valor)
            if isinstance(valor, (int, float)) and -2147483648 <= valor <= 2147483647:
                return True
            else:
                self.analizador.error(f"Error: El valor '{valor}' no está en el rango de 'number' (línea {linea}, columna {colum})")
                return False

        elif tipo == 'decimal':
            # decimal = 4 bytes (float de 32 bits)
            if isinstance(valor, str):
                    try:
                        valor = float(valor)
                    except ValueError:
                        pass
            if isinstance(valor, (int, float)) and -3.4e38 <= valor <= 3.4e38:
                return True
            else:
                self.analizador.error(f"Error: El valor '{valor}' no está en el rango de 'decimal' (línea {linea}, columna {colum})")
                return False

        elif tipo == 'text':
            # text = 1 byte por carácter
            if isinstance(valor, str):
                if len(valor) <= 255:
                    return True
                else:
                    self.analizador.error(f"Error: El texto excede el tamaño máximo de 255 caracteres (línea {linea}, columna {colum})")
                    return False
            else:
                self.analizador.error(f"Error: El valor '{valor}' no es texto válido (línea {linea}, columna {colum})")
                return False

        elif tipo == 'bool':
            # bool = 1 byte
            if isinstance(valor, bool):
                return True
            elif isinstance(valor, str) and valor.lower() in ['true', 'false']:
                return True
            else:
                self.analizador.error(f"Error: El valor '{valor}' no es booleano válido (línea {linea}, columna {colum})")
                return False

        elif tipo == 'void':
            # void = no almacena valores
            if valor is None:
                return True
            else:
                self.analizador.error(f"Error: El tipo 'void' no puede almacenar valores (línea {linea}, columna {colum})")
                return False

        else:
            self.analizador.error(f"Error: Tipo '{tipo}' no reconocido (línea {linea}, columna {colum})")
            return False
