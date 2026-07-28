import pygame
import sys
import socket
import threading
import queue
import random

pygame.init()

# Configuración del tablero
ancho, alto = 560, 600
tamaño_celda = 560 // 8

# Colores
blanco = (255, 255, 255)
negro = (0, 0, 0)
rojo = (220, 50, 50)
verde = (40, 180, 80)
azul = (100, 200, 255)
gris_claro = (240, 240, 240)

# Mensajes de estado como el de bienvenida y también de ganador, jaque o jaque mate
mensaje_estado = 'Bienvenido a Chess Game'
color_mensaje = blanco
juego_iniciado = False

# Variables para mostrar la casilla inválida
casilla_invalida = None
tiempo_invalido = 0

# Variables para control de enroque y promoción
piezas_movidas = set()
promocion_pendiente = None
contador_nuevas_piezas = 0

# Lógica de la red al hostear la partida y a la conexión entrante del otro jugador
HOST = 'localhost'
PORT = 5555
sock = None
net_queue = queue.Queue()
net_thread = None
modo_online = False
mi_color = 'blanco'
player1_color = 'blanco'
player2_color = 'negro'
host_ip_input = "localhost"
ip_input_activo = False
net_status = 'none'

# Control de turno (para el modo LAN)
turno = 'blanco'
partida_terminada = False

# Generación de piezas
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

# Símbolos para renderizar en promoción
simbolos_piezas = {
    'reina': {'blanco': '♕', 'negro': '♛'},
    'torre': {'blanco': '♖', 'negro': '♜'},
    'alfil': {'blanco': '♗', 'negro': '♝'},
    'caballo': {'blanco': '♘', 'negro': '♞'}
}

# Diccionario de las piezas de ajedrez
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

def hilo_esperar_host(ip_escucha):
    global sock, net_status, mensaje_estado
    try:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((ip_escucha, PORT))
        server_sock.listen(1)
        sock, addr = server_sock.accept()
        net_status = 'connected'
        mensaje_estado = "¡Conexión establecida! Empiezas tú (Blancas)."
        server_sock.close()
    except Exception as e:
        net_status = 'error'
        mensaje_estado = f"Error al esperar: {str(e)}"

def hilo_conectar_cliente(ip_destino):
    global sock, net_status, mensaje_estado
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip_destino, PORT))
        sock.settimeout(None)
        net_status = 'connected'
        mensaje_estado = "¡Conectado al servidor!"
    except Exception as e:
        net_status = 'error'
        mensaje_estado = f"Error al conectar: {str(e)}"

def recibir_datos():
    global sock, net_queue, partida_terminada
    while True:
        try:
            if sock:
                data = sock.recv(1024).decode()
                if data:
                    net_queue.put(data)
                else:
                    break
        except (socket.error, ConnectionResetError):
            break
        except:
            break
    if sock:
        sock.close()
        sock = None
    partida_terminada = True
    net_queue.put("GAMEOVER|DESCONECTADO")

def enviar_datos(mensaje):
    if sock:
        try:
            sock.send(mensaje.encode())
        except:
            pass

def dibujar_tablero():
    for file in range(8):
        for column in range(8):
            color = blanco if (file + column) % 2 == 0 else negro
            pygame.draw.rect(pantalla, color, (column * tamaño_celda, file * tamaño_celda, tamaño_celda, tamaño_celda))

def dibujar_pieza():
    for pieza, (column, file) in posiciones_piezas.items():
        if pieza in piezas:
            pantalla.blit(piezas[pieza], (column * tamaño_celda, file * tamaño_celda))

def dibujar_mensaje():
    fuente = pygame.font.SysFont('arial', 20, bold=True)
    texto = fuente.render(mensaje_estado, True, color_mensaje)
    rect = texto.get_rect(center=(ancho // 2, 560 + 20))
    pygame.draw.rect(pantalla, negro, (0, 560, ancho, 40))
    pantalla.blit(texto, rect)

def dibujar_boton(texto, rect, color_fondo, color_texto):
    pygame.draw.rect(pantalla, color_fondo, rect)
    pygame.draw.rect(pantalla, (0, 0, 0), rect, 2)
    fuente = pygame.font.SysFont('arial', 18, bold=True)
    texto_surf = fuente.render(texto, True, color_texto)
    rect_texto = texto_surf.get_rect(center=rect.center)
    pantalla.blit(texto_surf, rect_texto)

def dibujar_movimientos_validos():
    if pieza_seleccionada:
        col_actual, fil_actual = posiciones_piezas[pieza_seleccionada]
        superficie_actual = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
        superficie_actual.fill((255, 255, 0, 100))
        pantalla.blit(superficie_actual, (col_actual * tamaño_celda, fil_actual * tamaño_celda))
        
        superficie_movimiento = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
        pygame.draw.circle(superficie_movimiento, (40, 180, 80, 180), (tamaño_celda // 2, tamaño_celda // 2), 15)
        
        for fila in range(8):
            for columna in range(8):
                if movimiento_valido(pieza_seleccionada, (columna, fila)):
                    pantalla.blit(superficie_movimiento, (columna * tamaño_celda, fila * tamaño_celda))

def dibujar_casilla_invalida():
    global casilla_invalida
    if casilla_invalida:
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - tiempo_invalido < 500:
            col, fil = casilla_invalida
            superficie_error = pygame.Surface((tamaño_celda, tamaño_celda), pygame.SRCALPHA)
            superficie_error.fill((255, 0, 0, 120))
            pantalla.blit(superficie_error, (col * tamaño_celda, fil * tamaño_celda))
        else:
            casilla_invalida = None

def dibujar_menu_promocion(color):
    ancho_menu, alto_menu = 300, 100
    x_menu = (ancho - ancho_menu) // 2
    y_menu = (alto - 40 - alto_menu) // 2
    
    pygame.draw.rect(pantalla, gris_claro, (x_menu, y_menu, ancho_menu, alto_menu))
    pygame.draw.rect(pantalla, negro, (x_menu, y_menu, ancho_menu, alto_menu), 3)
    
    fuente = pygame.font.SysFont('arial', 16, bold=True)
    txt = fuente.render("Elige pieza de promoción:", True, negro)
    pantalla.blit(txt, (x_menu + 15, y_menu + 10))
    
    opciones = ['reina', 'torre', 'alfil', 'caballo']
    botones = {}
    tam_btn = 50
    espacio = 15
    inicio_x = x_menu + 15
    
    for i, tipo in enumerate(opciones):
        bx = inicio_x + i * (tam_btn + espacio)
        by = y_menu + 38
        brect = pygame.Rect(bx, by, tam_btn, tam_btn)
        pygame.draw.rect(pantalla, blanco, brect)
        pygame.draw.rect(pantalla, negro, brect, 2)
        
        simbolo = simbolos_piezas[tipo][color]
        color_rgb = blanco if color == 'blanco' else negro
        surf_p = generar_pieza(simbolo, color_rgb)
        surf_p_peq = pygame.transform.smoothscale(surf_p, (tam_btn - 10, tam_btn - 10))
        pantalla.blit(surf_p_peq, (bx + 5, by + 5))
        
        botones[tipo] = brect
        
    return botones

def obtener_color_pieza(pieza):
    if 'blanco' in pieza or 'blanca' in pieza:
        return 'blanco'
    return 'negro'

def obtener_pieza_en(col, fil, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    for pieza, (c, f) in posiciones_a_usar.items():
        if (c, f) == (col, fil):
            return pieza
    return None

def camino_libre(pieza, nueva_posicion, posiciones=None, color_ignorado=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    col, fila = posiciones_a_usar[pieza]
    nueva_col, nueva_fila = nueva_posicion
    dx = 1 if nueva_col > col else -1 if nueva_col < col else 0
    dy = 1 if nueva_fila > fila else -1 if nueva_fila < fila else 0
    x, y = col + dx, fila + dy
    while (x, y) != (nueva_col, nueva_fila):
        pieza_intermedia = obtener_pieza_en(x, y, posiciones_a_usar)
        if pieza_intermedia:
            if color_ignorado and obtener_color_pieza(pieza_intermedia) == color_ignorado:
                pass
            else:
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
        if obtener_color_pieza(pieza) == obtener_color_pieza(pieza_destino):
            return False

    if 'rey' in pieza:
        if abs(col - nueva_col) <= 1 and abs(fila - nueva_fila) <= 1:
            return True
        if fila == nueva_fila and abs(col - nueva_col) == 2:
            if pieza in piezas_movidas:
                return False
            if en_jaque(obtener_color_pieza(pieza), posiciones_a_usar):
                return False
            
            color = obtener_color_pieza(pieza)
            if nueva_col == 6:
                nombre_torre = 'torre_blanca2' if color == 'blanco' else 'torre_negra2'
                if nombre_torre in piezas_movidas or nombre_torre not in posiciones_a_usar:
                    return False
                if not camino_libre(nombre_torre, (6, fila), posiciones_a_usar):
                    return False
                if en_jaque(color, simular_movimiento(pieza, (5, fila), posiciones_a_usar)):
                    return False
                return True
            elif nueva_col == 2:
                nombre_torre = 'torre_blanca' if color == 'blanco' else 'torre_negra'
                if nombre_torre in piezas_movidas or nombre_torre not in posiciones_a_usar:
                    return False
                if not camino_libre(nombre_torre, (2, fila), posiciones_a_usar):
                    return False
                if en_jaque(color, simular_movimiento(pieza, (3, fila), posiciones_a_usar)):
                    return False
                return True
        return False

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

def movimiento_valido(pieza, nueva_posicion, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    if not movimiento_base_valido(pieza, nueva_posicion, posiciones_a_usar):
        return False
    color = obtener_color_pieza(pieza)
    posiciones_simuladas = simular_movimiento(pieza, nueva_posicion, posiciones_a_usar)
    return not en_jaque(color, posiciones_simuladas)

def pieza_ataca_cuadro(pieza, nueva_posicion, posiciones=None, color_rey=None):
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

def obtener_rey(color, posiciones=None):
    nombre_rey = 'rey_blanco' if color == 'blanco' else 'rey_negro'
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    return nombre_rey, posiciones_a_usar[nombre_rey]

def en_jaque(color, posiciones=None):
    rey, (col_rey, fil_rey) = obtener_rey(color, posiciones)
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    for pieza, (col, fil) in posiciones_a_usar.items():
        if pieza == rey: continue
        if obtener_color_pieza(pieza) == color: continue
        if pieza_ataca_cuadro(pieza, (col_rey, fil_rey), posiciones_a_usar):
            return True
    return False

def simular_movimiento(pieza, nueva_posicion, posiciones):
    posiciones_nuevas = posiciones.copy()
    pieza_destino = obtener_pieza_en(nueva_posicion[0], nueva_posicion[1], posiciones_nuevas)
    if pieza_destino:
        del posiciones_nuevas[pieza_destino]
    posiciones_nuevas[pieza] = nueva_posicion
    return posiciones_nuevas

def hay_movimientos_legales(color, posiciones=None):
    posiciones_a_usar = posiciones_piezas if posiciones is None else posiciones
    for pieza, (col, fil) in list(posiciones_a_usar.items()):
        if obtener_color_pieza(pieza) != color: continue
        for nueva_col in range(8):
            for nueva_fila in range(8):
                if not movimiento_valido(pieza, (nueva_col, nueva_fila), posiciones_a_usar): continue
                posiciones_simuladas = simular_movimiento(pieza, (nueva_col, nueva_fila), posiciones_a_usar)
                if not en_jaque(color, posiciones_simuladas):
                    return True
    return False

def evaluar_estado(turno_actual):
    if en_jaque(turno_actual):
        if not hay_movimientos_legales(turno_actual):
            return 'jaque_mate'
        return 'jaque'
    return 'jugando'

def main():
    global pantalla, turno, posiciones_piezas, pieza_seleccionada
    global mensaje_estado, color_mensaje, juego_iniciado
    global modo_online, mi_color, player1_color, player2_color, sock, net_thread, partida_terminada, net_status
    global host_ip_input, ip_input_activo, casilla_invalida, tiempo_invalido
    global promocion_pendiente, contador_nuevas_piezas, piezas_movidas

    pantalla = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption('Ajedrez')
    pieza_seleccionada = None

    modo_seleccionado = None
    
    boton_local = pygame.Rect(ancho//2 - 100, 150, 200, 40)
    input_rect = pygame.Rect(ancho//2 - 100, 240, 200, 30)
    boton_host = pygame.Rect(ancho//2 - 100, 310, 200, 40)
    boton_join = pygame.Rect(ancho//2 - 100, 370, 200, 40)

    while not modo_seleccionado:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_local.collidepoint(evento.pos):
                    modo_seleccionado = 'local'
                if boton_host.collidepoint(evento.pos):
                    modo_seleccionado = 'host'
                if boton_join.collidepoint(evento.pos):
                    modo_seleccionado = 'join'
                if input_rect.collidepoint(evento.pos):
                    ip_input_activo = True
                else:
                    ip_input_activo = False
            
            if evento.type == pygame.KEYDOWN:
                if ip_input_activo:
                    if evento.key == pygame.K_BACKSPACE:
                        host_ip_input = host_ip_input[:-1]
                    elif evento.key == pygame.K_RETURN:
                        ip_input_activo = False
                    else:
                        host_ip_input += evento.unicode

        pantalla.fill(blanco)
        fuente_titulo = pygame.font.SysFont('arial', 30, bold=True)
        titulo = fuente_titulo.render('SELECCIONA EL MODO', True, negro)
        pantalla.blit(titulo, (ancho//2 - titulo.get_width()//2, 80))
        
        fuente_label = pygame.font.SysFont('arial', 16, bold=True)
        label = fuente_label.render("Dirección IP (Host / Cliente):", True, negro)
        pantalla.blit(label, (ancho//2 - label.get_width()//2, 218))

        color_input = gris_claro if ip_input_activo else blanco
        pygame.draw.rect(pantalla, color_input, input_rect)
        pygame.draw.rect(pantalla, negro, input_rect, 2)
        
        fuente_input = pygame.font.SysFont('arial', 20)
        texto_ip = fuente_input.render(host_ip_input, True, negro)
        pantalla.blit(texto_ip, (input_rect.x + 5, input_rect.y + 5))

        fuente_inst = pygame.font.SysFont('arial', 14)
        texto_inst1 = fuente_inst.render('(Deja vacío para usar 0.0.0.0 si eres el Host)', True, (100,100,100))
        pantalla.blit(texto_inst1, (ancho//2 - texto_inst1.get_width()//2, 278))

        dibujar_boton("Local (2 Jugadores)", boton_local, azul, blanco)
        dibujar_boton("Crear Partida (Host)", boton_host, verde, blanco)
        dibujar_boton("Unirse a Partida", boton_join, (220, 100, 50), blanco)

        pygame.display.flip()

    if modo_seleccionado in ['host', 'join']:
        modo_online = True
        net_status = 'waiting'
        juego_iniciado = True
        
        ip_final = host_ip_input.strip()
        if ip_final == "":
            ip_final = "0.0.0.0"

        if modo_seleccionado == 'host':
            mensaje_estado = f"Esperando en IP: {ip_final}:{PORT}..."
            color_mensaje = (200, 200, 200)
            thread = threading.Thread(target=hilo_esperar_host, args=(ip_final,), daemon=True)
            thread.start()
        else:
            mensaje_estado = f"Conectando a {ip_final}:{PORT}..."
            color_mensaje = (200, 200, 200)
            thread = threading.Thread(target=hilo_conectar_cliente, args=(ip_final,), daemon=True)
            thread.start()
    else:
        modo_online = False
        mi_color = None
        player1_color = random.choice(['blanco', 'negro'])
        player2_color = 'negro' if player1_color == 'blanco' else 'blanco'
        juego_iniciado = True
        turno = 'blanco'
        mensaje_estado = f'Bienvenido al modo Local. Blancas: Jugador {"1" if player1_color == "blanco" else "2"}'
        color_mensaje = blanco
        net_status = 'connected'

    while True:
        if modo_online and net_status == 'waiting':
            pantalla.fill(blanco)
            fuente = pygame.font.SysFont('arial', 24, bold=True)
            texto = fuente.render(mensaje_estado, True, color_mensaje)
            rect = texto.get_rect(center=(ancho//2, 300))
            pantalla.blit(texto, rect)
            
            boton_cancelar = pygame.Rect(ancho//2 - 60, 350, 120, 40)
            dibujar_boton("Cancelar", boton_cancelar, rojo, blanco)
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    if sock: sock.close()
                    pygame.quit(); sys.exit()
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_cancelar.collidepoint(evento.pos):
                        net_status = 'error'
                        mensaje_estado = "Conexión cancelada por el usuario"
            
            pygame.display.flip()
            continue

        if modo_online and net_status == 'error':
            pantalla.fill(blanco)
            fuente = pygame.font.SysFont('arial', 24, bold=True)
            texto = fuente.render(mensaje_estado, True, rojo)
            rect = texto.get_rect(center=(ancho//2, 280))
            pantalla.blit(texto, rect)
            
            boton_volver = pygame.Rect(ancho//2 - 60, 320, 120, 40)
            dibujar_boton("Volver", boton_volver, verde, blanco)
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_volver.collidepoint(evento.pos):
                        main()
            pygame.display.flip()
            continue

        if modo_online and net_status == 'connected' and not net_thread:
            if modo_seleccionado == 'host':
                mi_color = random.choice(['blanco', 'negro'])
                enviar_datos(f"COLOR|{'negro' if mi_color == 'blanco' else 'blanco'}")
            else:
                data = sock.recv(1024).decode()
                if data.startswith("COLOR|"):
                    mi_color = data.split("|")[1]
            
            turno = 'blanco'
            if mi_color == 'blanco':
                mensaje_estado = f"Conectado. Eres {mi_color.capitalize()}. Es tu turno."
                color_mensaje = blanco
            else:
                mensaje_estado = f"Conectado. Eres {mi_color.capitalize()}. Esperando al oponente..."
                color_mensaje = (150, 150, 150)
            net_thread = threading.Thread(target=recibir_datos, daemon=True)
            net_thread.start()

        if modo_online and net_thread:
            try:
                while True:
                    data = net_queue.get_nowait()
                    if data.startswith("MOVE|"):
                        _, pieza_movida, col_str, fil_str, enroque_info = data.split("|")[:5]
                        col, fil = int(col_str), int(fil_str)
                        
                        pieza_capturada = obtener_pieza_en(col, fil)
                        if pieza_capturada:
                            del posiciones_piezas[pieza_capturada]
                            
                        posiciones_piezas[pieza_movida] = (col, fil)
                        piezas_movidas.add(pieza_movida)
                        
                        if enroque_info != "None":
                            tipo_enr, nombre_torre = enroque_info.split(":")
                            if tipo_enr == 'corto':
                                posiciones_piezas[nombre_torre] = (5, fil)
                            elif tipo_enr == 'largo':
                                posiciones_piezas[nombre_torre] = (3, fil)
                            piezas_movidas.add(nombre_torre)

                        color_oponente = 'negro' if mi_color == 'blanco' else 'blanco'
                        estado = evaluar_estado(mi_color)
                        if estado == 'jaque_mate':
                            partida_terminada = True
                            ganador = "Jugador 2" if mi_color == 'blanco' else "Jugador 1"
                            mensaje_estado = f"¡Jaque Mate! Gana {ganador}"
                            color_mensaje = rojo
                        elif estado == 'jaque':
                            mensaje_estado = "Tu turno, ¡estás en jaque!"
                            color_mensaje = rojo
                        else:
                            mensaje_estado = "Tu turno"
                            color_mensaje = blanco
                        turno = mi_color
                        
                    elif data.startswith("PROMO|"):
                        _, pieza_vieja, tipo_pieza, nuevo_nombre, col_s, fil_s = data.split("|")
                        col, fil = int(col_s), int(fil_s)
                        if pieza_vieja in posiciones_piezas:
                            del posiciones_piezas[pieza_vieja]
                        
                        color_rival = 'negro' if mi_color == 'blanco' else 'blanco'
                        simbolo = simbolos_piezas[tipo_pieza][color_rival]
                        c_rgb = blanco if color_rival == 'blanco' else negro
                        piezas[nuevo_nombre] = generar_pieza(simbolo, c_rgb)
                        posiciones_piezas[nuevo_nombre] = (col, fil)
                        piezas_movidas.add(nuevo_nombre)
                        
                        estado = evaluar_estado(mi_color)
                        if estado == 'jaque_mate':
                            partida_terminada = True
                            ganador = "Jugador 2" if mi_color == 'blanco' else "Jugador 1"
                            mensaje_estado = f"¡Jaque Mate! Gana {ganador}"
                            color_mensaje = rojo
                        elif estado == 'jaque':
                            mensaje_estado = "Tu turno, ¡estás en jaque!"
                            color_mensaje = rojo
                        else:
                            mensaje_estado = "Tu turno"
                            color_mensaje = blanco
                        turno = mi_color

                    elif data.startswith("GAMEOVER|"):
                        motivo = data.split("|")[1]
                        partida_terminada = True
                        mensaje_estado = f"Partida terminada. {motivo}"
                        color_mensaje = rojo
            except queue.Empty:
                pass

        dibujar_tablero()
        dibujar_movimientos_validos()
        dibujar_casilla_invalida()
        dibujar_pieza()
        
        botones_promo = None
        if promocion_pendiente:
            color_prom = promocion_pendiente['color']
            botones_promo = dibujar_menu_promocion(color_prom)

        dibujar_mensaje()
        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                if sock: sock.close()
                pygame.quit(); sys.exit()
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if partida_terminada: continue
                x, y = evento.pos

                if promocion_pendiente:
                    if botones_promo:
                        for tipo_pieza, rect in botones_promo.items():
                            if rect.collidepoint(x, y):
                                color = promocion_pendiente['color']
                                col, fil = promocion_pendiente['posicion']
                                pieza_a_borrar = promocion_pendiente['pieza']
                                
                                if pieza_a_borrar in posiciones_piezas:
                                    del posiciones_piezas[pieza_a_borrar]
                                
                                nueva_pieza_nombre = f'{tipo_pieza}_{color}_{contador_nuevas_piezas}'
                                contador_nuevas_piezas += 1
                                
                                simbolo = simbolos_piezas[tipo_pieza][color]
                                color_rgb = blanco if color == 'blanco' else negro
                                piezas[nueva_pieza_nombre] = generar_pieza(simbolo, color_rgb)
                                
                                posiciones_piezas[nueva_pieza_nombre] = (col, fil)
                                piezas_movidas.add(nueva_pieza_nombre)

                                if modo_online:
                                    enviar_datos(f"PROMO|{pieza_a_borrar}|{tipo_pieza}|{nueva_pieza_nombre}|{col}|{fil}")
                                    turno = 'negro' if mi_color == 'blanco' else 'blanco'
                                    mensaje_estado = "Esperando al oponente..."
                                    color_mensaje = (150, 150, 150)
                                else:
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
                                    if modo_online:
                                        ganador_txt = "Jugador 1" if turno != mi_color else "Jugador 2"
                                        mensaje_estado = f'Jaque mate - Gana {ganador_txt}'
                                        enviar_datos(f"GAMEOVER|Has perdido por Jaque Mate")
                                    else:
                                        if turno == 'blanco':
                                            mensaje_estado = f'Jaque mate - Gana Jugador 2'
                                        else:
                                            mensaje_estado = f'Jaque mate - Gana Jugador 1'
                                    color_mensaje = rojo
                                elif estado == 'jaque':
                                    if modo_online:
                                        if turno == mi_color:
                                            mensaje_estado = 'Tu turno, estás en jaque'
                                        else:
                                            mensaje_estado = '¡El oponente está en jaque!'
                                    else:
                                        mensaje_estado = f'¡Jugador {"1" if turno=="blanco" else "2"} está en jaque!'
                                    color_mensaje = rojo

                                promocion_pendiente = None
                                break
                    continue

                if modo_online and turno != mi_color:
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

                        datos_enroque_str = "None"
                        if 'rey' in pieza_seleccionada and abs(columna - col_origen) == 2:
                            color_rey = obtener_color_pieza(pieza_seleccionada)
                            if columna == 6: 
                                nombre_torre = 'torre_blanca2' if color_rey == 'blanco' else 'torre_negra2'
                                posiciones_piezas[nombre_torre] = (5, fila)
                                piezas_movidas.add(nombre_torre)
                                datos_enroque_str = f"corto:{nombre_torre}"
                            elif columna == 2: 
                                nombre_torre = 'torre_blanca' if color_rey == 'blanco' else 'torre_negra'
                                posiciones_piezas[nombre_torre] = (3, fila)
                                piezas_movidas.add(nombre_torre)
                                datos_enroque_str = f"largo:{nombre_torre}"

                        es_promocion = False
                        if 'peon' in pieza_seleccionada and (fila == 0 or fila == 7):
                            es_promocion = True
                            promocion_pendiente = {
                                'pieza': pieza_seleccionada,
                                'posicion': (columna, fila),
                                'color': obtener_color_pieza(pieza_seleccionada)
                            }

                        if not es_promocion:
                            if modo_online:
                                enviar_datos(f"MOVE|{pieza_seleccionada}|{columna}|{fila}|{datos_enroque_str}")

                            turno = 'negro' if turno == 'blanco' else 'blanco'

                            if modo_online:
                                if turno == mi_color:
                                    mensaje_estado = "Tu turno"
                                    color_mensaje = blanco
                                else:
                                    mensaje_estado = "Esperando al oponente..."
                                    color_mensaje = (150, 150, 150)
                            else:
                                if turno == player1_color:
                                    mensaje_estado = 'Turno del Jugador 1'
                                    color_mensaje = blanco
                                else:
                                    mensaje_estado = 'Turno del Jugador 2'
                                    color_mensaje = (200, 200, 200)

                            estado = evaluar_estado(turno)
                            if estado == 'jaque_mate':
                                partida_terminada = True
                                if modo_online:
                                    ganador_txt = "Jugador 1" if turno != mi_color else "Jugador 2"
                                    mensaje_estado = f'Jaque mate - Gana {ganador_txt}'
                                    enviar_datos(f"GAMEOVER|Has perdido por Jaque Mate")
                                else:
                                    if turno == 'blanco':
                                        mensaje_estado = f'Jaque mate - Gana Jugador 2'
                                    else:
                                        mensaje_estado = f'Jaque mate - Gana Jugador 1'
                                color_mensaje = rojo
                            elif estado == 'jaque':
                                if modo_online:
                                    if turno == mi_color:
                                        mensaje_estado = 'Tu turno, estás en jaque'
                                    else:
                                        mensaje_estado = '¡El oponente está en jaque!'
                                else:
                                    mensaje_estado = f'¡Jugador {"1" if turno=="blanco" else "2"} está en jaque!'
                                color_mensaje = rojo
                    else:
                        casilla_invalida = (columna, fila)
                        tiempo_invalido = pygame.time.get_ticks()
                    
                    pieza_seleccionada = None
                        
                else:
                    for pieza, (col, fil) in posiciones_piezas.items():
                        if (col, fil) == (columna, fila):
                            if obtener_color_pieza(pieza) == turno:
                                pieza_seleccionada = pieza
                                break

if __name__ == '__main__':
    pantalla = pygame.display.set_mode((ancho, alto))
    main()