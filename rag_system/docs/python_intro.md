# Introducción a Python

## ¿Qué es Python?

Python es un lenguaje de programación interpretado, multiparadigma y multiplataforma. Fue creado por Guido van Rossum y publicado por primera vez en 1991.

### Características principales

- **Interpretado**: No necesita compilación, se ejecuta directamente
- **Multiparadigma**: Soporta programación orientada a objetos, funcional y procedural
- **Tipado dinámico**: Las variables no tienen tipo fijo
- **Gestión automática de memoria**: Incluye recolector de basura
- **Sintaxis clara**: Usa indentación para delimitar bloques de código

## Historia

Python fue desarrollado a finales de los años 80 como sucesor del lenguaje ABC. El nombre proviene del grupo de comedia británico Monty Python.

### Versiones importantes

1. **Python 1.0** (1994): Primera versión oficial
2. **Python 2.0** (2000): Comprensión de listas, garbage collector
3. **Python 3.0** (2008): Versión incompatible con Python 2
4. **Python 3.12** (2023): Última versión estable

## Sintaxis básica

### Variables

```python
nombre = "Juan"
edad = 25
altura = 1.75
es_estudiante = True
```

### Estructuras de control

#### Condicionales

```python
if edad >= 18:
    print("Mayor de edad")
else:
    print("Menor de edad")
```

#### Bucles

```python
# Bucle for
for i in range(5):
    print(i)

# Bucle while
contador = 0
while contador < 5:
    print(contador)
    contador += 1
```

### Funciones

```python
def saludar(nombre):
    return f"Hola, {nombre}!"

mensaje = saludar("María")
print(mensaje)  # Hola, María!
```

## Tipos de datos comunes

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| int | Números enteros | 42 |
| float | Números decimales | 3.14 |
| str | Cadenas de texto | "Hola" |
| list | Listas ordenadas | [1, 2, 3] |
| dict | Diccionarios | {"clave": "valor"} |
| bool | Booleanos | True, False |

## Librerías estándar

Python incluye una amplia biblioteca estándar:

- **os**: Operaciones del sistema operativo
- **sys**: Parámetros y funciones del sistema
- **math**: Funciones matemáticas
- **datetime**: Manejo de fechas y horas
- **json**: Procesamiento de JSON
- **re**: Expresiones regulares

## Frameworks populares

### Desarrollo Web

- **Django**: Framework completo y robusto
- **Flask**: Microframework ligero
- **FastAPI**: Moderno y rápido para APIs

### Ciencia de Datos

- **NumPy**: Computación numérica
- **Pandas**: Análisis de datos
- **Matplotlib**: Visualización
- **Scikit-learn**: Machine Learning

## Mejores prácticas

1. **Seguir PEP 8**: Guía de estilo oficial
2. **Usar type hints**: Mejora legibilidad y detección de errores
3. **Escribir tests**: Usar unittest o pytest
4. **Documentar código**: Docstrings claros
5. **Manejar excepciones**: Try/except apropiado

## Ejemplo completo

```python
from typing import List, Dict

class Persona:
    def __init__(self, nombre: str, edad: int):
        self.nombre = nombre
        self.edad = edad
    
    def presentarse(self) -> str:
        return f"Soy {self.nombre} y tengo {self.edad} años"

def filtrar_mayores(personas: List[Persona], edad_minima: int = 18) -> List[Persona]:
    """Filtra personas mayores de una edad dada."""
    return [p for p in personas if p.edad >= edad_minima]

# Uso
personas = [
    Persona("Ana", 25),
    Persona("Luis", 16),
    Persona("Carlos", 30)
]

mayores = filtrar_mayores(personas)
for persona in mayores:
    print(persona.presentarse())
```

## Recursos de aprendizaje

- **Documentación oficial**: docs.python.org
- **Python Tutor**: pythontutor.com (visualizar ejecución)
- **Real Python**: tutoriales y artículos
- **Stack Overflow**: comunidad de ayuda

## Conclusión

Python es uno de los lenguajes más populares debido a su simplicidad, versatilidad y gran ecosistema de librerías. Es ideal tanto para principiantes como para profesionales en áreas como desarrollo web, ciencia de datos, automatización e inteligencia artificial.
