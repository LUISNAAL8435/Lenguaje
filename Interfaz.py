import tkinter as tk
from tkinter import ttk
from tkinter import filedialog,messagebox
from Lexico import analizar_codigo
from AnalizadorSintactico import AnalizadorSintactico
import subprocess
import os

analizador_global = None
analizador_global=None

def _scroll_both(*args):
        entrada_texto.yview(*args)
        linea.yview(*args)

def _on_scroll(*args):
        scroll.set(*args)
        linea.yview_moveto(args[0])
        entrada_texto.yview_moveto(args[0])
def _actualizar_lineas(event=None):
        linea.config(state='normal')
        linea.delete('1.0', tk.END)

        total_lineas = int(entrada_texto.index('end-1c').split('.')[0])
        lineas_texto = "\n".join(str(i) for i in range(1, total_lineas + 1))

        linea.insert('1.0', lineas_texto)
        linea.config(state='disabled')
def guardar():
      contenido= entrada_texto.get("1.0",tk.END)
      ruta=filedialog.asksaveasfilename(defaultextension=".pl",filetypes=[("Archivos aT","¨.aT"),("Todos los archivos","*.*")])

      if ruta:
            with open(ruta,"w",encoding="utf-8") as archivo:
                  archivo.write(contenido)
def run():
      nombre_archivo = "codigo_generado.ino"
      datos = entrada_texto.get("1.0",tk.END)
      tokens = analizar_codigo(datos)
      texLexico.delete(1.0,tk.END)
      texLexico.insert(tk.END, "\n".join(f"tipo:{t[0]:<12} valor:{t[1]} linea:{t[2]}" for t in tokens))
      errores = [t for t in tokens if t[0] == 'Error']
      if errores:
            primero=errores[0]
            textErrores.config(state="normal")
            textErrores.delete("1.0",tk.END)
            textErrores.insert(tk.END,f"Error léxico en línea {primero[2]}:'{primero[1]}'")
            textErrores.config(fg='lightgreen',state="disabled")
            return
      analizaadorSintactico(tokens)
      if analizador_global and analizador_global.codigo_intermedio:
            print("\n=== CÓDIGO TAC GENERADO ===")
            for i, instr in enumerate(analizador_global.codigo_intermedio):
                  print(f"{i}: {instr}")
            print("===========================\n")
      if analizador_global and analizador_global.codigo_mejorado:
            print("\n=== CÓDIGO TAC MEJORADO ===")
            for j, instrr in enumerate(analizador_global.codigo_mejorado):
                  print(f"{j}: {instrr}")
            print("===========================\n")

      if analizador_global and analizador_global.codigo_optimizadoo:
            print("\n=== CÓDIGO FINAL PARA ARDUINO/ESP32 ===")
            print("=" * 50)
            print(analizador_global.codigo_optimizadoo)
            print("=" * 50)
            
            # También puedes guardarlo en un archivo .ino
            with open("codigo_generado.ino", "w") as f:
                f.write(analizador_global.codigo_optimizadoo)
                carpeta_sketch = nombre_archivo.replace(".ino", "")
            if not os.path.exists(carpeta_sketch):
                os.makedirs(carpeta_sketch)

            # 3. Mover el archivo dentro de esa carpeta
            nuevo_path = os.path.join(carpeta_sketch, nombre_archivo)
            os.replace(nombre_archivo, nuevo_path)

            print(f"Archivo creado correctamente en:\n{nuevo_path}")

tabla_global = None  
def subir_codigo():
    archivo = filedialog.askopenfilename(
        title="Select File",
        filetypes=[("Archivos aT","*.ino"), ("Todos los archivos","*.*")]
    )

    if not archivo:
        return

    try:
        with open(archivo, 'r', encoding='latin-1') as f:
            code = f.read()
            entrada_texto.delete("1.0", tk.END)
            entrada_texto.insert(tk.END, code)
            _actualizar_lineas()

        # ===== COMPILAR =====
        compilar = subprocess.run(
            ["C:\\arduino-cli_1.3.1_Windows_64bit\\arduino-cli.exe", "compile", "--fqbn", "esp32:esp32:esp32", archivo],
            capture_output=True,
            text=True
        )

        if compilar.returncode != 0:
            messagebox.showerror("Error compilando", compilar.stderr)
            return

        # ===== SUBIR =====
        subir = subprocess.run(
            ["C:\\arduino-cli_1.3.1_Windows_64bit\\arduino-cli.exe", "upload", "-p", "COM9", "--fqbn", "esp32:esp32:esp32", archivo],
            capture_output=True,
            text=True
        )

        if subir.returncode != 0:
            messagebox.showerror("Error al subir", subir.stderr)
            return

        messagebox.showinfo("Éxito", "Código compilado y subido correctamente al ESP32.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema:\n{e}")

def analizaadorSintactico(tokens):
    global tabla_global, analizador_global  # Añade analizador_global
    try:
        analizador = AnalizadorSintactico(tokens)
        analizador.program()
        tabla_global = analizador.tablaGlobales
        analizador_global = analizador  # ¡IMPORTANTE! Guardar el analizador
        
        labelExito.config(text="Correct", fg="lightgreen")
        textErrores.config(state="normal")
        textErrores.delete("1.0", tk.END)
        textErrores.config(state="disabled")
        
    except Exception as e:
        labelExito.config(text=f"Incorrect:\n", fg="lightgreen")
        textErrores.config(state="normal")
        textErrores.delete("1.0", tk.END)
        textErrores.insert(tk.END, str(e) + "\n")
        textErrores.see(tk.END)
        textErrores.config(state="disabled")
def mostrar_codigo_tresDirec():
    global analizador_global
    
    if analizador_global is None:
        messagebox.showinfo("Código de 3 direcciones", 
                           "Primero ejecuta el análisis sintáctico con el botón RUN.")
        return
    
    try:
        ventana_tabla = tk.Toplevel(root)
        ventana_tabla.title("Código de Tres Direcciones")
        ventana_tabla.geometry("800x500")
        ventana_tabla.configure(bg="black")

        tk.Label(
            ventana_tabla,
            text="CÓDIGO INTERMEDIO TAC",
            font=("Consolas", 14, "bold"),
            bg="black",
            fg="cyan"
        ).pack(pady=10)
        
        # Widget de texto con scroll
        frame = tk.Frame(ventana_tabla, bg="black")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_codigo = tk.Text(
            frame,
            bg="black",
            fg="lightgreen",
            font=("Consolas", 11),
            width=80,
            height=20
        )
        scrollbar = tk.Scrollbar(frame, command=text_codigo.yview)
        text_codigo.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        text_codigo.pack(side="left", fill="both", expand=True)
        
        # Mostrar código TAC con formato mejorado
        codigo_tac = analizador_global.codigo_intermedio
        
        if not codigo_tac:
            text_codigo.insert(tk.END, "No se generó código TAC.\n")
        else:
            text_codigo.insert(tk.END, f"Se generaron {len(codigo_tac)} instrucciones TAC:\n")
            text_codigo.insert(tk.END, "="*60 + "\n\n")
            
            # Contador de instrucciones (ignorando etiquetas en la numeración)
            num_instr = 0
            
            for instr in codigo_tac:
                if isinstance(instr, tuple) and len(instr) == 4:
                    op, arg1, arg2, resultado = instr
                    
                    # Si es una etiqueta (termina con :)
                    if isinstance(op, str) and op.endswith(':'):
                        text_codigo.insert(tk.END, f"\n{op}\n")
                        continue
                    
                    num_instr += 1
                    linea = f"{num_instr:3d}: "
                    
                    # CASOS ESPECIALES PRIMERO:
                    
                    # 1. Asignación simple: ('=', 't0', 'suma', '-')
                    if op == '=' and resultado == '-':
                        # t0 = suma
                        linea += f"{arg2} = {arg1}"
                    # 1. literal: ('literal', 'INPUT', '-', 't0') → t0 = "INPUT"
                    elif op == 'literal':
                        linea += f"{resultado} = \"{arg1}\""

                    elif op == 'pinMode':
                        linea += f"pinMode({arg1}, {arg2})"
                    elif op == 'readPin':
                        linea += f"{resultado} = readPin({arg1})"

                    # 2. Asignación con temporal: ('=', 'valor', 'variable', '-')
                    elif op == '=' and arg2 != '-':
                        # variable = valor
                        linea += f"{arg2} = {arg1}"
                    
                    # 3. Operaciones binarias: ('+', 'a', 'b', 't0')
                    elif op in ['+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=']:
                        # t0 = a + b
                        linea += f"{resultado} = {arg1} {op} {arg2}"
                    
                    # 4. Operaciones lógicas: ('AND', 'a', 'b', 't0')
                    elif op in ['AND', 'OR']:
                        # t0 = a AND b
                        linea += f"{resultado} = {arg1} {op.lower()} {arg2}"
                    
                    # 5. Saltos condicionales: ('ifFalse', 'cond', '-', 'label')
                    elif op == 'ifFalse':
                        # if not cond goto label
                        linea += f"if not {arg1} goto {resultado}"
                    
                    # 6. Saltos: ('goto', 'label', '-', '-')
                    elif op == 'goto':
                        if arg1 != '-':
                             linea += f"goto {arg1}"
                        elif resultado != '-':
                             linea += f"goto {resultado}"
                        else:
                             linea += "goto (etiqueta siguiente)"
                    # 7. Condicional (para for): ('if', 'cond', '-', 'label')
                    elif op == 'if':
                        # if cond goto label
                        linea += f"if {arg1} goto {resultado}"
                    
                    # 8. Llamadas: ('call', 'func', 'args', 't0')
                    elif op == 'call':
                        if arg2 == '-':
                            # t0 = call func
                            linea += f"{resultado} = call {arg1}"
                        else:
                            # t0 = call func(args)
                            linea += f"{resultado} = call {arg1}({arg2})"
                    
                    # 9. Return: ('return', 'valor', '-', '-')
                    elif op == 'return':
                        if arg1 != '-':
                            # return valor
                            linea += f"return {arg1}"
                        else:
                            # return
                            linea += "return"
                    
                    # 10. Print: ('print', 'valor', '-', '-')
                    elif op == 'print':
                        # print valor
                        linea += f"print {arg1}"
                    
                    # 11. Instrucciones especiales del lenguaje
                    elif op in ['pinMode', 'readPin', 'OUT', 'literal']:
                        if arg2 == '-':
                            # pinMode pin
                            linea += f"{op} {arg1}"
                        else:
                            # pinMode pin, modo
                            linea += f"{op} {arg1}, {arg2}"
                    
                    # CASO POR DEFECTO (no debería llegar aquí)
                    else:
                        linea += f"{op} {arg1} {arg2} {resultado}"
                    
                    text_codigo.insert(tk.END, linea + "\n")
                
                else:
                    # Si no es una tupla de 4 elementos, mostrarla tal cual
                    num_instr += 1
                    text_codigo.insert(tk.END, f"{num_instr:3d}: {str(instr)}\n")
            
            text_codigo.insert(tk.END, "\n" + "="*60 + "\n")
            
        text_codigo.config(state="normal")
        
        # Botón para copiar al portapapeles
        def copiar_codigo():
            contenido = text_codigo.get("1.0", tk.END)
            root.clipboard_clear()
            root.clipboard_append(contenido)
            messagebox.showinfo("Copiar", "Código TAC copiado al portapapeles")
        
        btn_copiar = tk.Button(
            ventana_tabla,
            text="Copiar Código",
            command=copiar_codigo,
            bg="green",
            fg="white",
            font=("Arial", 10)
        )
        btn_copiar.pack(pady=5)
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo mostrar el código TAC:\n{e}")
def mostrar_tabla_simbolos():
      global tabla_global
      if tabla_global is None or not tabla_global.tabla:
            messagebox.showinfo("Tabla de Símbolos", "No hay símbolos registrados todavía.")
            return

      ventana_tabla = tk.Toplevel(root)
      ventana_tabla.title("Tabla de Símbolos")
      ventana_tabla.geometry("900x400")
      ventana_tabla.configure(bg="black")

      label = tk.Label(
            ventana_tabla,
            text="TABLA DE SÍMBOLOS",
            font=("Consolas", 14, "bold"),
            bg="black",
            fg="cyan"
      )
      label.pack(pady=10)

      columnas = ("nombre", "tipo", "valor", "categoria", "ambito", "linea", "columna", "inicializado", "parametro", "tamaño")
      tree = ttk.Treeview(ventana_tabla, columns=columnas, show="headings",height=15)
      encabezados = ["Nombre", "Tipo", "Valor", "Categoría", "Ámbito", "Línea", "Columna", "Inicializado", "Parámetro","Tamaño"]
      for col, texto in zip(columnas, encabezados):
        tree.heading(col, text=texto)
        tree.column(col, width=100, anchor="center")
      scroll_y = tk.Scrollbar(ventana_tabla, orient="vertical", command=tree.yview)
      tree.configure(yscrollcommand=scroll_y.set)
      scroll_y.pack(side="right", fill="y")
      tree.pack(fill="both", expand=True, padx=10, pady=5)
      # Insertar filas
      for nombre, attrs in tabla_global.tabla.items():
        tree.insert(
            "",
            tk.END,
            values=(
                nombre,
                attrs.get("tipo", ""),
                attrs.get("valor", ""),
                attrs.get("categoria", ""),
                attrs.get("Ambito", ""),
                attrs.get("linea", ""),
                attrs.get("columna", ""),
                attrs.get("Inicializado", ""),
                attrs.get("parametro", ""),
                attrs.get("tamaño", "")
            )
        )
      style = ttk.Style()
      style.theme_use("default")
      style.configure("Treeview",
                  background="black",
                  foreground="white",
                  rowheight=25,
                  fieldbackground="black")
      style.map('Treeview', background=[('selected', 'dodgerblue')])

            
def openFile():
      archivo=filedialog.askopenfilename(
            title="Select File",
            filetypes=[("Archivos aT","*aT"),("Todos los archivos","*.*")]
      )
      if archivo:
            try:
                  with open(archivo,'r',encoding='utf-8') as f:
                        code= f.read()
                        entrada_texto.delete("1.0",tk.END)
                        entrada_texto.insert(tk.END,code)
                        _actualizar_lineas()
            except Exception as e:
                    messagebox.showerror("Error", f"No se pudo analizar el archivo:\n{e}")
root = tk.Tk()
root.title("ATOM")
root.geometry("1300x600")
root.configure(bg="black")
#cONTENEDOR1
contenedor1=tk.Frame(root,bg="dodgerblue")
contenedor1.pack(fill="both",expand=True, padx=1,pady=1)
#contenedorAlto
contenedor = tk.Frame(contenedor1, bg="black", height=50)
contenedor.pack(padx=1,pady=1,fill="x")
btn_openFile=tk.Button(contenedor,width=10,height=1,text="OPEN FILE",command=openFile)
btn_openFile.pack(pady=2,padx=2,side="left")
btn_save=tk.Button(contenedor,width=10,height=1,text="SAVE",command=guardar)
btn_save.pack(pady=2,padx=2,side="left")
labelExito=tk.Label(contenedor,text="Estatus:",width=30,bg="black",fg="white")
labelExito.pack(pady=2,padx=2,side="left")
btn_tabla=tk.Button(contenedor,width=10,height=1,text="TABLA",command=mostrar_tabla_simbolos)
btn_tabla.pack(pady=2,padx=2,side="right")
btn_cod=tk.Button(contenedor,width=10,height=1,text="COD",command=mostrar_codigo_tresDirec)
btn_cod.pack(pady=2,padx=2,side="right")
btn_sub=tk.Button(contenedor,width=10,height=1,text="SUB",command=subir_codigo)
btn_sub.pack(pady=2,padx=2,side="right")
btn_run=tk.Button(contenedor,width=10,height=1,text="RUN",command=run)
btn_run.pack(pady=2,padx=2,side="right")
#ContenedorIntermedio
contenedor2=tk.Frame(contenedor1, bg="black",height=400)
contenedor2.pack(padx=1,pady=1,fill="x")

scroll = tk.Scrollbar(contenedor2, command=_scroll_both,bg="black")
scroll.pack(side="right", fill="y")
entrada_texto=tk.Text(contenedor2,bg="black",fg="white")
entrada_texto.pack(side="right",fill="both", expand=True)
linea=tk.Text(contenedor2, width=4, takefocus=0, border=0,background='black',fg="white", state='disabled')
linea.pack(side="left", fill="y")
entrada_texto.config(yscrollcommand=_on_scroll)
linea.config(yscrollcommand=_on_scroll)
# Función que se ejecuta al cambiar tamaño
def ajustar_altura(event):
    # event.width y event.height nos dan el tamaño actual de la ventana
    if root.state() == "zoomed":  # detecta si está maximizada
        contenedor2.config(height=500)  # altura mayor cuando maximizada
    else:
        contenedor2.config(height=400)

# Vinculamos la función al evento Configure
root.bind("<Configure>", ajustar_altura)

#contenedorBajo
contenedor3= tk.Frame(contenedor1,bg="black",height=150)
contenedor3.pack(side="bottom",padx=5, pady=5, fill="both", expand=True)

contenedor3.grid_rowconfigure(0, weight=1)  # Fila 0 se expande
contenedor3.grid_columnconfigure(0, weight=30)  # 40% para la primera columna
contenedor3.grid_columnconfigure(1, weight=70)  # 60% para la segunda columna
texLexico=tk.Text(contenedor3,bg="black",fg="lightgreen",width=40)
texLexico.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

textErrores=tk.Text(contenedor3,bg="black",fg="red",width=40)
textErrores.grid(row=0, column=1, sticky="nsew")




 # Evento de actualización
entrada_texto.bind("<KeyRelease>", _actualizar_lineas)
entrada_texto.bind("<MouseWheel>", _actualizar_lineas)
_actualizar_lineas()
#Se encarga de mostrar la ventana
root.mainloop()