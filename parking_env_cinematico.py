import numpy as np
import math

class CinematicParkingEnv:
    def __init__(self):
        # --- Configuración del Mundo ---
        # Usamos coordenadas de pantalla directas para evitar confusión
        # (0,0) es la esquina superior izquierda. Y crece hacia abajo.
        self.width = 400
        self.height = 600
        
        # Objetivo (El hueco amarillo)
        # x, y, ancho, alto
        self.spot = {'x': 250, 'y': 300, 'w': 60, 'h': 100}
        
        # Obstáculos (Coches negros)
        self.obstacles = [
            {'x': 250, 'y': 100, 'w': 60, 'h': 100}, # Coche de adelante
            {'x': 250, 'y': 500, 'w': 60, 'h': 100}, # Coche de atrás
            {'x': 320, 'y': 0,   'w': 80, 'h': 600}, # Pared derecha
            {'x': 0,   'y': 0,   'w': 100, 'h': 600} # Pared izquierda
        ]
        
        # Configuración del Auto
        self.car_w = 40
        self.car_l = 80
        self.max_speed = 5
        self.max_angle = math.radians(30)
        self.dt = 1.0 # Paso de tiempo simulado
        
        # Acciones: [Acelerar/Frenar, Girar]
        # 0: Quieto, 1: Adelante, 2: Atras, 3: Adelante-Der, 4: Adelante-Izq, 5: Atras-Der, 6: Atras-Izq
        self.action_space_size = 7
        
        self.reset()

    def reset(self):
        # Estado inicial: Al lado del coche de adelante (posición típica para empezar a estacionar)
        # x, y, velocidad, ángulo (0 es mirando abajo en pantalla)
        self.car = {
            'x': 180, 
            'y': 150, 
            'v': 0, 
            'angle': 0 
        }
        self.steps = 0
        return self.get_state()

    def step(self, action):
        self.steps += 1
        
        # 1. Interpretar Acción
        acc = 0
        steer = 0
        
        if action == 1: acc = 1          # Adelante
        elif action == 2: acc = -1       # Atras
        elif action == 3: acc = 1; steer = 1  # Adelante Der
        elif action == 4: acc = 1; steer = -1 # Adelante Izq
        elif action == 5: acc = -1; steer = 1 # Atras Der (Cola a derecha)
        elif action == 6: acc = -1; steer = -1 # Atras Izq
        
        # 2. Física (Modelo simple)
        self.car['v'] += acc * 0.5
        self.car['v'] = max(min(self.car['v'], self.max_speed), -self.max_speed)
        # Fricción
        self.car['v'] *= 0.9 
        
        # Movimiento
        self.car['angle'] += steer * 0.1 * (self.car['v'] / self.max_speed)
        self.car['x'] += math.sin(self.car['angle']) * self.car['v'] * self.dt
        self.car['y'] += math.cos(self.car['angle']) * self.car['v'] * self.dt
        
        # 3. Recompensas y Choques
        reward = -1 # Castigo por tiempo
        done = False
        
        # Choque con límites
        if (self.car['x'] < 0 or self.car['x'] > self.width or 
            self.car['y'] < 0 or self.car['y'] > self.height):
            reward = -100
            done = True
            
        # Choque con obstaculos (Simplificado: Radio de colisión)
        car_center = (self.car['x'] + self.car_w/2, self.car['y'] + self.car_l/2)
        for obs in self.obstacles:
            obs_center = (obs['x'] + obs['w']/2, obs['y'] + obs['h']/2)
            dist = math.hypot(car_center[0] - obs_center[0], car_center[1] - obs_center[1])
            if dist < 60: # Muy cerca
                reward = -100
                done = True

        # Verificar si estacionó (Dentro del Spot)
        spot_center = (self.spot['x'] + self.spot['w']/2, self.spot['y'] + self.spot['h']/2)
        dist_to_spot = math.hypot(car_center[0] - spot_center[0], car_center[1] - spot_center[1])
        
        # Recompensa por acercarse (Shaping)
        reward += (300 - dist_to_spot) / 100.0
        
        # ESTACIONADO PERFECTO
        if (self.spot['x'] < self.car['x'] < self.spot['x'] + 20 and
            self.spot['y'] < self.car['y'] < self.spot['y'] + 20 and
            abs(self.car['angle']) < 0.2):
            reward = 1000
            done = True
            
        if self.steps > 400:
            done = True
            
        return self.get_state(), reward, done

    def get_state(self):
        # Discretizamos la distancia relativa al objetivo para que aprenda rápido
        dx = int((self.spot['x'] - self.car['x']) / 20)
        dy = int((self.spot['y'] - self.car['y']) / 20)
        da = int(self.car['angle'] * 5)
        
        # Limitamos el rango de estados para que la tabla Q no sea infinita
        dx = max(min(dx, 10), -10)
        dy = max(min(dy, 10), -10)
        da = max(min(da, 6), -6)
        
        return (dx, dy, da)

    def get_state_space(self):
        # Rangos definidos arriba: 21 valores para dx, 21 para dy, 13 para angulo
        return (21, 21, 13)