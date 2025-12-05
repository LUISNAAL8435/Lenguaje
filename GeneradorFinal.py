class GeneradorCodigoArduino:
    def __init__(self, cuadruplas_optimizadas):
        self.cuadruplas = cuadruplas_optimizadas
        self.codigo = []
        self.indentacion = 0
        # NUEVO: Para detectar while
        self.en_while = False
        self.indice_inicio_while = -1
    
    def generar_codigo(self):
        """Genera código Arduino de manera SIMPLE y DIRECTA"""
        self.codigo = []
        
        self.generar_cabecera()
        self.generar_variables()
        self.generar_setup()
        self.generar_loop()
        
        return '\n'.join(self.codigo)
    
    def generar_cabecera(self):
        self.codigo.extend([
            '// ================================================',
            '// CÓDIGO ARDUINO/ESP32 - GENERADO AUTOMÁTICAMENTE',
            '// ================================================',
            '',
            '#include <Arduino.h>',
            ''
        ])
    
    def generar_variables(self):
        """Genera solo variables REALES"""
        variables = set()
        
        # Buscar variables en asignaciones
        for op, arg1, arg2, res in self.cuadruplas:
            if op == '=' and res and not res.startswith('t'):
                variables.add(res)
        
        if variables:
            self.codigo.append('// --- VARIABLES GLOBALES ---')
            for var in sorted(variables):
                # Determinar tipo
                if var in ['encender', 'valor', 'estado']:
                    self.codigo.append(f'bool {var};')
                else:
                    self.codigo.append(f'int {var};')
            self.codigo.append('')
    
    def generar_setup(self):
        self.codigo.append('void setup() {')
        self.indentacion = 1
        
        self.agregar_linea('Serial.begin(115200);')
        self.agregar_linea('delay(1000);')
        self.agregar_linea('Serial.println("Sistema Arduino iniciado");')
        self.agregar_linea('')
        
        # Procesar TAC línea por línea SIN recursión
        self.procesar_tac_directamente()
        while self.indentacion > 1:
            self.indentacion -= 1
            self.agregar_linea('}')
        self.indentacion = 0
        self.codigo.append('}')
        self.codigo.append('')
    
    def procesar_tac_directamente(self):
        """Procesa el TAC de manera directa y secuencial"""
        i = 0
        while i < len(self.cuadruplas):
            op, arg1, arg2, res = self.cuadruplas[i]
            
            # NUEVO: Detectar inicio de while (L4:)
            if op == 'L4:' and not self.en_while:
                # Verificar si la siguiente es ifFalse TRUE
                if i + 1 < len(self.cuadruplas) and self.cuadruplas[i+1][0] == 'ifFalse' and self.cuadruplas[i+1][1] == 'TRUE':
                    self.en_while = True
                    self.indice_inicio_while = i
                    self.agregar_linea('while (true) {')
                    self.indentacion += 1
                    i += 1  # Saltar el ifFalse TRUE
                    continue
            
            # NUEVO: Si estamos en while y encontramos goto L4
            if self.en_while and op == 'goto' and arg2 == 'L4':
                # Fin del while
                self.indentacion -= 1
                self.agregar_linea('}')
                self.en_while = False
                # Saltar a después del while (L5)
                for j in range(i, len(self.cuadruplas)):
                    if self.cuadruplas[j][0] == 'L5:':
                        i = j
                        break
                continue
            
            # 1. Asignación simple
            if op == '=':
                valor = self.convertir_valor(arg1)
                self.agregar_linea(f'{res} = {valor};')
            
            # 2. pinMode
            elif op == 'pinMode':
                pin = self.convertir_valor(arg1)
                modo = arg2
                self.agregar_linea(f'pinMode({pin}, {modo});')
            
            # NUEVO: 3. readPin (solo si no es parte de comparación ya procesada)
            elif op == 'readPin' and res.startswith('t'):
                pin = self.convertir_valor(arg1)
                self.agregar_linea(f'int {res} = digitalRead({pin});')
            
            # NUEVO: 4. Comparación (==)
            elif op == '==':
                temp_var = res
                valor1 = self.convertir_valor(arg1)
                valor2 = self.convertir_valor(arg2)
                self.agregar_linea(f'bool {temp_var} = ({valor1} == {valor2});')
            
            # 5. ifFalse (estructura if-else) - SIN CAMBIOS
            elif op == 'ifFalse':
                # NUEVO: Si estamos en while, procesar normal
                if self.en_while:
                    self.agregar_linea(f'if ({self.convertir_valor(arg1)}) {{')
                    self.indentacion += 1
                    # El cuerpo se procesará en siguientes iteraciones
                else:
                    i = self.procesar_if_else(i)
                    continue
            
            # 6. OUT (digitalWrite)
            elif op == 'OUT':
                pin = self.convertir_valor(arg1)
                estado = 'HIGH' if arg2 == '1' else 'LOW'
                self.agregar_linea(f'digitalWrite({pin}, {estado});')
            
            # 7. return (ignorar en setup)
            elif op == 'return':
                pass
            
            # 8. Saltar etiquetas (excepto las del while que ya manejamos)
            elif op.endswith(':') and not self.en_while:
                pass
            
            # NUEVO: 9. Labels dentro del while (L0:, L1:, etc.)
            elif op.endswith(':') and self.en_while:
                # Si es L0: o L1: dentro de if-else
                if op in ['L0:', 'L1:', 'L2:', 'L3:']:
                    if op == 'L0:':
                        self.indentacion -= 1
                        self.agregar_linea('} else {')
                        self.indentacion += 1
                    elif op == 'L1:':
                        self.indentacion -= 1
                        self.agregar_linea('}')
                    elif op == 'L2:':
                        self.indentacion -= 1
                        self.agregar_linea('}')
                    elif op == 'L3:':
                        pass  # Punto de reunión, no hacer nada
            
            i += 1
    
    # NUEVO: Método para detectar if-else dentro del while
    def detectar_fin_if_else(self, idx):
        """Busca el final de una estructura if-else"""
        for j in range(idx, len(self.cuadruplas)):
            if self.cuadruplas[j][0] in ['L1:', 'L3:']:
                return j
        return len(self.cuadruplas) - 1
    
    def procesar_if_else(self, idx):
        """Procesa una estructura if-else completa - SIN CAMBIOS"""
        op, cond, etiqueta_else, _ = self.cuadruplas[idx]
        
        # Buscar la etiqueta else (L0:)
        idx_L0 = -1
        for j in range(idx, len(self.cuadruplas)):
            if self.cuadruplas[j][0] == f'{etiqueta_else}:':
                idx_L0 = j
                break
        
        if idx_L0 == -1:
            return idx + 1
        
        # Buscar la etiqueta fin (L1:)
        idx_L1 = -1
        for j in range(idx_L0, len(self.cuadruplas)):
            if self.cuadruplas[j][0] == 'L1:':
                idx_L1 = j
                break
        
        if idx_L1 == -1:
            return idx + 1
        
        # Generar if
        condicion = self.convertir_valor(cond)
        self.agregar_linea(f'if ({condicion}) {{')
        self.indentacion += 1
        
        # Procesar bloque if (entre idx+1 y idx_L0-1)
        i = idx + 1
        while i < idx_L0:
            op_i, a1_i, a2_i, r_i = self.cuadruplas[i]
            
            if op_i == 'goto' and a1_i == 'L1':
                i += 1
                continue
            
            self.procesar_instruccion_simple(op_i, a1_i, a2_i, r_i)
            i += 1
        
        self.indentacion -= 1
        self.agregar_linea('} else {')
        self.indentacion += 1
        
        # Procesar bloque else (entre idx_L0+1 y idx_L1-1)
        i = idx_L0 + 1
        while i < idx_L1:
            op_i, a1_i, a2_i, r_i = self.cuadruplas[i]
            self.procesar_instruccion_simple(op_i, a1_i, a2_i, r_i)
            i += 1
        
        self.indentacion -= 1
        self.agregar_linea('}')
        
        # Retornar índice después del if-else
        return idx_L1 + 1
    
    def procesar_instruccion_simple(self, op, arg1, arg2, res):
        """Procesa una instrucción simple - SIN CAMBIOS"""
        if op == 'OUT':
            pin = self.convertir_valor(arg1)
            estado = 'HIGH' if arg2 == '1' else 'LOW'
            self.agregar_linea(f'digitalWrite({pin}, {estado});')
        
        elif op == '=':
            valor = self.convertir_valor(arg1)
            self.agregar_linea(f'{res} = {valor};')
        
        # NUEVO: Agregar soporte para readPin y ==
        elif op == 'readPin':
            pin = self.convertir_valor(arg1)
            self.agregar_linea(f'int {res} = digitalRead({pin});')
        
        elif op == '==':
            valor1 = self.convertir_valor(arg1)
            valor2 = self.convertir_valor(arg2)
            self.agregar_linea(f'bool {res} = ({valor1} == {valor2});')
    
    def convertir_valor(self, valor):
        """Convierte valores - SIN CAMBIOS"""
        if valor == 'TRUE':
            return 'true'
        elif valor == 'FALSE':
            return 'false'
        elif valor == 'ON':
            return 'HIGH'
        elif valor == 'OFF':
            return 'LOW'
        return valor
    
    def agregar_linea(self, texto):
        """Agrega línea con indentación - SIN CAMBIOS"""
        indent = '  ' * self.indentacion
        self.codigo.append(f'{indent}{texto}')
    
    def generar_loop(self):
        self.codigo.append('void loop() {')
        self.indentacion = 1
        self.agregar_linea('// Código repetitivo aquí')
        self.agregar_linea('delay(100);')
        self.indentacion = 0
        self.codigo.append('}')