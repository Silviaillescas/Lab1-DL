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
            if (c not in {'|', '('} and next_c not in {'|', ')', '*'}):
                result += '.'
    return result

# Función para convertir la expresión de infijo a postfijo (algoritmo Shunting-yard)
def infix_to_postfix(regex):
    precedence = {'*': 3, '.': 2, '|': 1}
    output = []
    stack = []
    for c in regex:
        if c.isalnum() or c in {'#', 'ε'}:
            output.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:
            while (stack and stack[-1] != '(' and
                   precedence.get(stack[-1], 0) >= precedence.get(c, 0)):
                output.append(stack.pop())
            stack.append(c)
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
    return stack.pop()

# Función para calcular la propiedad anulable (nullable)
def compute_nullable(node):
    if node is None:
        return False
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
    if node.value == '.':
        for p in node.left.lastpos:
            followpos[p].update(node.right.firstpos)
    if node.value == '*':
        for p in node.left.lastpos:
            followpos[p].update(node.left.firstpos)
    compute_followpos(node.left, followpos)
    compute_followpos(node.right, followpos)

# Función para construir el DFA usando followpos y el árbol sintáctico
def build_dfa(syntax_tree, followpos, pos_to_symbol):
    initial_state = frozenset(syntax_tree.firstpos)
    states = {initial_state: "S0"}  # Mapeo: conjunto de posiciones -> nombre de estado
    unmarked_states = [initial_state]
    dfa_transitions = {}  # (estado, símbolo) -> estado destino
    state_counter = 1

    # Definir el alfabeto: símbolos de las hojas, excluyendo ε y '#' (este último se usa para marcar fin)
    alphabet = {symbol for pos, symbol in pos_to_symbol.items() if symbol not in {'ε', '#'}}

    while unmarked_states:
        T = unmarked_states.pop(0)
        for a in alphabet:
            U = set()
            for p in T:
                if pos_to_symbol[p] == a:
                    U.update(followpos[p])
            if U:
                U_frozen = frozenset(U)
                if U_frozen not in states:
                    states[U_frozen] = f"S{state_counter}"
                    state_counter += 1
                    unmarked_states.append(U_frozen)
                dfa_transitions[(states[T], a)] = states[U_frozen]
    return states, dfa_transitions, initial_state

# Función para obtener los estados de aceptación (si incluyen la posición de '#')
def get_accepting_states(states, pos_to_symbol):
    accepting = []
    for state_set, name in states.items():
        for p in state_set:
            if pos_to_symbol[p] == '#':
                accepting.append(name)
                break
    return accepting

# Función para graficar el DFA usando Graphviz
def visualize_dfa(states, dfa_transitions, initial_state, accepting_states):
    dot = Digraph(comment='DFA')

    # Crear los nodos del DFA
    for state_set, label in states.items():
        if label in accepting_states:
            dot.node(label, label, shape='doublecircle', style='filled', fillcolor='lightblue')
        else:
            dot.node(label, label, shape='circle', style='filled', fillcolor='white')

    # Nodo inicial invisible y flecha hacia el estado inicial
    dot.node("", "", shape="none")
    dot.edge("", states[initial_state])

    # Agregar las transiciones
    for (src, symbol), dest in dfa_transitions.items():
        dot.edge(src, dest, label=symbol)

    return dot

# Función auxiliar para imprimir el árbol sintáctico (incluye nullable, firstpos y lastpos)
def print_tree(node, indent=""):
    if node is not None:
        print(indent + f"({node.value}, pos={node.position}, nullable={node.nullable}, "
              f"firstpos={node.firstpos}, lastpos={node.lastpos})")
        if node.left or node.right:
            print_tree(node.left, indent + "  ")
            print_tree(node.right, indent + "  ")

# Función principal que integra todos los pasos
if __name__ == "__main__":
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

    # Paso 5: Calcular nullable, firstpos y lastpos
    compute_nullable(syntax_tree)
    compute_firstpos(syntax_tree)
    compute_lastpos(syntax_tree)

    print("\nÁrbol sintáctico (después de calcular nullable, firstpos y lastpos):")
    print_tree(syntax_tree)

    # Paso 6: Calcular followpos
    followpos = {}
    pos_to_symbol = {}
    initialize_followpos(syntax_tree, followpos, pos_to_symbol)
    compute_followpos(syntax_tree, followpos)

    print("\nTabla de followpos:")
    print("{:<10} {:<10} {:<20}".format("Posición", "Símbolo", "Followpos"))
    for pos in sorted(followpos.keys()):
        print("{:<10} {:<10} {:<20}".format(pos, pos_to_symbol[pos], str(followpos[pos])))

    # Paso 7: Construir el DFA
    states, dfa_transitions, initial_state = build_dfa(syntax_tree, followpos, pos_to_symbol)
    accepting_states = get_accepting_states(states, pos_to_symbol)

    print("\nDFA - Tabla de Transiciones:")
    print("{:<10} {:<10} {:<10}".format("Estado", "Símbolo", "Siguiente Estado"))
    for (state, symbol), dest in dfa_transitions.items():
        print("{:<10} {:<10} {:<10}".format(state, symbol, dest))

    print("\nEstado inicial:", states[initial_state])
    print("Estados de aceptación:", accepting_states)

    # Paso 8: Graficar el DFA
    dfa_dot = visualize_dfa(states, dfa_transitions, initial_state, accepting_states)
    dfa_dot.render('dfa', view=True, format='png')
