import graphviz
import re
from collections import defaultdict

class RegexToDFA:
    def __init__(self, regex):
        """
        Inicializa la clase RegexToDFA con una expresión regular dada.
        Convierte la expresión regular a notación postfix (notación polaca inversa).
        """
        if not self.validate_regex(regex):
            raise ValueError("La expresión regular contiene errores de sintaxis.")
        
        self.regex = regex
        self.postfix = self.infix_to_postfix(regex)
    
    def validate_regex(self, regex):
        """
        Valida que la expresión regular tenga una sintaxis correcta.
        - Verifica que los paréntesis estén balanceados.
        - Revisa que no haya operadores mal colocados.
        """
        stack = 0
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789|*().")
        
        for i, char in enumerate(regex):
            if char not in valid_chars:
                return False  # Contiene caracteres inválidos
            if char == '(':
                stack += 1
            elif char == ')':
                stack -= 1
                if stack < 0:
                    return False  # Más paréntesis de cierre que de apertura
            if char in '|*' and (i == 0 or i == len(regex) - 1):
                return False  # Operadores en posición inválida
            if char == '|' and (regex[i-1] in '|(' or regex[i+1] in '|)'):
                return False  # '|' mal colocado
        
        return stack == 0  # Verificar que los paréntesis estén balanceados
    
    def infix_to_postfix(self, regex):
        """
        Convierte una expresión regular en notación infija a notación postfix
        utilizando el algoritmo de Shunting Yard.
        """
        precedence = {'*': 3, '.': 2, '|': 1, '(': 0, ')': 0}
        output = []
        stack = []
        
        regex = self.add_concatenation_operator(regex)  # Agregar operador de concatenación explícito
        
        for char in regex:
            if char.isalnum():  # Si es un operando, agregar a la salida
                output.append(char)
            elif char == '(':
                stack.append(char)  # Agregar '(' a la pila
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())  # Extraer y agregar a la salida hasta encontrar '('
                stack.pop()  # Eliminar '(' de la pila
            else:
                while stack and precedence[char] <= precedence.get(stack[-1], 0):
                    output.append(stack.pop())  # Extraer elementos de mayor precedencia
                stack.append(char)
        
        while stack:
            output.append(stack.pop())  # Extraer los operadores restantes en la pila
        
        return ''.join(output)
    
    def add_concatenation_operator(self, regex):
        """
        Agrega el operador de concatenación explícito ('.') donde sea necesario en la expresión regular.
        """
        output = []
        operators = {'|', '*'}
        
        for i in range(len(regex) - 1):
            output.append(regex[i])
            # Si el carácter actual es un operando, ')', o '*', y el siguiente es un operando o '(', agregar '.'
            if (regex[i].isalnum() or regex[i] == ')' or regex[i] == '*') and \
               (regex[i+1].isalnum() or regex[i+1] == '('):
                output.append('.')
        output.append(regex[-1])
        
        return ''.join(output)

# Ejemplo de uso
if __name__ == "__main__":
    regex = "(a|b)*abb"
    try:
        dfa_generator = RegexToDFA(regex)
        print("Notación Postfix:", dfa_generator.postfix)
    except ValueError as e:
        print("Error:", e)
