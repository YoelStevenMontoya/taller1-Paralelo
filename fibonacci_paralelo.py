# Taller 1 - Algoritmos paralelos
# Infraestructuras Paralelas y Distribuidas (750023C)
#
# Yoel Steven Montoya (2416571)
# Manuela Martinez Moncada (2375458)
#
# Calculo de los primeros N numeros de Fibonacci usando concurrent.futures.
# Se compara la version secuencial contra hilos (ThreadPoolExecutor)
# y procesos (ProcessPoolExecutor).

import os
import time
import concurrent.futures

#ESTO ES DE LA PRUEBAA
N = 20                           # cuantos Fibonacci calculamos: F(0) ... F(N-1)
VALORES_PESADOS = list(range(25, 35))   # segunda prueba, con calculos mas costosos


# Funciones 
# ---------------------------------------------------------------------------

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_iterativo(n):
    #Version iterativa. La uso solo para verificar que los resultados son correctos. No se puede paralelizar
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a



# Version secuencial (referencia para medir el speedup)
# ---------------------------------------------------------------------------

def calcular_secuencial(valores):
    inicio = time.perf_counter()

    resultados = []
    for v in valores:            #aqui si se puede paralelizar
        resultados.append(fibonacci(v))

    fin = time.perf_counter()
    return resultados, fin - inicio


# Version paralela
# ---------------------------------------------------------------------------

def calcular_paralelo(valores, tipo_executor, workers):
    """Calcula fibonacci(v) para cada v en 'valores' usando el executor que le pasen.
    Aqui NO se imprime nada: los workers solo calculan y devuelven el numero.
    """
    inicio = time.perf_counter()

    with tipo_executor(max_workers=workers) as executor:
        # Ciclo 1 (paralelizable): mandar una tarea por cada valor.
        # Las tareas no dependen entre si, asi que pueden correr al tiempo.
        futuros = [executor.submit(fibonacci, v) for v in valores]

        # Ciclo 2: recoger los resultados EN EL ORDEN EN QUE SE ENVIARON.
        # Ojo: no uso as_completed() porque devuelve los futuros en el orden en
        # que TERMINAN, y como F(3) termina mucho antes que F(19), la lista
        # quedaria desordenada (el codigo base tenia justo ese problema).
        resultados = [futuro.result() for futuro in futuros]

    fin = time.perf_counter()
    return resultados, fin - inicio


# Presentacion de resultados (todo el print se hace aqui)
# ---------------------------------------------------------------------------

def formatear_resultados(valores, resultados):
    lineas = []
    for v, r in zip(valores, resultados):
        lineas.append(f"  F({v}) = {r}")
    return "\n".join(lineas)


def fila_tabla(nombre, tiempo, t_seq, workers):
    speedup = t_seq / tiempo
    if nombre == "Secuencial":
        return f"  {nombre:<22}{tiempo:>12.4f}{speedup:>12.2f}{'-':>14}"
    eficiencia = speedup / workers * 100
    return f"  {nombre:<22}{tiempo:>12.4f}{speedup:>12.2f}{eficiencia:>13.1f}%"


def correr_experimento(titulo, valores, workers, mostrar_serie):
    """Corre las 3 versiones con los mismos valores, verifica y arma el reporte."""
    esperados = [fibonacci_iterativo(v) for v in valores]

    res_seq, t_seq = calcular_secuencial(valores)
    res_hilos, t_hilos = calcular_paralelo(valores, concurrent.futures.ThreadPoolExecutor, workers)
    res_procs, t_procs = calcular_paralelo(valores, concurrent.futures.ProcessPoolExecutor, workers)

    todo_ok = (res_seq == esperados and res_hilos == esperados and res_procs == esperados)

    # Armo el reporte completo como un solo string y lo imprimo UNA sola vez.
    # Asi la salida sale ordenada y no se mezcla con nada mas.
    reporte = []
    reporte.append("=" * 60)
    reporte.append(titulo)
    reporte.append("=" * 60)

    if mostrar_serie:
        reporte.append("Serie calculada (version con procesos):")
        reporte.append(formatear_resultados(valores, res_procs))
        reporte.append("")

    reporte.append(f"Verificacion contra la version iterativa: {'OK' if todo_ok else 'ERROR'}")
    reporte.append("")
    reporte.append(f"  {'Version':<22}{'Tiempo (s)':>12}{'Speedup':>12}{'Eficiencia':>14}")
    reporte.append("  " + "-" * 58)
    reporte.append(fila_tabla("Secuencial", t_seq, t_seq, 1))
    reporte.append(fila_tabla(f"Hilos ({workers})", t_hilos, t_seq, workers))
    reporte.append(fila_tabla(f"Procesos ({workers})", t_procs, t_seq, workers))
    reporte.append("")

    print("\n".join(reporte))

# Programa principal
# ---------------------------------------------------------------------------

# El if __name__ == "__main__" es obligatorio con ProcessPoolExecutor,
# sobre todo en Windows, si no cada proceso hijo volveria a ejecutar todo el archivo.
if __name__ == "__main__":
    workers = os.cpu_count() or 4
    print(f"Nucleos disponibles (workers usados): {workers}\n")

    # Prueba 1: lo que pide el enunciado (primeros N numeros).
    # Son calculos muy pequenos, asi que el costo de crear procesos/hilos pesa bastante.
    valores = list(range(N))
    correr_experimento(f"PRUEBA 1: primeros {N} numeros de Fibonacci", valores, workers, mostrar_serie=True)

    # Prueba 2: calculos mas pesados para que se note el efecto de la paralelizacion.
    correr_experimento(
        f"PRUEBA 2: F({VALORES_PESADOS[0]}) hasta F({VALORES_PESADOS[-1]}) (carga pesada)",
        VALORES_PESADOS,
        workers,
        mostrar_serie=True,
    )