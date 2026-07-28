import pygame
import sys
import random

pygame.init()

# Configuración del tablero
ancho, alto = 560, 600
tamaño_celda = 560 // 8
pantalla = None

# Colores
blanco = (255, 255, 255)
negro = (0, 0, 0)
rojo = (220, 50, 50)
verde = (40, 180, 80)
gris = (150, 150, 150)
fondo_menu = (50, 50, 50, 220)

# Variables de estado del juego
mensaje_estado = 'Bienvenido a Chess Game'
color_mensaje = blanco
tiempo_inicio = None
tiempo_mensaje_bienvenida = 3000
tiempo_mensaje_instruccion = 6000
juego_iniciado = False

# Variables para el menú de inicio
menu_state = 'main'
boton_2p_rect = None
boton_vs_ia_rect = None
boton_reiniciar_rect = None

casilla_invalida = None
tiempo_invalido = 0

turno = 'blanco'
player1_color = 'blanco'
player2_color = 'negro'
pieza_seleccionada = None
partida_terminada = False

# Variables para Enroque y Promoción
piezas_movidas = set()
promocion_pendiente = None  
contador_nuevas_piezas = 0  


modo_ia = False
tiempo_espera_ia = 0

def generar_pieza(simbolo_unicode, color):
    superficie = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
    fuente = pygame.font.SysFont('segoeuisymbol', int(tamaño_celda * 1.0))
    texto = fuente.render(simbolo_unicode, True, color)
    rect = texto.get_rect(center=(tamaño_celda // 2, tamaño_celda // 2))
    
    color_borde = negro if color == blanco else blanco if color == negro else (128, 128, 128)

    for dx in [-1, 1]:
        for dy in [-1, 1]:
            texto_borde = fuente.render(simbolo_unicode, True, color_borde)
            superficie.blit(texto_borde, (rect.x + dx, rect.y + dy))

    superficie.blit(texto, rect)
    return superficie

# Símbolos base para la promoción
simbolos_piezas = {
    'reina': {'blanco': '♕', 'negro': '♛'},
    'torre': {'blanco': '♖', 'negro': '♜'},
    'alfil': {'blanco': '♗', 'negro': '♝'},
    'caballo': {'blanco': '♘', 'negro': '♞'}
}

piezas = {
    'rey_blanco': generar_pieza('♔', blanco), 'rey_negro': generar_pieza('♚', negro),
    'reina_blanca': generar_pieza('♕', blanco), 'reina_negra': generar_pieza('♛', negro),
    'torre_blanca': generar_pieza('♖', blanco), 'torre_blanca2': generar_pieza('♖', blanco),
    'torre_negra': generar_pieza('♜', negro), 'torre_negra2': generar_pieza('♜', negro),
    'alfil_blanco': generar_pieza('♗', blanco), 'alfil_blanco2': generar_pieza('♗', blanco),
    'alfil_negro': generar_pieza('♝', negro), 'alfil_negro2': generar_pieza('♝', negro),
    'caballo_blanco': generar_pieza('♘', blanco), 'caballo_blanco2': generar_pieza('♘', blanco),
    'caballo_negro': generar_pieza('♞', negro), 'caballo_negro2': generar_pieza('♞', negro),
    **{f'peon_blanco{i}': generar_pieza('♙', blanco) for i in range(8)},
    **{f'peon_negro{i}': generar_pieza('♟', negro) for i in range(8)}
}

posiciones_iniciales = {
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

posiciones_piezas = posiciones_iniciales.copy()

def obtener_color_pieza(pieza):
    if 'blanco' in pieza or 'blanca' in pieza: return 'blanco'
    return 'negro'

def obtener_pieza_en(col, fil, posiciones=None):
    pos = posiciones_piezas if posiciones is None else posiciones
    for p, (c, f) in pos.items():
        if (c, f) == (col, fil): return p
    return None

def camino_libre(col_origen, fil_origen, col_destino, fil_destino, posiciones=None):
    pos = posiciones_piezas if posiciones is None else posiciones
    dx = 1 if col_destino > col_origen else -1 if col_destino < col_origen else 0
    dy = 1 if fil_destino > fil_origen else -1 if fil_destino < fil_origen else 0
    x, y = col_origen + dx, fil_origen + dy
    while (x, y) != (col_destino, fil_destino):
        if obtener_pieza_en(x, y, pos): return False
        x += dx
        y += dy
    return True

def casilla_atacada(col, fil, color_defensor, posiciones):
    color_enemigo = 'negro' if color_defensor == 'blanco' else 'blanco'
    for pieza, (c, f) in posiciones.items():
        if obtener_color_pieza(pieza) == color_enemigo:
            if movimiento_base_valido(pieza, (col, fil), posiciones, ignorar_enroque=True):
                return True
    return False

def movimiento_base_valido(pieza, nueva_posicion, posiciones=None, ignorar_enroque=False):
    pos = posiciones_piezas if posiciones is None else posiciones
    col, fila = pos[pieza]
    nueva_col, nueva_fila = nueva_posicion
    
    if (col, fila) == (nueva_col, nueva_fila): return False
        
    pieza_destino = obtener_pieza_en(nueva_col, nueva_fila, pos)
    if pieza_destino and obtener_color_pieza(pieza) == obtener_color_pieza(pieza_destino):
        return False

    if 'rey' in pieza:
        if abs(col - nueva_col) <= 1 and abs(fila - nueva_fila) <= 1:
            return True
        if not ignorar_enroque and fila == nueva_fila and abs(col - nueva_col) == 2:
            if pieza in piezas_movidas or en_jaque(obtener_color_pieza(pieza), pos):
                return False
            
            if nueva_col == 6:
                torre = f'torre_{"blanca" if obtener_color_pieza(pieza) == "blanco" else "negra"}2'
                if torre in pos and torre not in piezas_movidas:
                    if camino_libre(col, fila, 7, fila, pos):
                        if not casilla_atacada(5, fila, obtener_color_pieza(pieza), pos):
                            return True
            elif nueva_col == 2:
                if obtener_color_pieza(pieza) == "blanco":
                    torre = 'torre_blanca'
                else:
                    torre = 'torre_negra'
                    
                if torre in pos and torre not in piezas_movidas:
                    if camino_libre(col, fila, 0, fila, pos):
                        if not casilla_atacada(3, fila, obtener_color_pieza(pieza), pos):
                            return True
        return False
        
    elif 'reina' in pieza:
        if col == nueva_col or fila == nueva_fila or abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(col, fila, nueva_col, nueva_fila, pos)
        return False
    elif 'torre' in pieza:
        if col == nueva_col or fila == nueva_fila:
            return camino_libre(col, fila, nueva_col, nueva_fila, pos)
        return False
    elif 'alfil' in pieza:
        if abs(col - nueva_col) == abs(fila - nueva_fila):
            return camino_libre(col, fila, nueva_col, nueva_fila, pos)
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
                    if not obtener_pieza_en(col, fila + direccion, pos):
                        return True
            return False
        if abs(nueva_col - col) == 1 and nueva_fila == fila + direccion:
            return pieza_destino is not None
    return False

def simular_movimiento(pieza, nueva_posicion, posiciones):
    pos_nuevas = posiciones.copy()
    pieza_destino = obtener_pieza_en(nueva_posicion[0], nueva_posicion[1], pos_nuevas)
    if pieza_destino:
        del pos_nuevas[pieza_destino]
    pos_nuevas[pieza] = nueva_posicion
    return pos_nuevas

def en_jaque(color, posiciones=None):
    pos = posiciones_piezas if posiciones is None else posiciones
    nombre_rey = 'rey_blanco' if color == 'blanco' else 'rey_negro'
    if nombre_rey not in pos: return False
    col_rey, fil_rey = pos[nombre_rey]
    return casilla_atacada(col_rey, fil_rey, color, pos)

def movimiento_valido(pieza, nueva_posicion, posiciones=None):
    pos = posiciones_piezas if posiciones is None else posiciones
    if not movimiento_base_valido(pieza, nueva_posicion, pos):
        return False
    posiciones_simuladas = simular_movimiento(pieza, nueva_posicion, pos)
    return not en_jaque(obtener_color_pieza(pieza), posiciones_simuladas)

def hay_movimientos_legales(color):
    for pieza, (col, fil) in list(posiciones_piezas.items()):
        if obtener_color_pieza(pieza) != color: continue
        for nueva_col in range(8):
            for nueva_fila in range(8):
                if movimiento_valido(pieza, (nueva_col, nueva_fila)):
                    return True
    return False

def evaluar_estado(turno_actual):
    if en_jaque(turno_actual):
        if not hay_movimientos_legales(turno_actual): return 'jaque_mate'
        return 'jaque'
    if not hay_movimientos_legales(turno_actual): return 'ahogado'
    return 'jugando'

def obtener_valor_pieza(pieza):
    if 'rey' in pieza: return 100
    if 'reina' in pieza: return 9
    if 'torre' in pieza: return 5
    if 'alfil' in pieza or 'caballo' in pieza: return 3
    if 'peon' in pieza: return 1
    return 0

def movimiento_ia():
    global posiciones_piezas, piezas_movidas, turno, partida_terminada
    color_ia = turno
    
    mejores_movimientos = []
    mejor_puntaje = -1
    
    for pieza, (col, fil) in posiciones_piezas.items():
        if obtener_color_pieza(pieza) != color_ia: continue
        
        for nueva_col in range(8):
            for nueva_fila in range(8):
                if movimiento_valido(pieza, (nueva_col, nueva_fila)):
                    pieza_capturada = obtener_pieza_en(nueva_col, nueva_fila, posiciones_piezas)
                    puntaje = 0
        
                    if pieza_capturada:
                        puntaje = obtener_valor_pieza(pieza_capturada)
                    
                    if puntaje > mejor_puntaje:
                        mejor_puntaje = puntaje
                        mejores_movimientos = [(pieza, (nueva_col, nueva_fila))]
                    elif puntaje == mejor_puntaje:
                        mejores_movimientos.append((pieza, (nueva_col, nueva_fila)))
    
    if not mejores_movimientos:
        return
    

    pieza, (col, fil) = random.choice(mejores_movimientos)
    
    col_origen, fil_origen = posiciones_piezas[pieza]
    pieza_capturada = obtener_pieza_en(col, fil)
    if pieza_capturada: del posiciones_piezas[pieza_capturada]
    
    posiciones_piezas[pieza] = (col, fil)
    piezas_movidas.add(pieza)
    
    if 'rey' in pieza and abs(col - col_origen) == 2:
        color = obtener_color_pieza(pieza)
        if col == 6: 
            nombre_torre = f'torre_{"blanca" if color == "blanco" else "negra"}2'
            posiciones_piezas[nombre_torre] = (5, fil)
            piezas_movidas.add(nombre_torre)
        elif col == 2: 
            nombre_torre = f'torre_{"blanca" if color == "blanco" else "negra"}'
            posiciones_piezas[nombre_torre] = (3, fil)
            piezas_movidas.add(nombre_torre)
            
    if 'peon' in pieza and (fil == 0 or fil == 7):
        color = obtener_color_pieza(pieza)
        if pieza in posiciones_piezas:
            del posiciones_piezas[pieza]
        nueva_pieza_nombre = f'reina_{"blanca" if color=="blanco" else "negra"}_ia_{contador_nuevas_piezas}'
        piezas[nueva_pieza_nombre] = generar_pieza('♕' if color=='blanco' else '♛', blanco if color=='blanco' else negro)
        posiciones_piezas[nueva_pieza_nombre] = (col, fil)
        piezas_movidas.add(nueva_pieza_nombre)
    
    actualizar_turno_y_estado()

def dibujar_tablero():
    for file in range(8):
        for column in range(8):
            color = blanco if (file + column) % 2 == 0 else negro
            pygame.draw.rect(pantalla, color, (column * tamaño_celda, file * tamaño_celda, tamaño_celda, tamaño_celda))

def dibujar_pieza():
    for pieza, (column, file) in posiciones_piezas.items():
        if pieza in piezas:  
            pantalla.blit(piezas[pieza], (column * tamaño_celda, file * tamaño_celda))

def dibujar_movimientos_validos():
    if pieza_seleccionada:
        col_actual, fil_actual = posiciones_piezas[pieza_seleccionada]
        sup_actual = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
        sup_actual.fill((255, 255, 0, 100))
        pantalla.blit(sup_actual, (col_actual * tamaño_celda, fil_actual * tamaño_celda))
        
        sup_mov = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
        pygame.draw.circle(sup_mov, (40, 180, 80, 180), (tamaño_celda // 2, tamaño_celda // 2), 15)
        for fila in range(8):
            for columna in range(8):
                if movimiento_valido(pieza_seleccionada, (columna, fila)):
                    pantalla.blit(sup_mov, (columna * tamaño_celda, fila * tamaño_celda))

def dibujar_casilla_invalida():
    global casilla_invalida
    if casilla_invalida:
        if pygame.time.get_ticks() - tiempo_invalido < 500:
            col, fil = casilla_invalida
            sup_error = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
            sup_error.fill((255, 0, 0, 120))
            pantalla.blit(sup_error, (col * tamaño_celda, fil * tamaño_celda))
        else:
            casilla_invalida = None

def dibujar_mensaje():
    fuente = pygame.font.SysFont('arial', 20, bold=True)
    texto = fuente.render(mensaje_estado, True, color_mensaje)
    rect = texto.get_rect(center=(ancho // 2, 560 + 20))
    pygame.draw.rect(pantalla, negro, (0, 560, ancho, 40))
    pantalla.blit(texto, rect)

def dibujar_boton(texto, y, ancho_btn, alto_btn, color_fondo):
    rect = pygame.Rect((ancho - ancho_btn) // 2, y, ancho_btn, alto_btn)
    pygame.draw.rect(pantalla, color_fondo, rect)
    pygame.draw.rect(pantalla, blanco, rect, 2)
    fuente = pygame.font.SysFont('arial', 18, bold=True)
    txt_surf = fuente.render(texto, True, blanco)
    pantalla.blit(txt_surf, txt_surf.get_rect(center=rect.center))
    return rect

def dibujar_menu_promocion():
    if not promocion_pendiente: return None
    
    sup_oscura = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    sup_oscura.fill((0, 0, 0, 150))
    pantalla.blit(sup_oscura, (0, 0))

    ancho_menu, alto_menu = 300, 100
    x_menu = (ancho - ancho_menu) // 2
    y_menu = (alto - alto_menu) // 2
    pygame.draw.rect(pantalla, (40, 40, 40), (x_menu, y_menu, ancho_menu, alto_menu))
    pygame.draw.rect(pantalla, verde, (x_menu, y_menu, ancho_menu, alto_menu), 3)

    opciones = ['reina', 'torre', 'alfil', 'caballo']
    color = promocion_pendiente['color']
    botones_rects = {}
    
    espacio = ancho_menu // 4
    for i, opcion in enumerate(opciones):
        rect_opcion = pygame.Rect(x_menu + (i * espacio), y_menu, espacio, alto_menu)
        pygame.draw.rect(pantalla, (60, 60, 60), rect_opcion)
        pygame.draw.rect(pantalla, (100, 100, 100), rect_opcion, 1)
        
        simbolo = simbolos_piezas[opcion][color]
        img_pieza = generar_pieza(simbolo, blanco if color == 'blanco' else negro)
        img_rect = img_pieza.get_rect(center=rect_opcion.center)
        pantalla.blit(img_pieza, img_rect)
        
        botones_rects[opcion] = rect_opcion
        
    fuente = pygame.font.SysFont('arial', 16, bold=True)
    txt = fuente.render("Elige tu nueva pieza", True, blanco)
    pantalla.blit(txt, txt.get_rect(center=(ancho//2, y_menu - 20)))

    return botones_rects

def reiniciar_partida():
    global posiciones_piezas, turno, player1_color, player2_color, pieza_seleccionada
    global partida_terminada, mensaje_estado, color_mensaje, tiempo_inicio, casilla_invalida
    global piezas_movidas, promocion_pendiente, contador_nuevas_piezas, modo_ia
    
    posiciones_piezas = posiciones_iniciales.copy()
    piezas_movidas.clear()
    promocion_pendiente = None
    contador_nuevas_piezas = 0
    player1_color = random.choice(['blanco', 'negro'])
    player2_color = 'negro' if player1_color == 'blanco' else 'blanco'
    turno = 'blanco'
    pieza_seleccionada = None
    partida_terminada = False
    casilla_invalida = None
    tiempo_inicio = pygame.time.get_ticks()
    mensaje_estado = 'Recuerda que el blanco empieza primero'
    color_mensaje = blanco

def actualizar_turno_y_estado():
    global turno, mensaje_estado, color_mensaje, partida_terminada
    turno = 'negro' if turno == 'blanco' else 'blanco'

    if turno == player1_color:
        mensaje_estado = 'Turno del Jugador 1'
        color_mensaje = blanco
    else:
        mensaje_estado = 'Turno del Jugador 2' if not modo_ia else 'Pensando...'
        color_mensaje = (200, 200, 200)

    estado = evaluar_estado(turno)
    if estado == 'jaque_mate':
        partida_terminada = True
        if modo_ia and turno == player1_color:
            ganador = 'Jugador'
        elif modo_ia and turno == player2_color:
            ganador = 'IA'
        else:
            ganador = 'Jugador 2' if turno == 'blanco' else 'Jugador 1'
        mensaje_estado = f'Jaque mate - Gana {ganador}'
        color_mensaje = rojo
    elif estado == 'jaque':
        if modo_ia:
            jugador_jaque = 'Jugador' if turno == player1_color else 'IA'
        else:
            jugador_jaque = 'Jugador 1' if turno == player1_color else 'Jugador 2'
        mensaje_estado = f'¡{jugador_jaque} está en jaque!'
        color_mensaje = rojo
    elif estado == 'ahogado':
        partida_terminada = True
        mensaje_estado = 'Empate por Rey ahogado'
        color_mensaje = gris

def main():
    global pantalla, turno, posiciones_piezas, pieza_seleccionada, mensaje_estado, color_mensaje
    global tiempo_inicio, juego_iniciado, player1_color, player2_color
    global casilla_invalida, tiempo_invalido, partida_terminada, menu_state
    global piezas_movidas, promocion_pendiente, contador_nuevas_piezas
    global boton_2p_rect, boton_vs_ia_rect, boton_reiniciar_rect
    global modo_ia, tiempo_espera_ia

    pantalla = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption('Ajedrez con IA')
    reiniciar_partida()
    menu_state = 'main'
    mensaje_estado = 'Bienvenido al Ajedrez'
    botones_promo = {}

    while True:
        tiempo_actual = pygame.time.get_ticks()
        
        if juego_iniciado and not partida_terminada and not promocion_pendiente:
            tiempo_transcurrido = tiempo_actual - tiempo_inicio
            if tiempo_transcurrido > tiempo_mensaje_instruccion and mensaje_estado == 'Recuerda que el blanco empieza primero':
                if turno == player1_color:
                    mensaje_estado = 'Turno del Jugador' if modo_ia else 'Turno del Jugador 1'
                    color_mensaje = blanco
                else:
                    mensaje_estado = 'Turno de la IA' if modo_ia else 'Turno del Jugador 2'
                    color_mensaje = (200, 200, 200)
            elif tiempo_transcurrido > tiempo_mensaje_bienvenida and mensaje_estado.startswith('Bienvenido'):
                mensaje_estado = 'Recuerda que el blanco empieza primero'
        
        if juego_iniciado and modo_ia and not partida_terminada and not promocion_pendiente and turno != player1_color:
            if tiempo_espera_ia == 0:
                tiempo_espera_ia = tiempo_actual + 300
            elif tiempo_actual >= tiempo_espera_ia:
                movimiento_ia()
                tiempo_espera_ia = 0
                pieza_seleccionada = None

        pantalla.fill(blanco)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = evento.pos
                
                if menu_state == 'main':
                    if boton_2p_rect and boton_2p_rect.collidepoint(x, y):
                        modo_ia = False
                        menu_state = 'playing'
                        juego_iniciado = True
                        tiempo_inicio = pygame.time.get_ticks()
                        mensaje_estado = 'Recuerda que el blanco empieza primero'
                        continue
                    elif boton_vs_ia_rect and boton_vs_ia_rect.collidepoint(x, y):
                        modo_ia = True
                        menu_state = 'playing'
                        juego_iniciado = True
                        tiempo_inicio = pygame.time.get_ticks()
                        mensaje_estado = 'Recuerda que el blanco empieza primero'
                        continue
                
                if juego_iniciado and modo_ia and not partida_terminada and turno != player1_color:
                    continue
                
                if partida_terminada and boton_reiniciar_rect and boton_reiniciar_rect.collidepoint(x, y):
                    reiniciar_partida()
                    continue

                if partida_terminada or not juego_iniciado: continue

                if promocion_pendiente:
                    if botones_promo:
                        for tipo_pieza, rect in botones_promo.items():
                            if rect.collidepoint(x, y):
                                color = promocion_pendiente['color']
                                col, fil = promocion_pendiente['posicion']
                                pieza_a_borrar = promocion_pendiente['pieza']
                                
                                if pieza_a_borrar in posiciones_piezas:
                                    del posiciones_piezas[pieza_a_borrar]
                                
                                nueva_pieza_nombre = f'{tipo_pieza}_{"blanca" if color=="blanco" else "negra"}_pro_{contador_nuevas_piezas}'
                                contador_nuevas_piezas += 1
                                
                                simbolo = simbolos_piezas[tipo_pieza][color]
                                color_rgb = blanco if color == 'blanco' else negro
                                piezas[nueva_pieza_nombre] = generar_pieza(simbolo, color_rgb)
                                
                                posiciones_piezas[nueva_pieza_nombre] = (col, fil)
                                piezas_movidas.add(nueva_pieza_nombre)
                                
                                promocion_pendiente = None
                                actualizar_turno_y_estado()
                                break
                    continue 

                columna, fila = x // tamaño_celda, y // tamaño_celda
                
                if pieza_seleccionada:
                    col_origen, fil_origen = posiciones_piezas[pieza_seleccionada]
                    
                    if movimiento_valido(pieza_seleccionada, (columna, fila)):
                        pieza_capturada = obtener_pieza_en(columna, fila)
                        if pieza_capturada:
                            del posiciones_piezas[pieza_capturada]

                        posiciones_piezas[pieza_seleccionada] = (columna, fila)
                        piezas_movidas.add(pieza_seleccionada)

                        if 'rey' in pieza_seleccionada and abs(columna - col_origen) == 2:
                            color_rey = obtener_color_pieza(pieza_seleccionada)
                            if columna == 6: 
                                nombre_torre = f'torre_{"blanca" if color_rey == "blanco" else "negra"}2'
                                posiciones_piezas[nombre_torre] = (5, fila)
                                piezas_movidas.add(nombre_torre)
                            elif columna == 2: 
                                if color_rey == 'blanco':
                                    nombre_torre = 'torre_blanca'
                                else:
                                    nombre_torre = 'torre_negra'
                                posiciones_piezas[nombre_torre] = (3, fila)
                                piezas_movidas.add(nombre_torre)

                        if 'peon' in pieza_seleccionada and (fila == 0 or fila == 7):
                            promocion_pendiente = {
                                'pieza': pieza_seleccionada,
                                'posicion': (columna, fila),
                                'color': obtener_color_pieza(pieza_seleccionada)
                            }
                        else:
                            actualizar_turno_y_estado()

                    else:
                        casilla_invalida = (columna, fila)
                        tiempo_invalido = pygame.time.get_ticks()

                    pieza_seleccionada = None

                else:
                    for pieza, (col, fil) in posiciones_piezas.items():
                        if (col, fil) == (columna, fila):
                            color_pieza = obtener_color_pieza(pieza)
                            if color_pieza == turno:
                                pieza_seleccionada = pieza
                                break

        dibujar_tablero()
        if not promocion_pendiente:
            dibujar_movimientos_validos()
        dibujar_casilla_invalida()
        dibujar_pieza()
        
        if menu_state == 'main':
            boton_2p_rect = dibujar_boton('2 Jugadores', 260, 150, 40, verde)
            boton_vs_ia_rect = dibujar_boton('vs IA', 320, 150, 40, (220, 50, 50))
            
        dibujar_mensaje()
        
        if partida_terminada and juego_iniciado:
            boton_reiniciar_rect = dibujar_boton('Reiniciar', 290, 150, 40, (50, 120, 220))
            
        if promocion_pendiente:
            botones_promo = dibujar_menu_promocion()
            
        pygame.display.flip()

if __name__ == '__main__':
    main()