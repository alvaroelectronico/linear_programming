Quiero desarrollar código que me permita resolver problemas de programación lineal. 

Quiero implementar el método del Simplex, el método de las dos fases y el metodo del Simplex (simplex dual).

* A partir de un problema formulado como texto plano como sigue:
max 3x1 + 4x2
x1+2x2<=50
x1+x2>=10
Y quiero que identifique coeficientes, signos, etc. Puede haber espacios, nombres diferentes de x_1, x_2, etc.

* Quiero que los nombres de variables puedan ser cualquier y que introduzcas variables de holgura cuando hagan falta como: h_1, h_2...

* Quiero leer los elementos del problema: número de variables, número de restricciones, matriz de coeficientes A, matriz de contribuciones unitarias al beneficio c, matriz de disponibilidad de los recursos b, signo de las restricciones.
* Quiero poder recuperar esos elementos en formato .tex
* Quiero poder formular el problema en forma estandar en .tex
* Quiero poder formular el problema en forma canónica en .tex
* En el caso del método de las dos fases, quiero poder recuperar el .tex la formulación de la primera fase y la formulación del problema de las segunda fase. Para ello, sigue la nomenclatura de la documentación que te doy.


Quiero poder recuperar la siguiente información para cualquier base de un problema del problema, tanto en el formato en el que se consuma internamente la información como en .tex para luego componer exámenes y sus soluciones.
* Base, B
* Inversa de la base B^-1
* Contribuciones unitarias al beneficio de las variables básicas, c^B
* Precio sombra de las restricciones \pi^i
* Criterio del simplex, coste reducido, de las variables V^B_j


Cuando resuelvo un problema con un método, quiero poder recuperar:
* Todas las bases por las que transita el método
* La tabla con la información de todas las bases por las que transita

En general, para un conjunto de bases (que puede ser solo una, la primera, una intermedia o la última de uno de los metodos de resolución) quiero poder obtener la o las tablas, con este formato:

\begin{center}
\begin{tabular}{c|c|ccccc|}
 & $z$ & $x_1$ & $x_2$ & $x_3$ & $h_1$ & $h_2$\\ 
 & $0$ & $-3$ & $-4$ & $-5$ & $0$ & $0$ \\ 
\hline
$h_1$ & 50  & $2$ & $3$ & $4$ & $1$ & $0$\\ 
$h_2$ & -20  & $-1$ & $-1$ & $-1$ & $0$ & $1$\\ 
\hline
 & $60$ & $0$ & $-1$ & $-2$ & $0$ & $-3$ \\ 
\hline
$h_1$ & 10  & $0$ & $1$ & $2$ & $1$ & $2$\\ 
$x_1$ & 20  & $1$ & $1$ & $1$ & $0$ & $-1$\\ 
\hline
\end{tabular}

Quiero poder generar texto en .tex para luego elaborar exámenes, documentos, etc. En particular, quiero:
* Recuperar elementos de una variable básica: base, inversa de la base, precios sombra, criterios del simplex. En el caso de los precio sombra o de los criterios del simplex, quiero que haya un argumento para que sea verboso o no, y que en caso de que sí, recupere la fórmula genérica y el detalle de todos los elementos para calcularlo.
* Recuperar el análisis de sensibilidad con el detalle de todos los cálculos para un término b_i y para un término c_j

Quiero que exista un argumento en donde proceda para que se generen los números como \frac{}{} o sin ello (y que por defecto sea sin ello).

Redacta comentarios y código en inglés.

En old_code tienes código que hacía lo que quiero hacer ahora, pero que quiero rehacer de cero, paso a ppaso.

En \examples tienes muchos ejemplos del tipo de exámenes que pongo y cómo quiero generar fragmentos de texto, etc.