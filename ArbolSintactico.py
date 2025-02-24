from graphviz import Digraph

# Clase para representar un nodo del árbol sintáctico
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value      # Operador o símbolo
        self.left = left        # Hijo izquierdo
        self.right = right      # Hijo derecho
        self.position = None    # Posición de la hoja (se asigna solo a hojas)
        self.nullable = None    # Propiedad anulable

    def __repr__(self):
        return f"Node({self.value}, pos={self.position}, nullable={self.nullable})"

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
            # Crear nodo hoja y asignar posición
            node = Node(symbol)
            node.position = position_counter
            position_counter += 1
            stack.append(node)
        elif symbol == '*':
            # Operador unario: pop un hijo
            child = stack.pop()
            node = Node(symbol, left=child)
            stack.append(node)
        elif symbol in {'.', '|'}:
            # Operador binario: pop dos hijos (el segundo es el derecho)
            right = stack.pop()
            left = stack.pop()
            node = Node(symbol, left, right)
            stack.append(node)
        else:
            pass
    return stack.pop()

# Función para calcular la propiedad anulable (nullable) en el árbol sintáctico
def compute_nullable(node):
    if node is None:
        return False
    # Si es una hoja:
    if node.left is None and node.right is None:
        # Si es epsilon, anulable es True; para cualquier otro símbolo es False
        if node.value == 'ε':
            node.nullable = True
        else:
            node.nullable = False
        return node.nullable
    # Para operador unión: c1|c2 => nullable = nullable(c1) OR nullable(c2)
    if node.value == '|':
        left_nullable = compute_nullable(node.left)
        right_nullable = compute_nullable(node.right)
        node.nullable = left_nullable or right_nullable
        return node.nullable
    # Para operador concatenación: c1.c2 => nullable = nullable(c1) AND nullable(c2)
    if node.value == '.':
        left_nullable = compute_nullable(node.left)
        right_nullable = compute_nullable(node.right)
        node.nullable = left_nullable and right_nullable
        return node.nullable
    # Para operador Kleene: c* => siempre True
    if node.value == '*':
        compute_nullable(node.left)  # Calcular para el hijo (aunque no afecta)
        node.nullable = True
        return node.nullable
    return False

# Función auxiliar para imprimir el árbol de forma estructurada (incluye anulable)
def print_tree(node, indent=""):
    if node is not None:
        print(indent + f"({node.value}, pos={node.position}, nullable={node.nullable})")
        if node.left or node.right:
            print_tree(node.left, indent + "  ")
            print_tree(node.right, indent + "  ")

# Función para visualizar el árbol sintáctico usando Graphviz
def visualize_tree(node):
    dot = Digraph(comment='Árbol Sintáctico')

    def add_nodes_edges(current_node, parent_id=None):
        if current_node is None:
            return
        # Usamos id() para identificadores únicos
        node_id = str(id(current_node))
        # El label muestra el valor, posición y propiedad anulable
        label = f"{current_node.value}\\npos: {current_node.position}\\nnullable: {current_node.nullable}"
        dot.node(node_id, label)
        if parent_id:
            dot.edge(parent_id, node_id)
        add_nodes_edges(current_node.left, node_id)
        add_nodes_edges(current_node.right, node_id)

    add_nodes_edges(node)
    return dot

# Función principal para ejecutar el proceso
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
    print("Árbol sintáctico (antes de calcular anulable):")
    print_tree(syntax_tree)

    # Paso 5: Calcular la función anulable para cada nodo
    compute_nullable(syntax_tree)
    print("\nÁrbol sintáctico (después de calcular anulable):")
    print_tree(syntax_tree)

    # Visualizar el árbol sintáctico con Graphviz
    dot = visualize_tree(syntax_tree)
    dot.render('syntax_tree', view=True, format='png')
