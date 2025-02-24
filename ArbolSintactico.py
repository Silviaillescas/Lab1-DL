from graphviz import Digraph

# Clase para representar un nodo del árbol sintáctico
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value          # Operador o símbolo
        self.left = left            # Hijo izquierdo
        self.right = right          # Hijo derecho
        self.position = None        # Posición de la hoja (solo hojas)
        self.nullable = None        # Propiedad anulable
        self.firstpos = set()       # Conjunto de primeras posiciones
        self.lastpos = set()        # Conjunto de últimas posiciones

    def __repr__(self):
        return (f"Node({self.value}, pos={self.position}, nullable={self.nullable}, "
                f"firstpos={self.firstpos}, lastpos={self.lastpos})")

# Función para insertar el operador de concatenación ('.') de forma explícita
def add_concat_operator(regex):
    result = ""
    for i in range(len(regex)):
        c = regex[i]
        result += c
        if i + 1 < len(regex):
            next_c = regex[i+1]
            # Se inserta concatenación si:
            #  - c NO es '|' o '('
            #  - next_c NO es '|' o ')' o '*'
            if (c not in {'|', '('} and next_c not in {'|', ')', '*'}):
                result += '.'
    return result

# Función para convertir la expresión de infijo a postfijo (algoritmo Shunting-yard)
def infix_to_postfix(regex):
    precedence = {'*': 3, '.': 2, '|': 1}
    output = []
    stack = []
    for c in regex:
        if c.isalnum() or c in {'#', 'ε'}:  # operandos: letras, '#' o ε
            output.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            # Sacar operadores hasta encontrar '('
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()  # Remover '('
        else:
            # c es un operador: '*', '.', '|'
            while (stack and stack[-1] != '(' and
                   precedence.get(stack[-1], 0) >= precedence.get(c, 0)):
                output.append(stack.pop())
            stack.append(c)
    # Vaciar la pila
    while stack:
        output.append(stack.pop())
    return "".join(output)

# Función para construir el árbol sintáctico a partir de la notación postfija
def build_syntax_tree(postfix):
    stack = []
    position_counter = 1  # Contador para etiquetar las hojas
    for symbol in postfix:
        if symbol.isalnum() or symbol in {'#', 'ε'}:
            node = Node(symbol)
            node.position = position_counter
            position_counter += 1
            stack.append(node)
        elif symbol == '*':
            child = stack.pop()
            node = Node(symbol, left=child)
            stack.append(node)
        elif symbol in {'.', '|'}:
            right = stack.pop()
            left = stack.pop()
            node = Node(symbol, left, right)
            stack.append(node)
        else:
            pass
    return stack.pop()

# Función para calcular la propiedad anulable (nullable)
def compute_nullable(node):
    if node is None:
        return False
    # Si es hoja:
    if node.left is None and node.right is None:
        node.nullable = True if node.value == 'ε' else False
        return node.nullable
    if node.value == '|':
        left_nullable = compute_nullable(node.left)
        right_nullable = compute_nullable(node.right)
        node.nullable = left_nullable or right_nullable
        return node.nullable
    if node.value == '.':
        left_nullable = compute_nullable(node.left)
        right_nullable = compute_nullable(node.right)
        node.nullable = left_nullable and right_nullable
        return node.nullable
    if node.value == '*':
        compute_nullable(node.left)
        node.nullable = True
        return node.nullable
    return False

# Función para calcular firstpos en el árbol sintáctico
def compute_firstpos(node):
    if node is None:
        return set()
    # Si es hoja:
    if node.left is None and node.right is None:
        node.firstpos = set() if node.value == 'ε' else {node.position}
        return node.firstpos
    if node.value == '|':
        left_first = compute_firstpos(node.left)
        right_first = compute_firstpos(node.right)
        node.firstpos = left_first.union(right_first)
        return node.firstpos
    if node.value == '.':
        left_first = compute_firstpos(node.left)
        right_first = compute_firstpos(node.right)
        if node.left.nullable:
            node.firstpos = left_first.union(right_first)
        else:
            node.firstpos = left_first
        return node.firstpos
    if node.value == '*':
        child_first = compute_firstpos(node.left)
        node.firstpos = child_first
        return node.firstpos
    return set()

# Función para calcular lastpos en el árbol sintáctico
def compute_lastpos(node):
    if node is None:
        return set()
    # Si es hoja:
    if node.left is None and node.right is None:
        node.lastpos = set() if node.value == 'ε' else {node.position}
        return node.lastpos
    if node.value == '|':
        left_last = compute_lastpos(node.left)
        right_last = compute_lastpos(node.right)
        node.lastpos = left_last.union(right_last)
        return node.lastpos
    if node.value == '.':
        left_last = compute_lastpos(node.left)
        right_last = compute_lastpos(node.right)
        # Si c2 es anulable, se unen las últimas posiciones de c1 y c2; si no, solo c2
        if node.right.nullable:
            node.lastpos = left_last.union(right_last)
        else:
            node.lastpos = right_last
        return node.lastpos
    if node.value == '*':
        child_last = compute_lastpos(node.left)
        node.lastpos = child_last
        return node.lastpos
    return set()

# Función para inicializar la tabla de followpos (diccionario)
# pos_to_symbol guarda el símbolo de cada posición
def initialize_followpos(node, followpos, pos_to_symbol):
    if node is None:
        return
    if node.left is None and node.right is None:
        followpos[node.position] = set()
        pos_to_symbol[node.position] = node.value
    else:
        initialize_followpos(node.left, followpos, pos_to_symbol)
        initialize_followpos(node.right, followpos, pos_to_symbol)

# Función para calcular followpos en el árbol sintáctico
def compute_followpos(node, followpos):
    if node is None:
        return
    # Si es un nodo de concatenación: para cada posición en lastpos(c1) se agrega firstpos(c2)
    if node.value == '.':
        for p in node.left.lastpos:
            followpos[p].update(node.right.firstpos)
    # Si es un nodo de Kleene: para cada posición en lastpos(c) se agrega firstpos(c)
    if node.value == '*':
        for p in node.left.lastpos:
            followpos[p].update(node.left.firstpos)
    compute_followpos(node.left, followpos)
    compute_followpos(node.right, followpos)

# Función auxiliar para imprimir el árbol (incluye nullable, firstpos y lastpos)
def print_tree(node, indent=""):
    if node is not None:
        print(indent + f"({node.value}, pos={node.position}, nullable={node.nullable}, "
              f"firstpos={node.firstpos}, lastpos={node.lastpos})")
        if node.left or node.right:
            print_tree(node.left, indent + "  ")
            print_tree(node.right, indent + "  ")

# Función para visualizar el árbol sintáctico con Graphviz (se muestra firstpos y lastpos)
def visualize_tree(node):
    dot = Digraph(comment='Árbol Sintáctico')
    
    def add_nodes_edges(current_node, parent_id=None):
        if current_node is None:
            return
        node_id = str(id(current_node))
        label = (f"{current_node.value}\\npos: {current_node.position}\\n"
                 f"nullable: {current_node.nullable}\\n"
                 f"firstpos: {current_node.firstpos}\\n"
                 f"lastpos: {current_node.lastpos}")
        # Asigna color según si es hoja (verde) o rama (café)
        if current_node.left is None and current_node.right is None:
            dot.node(node_id, label, style='filled', fillcolor='lightgreen')
        else:
            dot.node(node_id, label, style='filled', fillcolor='burlywood')
        if parent_id:
            dot.edge(parent_id, node_id)
        add_nodes_edges(current_node.left, node_id)
        add_nodes_edges(current_node.right, node_id)
    
    add_nodes_edges(node)
    return dot

# Función principal para ejecutar todo el proceso
if __name__ == "__main__":
    # Solicitar la expresión regular al usuario
    regex_input = input("Ingresa la expresión regular: ")
    
    # Paso 1: Aumentar la expresión agregando '#' al final
    regex_augmented = regex_input + "#"
    print("Expresión aumentada:", regex_augmented)
    
    # Paso 2: Insertar el operador de concatenación explícito
    regex_with_concat = add_concat_operator(regex_augmented)
    print("Expresión con concatenación explícita:", regex_with_concat)
    
    # Paso 3: Convertir la expresión de infijo a postfijo
    postfix = infix_to_postfix(regex_with_concat)
    print("Expresión en notación postfija:", postfix)
    
    # Paso 4: Construir el árbol sintáctico y etiquetar las hojas
    syntax_tree = build_syntax_tree(postfix)
    print("Árbol sintáctico (antes de calcular funciones):")
    print_tree(syntax_tree)
    
    # Paso 5: Calcular la función anulable (nullable)
    compute_nullable(syntax_tree)
    
    # Paso 6: Calcular la función firstpos para cada nodo
    compute_firstpos(syntax_tree)
    
    # Paso 7: Calcular la función lastpos para cada nodo
    compute_lastpos(syntax_tree)
    
    print("\nÁrbol sintáctico (después de calcular nullable, firstpos y lastpos):")
    print_tree(syntax_tree)
    
    # Paso 8: Calcular followpos
    # Inicializamos la tabla de followpos y un diccionario auxiliar que mapea posición a símbolo
    followpos = {}
    pos_to_symbol = {}
    initialize_followpos(syntax_tree, followpos, pos_to_symbol)
    compute_followpos(syntax_tree, followpos)
    
    # Mostrar la tabla de followpos
    print("\nTabla de followpos:")
    print("{:<10} {:<10} {:<20}".format("Posición", "Símbolo", "Followpos"))
    for pos in sorted(followpos.keys()):
        print("{:<10} {:<10} {:<20}".format(pos, pos_to_symbol[pos], str(followpos[pos])))
    
    # Visualizar el árbol sintáctico con Graphviz
    dot = visualize_tree(syntax_tree)
    dot.render('syntax_tree', view=True, format='png')
