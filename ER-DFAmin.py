from graphviz import Digraph

# ---------------------------
# Parte 1: Procesamiento de la expresión regular y árbol sintáctico
# ---------------------------

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

# Inserta explícitamente el operador de concatenación ('.')
def add_concat_operator(regex):
    result = ""
    for i in range(len(regex)):
        c = regex[i]
        result += c
        if i + 1 < len(regex):
            next_c = regex[i+1]
            # Se inserta concatenación si c no es '|' ni '(' y next_c no es '|' ni ')' ni '*'
            if (c not in {'|', '('} and next_c not in {'|', ')', '*'}):
                result += '.'
    return result

# Conversión de expresión infijo a postfijo (Shunting-yard)
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
            stack.pop()  # Remover '('
        else:
            while (stack and stack[-1] != '(' and
                   precedence.get(stack[-1], 0) >= precedence.get(c, 0)):
                output.append(stack.pop())
            stack.append(c)
    while stack:
        output.append(stack.pop())
    return "".join(output)

# Construcción del árbol sintáctico a partir de la notación postfija
def build_syntax_tree(postfix):
    stack = []
    position_counter = 1  # Para etiquetar las hojas
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

# Cálculo de nullable, firstpos y lastpos

def compute_nullable(node):
    if node is None:
        return False
    if node.left is None and node.right is None:
        node.nullable = True if node.value == 'ε' else False
        return node.nullable
    if node.value == '|':
        node.nullable = compute_nullable(node.left) or compute_nullable(node.right)
        return node.nullable
    if node.value == '.':
        node.nullable = compute_nullable(node.left) and compute_nullable(node.right)
        return node.nullable
    if node.value == '*':
        compute_nullable(node.left)
        node.nullable = True
        return node.nullable
    return False

def compute_firstpos(node):
    if node is None:
        return set()
    if node.left is None and node.right is None:
        node.firstpos = set() if node.value == 'ε' else {node.position}
        return node.firstpos
    if node.value == '|':
        node.firstpos = compute_firstpos(node.left).union(compute_firstpos(node.right))
        return node.firstpos
    if node.value == '.':
        left_first = compute_firstpos(node.left)
        right_first = compute_firstpos(node.right)
        node.firstpos = left_first.union(right_first) if node.left.nullable else left_first
        return node.firstpos
    if node.value == '*':
        node.firstpos = compute_firstpos(node.left)
        return node.firstpos
    return set()

def compute_lastpos(node):
    if node is None:
        return set()
    if node.left is None and node.right is None:
        node.lastpos = set() if node.value == 'ε' else {node.position}
        return node.lastpos
    if node.value == '|':
        node.lastpos = compute_lastpos(node.left).union(compute_lastpos(node.right))
        return node.lastpos
    if node.value == '.':
        left_last = compute_lastpos(node.left)
        right_last = compute_lastpos(node.right)
        node.lastpos = left_last.union(right_last) if node.right.nullable else right_last
        return node.lastpos
    if node.value == '*':
        node.lastpos = compute_lastpos(node.left)
        return node.lastpos
    return set()

# Visualización del árbol sintáctico usando Graphviz
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
        # Colorear: hojas en verde, ramas en café
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

# Función para imprimir el árbol (para depuración)
def print_tree(node, indent=""):
    if node is not None:
        print(indent + f"({node.value}, pos={node.position}, nullable={node.nullable}, "
              f"firstpos={node.firstpos}, lastpos={node.lastpos})")
        if node.left or node.right:
            print_tree(node.left, indent + "  ")
            print_tree(node.right, indent + "  ")

# ---------------------------
# Parte 2: Cálculo de followpos y construcción del DFA
# ---------------------------

# Inicializa la tabla de followpos y mapea posición a símbolo
def initialize_followpos(node, followpos, pos_to_symbol):
    if node is None:
        return
    if node.left is None and node.right is None:
        followpos[node.position] = set()
        pos_to_symbol[node.position] = node.value
    else:
        initialize_followpos(node.left, followpos, pos_to_symbol)
        initialize_followpos(node.right, followpos, pos_to_symbol)

# Calcula followpos según reglas:
# - En c1.c2, para cada posición en lastpos(c1), se añade firstpos(c2)
# - En c*, para cada posición en lastpos(c), se añade firstpos(c)
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

# Construcción del DFA a partir del árbol y tabla followpos
def build_dfa(syntax_tree, followpos, pos_to_symbol):
    initial_state = frozenset(syntax_tree.firstpos)
    states = {initial_state: "S0"}  # Mapeo: conjunto de posiciones -> nombre de estado
    unmarked_states = [initial_state]
    dfa_transitions = {}  # (estado, símbolo) -> estado destino
    state_counter = 1

    # Alfabeto: símbolos de las hojas, excluyendo 'ε' y '#' (este último marca fin)
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

# Obtiene los estados de aceptación: aquellos que contienen la posición del símbolo '#'
def get_accepting_states(states, pos_to_symbol):
    accepting = []
    for state_set, name in states.items():
        for p in state_set:
            if pos_to_symbol[p] == '#':
                accepting.append(name)
                break
    return accepting

# Visualiza el DFA usando Graphviz
def visualize_dfa(dfa_states, dfa_transitions, initial_state, accepting_states, filename):
    dot = Digraph(comment='DFA')

    # Crear nodos (se espera que dfa_states sea un conjunto de nombres de estado)
    for state in dfa_states:
        if state in accepting_states:
            dot.node(state, state, shape='doublecircle', style='filled', fillcolor='lightblue')
        else:
            dot.node(state, state, shape='circle', style='filled', fillcolor='white')
    # Nodo inicial invisible y flecha hacia el estado inicial
    dot.node("", "", shape="none")
    dot.edge("", initial_state)

    # Agregar transiciones
    for (src, symbol), dest in dfa_transitions.items():
        dot.edge(src, dest, label=symbol)

    dot.render(filename, view=True, format='png')
    return dot

# ---------------------------
# Parte 3: Minimización del DFA (método de particiones)
# ---------------------------
def minimize_dfa(dfa_transitions, states, initial_state, accepting_states):
    # Q: conjunto de todos los nombres de estado
    Q = set(states.values())
    # Partición inicial: estados de aceptación y no aceptación
    P = []
    if accepting_states:
        P.append(set(accepting_states))
    non_accepting = Q - set(accepting_states)
    if non_accepting:
        P.append(non_accepting)

    # Alfabeto: extraído de la tabla de transiciones
    alphabet = {symbol for (state, symbol) in dfa_transitions.keys()}

    changed = True
    while changed:
        changed = False
        new_P = []
        # Mapeo: estado -> índice del bloque en P
        state_to_block = {}
        for i, block in enumerate(P):
            for state in block:
                state_to_block[state] = i
        # Refinar cada bloque de la partición
        for block in P:
            groups = {}
            for state in block:
                # Se obtiene el comportamiento para cada símbolo: a qué bloque se transita
                behavior = tuple(state_to_block.get(dfa_transitions.get((state, a))) for a in sorted(alphabet))
                groups.setdefault(behavior, set()).add(state)
            if len(groups) == 1:
                new_P.append(block)
            else:
                new_P.extend(groups.values())
                changed = True
        P = new_P

    # Asignar nuevos nombres a cada bloque
    block_to_name = {}
    for i, block in enumerate(P):
        block_to_name[frozenset(block)] = f"M{i}"

    # Mapeo: cada estado antiguo a su nuevo nombre
    state_to_new = {}
    for block in P:
        new_name = block_to_name[frozenset(block)]
        for state in block:
            state_to_new[state] = new_name

    # Reconstruir la tabla de transiciones del DFA minimizado
    new_dfa_transitions = {}
    for (state, symbol), target in dfa_transitions.items():
        new_src = state_to_new[state]
        new_target = state_to_new[target]
        new_dfa_transitions[(new_src, symbol)] = new_target

    # Nuevo estado inicial: el bloque que contiene el estado inicial original
    new_initial_state = state_to_new[states[initial_state]]
    # Estados de aceptación minimizados: bloques que contengan algún estado de aceptación
    new_accepting_states = set()
    for block in P:
        if block.intersection(set(accepting_states)):
            new_accepting_states.add(block_to_name[frozenset(block)])

    new_states = set(block_to_name.values())
    return new_states, new_dfa_transitions, new_initial_state, new_accepting_states

def process_string(dfa_transitions, initial_state, accepting_states, test_string):
    """ Procesa una cadena en el AFD generado y determina si es aceptada. """
    current_state = initial_state
    for char in test_string:
        if (current_state, char) in dfa_transitions:
            current_state = dfa_transitions[(current_state, char)]
        else:
            return False  # Transición no válida, la cadena no es aceptada
    return current_state in accepting_states

# ---------------------------
# Función principal: integra todos los pasos
# ---------------------------
if __name__ == "__main__":
    # Entrada de la expresión regular
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
    print("\nÁrbol sintáctico (antes de calcular funciones):")
    print_tree(syntax_tree)

    # Paso 5: Calcular nullable, firstpos y lastpos
    compute_nullable(syntax_tree)
    compute_firstpos(syntax_tree)
    compute_lastpos(syntax_tree)
    print("\nÁrbol sintáctico (después de calcular nullable, firstpos y lastpos):")
    print_tree(syntax_tree)

    # Visualizar el árbol sintáctico
    tree_dot = visualize_tree(syntax_tree)
    tree_dot.render("syntax_tree", view=True, format="png")

    # Paso 6: Calcular followpos
    followpos = {}
    pos_to_symbol = {}
    initialize_followpos(syntax_tree, followpos, pos_to_symbol)
    compute_followpos(syntax_tree, followpos)
    print("\nTabla de followpos:")
    print("{:<10} {:<10} {:<20}".format("Posición", "Símbolo", "Followpos"))
    for pos in sorted(followpos.keys()):
        print("{:<10} {:<10} {:<20}".format(pos, pos_to_symbol[pos], str(followpos[pos])))

    # Paso 7: Construir el DFA a partir del árbol sintáctico
    states, dfa_transitions, initial_state = build_dfa(syntax_tree, followpos, pos_to_symbol)
    accepting_states = get_accepting_states(states, pos_to_symbol)

    print("\nDFA - Tabla de Transiciones:")
    print("{:<10} {:<10} {:<10}".format("Estado", "Símbolo", "Siguiente Estado"))
    for (state, symbol), dest in dfa_transitions.items():
        print("{:<10} {:<10} {:<10}".format(state, symbol, dest))
    print("\nEstado inicial:", states[initial_state])
    print("Estados de aceptación:", accepting_states)

    # Dibujo del DFA normal (no minimizado)
    visualize_dfa(set(states.values()), dfa_transitions, states[initial_state], accepting_states, "dfa_normal")

    # Paso 8: Minimizar el DFA
    new_states, new_dfa_transitions, new_initial_state, new_accepting_states = minimize_dfa(
        dfa_transitions, states, initial_state, accepting_states)

    print("\nDFA Minimizado - Tabla de Transiciones:")
    print("{:<10} {:<10} {:<10}".format("Estado", "Símbolo", "Siguiente Estado"))
    for (state, symbol), dest in new_dfa_transitions.items():
        print("{:<10} {:<10} {:<10}".format(state, symbol, dest))
    print("\nEstado inicial (minimizado):", new_initial_state)
    print("Estados de aceptación (minimizado):", new_accepting_states)

    # Dibujo del DFA minimizado
    visualize_dfa(new_states, new_dfa_transitions, new_initial_state, new_accepting_states, "dfa_minimizado")

    # Solicitar cadena de entrada al usuario
    test_string = input("Ingresa la cadena a evaluar: ")

    # Evaluar la cadena con el AFD generado
    accepted = process_string(new_dfa_transitions, new_initial_state, new_accepting_states, test_string)

    # Mostrar el resultado de la evaluación
    print(f"La cadena '{test_string}' es {'ACEPTADA' if accepted else 'RECHAZADA'} por el AFD.")
