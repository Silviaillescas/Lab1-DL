# Lab1-DL
Michelle Mejía 22596 - Silvia Illescas 22376

# Generación y Minimización de un AFD desde una Expresión Regular

Este proyecto implementa la construcción directa de un **Autómata Finito Determinista (AFD)** a partir de una **expresión regular**, su **minimización** y la **simulación de cadenas de entrada** para verificar su aceptación.

## Características del Proyecto

- Convierte una **expresión regular** en **notación postfija** (usando el algoritmo Shunting Yard).
- Construye el **árbol sintáctico** correspondiente a la expresión regular.
- Calcula **nullable, firstpos, lastpos y followpos** para la construcción del AFD.
- Construye el **AFD** a partir del árbol sintáctico.
- **Minimiza el AFD** usando el **método de particiones**.
- **Simula la ejecución** del AFD para verificar si una cadena es aceptada o no.
- **Genera representaciones visuales** del árbol sintáctico, el AFD y el AFD minimizado con **Graphviz**.

## Requisitos

Para ejecutar el proyecto, necesitas tener instalado:

- **Python 3.x**
- **Graphviz** (para la generación de los diagramas)
- Librería **graphviz** de Python (instalable con `pip`)

Instala las dependencias con:

```sh
pip install graphviz
```

## Uso del Programa

1. Ejecuta el script:

```sh
python nombre_del_script.py
```

2. Ingresa la expresión regular cuando se solicite.

3. Se generará la conversión a notación postfija, el árbol sintáctico y el AFD.

4. Se visualizarán las tablas de transiciones y el AFD minimizado.

5. Luego, podrás ingresar una cadena para verificar si es aceptada o rechazada por el AFD.

### Ejemplo de Uso

```
Ingresa la expresión regular: (a|b)*abb
Expresión aumentada: (a|b)*abb#
Expresión en notación postfija: ab|*a.b.b.#.

DFA - Tabla de Transiciones:
Estado    Símbolo  Siguiente Estado
S0        a        S1
S0        b        S0
...

DFA Minimizado:
Estado inicial (minimizado): M2
Estados de aceptación (minimizado): {'M0'}

Ingresa la cadena a evaluar: abb
La cadena 'abb' es ACEPTADA por el AFD.
```

## Archivos Generados

- **syntax_tree.png**: Representación visual del árbol sintáctico.
- **dfa_normal.png**: Representación del AFD antes de la minimización.
- **dfa_minimizado.png**: Representación del AFD minimizado.

## Consideraciones

- El programa asume que la expresión regular ingresada está correctamente balanceada y es válida.
- Para la generación visual de los autómatas, **Graphviz** debe estar correctamente instalado en el sistema.


## Referencias y Créditos

El código fue desarrollado con apoyo de diversas fuentes, incluyendo documentación académica y herramientas de asistencia basadas en inteligencia artificial.

En particular, se utilizó ChatGPT de OpenAI para generar, estructurar y optimizar el código basado en los requerimientos específicos del laboratorio.
