import re

def analizar_codigo(code):
    tokens=[
        ('Comentario', r'//.*'),
        ('Multicomentario',r'/\*[\s\S]*?\*/'),

        ('text', r'"[^"\n]*"'),
        ('decimal', r'\d+\.\d+'),
        ('number', r'\d+'),
        ('bool', r'\b(?:TRUE|FALSE|ON|OFF)\b'),

        ('TipoDato',    r'\b(?:number|decimal|text|bool|void)\b'),

        ('Reservadas', r'\b(?:program|if|else|while|for|init|method|loop|print|return|Out|readPin|INPUT|OUTPUT|pinMode)\b'),
        ('Aritmeticos',r'\+|-|\*|/'),
        ('Relacionales',r'==|!=|<=|>=|<|>'),
        ('Logicos',r'\b(?:AND|OR)\b'),
        ('Asignacion',        r'='),
        ('Delimitador', r'[;,\(\)\{\}]'),

        ('Identificador', r'[a-z][a-zA-Z0-9_]*'),

        ('SaltoLinea', r'\n'),
        ('Espacio',r'[ \t]+'),
        ('PalabraInvalida', r'[A-Z][a-zA-Z0-9_]*'),
        ('MISMATH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in tokens)
    tokens_list = []
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        tipo = mo.lastgroup
        valor = mo.group()
        column = mo.start() - line_start + 1
        if tipo == 'SaltoLinea':
            line_num += 1
            line_start = mo.end()
            continue
        elif tipo in ['Espacio', 'Comentario', 'Multicomentario']:
            continue
        elif tipo in ['MISMATH','PalabraInvalida']:
            tokens_list.append(('Error',valor,line_num,column))
        else:
            tokens_list.append((tipo,valor,line_num,column))
    return tokens_list
