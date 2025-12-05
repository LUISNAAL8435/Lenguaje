from TablaSimbolos import TablaSimbolos
from Gestordetamano import Gestordetamano
from Verificarrango import Verificarrango

class AnalizadorSintactico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.token_actual = self.tokens[self.posicion] if self.tokens else None
        self.tablaGlobales = TablaSimbolos()
        self.tablaLocales = None
        self.metodo_tipo_actual = None
        self.metodo_nombre_actual = None
        self.verificartamano = Gestordetamano()
        self.codigo_intermedio = []  # Se llenará al final del análisis
        self.temporal_counter = 0
        self.etiqueta_counter = 0    # Separado para etiquetas

        self.verificar_rango = Verificarrango(analizador=self)

    def nuevo_temporal(self):
        t = f"t{self.temporal_counter}"
        self.temporal_counter += 1
        return t
    
    def nuevo_etiqueta(self):
        l = f"L{self.etiqueta_counter}"
        self.etiqueta_counter += 1
        return l
    
    def error(self, mensaje, linea=None, columna=None):
        if linea is None:
            if self.token_actual:
                _, _, linea, columna = self.token_actual
            else:
                linea = columna = 'desconocida'
        raise SyntaxError(f"Error de sintaxis en línea {linea} : {mensaje}")
    
    def avanzar(self):
        self.posicion += 1
        if self.posicion < len(self.tokens):
            self.token_actual = self.tokens[self.posicion]
        else:
            self.token_actual = None
    
    def consumir(self, linea, colum, tipo_esperado=None, valor_esperado=None):
        if not self.token_actual:
            self.error(f"Se esperaba {tipo_esperado} {valor_esperado if valor_esperado else ''}, pero se encontró fin de archivo")
        
        tipo, valor, lineaa, columm = self.token_actual
        
        if tipo_esperado is not None and tipo != tipo_esperado:
            self.error(f"Se esperaba token tipo '{tipo_esperado}', pero se encontró '{tipo}' (valor '{valor}')", lineaa, columm)
        
        if valor_esperado is not None and valor != valor_esperado:
            self.error(f"Se esperaba '{valor_esperado}', pero se encontró '{valor}'", lineaa, columm)
        
        self.avanzar()
    
    def program(self):
        """Punto de entrada principal del análisis"""
        if self.token_actual and self.token_actual[0] not in ['TipoDato', 'Reservadas']:
            self.error("Error de inicio: Se esperaba declaración o método")
        
        # Analizar declaraciones globales
        _, _, _, codigo_declaraciones, _=self.parse_ListaDeclaraciones(None, tablaGlobal=self.tablaGlobales)
        
        # Analizar métodos y obtener su código
        _, _, _, codigo_metodos, _ = self.parse_ListaMetodos(None, tablaGlobal=self.tablaGlobales)
        codigo_completo = []
        if codigo_declaraciones:
            codigo_completo.extend(codigo_declaraciones)
        if codigo_metodos:
            codigo_completo.extend(codigo_metodos)
        # Almacenar todo el código intermedio generado
        self.codigo_intermedio = codigo_completo
    
    def parse_ListaDeclaraciones(self, tablaLocal=None, tablaGlobal=None):
        if self.token_actual and self.token_actual[0] == 'TipoDato':
            resultado_decl=self.parse_Declaracion(tablaLocal, tablaGlobal)
            _, _, _, codigo_restante, _ =self.parse_ListaDeclaraciones(tablaLocal, tablaGlobal)
        # else: EPSILON - no hacer nada
                # Combinar códigos
            codigo_combinado = []
            if resultado_decl and 'codigo' in resultado_decl:
                codigo_combinado.extend(resultado_decl['codigo'])
            if codigo_restante:
                codigo_combinado.extend(codigo_restante)
            
            return None, None, None, codigo_combinado, None
        else:
            # No hay más declaraciones
            return None, None, None, [], None
        
    def parse_ListaMetodos(self, tablaLocal=None, tablaGlobal=None):
        """Retorna: (tipo, valor, tamaño, código, lugar)"""
        if self.token_actual and self.token_actual[0] == 'Reservadas' and self.token_actual[1] == 'method':
            # Analizar primer método
            resultado_metodo = self.parse_Metodo(tablaLocal, tablaGlobal)
            
            # Analizar métodos restantes (recursivo)
            _, _, _, codigo_restante, _ = self.parse_ListaMetodos(tablaLocal, tablaGlobal)
            
            # Combinar códigos
            codigo_combinado = []
            if resultado_metodo and 'codigo' in resultado_metodo:
                codigo_combinado.extend(resultado_metodo['codigo'])
            if codigo_restante:
                codigo_combinado.extend(codigo_restante)
            
            return None, None, None, codigo_combinado, None
        else:
            # No hay más métodos
            return None, None, None, [], None
    
    def parse_Metodo(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'method')

        # tipo del metodo
        tipo_metodo, _, tam = self.parse_Tipo()
        self.metodo_tipo_actual = tipo_metodo

        # identificador
        if not self.token_actual:
            self.error("Se esperaba identificador de método, pero fin de archivo")

        tipo_tok, id_nombre, linea, colum = self.token_actual

        if id_nombre == 'init':
            self.consumir(linea, colum, 'Reservadas', id_nombre)
        elif tipo_tok == 'Identificador':
            self.consumir(linea, colum, 'Identificador', id_nombre)
        else:
            self.error(f"Nombre de método no válido: '{id_nombre}'", linea, colum)
        
        if id_nombre == 'init':
            if tipo_metodo != 'void':
                self.error("El método 'init' debe ser de tipo 'void'", linea, colum)
            if tablaGlobal.existe('init'):
                self.error("El método 'init' solo puede declararse una vez", linea, colum)
        
        if tablaGlobal.existe(id_nombre):
            self.error(f"El método '{id_nombre}' ya está declarado", linea, colum)
        else:
            tablaGlobal.insertar(id_nombre, {
                'tipo': tipo_metodo, 
                'valor': None,
                'categoria': 'metodo',
                'Ambito': 'global',
                'linea': linea, 
                'columna': colum,
                'Inicializado': False,
                'parametros': [],
                'tamaño': tam
            })
        
        self.metodo_nombre_actual = id_nombre

        # tabla local nueva para el método
        tablaLocal = TablaSimbolos()

        # parametros
        self.consumir(linea, colum, 'Delimitador', '(')
        lista_parametros = self.parse_ListaParametros(tablaLocal, tablaGlobal)
        self.consumir(linea, colum, 'Delimitador', ')')

        if id_nombre == 'init' and lista_parametros:
            self.error("El método 'init' no debe tener parámetros", linea, colum)

        # actualizar parametros en la tabla global
        metodo_entry = self.tablaGlobales.obtener(id_nombre)
        metodo_entry['parametros'] = lista_parametros

        # cuerpo del método
        self.consumir(linea, colum, 'Delimitador', '{')
        
        # Analizar sentencias y obtener su código
        _, _, _, codigo_cuerpo, _ = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
        
        self.consumir(linea, colum, 'Delimitador', '}')

        # Generar código para el método
        codigo_metodo = []
        # Etiqueta de inicio del método
        codigo_metodo.append((f"{id_nombre}:", '-', '-', '-'))
        # Código del cuerpo
        if codigo_cuerpo:
            codigo_metodo.extend(codigo_cuerpo)
        # Return implícito si es void
        if tipo_metodo == 'void':
            codigo_metodo.append(('return', '-', '-', '-'))

        # limpiar
        tablaLocal = None
        self.metodo_tipo_actual = None
        self.metodo_nombre_actual = None
        
        return {'codigo': codigo_metodo}
    
    def parse_ListaParametros(self, tablaLocal=None, tablaGlobal=None):
        parametros = []

        if self.token_actual and self.token_actual[0] == 'TipoDato':
            parametro = self.parse_Parametro(tablaLocal, tablaGlobal)
            mas_parametros = self.parse_MasParametros(tablaLocal, tablaGlobal)
            parametros = [parametro] + mas_parametros
        return parametros
    
    def parse_MasParametros(self, tablaLocal=None, tablaGlobal=None):
        parametros = []
        
        if self.token_actual and self.token_actual[0] == 'Delimitador' and self.token_actual[1] == ',':
            self.consumir(self.token_actual[2], self.token_actual[3], 'Delimitador', ',')
            parametro = self.parse_Parametro(tablaLocal, tablaGlobal)
            mas_parametros = self.parse_MasParametros(tablaLocal, tablaGlobal)
            parametros = [parametro] + mas_parametros
        return parametros
    
    def parse_Parametro(self, tablaLocal=None, tablaGlobal=None):
        tipo, _, tam = self.parse_Tipo()
        
        tipo_tok, id_nombre, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Identificador', id_nombre)

        if tablaLocal.existe(id_nombre):
            self.error(f"El parámetro '{id_nombre}' ya está declarado en este método", linea, colum)
        else:
            tablaLocal.insertar(id_nombre, {
                'tipo': tipo, 
                'categoria': 'parametro',
                'ambito': self.metodo_nombre_actual,
                'linea': linea, 
                'columna': colum, 
                'Inizializado': True,
                'parametro': True,
                'tamaño': tam
            })
        
        return {'tipo': tipo, 'nombre': id_nombre}
    
    def parse_Tipo(self):
        tipos_validos = ['number', 'decimal', 'text', 'bool', 'void']
        tipo_tok, tipo_valor, linea, colum = self.token_actual
        if tipo_tok == 'TipoDato' and tipo_valor in tipos_validos:
            self.consumir(linea, colum, 'TipoDato', tipo_valor)
            return tipo_valor, linea, self.verificartamano.tamano(tipo_valor)
        else:
            self.error(f"Tipo de dato inválido: {tipo_valor}", linea, colum)
    
    def parse_ListaSentencias(self, tablaLocal=None, tablaGlobal=None):
        """Retorna: (tipo, valor, tamaño, código, lugar)"""
        if not self.token_actual:
            return None, None, None, [], None
        
        tokens_inicio_sentencia = ['Reservadas', 'Identificador', 'TipoDato']

        if self.token_actual[0] not in tokens_inicio_sentencia:
            return None, None, None, [], None
        
        # Analizar primera sentencia
        _, _, _, codigo_sentencia, _ = self.parse_Sentencia(tablaLocal, tablaGlobal)
        
        # Analizar sentencias restantes (recursivo)
        _, _, _, codigo_restante, _ = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
        
        # Combinar códigos
        codigo_total = []
        if codigo_sentencia:
            codigo_total.extend(codigo_sentencia)
        if codigo_restante:
            codigo_total.extend(codigo_restante)
        
        return None, None, None, codigo_total, None

    def parse_Sentencia(self, tablaLocal=None, tablaGlobal=None):
        """Retorna: (tipo, valor, tamaño, código, lugar)"""
        tipo, valor, linea, colum = self.token_actual
        codigo = []
        
        if tipo == 'TipoDato':
            resultado = self.parse_Declaracion(tablaLocal, tablaGlobal)
            codigo = resultado['codigo']
            
        elif tipo == 'Identificador':
            if self.posicion + 1 < len(self.tokens):
                tipo_sig, valor_sig, _, _ = self.tokens[self.posicion + 1]
                if tipo_sig == 'Delimitador' and valor_sig == '(':
                    print("llamada")
                    resultado = self.parse_llamadaMetodo(tablaLocal, tablaGlobal)
                    codigo = resultado['codigo']
                elif tipo_sig == 'Asignacion' and valor_sig == '=':
                    print("Analizando asignacion")
                    resultado = self.parse_Asignacion(tablaLocal, tablaGlobal)
                    codigo = resultado['codigo']
                else:
                    self.error(f"Sentencia no reconocida después de identificador", linea, colum)
            else:
                self.error("Token inesperado después de identificador", linea, colum)
                
        elif tipo == 'Reservadas':
            if valor == 'pinMode':
                print("Analizando pinMode")
                resultado = self.parse_PinMode(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'readPin':
                resultado = self.parse_ReadPin(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'if':
                resultado = self.parse_If(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'while':
                resultado = self.parse_While(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'Out':
                resultado = self.parse_Out(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'for':
                resultado = self.parse_For(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            elif valor == 'print':
                resultado = self.parse_Print(tablaLocal, tablaGlobal)
                _, _, _, codigo, _ = resultado
            elif valor == 'return':
                resultado = self.parse_Return(tablaLocal, tablaGlobal)
                codigo = resultado['codigo']
            else:
                self.error(f"Sentencia no reconocida: {valor}", linea, colum)
        else:
            self.error(f"Tipo de token no reconocido para sentencia: {tipo}", linea, colum)
        
        # IMPORTANTE: NO agregar a self.codigo_intermedio aquí
        # Solo retornar el código para acumulación recursiva
        return None, None, None, codigo, None
    
    def parse_Return(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'return')
        
        retorno = {'tipo': None, 'codigo': [], 'lugar': None}
        
        if self.token_actual and self.token_actual[1] != ';':
            exp = self.parse_Expresion(tablaLocal, tablaGlobal)
            
            if exp['tipo'] != self.metodo_tipo_actual:
                self.error(f"El tipo de retorno '{exp['tipo']}' no coincide con el tipo del método '{self.metodo_tipo_actual}'", linea, colum)
            
            retorno['tipo'] = exp['tipo']
            retorno['lugar'] = exp['lugar']
            retorno['codigo'] = exp['codigo'] + [('return', exp['lugar'], '-', '-')]
            self.consumir(linea, colum, 'Delimitador', ';')
        else:
            self.consumir(linea, colum, 'Delimitador', ';')
            if self.metodo_tipo_actual != "void":
                self.error(f"El método '{self.metodo_nombre_actual}' debe retornar un valor de tipo '{self.metodo_tipo_actual}'", linea, colum)
            retorno['tipo'] = 'void'
            retorno['lugar'] = None
            retorno['codigo'] = [('return', '-', '-', '-')]
        
        return retorno
    
    def parse_llamadaMetodo(self, tablaLocal=None, tablaGlobal=None):
        tipo, id_nombre, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Identificador', id_nombre)

        if not self.tablaGlobales.existe(id_nombre):
            self.error(f"El método '{id_nombre}' no está declarado", linea, colum)

        metodo = tablaGlobal.obtener(id_nombre)

        self.consumir(linea, colum, 'Delimitador', '(')
        parametros_llamada = self.parse_ParametrosLlamada(tablaLocal, tablaGlobal)
        self.consumir(linea, colum, 'Delimitador', ')')

        if len(parametros_llamada['tipos']) != len(metodo['parametros']):
            self.error(f"Número incorrecto de argumentos en la llamada al método '{id_nombre}'. Se esperaban {len(metodo['parametros'])}, pero se recibieron {len(parametros_llamada['tipos'])}", linea, colum)
        
        for i in range(len(parametros_llamada['tipos'])):
            tipo_esperado = metodo['parametros'][i]['tipo']
            tipo_recibido = parametros_llamada['tipos'][i]
            if tipo_esperado != tipo_recibido:
                self.error(f"Tipo de argumento incorrecto en la posición {i+1} en la llamada al método '{id_nombre}'. Se esperaba '{tipo_esperado}', pero se recibió '{tipo_recibido}'", linea, colum)
        
        t = self.nuevo_temporal()
        lugares = ', '.join(parametros_llamada['lugar']) if parametros_llamada['lugar'] else ''
        codigo = parametros_llamada['codigo'] + [('call', id_nombre, lugares, t)]
        
        return {'tipo': metodo['tipo'], 'lugar': t, 'codigo': codigo}
    
    def parse_ParametrosLlamada(self, tablaLocal=None, tablaGlobal=None):
        if self.token_actual and self.token_actual[1] == ')':
            return {'tipos': [], 'lugar': [], 'codigo': []}
        
        exp = self.parse_Expresion(tablaLocal, tablaGlobal)
        mas_parametros = self.parse_MasParametrosLlamada(tablaLocal, tablaGlobal)
        
        return {
            'tipos': [exp['tipo']] + mas_parametros['tipos'],
            'lugar': [exp['lugar']] + mas_parametros['lugar'],
            'codigo': exp['codigo'] + mas_parametros['codigo']
        }
    
    def parse_MasParametrosLlamada(self, tablaLocal=None, tablaGlobal=None):
        if self.token_actual and self.token_actual[0] == 'Delimitador' and self.token_actual[1] == ',':
            self.consumir(self.token_actual[2], self.token_actual[3], 'Delimitador', ',')
            exp = self.parse_Expresion(tablaLocal, tablaGlobal)
            mas_parametros = self.parse_MasParametrosLlamada(tablaLocal, tablaGlobal)
            
            return {
                'tipos': [exp['tipo']] + mas_parametros['tipos'],
                'lugar': [exp['lugar']] + mas_parametros['lugar'],
                'codigo': exp['codigo'] + mas_parametros['codigo']
            }
        else:
            return {'tipos': [], 'lugar': [], 'codigo': []}
    
    def parse_Declaracion(self, tablaLocal=None, tablaGlobal=None):
        tipo, linea, tam = self.parse_Tipo()
        
        if not self.token_actual:
            self.error("Se esperaba un identificador, pero se encontró fin de archivo", linea)
        
        tipo_tok, id_nombre, linea, colum = self.token_actual
        
        if tipo_tok == 'Identificador':
            self.consumir(linea, colum, 'Identificador', id_nombre)
        else:
            self.error(f"Error: Línea: '{linea}', Columna: '{colum}', Se esperaba un Identificador")

        tabla_objetivo = tablaLocal if tablaLocal else tablaGlobal
        ambito = self.metodo_nombre_actual if tablaLocal else "global"
        
        if tabla_objetivo.existe(id_nombre):
            self.error(f"Error: La variable '{id_nombre}' ya está declarada en este ámbito")
        
        codigo = []
        
        # Verificar si hay asignación
        if self.token_actual and self.token_actual[0] == 'Asignacion':
            self.consumir(self.token_actual[2], self.token_actual[3], 'Asignacion', self.token_actual[1])
            
            if self.token_actual and self.token_actual[0] == 'Delimitador' and self.token_actual[1] == ';':
                self.error(f"Falta valor después del operador '=' para la variable '{id_nombre}'", 
                           self.token_actual[2], self.token_actual[3])
            
            hayAsignacion, exp = self.parse_DeclaracionOpcional(tablaLocal, tablaGlobal)
            
            if hayAsignacion:
                if exp['tipo'] != tipo:
                    self.error(f"Tipo incompatible en la asignación a '{id_nombre}'. Se esperaba '{tipo}', pero se recibió '{exp['tipo']}'", linea, colum)
                
                tabla_objetivo.insertar(id_nombre, {
                    'tipo': tipo,
                    'valor': exp['lugar'],
                    'categoria': 'variable',
                    'Ambito': ambito,
                    'linea': linea,
                    'columna': colum,
                    'Inicializado': True,
                    'parametro': False,
                    'tamaño': tam
                })
                codigo += exp['codigo'] + [('=', exp['lugar'], id_nombre, '-')]
            else:
                tabla_objetivo.insertar(id_nombre, {
                    'tipo': tipo,
                    'valor': None,
                    'categoria': 'variable',
                    'Ambito': ambito,
                    'linea': linea,
                    'columna': colum,
                    'Inicializado': False,
                    'parametro': False,
                    'tamaño': tam
                })
        else:
            tabla_objetivo.insertar(id_nombre, {
                'tipo': tipo,
                'valor': None,
                'categoria': 'variable',
                'Ambito': ambito,
                'linea': linea,
                'columna': colum,
                'Inicializado': False,
                'parametro': False,
                'tamaño': tam
            })
        
        self.consumir(linea, colum, 'Delimitador', ';')
        return {'codigo': codigo}
    
    def parse_Print(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'print')
        self.consumir(linea, colum, 'Delimitador', '(')
        
        exp_result = self.parse_Expresion(tablaLocal, tablaGlobal)
        exp_tipo = exp_result['tipo']
        exp_lugar = exp_result['lugar']
        exp_codigo = exp_result['codigo']
        
        if exp_tipo not in ['number', 'decimal', 'text', 'bool']:
            self.error(f"Tipo no válido para print: '{exp_tipo}'. Debe ser 'number', 'decimal', 'text' o 'bool'", linea, colum)
        
        self.consumir(linea, colum, 'Delimitador', ')')
        self.consumir(linea, colum, 'Delimitador', ';')

        codigo = exp_codigo + [('print', exp_lugar, '-', '-')]
        return None, None, None, codigo, None
    
    def parse_DeclaracionOpcional(self, tablaLocal=None, tablaGlobal=None):
        exp = self.parse_Expresion(tablaLocal, tablaGlobal)
        return True, {'tipo': exp['tipo'], 'lugar': exp['lugar'], 'codigo': exp['codigo']}
    
    def parse_Asignacion(self, tablaLocal=None, tablaGlobal=None):
        tipo, id_nombre, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Identificador', id_nombre)

        # Buscar variable en tablas
        var = None
        if tablaLocal and tablaLocal.existe(id_nombre):
            var = tablaLocal.obtener(id_nombre)
        elif tablaGlobal and tablaGlobal.existe(id_nombre):
            var = tablaGlobal.obtener(id_nombre)
        else:
            self.error(f"La variable '{id_nombre}' no está declarada", linea, colum)
        
        self.consumir(self.token_actual[2], self.token_actual[3], 'Asignacion', '=')
        
        # Verificar que no haya punto y coma inmediatamente
        if self.token_actual and self.token_actual[0] == 'Delimitador' and self.token_actual[1] == ';':
            self.error(f"Falta valor después del operador '=' para la variable '{id_nombre}'", 
                       self.token_actual[2], self.token_actual[3])
        
        exp = self.parse_Expresion(tablaLocal, tablaGlobal)

        if exp['tipo'] != var['tipo']:
            self.error(f"Tipo incompatible en la asignación a '{id_nombre}'. Se esperaba '{var['tipo']}', pero se recibió '{exp['tipo']}'", linea, colum)
        var['valor']=exp['valor']
        var['Inicializado']=True
        self.consumir(self.token_actual[2], self.token_actual[3], 'Delimitador', ';')
        codigo = exp['codigo'] + [('=', exp['lugar'], id_nombre, '-')]
        return {'codigo': codigo}
    
    def parse_PinMode(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'pinMode')
        
        tipo, valor, linea, colum = self.token_actual
        if self.token_actual and self.token_actual[1] != '(':
            self.error(f"Se esperaba un delimitador ( pero se encontró '{valor}'")
        
        self.consumir(linea, colum, 'Delimitador', '(')
        
        if not self.token_actual:
            self.error("Se esperaba identificador de pin")
        
        tipo, valor, linea, colum = self.token_actual
        id_pin = valor
        
        if tipo != 'Identificador':
            self.error(f"Se esperaba un identificador pero se encontró '{id_pin}'")
        
        # Verificar tipo del pin
        id_tipo = None
        if tablaLocal is not None and tablaLocal.existe(id_pin):
            id_tipo = tablaLocal.obtener(id_pin)['tipo']
        elif tablaGlobal is not None and tablaGlobal.existe(id_pin):
            id_tipo = tablaGlobal.obtener(id_pin)['tipo']
        else:
            self.error(f"El pin '{id_pin}' no está declarado", linea, colum)
        
        if id_tipo != 'number':
            self.error(f"El pin '{id_pin}' debe ser de tipo 'number', pero es de tipo '{id_tipo}'", linea, colum)
        
        self.consumir(linea, colum, 'Identificador', id_pin)
        
        if self.token_actual and self.token_actual[1] != ',':
            self.error(f"Se esperaba una , pero se encontró '{self.token_actual[1]}'")
        
        self.consumir(linea, colum, 'Delimitador', ',')
        tipo, valor, linea, colum = self.token_actual

        if valor not in ['INPUT', 'OUTPUT']:
            self.error(f"El modo '{valor}' no es válido. Debe ser 'INPUT' o 'OUTPUT'", linea, colum)
        
        self.consumir(linea, colum, 'Reservadas', valor)
        
        if self.token_actual and self.token_actual[1] != ')':
            self.error(f"Se esperaba un ) pero se encontró '{self.token_actual[1]}'")
        
        self.consumir(linea, colum, 'Delimitador', ')')
        
        if self.token_actual and self.token_actual[1] != ';':
            self.error(f"Se esperaba ; pero se encontró '{self.token_actual[1]}'", self.token_actual[2])
        
        self.consumir(linea, colum, 'Delimitador', ';')
        
        # Generar código intermedio
        t = self.nuevo_temporal()
        codigo_literal = [('literal', valor, '-', t)]
        codigo_pinmode = codigo_literal + [('pinMode', id_pin, t, '-')]
        return {'codigo': codigo_pinmode}
    
    def parse_ReadPin(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        print(f"Analizando readPin en línea {linea}, columna {colum}")
        self.consumir(linea, colum, 'Reservadas', 'readPin')
        
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Delimitador', '(')
        
        tipo, valor, linea, colum = self.token_actual
        if tipo != 'Identificador':
            self.error(f"Se esperaba un identificador de pin, pero se encontró '{valor}'", linea, colum)
        
        id_pin = valor
        
        # Verificar tipo del pin
        id_tipo = None
        if tablaLocal is not None and tablaLocal.existe(id_pin):
            id_tipo = tablaLocal.obtener(id_pin)['tipo']
        elif tablaGlobal is not None and tablaGlobal.existe(id_pin):
            id_tipo = tablaGlobal.obtener(id_pin)['tipo']
        else:
            self.error(f"El pin '{id_pin}' no está declarado", linea, colum)
        
        if id_tipo != 'number':
            self.error(f"El pin '{id_pin}' debe ser de tipo 'number', pero es de tipo '{id_tipo}'", linea, colum)
        
        self.consumir(linea, colum, 'Identificador', id_pin)
        
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Delimitador', ')')
        
        t = self.nuevo_temporal()
        codigo = [("readPin", id_pin, "-", t)]
        return 'bool', None, 4, t, codigo
    
    def parse_Out(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'Out')
        self.consumir(linea, colum, 'Delimitador', '(')
        
        tipo, valor, linea, colum = self.token_actual
        if tipo != 'Identificador':
            self.error(f"Se esperaba un identificador de pin, pero se encontró '{valor}'", linea, colum)
        
        id_pin = valor
        
        # Verificar tipo del pin
        id_tipo = None
        if tablaLocal is not None and tablaLocal.existe(id_pin):
            id_tipo = tablaLocal.obtener(id_pin)['tipo']
        elif tablaGlobal is not None and tablaGlobal.existe(id_pin):
            id_tipo = tablaGlobal.obtener(id_pin)['tipo']
        else:
            self.error(f"El pin '{id_pin}' no está declarado", linea, colum)
        
        if id_tipo != 'number':
            self.error(f"El pin '{id_pin}' debe ser de tipo 'number', pero es de tipo '{id_tipo}'", linea, colum)
        
        self.consumir(linea, colum, 'Identificador', id_pin)
        self.consumir(linea, colum, 'Delimitador', ',')
        
        tipo, valor, linea, colum = self.token_actual
        
        if valor == 'ON':
            estado = 1
        elif valor == 'OFF':
            estado = 0
        else:
            self.error(f"El valor '{valor}' no es válido. Debe ser 'ON' o 'OFF'", linea, colum)
        
        self.consumir(linea, colum, 'bool', valor)
        self.consumir(linea, colum, 'Delimitador', ')')
        self.consumir(linea, colum, 'Delimitador', ';')
        
        t = self.nuevo_temporal()
        codigo = [('literal', str(estado), '-', t), ('OUT', id_pin, t, '-')]
        return {'codigo': codigo, 'tipo': 'bool', 'lugar': t}
    
    def parse_If(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'if')
        self.consumir(linea, colum, 'Delimitador', '(')
        
        cond = self.parse_Expresion(tablaLocal, tablaGlobal)
        
        if cond['tipo'] != 'bool':
            self.error(f"La condición del 'if' debe ser de tipo 'bool', pero es de tipo '{cond['tipo']}'", linea, colum)
        
        self.consumir(linea, colum, 'Delimitador', ')')
        self.consumir(linea, colum, 'Delimitador', '{')
        
        sentencias_if = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
        _, _, _, sentencias_if_codigo, _ = sentencias_if
        
        self.consumir(linea, colum, 'Delimitador', '}')
        
        else_opc = self.parse_ElseOpcional(tablaLocal, tablaGlobal)
        else_codigo = else_opc['codigo']

        labelElse = self.nuevo_etiqueta()
        labelEnd = self.nuevo_etiqueta()
        
        codigo = []
        codigo += cond['codigo']
        codigo.append(('ifFalse', cond['lugar'], '-', labelElse))
        codigo += sentencias_if_codigo
        codigo.append(('goto', '-', '-', labelEnd))
        codigo.append((labelElse + ':', '-', '-', '-'))
        codigo += else_codigo
        codigo.append((labelEnd + ':', '-', '-', '-'))

        return {'codigo': codigo}
    
    def parse_ElseOpcional(self, tablaLocal=None, tablaGlobal=None):
        if self.token_actual and self.token_actual[1] == 'else':
            tipo, valor, linea, colum = self.token_actual
            self.consumir(linea, colum, 'Reservadas', 'else')
            self.consumir(linea, colum, 'Delimitador', '{')
            
            sentencias_else = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
            _, _, _, sentencias_else_codigo, _ = sentencias_else
            
            self.consumir(linea, colum, 'Delimitador', '}')
            return {'codigo': sentencias_else_codigo}
        else:
            return {'codigo': []}
    
    def parse_While(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'while')
        self.consumir(linea, colum, 'Delimitador', '(')
        
        cond = self.parse_Expresion(tablaLocal, tablaGlobal)
        
        if cond['tipo'] != 'bool':
            self.error(f"La condición del 'while' debe ser de tipo 'bool', pero es de tipo '{cond['tipo']}'", linea, colum)
        
        self.consumir(linea, colum, 'Delimitador', ')')
        self.consumir(linea, colum, 'Delimitador', '{')
        
        sentencias_if = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
        _, _, _, sentencias_if_codigo, _ = sentencias_if
        
        self.consumir(linea, colum, 'Delimitador', '}')
        
        labelInicio = self.nuevo_etiqueta()
        labelEnd = self.nuevo_etiqueta()
        
        codigo = []
        codigo.append((labelInicio + ':', '-', '-', '-'))
        codigo += cond['codigo']
        codigo.append(('ifFalse', cond['lugar'], '-', labelEnd))
        codigo += sentencias_if_codigo
        codigo.append(('goto', '-', '-', labelInicio))
        codigo.append((labelEnd + ':', '-', '-', '-'))

        return {'codigo': codigo}
    
    def parse_For(self, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        self.consumir(linea, colum, 'Reservadas', 'for')
        self.consumir(linea, colum, 'Delimitador', '(')

        tipo, valor, linea, colum = self.token_actual
        if tipo != 'number':
            self.error(f"Se esperaba un número dentro del 'for', pero se encontró '{tipo}'", linea, colum)
        try:
            numero_for = int(valor)
        except ValueError:
            self.error(f"El valor '{valor}' no es un número válido", linea, colum)

        if numero_for < 0:
            self.error(f"El valor del 'for' no puede ser negativo (valor = {numero_for})", linea, colum)
        
        self.consumir(linea, colum, 'number', valor)
        self.consumir(linea, colum, 'Delimitador', ')')
        self.consumir(linea, colum, 'Delimitador', '{')
        
        sentencias = self.parse_ListaSentencias(tablaLocal, tablaGlobal)
        _, _, _, sentencias_codigo, _ = sentencias
        
        self.consumir(linea, colum, 'Delimitador', '}')

        t = self.nuevo_temporal()
        labelInicio = self.nuevo_etiqueta()
        labelEnd = self.nuevo_etiqueta()
        
        codigo = []
        codigo.append(('=', str(numero_for), t, '-'))
        codigo.append((labelInicio + ':', '-', '-', '-'))
        t_condicion = self.nuevo_temporal()
        codigo.append(('<=', t, '0', t_condicion))
        codigo.append(('ifFalse', t_condicion, '-', labelEnd))
        codigo += sentencias_codigo
        t_decremento = self.nuevo_temporal()
        codigo.append(('-', t, '1', t_decremento))
        codigo.append(('=', t_decremento, t, '-'))

        codigo.append(('goto', labelInicio, '-', '-'))
        codigo.append((labelEnd + ':', '-', '-', '-'))
        
        return {'codigo': codigo}

    def parse_Expresion(self, tablaLocal=None, tablaGlobal=None):
        # Corregido: parse_Expresion debe retornar un diccionario para consistencia
        tipo_sub, valor_sub, tam_sub, lugar_sub, codigo_sub = self.parse_SubExpresion(tablaLocal, tablaGlobal)

        resultado = self.parse_ExpresionPrima(
            her_tipo=tipo_sub, 
            her_valor=valor_sub, 
            her_tam=tam_sub,
            her_lugar=lugar_sub,
            her_codigo=codigo_sub,
            tablaLocal=tablaLocal, 
            tablaGlobal=tablaGlobal
        )
        
        tipo_final, valor_final, tam_final, lugar_final, codigo_final = resultado
        
        return {
            'tipo': tipo_final,
            'valor': valor_final,
            'lugar': lugar_final,
            'codigo': codigo_final
        }
    
    def parse_ExpresionPrima(self, her_tipo, her_valor, her_tam, her_lugar, her_codigo, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        
        if self.token_actual and self.token_actual[0] == 'Aritmeticos' and self.token_actual[1] == '+':
            print("Encontrado operador +")
            self.consumir(linea, colum, 'Aritmeticos', '+')

            tipo_sub, sub_valor, tam_sub, lugar_sub, codigo_sub = self.parse_SubExpresion(tablaLocal, tablaGlobal)
            
            if her_tipo in ['number', 'decimal'] and tipo_sub in ['number', 'decimal']:
                #if her_valor == None:
                 #   self.error("valor no iniciali")
                #if sub_valor == None:
                 #   self.error("valor no iniciali")
                if her_tipo == 'decimal' or tipo_sub == 'decimal':
                    resultado_tipo = 'decimal'
                else:
                    resultado_tipo = 'number'
            elif her_tipo == 'text' and tipo_sub == 'number':
                resultado_tipo = 'text'
            elif her_tipo == 'number' and tipo_sub == 'text':
                resultado_tipo = 'text'
            elif her_tipo == 'text' and tipo_sub == 'text':
                resultado_tipo = 'text'
            else:
                self.error(f"Operación '+' no válida entre tipos '{her_tipo}' y '{tipo_sub}'")
            
            resultado_tamano = self.verificartamano.tamano(resultado_tipo)
            t = self.nuevo_temporal()
            
            sin_codigo = her_codigo + codigo_sub + [('+', her_lugar, lugar_sub, t)]
            sin_tipo = resultado_tipo
            sin_tamano = resultado_tamano

            return self.parse_ExpresionPrima(
                her_tipo=sin_tipo, 
                her_valor=None, 
                her_tam=sin_tamano,
                her_lugar=t,
                her_codigo=sin_codigo,
                tablaLocal=tablaLocal, 
                tablaGlobal=tablaGlobal
            )
        
        elif self.token_actual and self.token_actual[0] == 'Aritmeticos' and self.token_actual[1] == '-':
            self.consumir(linea, colum, 'Aritmeticos', '-')

            tipo_sub, sub_valor, tam_sub, lugar_sub, codigo_sub = self.parse_SubExpresion(tablaLocal, tablaGlobal)

            if her_tipo in ['number', 'decimal'] and tipo_sub in ['number', 'decimal']:
                #if her_valor == None:
                 #   self.error("valor no inicializad")
                #if sub_valor == None:
                 #   self.error("valor no inicializad")
                if her_tipo == 'decimal' or tipo_sub == 'decimal':
                    resultado_tipo = 'decimal'
                else:
                    resultado_tipo = 'number'
            else:
                self.error(f"Operación '-' no válida entre tipos '{her_tipo}' y '{tipo_sub}'")
            
            resultado_tamano = self.verificartamano.tamano(resultado_tipo)
            t = self.nuevo_temporal()
            
            sin_codigo = her_codigo + codigo_sub + [('-', her_lugar, lugar_sub, t)]
            sin_tipo = resultado_tipo
            sin_tamano = resultado_tamano

            return self.parse_ExpresionPrima(
                her_tipo=sin_tipo,
                her_valor=None,
                her_tam=sin_tamano,
                her_lugar=t,
                her_codigo=sin_codigo,
                tablaLocal=tablaLocal,
                tablaGlobal=tablaGlobal
            )
        else:
            return (her_tipo, her_valor, her_tam, her_lugar, her_codigo)

    def parse_SubExpresion(self, tablaLocal=None, tablaGlobal=None):
        tipo_sub, valor_sub, tam_sub, lugar_sub, codigo_sub = self.parse_TerceraExpresion(tablaLocal, tablaGlobal)

        resultado = self.parse_SubExpresionPrima(
            her_tipo=tipo_sub,
            her_valor=valor_sub,
            her_tam=tam_sub,
            her_lugar=lugar_sub,
            her_codigo=codigo_sub,
            tablaLocal=tablaLocal,
            tablaGlobal=tablaGlobal
        )
        
        sin_tipo, sin_valor, sin_tam, sin_lugar, sin_codigo = resultado
        return sin_tipo, sin_valor, sin_tam, sin_lugar, sin_codigo

    def parse_SubExpresionPrima(self, her_tipo, her_valor, her_tam, her_lugar, her_codigo, tablaLocal=None, tablaGlobal=None):
        tipo, valor, linea, colum = self.token_actual
        
        if self.token_actual and self.token_actual[0] == 'Aritmeticos' and self.token_actual[1] == '*':
            self.consumir(linea, colum, 'Aritmeticos', '*')

            tipo_sub, sub_valor, tam_sub, lugar_sub, codigo_sub = self.parse_TerceraExpresion(tablaLocal, tablaGlobal)

            if her_tipo in ['number', 'decimal'] and tipo_sub in ['number', 'decimal']:
                #if her_valor == None:
                 #   self.error("valor no inicializadaaa")
                #if sub_valor == None:
                 #   self.error("valor no inicializadaaa")
                if her_tipo == 'decimal' or tipo_sub == 'decimal':
                    tipo_resultado = 'decimal'
                else:
                    tipo_resultado = 'number'
                if her_valor is not None:
                    self.verificar_rango.verificar(her_tipo, her_valor, linea, colum)
                if sub_valor is not None:
                    self.verificar_rango.verificar(tipo_sub, sub_valor, linea, colum)
            else:
                self.error(f"Operación '*' no válida entre tipos '{her_tipo}' y '{tipo_sub}'")
            
            resultado_tamano = self.verificartamano.tamano(tipo_resultado)
            t = self.nuevo_temporal()
            
            sin_codigo = her_codigo + codigo_sub + [('*', her_lugar, lugar_sub, t)]
            sin_tipo = tipo_resultado
            sin_tamano = resultado_tamano

            return self.parse_SubExpresionPrima(
                her_tipo=sin_tipo,
                her_valor=None,
                her_tam=sin_tamano,
                her_lugar=t,
                her_codigo=sin_codigo,
                tablaLocal=tablaLocal,
                tablaGlobal=tablaGlobal
            )
        
        elif self.token_actual and self.token_actual[0] == 'Aritmeticos' and self.token_actual[1] == '/':
            self.consumir(linea, colum, 'Aritmeticos', '/')
            print("Encontrado operador /")

            tipo_sub, sub_valor, tam_sub, lugar_sub, codigo_sub = self.parse_TerceraExpresion(tablaLocal, tablaGlobal)

            if her_tipo in ['number', 'decimal'] and tipo_sub in ['number', 'decimal']:
                print(f"her_tipooo: {her_tipo}, tipo_sub: {tipo_sub}, her_valor: {her_valor}, sub_valor: {sub_valor}")
                #if her_valor == None:
                 #   self.error("valor no inicializadaa")
                #if sub_valor == None:
                 #   self.error("valor no inicializadaa")
                if sub_valor == 0 or sub_valor == 0.0:
                    print("División por cero detectada")
                    self.error("División por 0 detectada")
                resultado_tipo = 'decimal'
            else:
                self.error(f"Operación '/' no válida entre tipos '{her_tipo}' y '{tipo_sub}'")
            
            resultado_tamano = self.verificartamano.tamano(resultado_tipo)
            t = self.nuevo_temporal()
            
            sin_codigo = her_codigo + codigo_sub + [('/', her_lugar, lugar_sub, t)]
            sin_tipo = resultado_tipo
            sin_tamano = resultado_tamano

            return self.parse_SubExpresionPrima(
                her_tipo=sin_tipo,
                her_valor=None,
                her_tam=sin_tamano,
                her_lugar=t,
                her_codigo=sin_codigo,
                tablaLocal=tablaLocal,
                tablaGlobal=tablaGlobal
            )
        else:
            return (her_tipo, her_valor, her_tam, her_lugar, her_codigo)
    
    def parse_TerceraExpresion(self, tablaLocal=None, tablaGlobal=None):
        tipoTok, valorTok, linea, colum = self.token_actual

        # IDENTIFICADOR
        if tipoTok == 'Identificador':
            id_nombre = valorTok
            self.consumir(linea, colum, 'Identificador', valorTok)

            simbolo = None
            if tablaLocal and tablaLocal.existe(id_nombre):
                simbolo = tablaLocal.obtener(id_nombre)
            elif tablaGlobal and tablaGlobal.existe(id_nombre):
                simbolo = tablaGlobal.obtener(id_nombre)
            else:
                self.error(f"Identificador '{id_nombre}' no declarado", linea, colum)

            tipo = simbolo['tipo']
            valor = simbolo.get('valor', None)
            tam = simbolo.get('tamaño', self.verificartamano.tamano(tipo))
            lugar = id_nombre
            codigo = []

            return tipo, valor, tam, lugar, codigo

        # NUMBER
        if tipoTok == 'number':
            self.consumir(linea, colum, 'number', valorTok)
            self.verificar_rango.verificar('number', valorTok, linea, colum)
            return 'number', int(valorTok), 4, valorTok, []

        # DECIMAL
        if tipoTok == 'decimal':
            self.consumir(linea, colum, 'decimal', valorTok)
            self.verificar_rango.verificar('decimal', valorTok, linea, colum)
            return 'decimal', float(valorTok), 4, valorTok, []

        # STRING
        if tipoTok == 'text':
            self.consumir(linea, colum, 'text', valorTok)
            tam = len(valorTok) - 2  # Restar las comillas
            return 'text', valorTok, tam, valorTok, []
        
        if tipoTok == 'Reservadas' and valorTok == 'readPin':
            return self.parse_ReadPin(tablaLocal, tablaGlobal)
        # BOOL
        if tipoTok == 'bool':
            self.consumir(linea, colum, 'bool', valorTok)
            return 'bool', valorTok, 1, valorTok, []

        # ( Z )
        if tipoTok == 'Delimitador' and valorTok == '(':
            self.consumir(linea, colum, 'Delimitador', '(')

            tipoZ, valZ, tamZ, lugarZ, codigoZ = self.parse_Z(tablaLocal, tablaGlobal)

            if self.token_actual[1] != ')':
                self.error("Se esperaba ')'", linea, colum)
            
            self.consumir(self.token_actual[2], self.token_actual[3], 'Delimitador', ')')

            her = {'tipo': tipoZ, 'valor': valZ, 'tam': tamZ, 'lugar': lugarZ, 'codigo': codigoZ}

            return self.parse_S(her, tablaLocal, tablaGlobal)

        self.error("Token inesperado en TerceraExpresion", linea, colum)

    def parse_Z(self, tablaLocal=None, tablaGlobal=None):
        """<Z> --> <Expresion> <Z'>"""
        # Parsear la expresión base
        resultado_expresion = self.parse_Expresion(tablaLocal, tablaGlobal)
        
        tipo = resultado_expresion['tipo']
        valor = resultado_expresion['valor']
        lugar = resultado_expresion['lugar']
        codigo = resultado_expresion['codigo']
        
        tam = self.verificartamano.tamano(tipo) if tipo else None

        # Llamar a Z' con la herencia de la expresión
        return self.parse_Zprima(
            her={'tipo': tipo, 'valor': valor, 'tam': tam, 'lugar': lugar, 'codigo': codigo},
            tablaLocal=tablaLocal,
            tablaGlobal=tablaGlobal
        )

    def parse_Zprima(self, her, tablaLocal=None, tablaGlobal=None):
        if her['tipo'] is None:
            return None, None, None, None, None
        
        tipo, valor, linea, colum = self.token_actual
        
        # Verificar si hay operador comparativo
        if tipo == 'Relacionales' and valor in ['<', '>', '<=', '>=', '==', '!=']:
            operador = valor
            print(f"Operador comparativo encontrado: {operador}")
            self.consumir(linea, colum, 'Relacionales', operador)
            
            # Parsear la expresión del lado derecho
            resultado_expresion2 = self.parse_Expresion(tablaLocal, tablaGlobal)
            tipo2 = resultado_expresion2['tipo']
            valor2 = resultado_expresion2['valor']
            lugar2 = resultado_expresion2['lugar']
            codigo2 = resultado_expresion2['codigo']
            
            # Validar compatibilidad de tipos
            if operador in ['<', '>', '<=', '>=']:
                if not (her['tipo'] in ['number', 'decimal'] and tipo2 in ['number', 'decimal']):
                    self.error("Comparación numérica con tipos incompatibles", linea, colum)
            if operador in ['==', '!=']:
                if not (her['tipo'] == tipo2 or (her['tipo'] in ['number', 'decimal'] and tipo2 in ['number', 'decimal'])):
                    self.error("Comparación incompatible", linea, colum)

            t = self.nuevo_temporal()
            nuevo_codigo = []
            nuevo_codigo += her['codigo']
            nuevo_codigo += codigo2
            nuevo_codigo.append((operador, her['lugar'], lugar2, t))
            
            nueva_her = {
                'tipo': 'bool',
                'valor': None,
                'tam': 1,
                'lugar': t,
                'codigo': nuevo_codigo
            }
            
            return self.parse_S(nueva_her, tablaLocal, tablaGlobal)
        
        return her['tipo'], her['valor'], her['tam'], her['lugar'], her['codigo']
    
    def parse_S(self, her, tablaLocal=None, tablaGlobal=None):
        tipoTok, valTok, linea, colum = self.token_actual

        if tipoTok == 'Logicos' and valTok in ['AND', 'OR']:
            op = valTok
            self.consumir(linea, colum, 'Logicos', op)

            # Parse Z
            resultado_z = self.parse_Z(tablaLocal, tablaGlobal)
            tipo2 = resultado_z[0]  # tipo
            valor2 = resultado_z[1]  # valor
            lugar2 = resultado_z[3]  # lugar
            codigo2 = resultado_z[4]  # codigo

            if her['tipo'] != 'bool' or tipo2 != 'bool':
                self.error("Operador lógico aplicado a tipos no booleanos", linea, colum)

            t = self.nuevo_temporal()  # Corregido: era nuevoTemporal()

            nuevo_codigo = []
            nuevo_codigo += her['codigo']
            nuevo_codigo += codigo2
            nuevo_codigo.append((op, her['lugar'], lugar2, t))

            nueva_her = {
                'tipo': 'bool',
                'valor': None,
                'tam': 1,
                'lugar': t,
                'codigo': nuevo_codigo
            }

            # Si hay más operadores lógicos, recursividad
            return self.parse_S(nueva_her, tablaLocal, tablaGlobal)

        # EPSILON
        return her['tipo'], her['valor'], her['tam'], her['lugar'], her['codigo']