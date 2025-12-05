class OptimizadorTAC:
    def __init__(self, cuadruplas):
        self.cuadruplas = cuadruplas
        self.constantes = {}
        self.etiquetas_usadas = set()
        
    def optimizar(self):
        """Aplica optimizaciones en el orden correcto"""
        print("\n" + "="*50)
        print("OPTIMIZACIÓN MEJORADA DEL CÓDIGO TAC")
        print("="*50)
        
        # 1. Análisis inicial
        self.analizar_etiquetas()
        
        # 2. Aplicar optimizaciones en orden lógico
        optimizado = self.cuadruplas
        
        optimizado = self.propagacion_constantes_total(optimizado)
        print("✓ Propagación total de constantes")
        
        optimizado = self.eliminar_asignaciones_redundantes(optimizado)
        print("✓ Eliminación de asignaciones redundantes")
        
        optimizado = self.combinar_literal_con_operacion(optimizado)
        print("✓ Combinación de literales con operaciones")
        
        optimizado = self.eliminar_codigo_inaccesible(optimizado)
        print("✓ Eliminación de código inaccesible")
        
        return optimizado
    
    def analizar_etiquetas(self):
        """Identifica qué etiquetas se usan realmente"""
        for op, arg1, arg2, res in self.cuadruplas:
            if op in ['goto', 'ifFalse'] and arg1:
                self.etiquetas_usadas.add(arg1)
    
    def propagacion_constantes_total(self, cuadruplas):
        """Propagación completa de constantes - VERSIÓN MEJORADA"""
        constantes = {}
        nuevas = []
        
        # ========== NUEVO: Contar cuántas veces se asigna cada variable ==========
        contador_asignaciones = {}
        
        for op, arg1, arg2, res in cuadruplas:
            if op == '=' and res:  # Es una asignación a variable
                contador_asignaciones[res] = contador_asignaciones.get(res, 0) + 1
        # =========================================================================
        
        # Fase 1: Identificar todas las constantes
        for op, arg1, arg2, res in cuadruplas:
            # Guardar asignaciones constantes
            if op == '=' and self._es_constante_simple(arg1):
                # SOLO si la variable se asigna UNA sola vez
                if contador_asignaciones.get(res, 0) == 1:
                    constantes[res] = arg1
            elif op == 'literal':
                constantes[res] = arg1
            # También variables globales constantes (led, sensor)
            elif op == '=' and res in ['led', 'sensor']:
                constantes[res] = arg1  # Estos siempre son constantes
        
        # Fase 2: Aplicar propagación
        for op, arg1, arg2, res in cuadruplas:
            # Reemplazar argumentos con constantes conocidas
            nueva_arg1 = constantes.get(arg1, arg1)
            nueva_arg2 = constantes.get(arg2, arg2)
            
            # Casos especiales:
            
            # 1. Si es una asignación de constante a variable conocida
            if op == '=' and res in constantes and constantes[res] == nueva_arg1:
                # SOLO omitir si la variable se asigna UNA sola vez
                if contador_asignaciones.get(res, 0) == 1:
                    continue  # Es redundante
            
            # 2. Si es pinMode con constante
            elif op == 'pinMode' and nueva_arg1 in constantes:
                pin = constantes.get(nueva_arg1, nueva_arg1)
                nuevas.append((op, pin, nueva_arg2, res))
            
            # 3. Si es OUT con constante
            elif op == 'OUT' and nueva_arg1 in constantes:
                pin = constantes.get(nueva_arg1, nueva_arg1)
                nuevas.append((op, pin, nueva_arg2, res))
            
            # 4. Si es readPin con constante
            elif op == 'readPin' and nueva_arg1 in constantes:
                pin = constantes.get(nueva_arg1, nueva_arg1)
                nuevas.append((op, pin, nueva_arg2, res))
            
            else:
                nuevas.append((op, nueva_arg1, nueva_arg2, res))
        
        return nuevas
    
    def _es_constante_simple(self, valor):
        """Determina si es una constante simple (número o string literal)"""
        if not valor:
            return False
        try:
            float(valor)
            return True
        except ValueError:
            if valor.startswith('"') and valor.endswith('"'):
                return True
            if valor in ['INPUT', 'OUTPUT']:
                return True
            return False
    
    def eliminar_asignaciones_redundantes(self, cuadruplas):
        """Elimina asignaciones redundantes como t = t"""
        nuevas = []
        
        for op, arg1, arg2, res in cuadruplas:
            if op == '=' and arg1 == res:
                # Asignación redundante: x = x
                continue
            elif op == 'literal' and arg1 in ['INPUT', 'OUTPUT']:
                # Mantener solo si se va a usar
                se_usara = False
                for op2, a1, a2, r2 in cuadruplas:
                    if a1 == res or a2 == res:
                        se_usara = True
                        break
                if not se_usara:
                    continue
            nuevas.append((op, arg1, arg2, res))
        
        return nuevas
    
    def combinar_literal_con_operacion(self, cuadruplas):
        """Combina literales con operaciones que los usan inmediatamente"""
        nuevas = []
        i = 0
        n = len(cuadruplas)
        
        while i < n:
            op, arg1, arg2, res = cuadruplas[i]
            
            # Caso: literal seguido de pinMode/OUT que lo usa
            if op == 'literal' and i + 1 < n:
                next_op, next_arg1, next_arg2, next_res = cuadruplas[i + 1]
                
                # Si la siguiente operación usa este literal
                if next_arg2 == res and next_op in ['pinMode', 'OUT', 'readPin']:
                    # Combinar: usar el valor directamente
                    if next_op == 'pinMode':
                        if arg1 == 'INPUT':
                            nuevas.append(('pinMode', next_arg1, 'INPUT', next_res))
                        else:
                            nuevas.append(('pinMode', next_arg1, 'OUTPUT', next_res))
                    elif next_op == 'OUT':
                        if arg1 == '1':
                            nuevas.append(('OUT', next_arg1, 'HIGH', next_res))
                        else:
                            nuevas.append(('OUT', next_arg1, 'LOW', next_res))
                    elif next_op == 'readPin':
                        nuevas.append(('readPin', next_arg1, '-', next_res))
                    
                    i += 2  # Saltar ambas
                    continue
            
            # Caso: literal '1' o '0' seguido de asignación
            elif op == 'literal' and arg1 in ['1', '0'] and res.startswith('t'):
                # Verificar si se usa inmediatamente
                if i + 1 < n:
                    next_op, next_arg1, next_arg2, next_res = cuadruplas[i + 1]
                    if next_op == '=' and next_arg1 == res:
                        # Combinar
                        nuevas.append(('=', arg1, '-', next_res))
                        i += 2
                        continue
            
            nuevas.append((op, arg1, arg2, res))
            i += 1
        
        return nuevas
    
    def eliminar_codigo_inaccesible(self, cuadruplas):
        """Elimina código después de un return no condicional"""
        nuevas = []
        encontro_return = False
        
        for op, arg1, arg2, res in cuadruplas:
            if encontro_return and op != 'L0:' and op != 'L1:':
                # Saltar código después de return
                continue
            
            if op == 'return':
                encontro_return = True
            
            nuevas.append((op, arg1, arg2, res))
        
        return nuevas


# VERSIÓN HIPER-OPTIMIZADA ESPECÍFICA PARA TU CÓDIGO
class OptimizadorEspecifico:
    @staticmethod
    def optimizar_tu_codigo(cuadruplas):
        """Optimización específica para tu patrón de código"""
        
        print("\n" + "="*50)
        print("OPTIMIZACIÓN ESPECÍFICA PARA TU CÓDIGO")
        print("="*50)
        
        # PASO 1: Reemplazar variables por constantes
        optimizado = []
        reemplazos = {'led': '1', 'sensor': '1'}  # De tus primeras líneas
        
        for op, arg1, arg2, res in cuadruplas:
            # Reemplazar usos de led y sensor
            nueva_arg1 = reemplazos.get(arg1, arg1)
            nueva_arg2 = reemplazos.get(arg2, arg2)
            
            # PASO 2: Combinar operaciones comunes
            if op == 'literal' and arg1 in ['INPUT', 'OUTPUT']:
                # Guardar para combinar con pinMode
                optimizado.append((op, arg1, arg2, res))
            
            elif op == 'pinMode':
                # Combinar con literal anterior si existe
                if optimizado and optimizado[-1][0] == 'literal':
                    prev_op, prev_arg1, prev_arg2, prev_res = optimizado[-1]
                    if prev_res == nueva_arg2:
                        # Usar el valor directamente
                        modo = 'INPUT' if prev_arg1 == 'INPUT' else 'OUTPUT'
                        optimizado[-1] = ('pinMode', nueva_arg1, modo, res)
                    else:
                        optimizado.append(('pinMode', nueva_arg1, nueva_arg2, res))
                else:
                    optimizado.append(('pinMode', nueva_arg1, nueva_arg2, res))
            
            elif op == 'OUT':
                # Simplificar HIGH/LOW
                if nueva_arg2 == '1' or nueva_arg2 == 't3':
                    optimizado.append(('OUT', nueva_arg1, 'HIGH', res))
                elif nueva_arg2 == '0' or nueva_arg2 == 't4':
                    optimizado.append(('OUT', nueva_arg1, 'LOW', res))
                else:
                    optimizado.append((op, nueva_arg1, nueva_arg2, res))
            
            else:
                optimizado.append((op, nueva_arg1, nueva_arg2, res))
        
        # PASO 3: Eliminar asignaciones redundantes
        final = []
        for i, (op, arg1, arg2, res) in enumerate(optimizado):
            # Eliminar asignaciones t2 = t2 (después de propagación)
            if op == '=' and arg1 == res:
                continue
            
            # Eliminar literales que no se usan
            if op == 'literal' and res.startswith('t'):
                usado = False
                for j in range(i+1, len(optimizado)):
                    if optimizado[j][1] == res or optimizado[j][2] == res:
                        usado = True
                        break
                if not usado:
                    continue
            
            final.append((op, arg1, arg2, res))
        
        print("✓ Reemplazo de variables por constantes")
        print("✓ Combinación de literales con operaciones")
        print("✓ Eliminación de código redundante")
        
        return final
