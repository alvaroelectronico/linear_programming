---
name: nuevo-ejercicio
description: Crea un ejercicio de programación lineal nuevo en ejercicios/<id>.py (enunciado y solución en LaTeX vía linprog), genera sus .tex y los muestra. Usar cuando el usuario pida crear o añadir un ejercicio, problema o enunciado de examen.
---

# Nuevo ejercicio de programación lineal

Crear `ejercicios/<id>.py` a partir de la descripción del usuario, generar sus
`.tex` y enseñárselos. El resultado son fragmentos LaTeX en español que
`main.tex` importa con `\input{tex/<id>}` y `\input{tex/<id>_sol}`.

## Pasos

1. **Reunir los datos.** Hace falta: un `id` (snake_case, será el nombre del
   archivo y de los .tex), el modelo (objetivo + restricciones, en el formato
   de texto plano que acepta `parse_problem`), el enunciado (narrativa en
   español si es un problema aplicado, o el arranque estándar "Dado el
   siguiente problema..."), y las preguntas del `enumerate`. Si falta algo
   esencial, preguntar; si el usuario da una historia aplicada sin modelo,
   formular el modelo y confirmarlo con él antes de seguir.

2. **Leer las referencias.** `ejercicios/_plantilla.py` (la API disponible y
   la estructura del módulo) y un ejercicio existente (p. ej.
   `ejercicios/dos_fases_a.py`). Para el estilo de redacción, los
   solucionarios reales en `examples/` son la referencia de tono y formato.

3. **Verificar el modelo antes de escribir.** Resolverlo en un python de un
   solo uso (`python -c ...`) y comprobar que el estado (óptimo / no acotado /
   no factible), el método y los valores son los que el ejercicio pretende.
   Elegir el solver según el problema: `simplex` (todo `<=`), `two_phase`
   (hay `=` o `>=`), `dual_simplex` (requiere V<=0 inicial; usar
   `problem.split_equalities()` si hay igualdades).

4. **Escribir `ejercicios/<id>.py`** siguiendo la plantilla: módulo con
   `problem = parse_problem(...)`, `statement()` y `solution()` que devuelven
   `join_blocks(...)` intercalando texto y llamadas a `linprog.latex` /
   `linprog.sensitivity`. Convenciones:
   - Contenido en español; código y comentarios en inglés.
   - Usar los encabezados `latex.HDR_*` y `latex.LBL_OPTIMAL_SOLUTION`, no
     literales nuevos.
   - `frac=True` en tablas y matrices con fracciones (estilo solucionario);
     el texto corrido usa el formato inline por defecto.
   - Para simplex dual, renderizar la tabla con `include_artificials=False` y
     considerar `value_label="s"` si el enunciado reformula min→max.
   - Cerrar la solución con `sol.message` (vacío si hay óptimo; frase en
     español si no acotado / no factible).

5. **Generar y enseñar.** Ejecutar `python -m ejercicios <id>`, mostrar los
   `.tex` generados y preguntar si se añaden las líneas `\input` a
   `main.tex` (no añadirlas sin confirmar). Iterar sobre el contenido con el
   usuario hasta que lo dé por bueno.

## Límites

- No tocar `linprog/` (la librería) ni los goldens de `tests/` para acomodar
  un ejercicio: si el render no encaja, se discute primero.
- No compilar el PDF salvo que el usuario lo pida (`pdflatex main.tex`).
