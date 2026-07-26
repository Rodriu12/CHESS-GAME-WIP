import pygame
import sys
import random

pygame.init()

# Configuración del tablero
# El ancho y alto del tablero está definido en 560x600 píxeles 
ancho, alto = 560, 600
tamaño_celda = 560 // 8
pantalla = None

# Colores del tablero y de los mensajes que envía el juego.
blanco = (255, 255, 255)
negro = (0, 0, 0)
rojo = (220, 50, 50)
verde = (40, 180, 80)

# Mensajes de estado como el de bienvenida y también de ganador, jaque o jaque mate
mensaje_estado = 'Bienvenido a Chess Game'
color_mensaje = blanco
tiempo_inicio = None
tiempo_mensaje_bienvenida = 3000
tiempo_mensaje_instruccion = 6000
juego_iniciado = False
boton_rect = None

# Control del turno de cada jugador y asignación aleatoria del color blanco.
turno = 'blanco'
player1_color = 'blanco'
player2_color = 'negro'

# Generación de piezas (con bordes para evitar conflictos con los colores de las piezas)
def generar_pieza(simbolo_unicode, color):
    superficie = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
    fuente = pygame.font.SysFont('segoeuisymbol', int(tamaño_celda * 1.0))
    
    texto = fuente.render(simbolo_unicode, True, color)
    rect = texto.get_rect(center=(tamaño_celda // 2, tamaño_celda // 2))
    
    if color == blanco:
        color_borde = negro
    elif color == negro:
        color_borde = blanco
    else:
        color_borde = (128, 128, 128)

    for dx in [-1, 1]:
        for dy in [-1, 1]:
            texto_borde = fuente.render(simbolo_unicode, True, color_borde)
            superficie.blit(texto_borde, (rect.x + dx, rect.y + dy))

    superficie.blit(texto, rect)
    return superficie

# Diccionario de las piezas de ajedrez (usamos Unicode para no depender de imágenes)
# Así se evitan conflictos con los colores y el fondo de la imagen.
# Unicode permite ponerle bordes a las piezas y que no se vuelvan invisibles al ponerlas en las casillas.

piezas = {
    'rey_blanco': generar_pieza('♔', blanco),
    'rey_negro': generar_pieza('♚', negro),
    'reina_blanca': generar_pieza('♕', blanco),
    'reina_negra': generar_pieza('♛', negro),
    'torre_blanca': generar_pieza('♖', blanco),
    'torre_blanca2': generar_pieza('♖', blanco),
    'torre_negra': generar_pieza('♜', negro),
    'torre_negra2': generar_pieza('♜', negro),
    'alfil_blanco': generar_pieza('♗', blanco),
    'alfil_blanco2': generar_pieza('♗', blanco),
    'alfil_negro': generar_pieza('♝', negro),
    'alfil_negro2': generar_pieza('♝', negro),
    'caballo_blanco': generar_pieza('♘', blanco),
    'caballo_blanco2': generar_pieza('♘', blanco),
    'caballo_negro': generar_pieza('♞', negro),
    'caballo_negro2': generar_pieza('♞', negro),
    **{f'peon_blanco{i}': generar_pieza('♙', blanco) for i in range(8)},
    **{f'peon_negro{i}': generar_pieza('♟', negro) for i in range(8)}
}

# Posiciones de las piezas de ajedrez
posiciones_piezas = {
    'rey_blanco': (4,0), 'rey_negro': (4,7),
    'reina_blanca': (3,0), 'reina_negra': (3,7),
    'torre_blanca': (0,0), 'torre_blanca2': (7,0),
    'torre_negra': (0,7), 'torre_negra2': (7,7),
    'alfil_blanco': (2,0), 'alfil_blanco2': (5,0),
    'alfil_negro': (2,7), 'alfil_negro2': (5,7),
    'caballo_blanco': (1,0), 'caballo_blanco2': (6,0),
    'caballo_negro': (1,7), 'caballo_negro2': (6,7),
    **{f'peon_blanco{i}': (i,1) for i in range(8)},
    **{f'peon_negro{i}': (i,6) for i in range(8)},
}

def dibujar_tablero():
    for file in range(8):
        for column in range(8):
            color = blanco if (file + column) % 2 == 0 else negro
            pygame.draw.rect(pantalla, color, (column * tamaño_celda, file * tamaño_celda, tamaño_celda, tamaño_celda))

def dibujar_pieza():
    for pieza, (column, file) in posiciones_piezas.items():
        pantalla.blit(piezas[pieza], (column * tamaño_celda, file * tamaño_celda))


def dibujar_mensaje():
    fuente = pygame.font.SysFont('arial', 20, bold=True)
    texto = fuente.render(mensaje_estado, True, color_mensaje)
    rect = texto.get_rect(center=(ancho // 2, 560 + 20))
    
    pygame.draw.rect(pantalla, negro, (0, 560, ancho, 40))
    pantalla.blit(texto, rect)


def dibujar_boton_empezar():
    global boton_rect
    ancho_boton = 150
    alto_boton = 40
    x_boton = (ancho - ancho_boton) // 2
    y_boton = 280
    
    boton_rect = pygame.Rect(x_boton, y_boton, ancho_boton, alto_boton)
    pygame.draw.rect(pantalla, verde, boton_rect)
    pygame.draw.rect(pantalla, (0, 0, 0), boton_rect, 2)
    
    fuente = pygame.font.SysFont('arial', 18, bold=True)
    texto = fuente.render('Empezar', True, (255, 255, 255))
    rect_texto = texto.get_rect(center=boton_rect.center)
    pantalla.blit(texto, rect_texto)

# Lógica de como funciona el juego

# 0. Función que verifica cuál pieza es aliada para evitar que la ataque y coma.
def obtener_color_pieza(pieza):
    if 'blanco' in pieza or 'blanca' in pieza:
        return 'blanco'
    if 'negro' in pieza or 'negra' in pieza:
        return 'negro'
    return 'negro'

# 1. Función para verificar dónde está cada pieza y mostrarla en la interfaz del tablero
def obtener_pieza_en(col, fil, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    for pieza, (c, f) in posiciones_a_usar.items():
        if (c, f) == (col, fil):
            return pieza
    return None

# 2. Verifica si el camino al que quiera mover la pieza está libre u ocupado
def camino_libre(pieza, nueva_posicion, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    col, fila = posiciones_a_usar[pieza]
    nueva_col, nueva_fila = nueva_posicion
    
    dx = 1 if nueva_col > col else -1 if nueva_col < col else 0
    dy = 1 if nueva_fila > fila else -1 if nueva_fila < fila else 0
    
    x, y = col + dx, fila + dy
    while (x, y) != (nueva_col, nueva_fila):
        if obtener_pieza_en(x, y, posiciones_a_usar):
            return False
        x += dx
        y += dy
    return True

def movimiento_base_valido(pieza, nueva_posicion, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    col, fila = posiciones_a_usar[pieza]
    nueva_col, nueva_fila = nueva_posicion
    
    if (col, fila) == (nueva_col, nueva_fila):
        return False
        
    pieza_destino = obtener_pieza_en(nueva_col, nueva_fila, posiciones_a_usar)
    if pieza_destino:
        color_origen = obtener_color_pieza(pieza)
        color_destino = obtener_color_pieza(pieza_destino)
        
        if color_origen == color_destino:
            return False

    if 'rey' in pieza:
        return abs(col - nueva_col) <= 1 and abs(fila - nueva_fila) <= 1
    
    elif 'reina' in pieza:
        if col == nueva_col or fila == nueva_fila or abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
        
    elif 'torre' in pieza:
        if col == nueva_col or fila == nueva_fila:
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
        
    elif 'alfil' in pieza:
        if abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
        
    elif 'caballo' in pieza:
        return (abs(col - nueva_col), abs(fila - nueva_fila)) in [(1,2), (2,1)]
        
    elif 'peon' in pieza:
        direccion = 1 if 'blanco' in pieza else -1
        
        if nueva_col == col:
            if nueva_fila == fila + direccion and not pieza_destino:
                return True
            if (fila == 1 and 'blanco' in pieza) or (fila == 6 and 'negro' in pieza):
                if nueva_fila == fila + 2 * direccion and not pieza_destino:
                    if not obtener_pieza_en(col, fila + direccion, posiciones_a_usar):
                        return True
            return False
            
        if abs(nueva_col - col) == 1 and nueva_fila == fila + direccion:
            return pieza_destino is not None
        return False

    return False


def movimiento_valido(pieza, nueva_posicion, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    if not movimiento_base_valido(pieza, nueva_posicion, posiciones_a_usar):
        return False

    color = obtener_color_pieza(pieza)
    posiciones_simuladas = simular_movimiento(pieza, nueva_posicion, posiciones_a_usar)
    return not en_jaque(color, posiciones_simuladas)


def pieza_ataca_cuadro(pieza, nueva_posicion, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    col, fila = posiciones_a_usar[pieza]
    nueva_col, nueva_fila = nueva_posicion

    if (col, fila) == (nueva_col, nueva_fila):
        return False

    pieza_destino = obtener_pieza_en(nueva_col, nueva_fila, posiciones_a_usar)
    if pieza_destino:
        if obtener_color_pieza(pieza) == obtener_color_pieza(pieza_destino):
            return False

    if 'rey' in pieza:
        return abs(col - nueva_col) <= 1 and abs(fila - nueva_fila) <= 1
    elif 'reina' in pieza:
        if col == nueva_col or fila == nueva_fila or abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
    elif 'torre' in pieza:
        if col == nueva_col or fila == nueva_fila:
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
    elif 'alfil' in pieza:
        if abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(pieza, nueva_posicion, posiciones_a_usar)
        return False
    elif 'caballo' in pieza:
        return (abs(col - nueva_col), abs(fila - nueva_fila)) in [(1, 2), (2, 1)]
    elif 'peon' in pieza:
        direccion = 1 if 'blanco' in pieza else -1
        return abs(nueva_col - col) == 1 and nueva_fila == fila + direccion
    return False

# 4. Comprueba cuál bando está en jaque
def obtener_rey(color, posiciones=None):
    nombre_rey = 'rey_blanco' if color == 'blanco' else 'rey_negro'
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    return nombre_rey, posiciones_a_usar[nombre_rey]


def en_jaque(color, posiciones=None):
    rey, (col_rey, fil_rey) = obtener_rey(color, posiciones)
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones

    for pieza, (col, fil) in posiciones_a_usar.items():
        if pieza == rey:
            continue
        if obtener_color_pieza(pieza) == color:
            continue
        if pieza_ataca_cuadro(pieza, (col_rey, fil_rey), posiciones_a_usar):
            return True
    return False

# 5. Comprueba si el rey está en jaque o jaque mate
def simular_movimiento(pieza, nueva_posicion, posiciones):
    posiciones_nuevas = posiciones.copy()
    pieza_destino = obtener_pieza_en(nueva_posicion[0], nueva_posicion[1], posiciones_nuevas)
    if pieza_destino:
        del posiciones_nuevas[pieza_destino]
    posiciones_nuevas[pieza] = nueva_posicion
    return posiciones_nuevas

# 6. Saber si un bando tiene algún movimiento válido dentro del juego
def hay_movimientos_legales(color, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones

    for pieza, (col, fil) in list(posiciones_a_usar.items()):
        if obtener_color_pieza(pieza) != color:
            continue

        for nueva_col in range(8):
            for nueva_fila in range(8):
                if not movimiento_valido(pieza, (nueva_col, nueva_fila), posiciones_a_usar):
                    continue

                posiciones_simuladas = simular_movimiento(pieza, (nueva_col, nueva_fila), posiciones_a_usar)
                if not en_jaque(color, posiciones_simuladas):
                    return True

    return False

# 7. Evaluar si la partida está en jaque o jaque mate dependiendo del bando (negro o blanco)
def evaluar_estado(turno_actual):
    if en_jaque(turno_actual):
        if not hay_movimientos_legales(turno_actual):
            return 'jaque_mate'
        return 'jaque'
    return 'jugando'

# Bucle principal que mantiene el juego abierto y llamada a las funciones del juego
# Este llama al botón de empezar el juego para que al apretarlo libere el tablero para hacer los movimientos
def main():
    global pantalla, turno, posiciones_piezas, pieza_seleccionada, mensaje_estado, color_mensaje, tiempo_inicio, juego_iniciado, player1_color, player2_color

    pantalla = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption('Ajedrez')
    player1_color = random.choice(['blanco', 'negro'])
    player2_color = 'negro' if player1_color == 'blanco' else 'blanco'
    turno = 'blanco'
    pieza_seleccionada = None
    partida_terminada = False
    tiempo_inicio = pygame.time.get_ticks()
    mensaje_estado = 'Bienvenido a Chess Game'
    color_mensaje = blanco

    while True:
        tiempo_actual = pygame.time.get_ticks()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        
        if tiempo_transcurrido > tiempo_mensaje_instruccion and mensaje_estado == 'Recuerda que el blanco empieza primero':
            if turno == player1_color:
                mensaje_estado = 'Turno del Jugador 1'
            else:
                mensaje_estado = 'Turno del Jugador 2'
            color_mensaje = blanco
        elif tiempo_transcurrido > tiempo_mensaje_bienvenida and mensaje_estado.startswith('Bienvenido'):
            mensaje_estado = 'Recuerda que el blanco empieza primero'
            color_mensaje = blanco
        
        pantalla.fill(blanco)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = evento.pos
                
                if not juego_iniciado and boton_rect and boton_rect.collidepoint(x, y):
                    juego_iniciado = True
                    tiempo_inicio = pygame.time.get_ticks()
                    mensaje_estado = 'Recuerda que el blanco empieza primero'
                    continue
                
                if partida_terminada or not juego_iniciado:
                    continue

                columna, fila = x // tamaño_celda, y // tamaño_celda
                
                if pieza_seleccionada:
                    if movimiento_valido(pieza_seleccionada, (columna, fila)):
                        pieza_capturada = obtener_pieza_en(columna, fila)
                        if pieza_capturada:
                            del posiciones_piezas[pieza_capturada]

                        posiciones_piezas[pieza_seleccionada] = (columna, fila)
                        turno = 'negro' if turno == 'blanco' else 'blanco'

                        if turno == player1_color:
                            mensaje_estado = 'Turno del Jugador 1'
                            color_mensaje = blanco
                        else:
                            mensaje_estado = 'Turno del Jugador 2'
                            color_mensaje = (200, 200, 200)

                        estado = evaluar_estado(turno)
                        if estado == 'jaque_mate':
                            partida_terminada = True
                            if turno == 'blanco':
                                mensaje_estado = f'Jaque mate - Gana Jugador 2'
                            else:
                                mensaje_estado = f'Jaque mate - Gana Jugador 1'
                            color_mensaje = rojo
                            print(f"Jaque mate para {turno}.")
                        elif estado == 'jaque':
                            if turno == player1_color:
                                mensaje_estado = f'¡Jugador 1 está en jaque!'
                            else:
                                mensaje_estado = f'¡Jugador 2 está en jaque!'
                            color_mensaje = rojo
                            print(f"¡{turno} está en jaque!")
                    else:
                        mensaje_estado = 'Movimiento inválido. Revisa el camino o si tu rey queda en jaque.'
                        color_mensaje = rojo

                    pieza_seleccionada = None

                else:
                    for pieza, (col, fil) in posiciones_piezas.items():
                        if (col, fil) == (columna, fila):
                            if obtener_color_pieza(pieza) == turno:
                                pieza_seleccionada = pieza
                                break

        dibujar_tablero()
        dibujar_pieza()
        if not juego_iniciado:
            dibujar_boton_empezar()
        dibujar_mensaje()
        pygame.display.flip()


if __name__ == '__main__':
    main()