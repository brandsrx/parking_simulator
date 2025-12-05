import pygame
import math
from parking_env_cinematico import CinematicParkingEnv
from q_learning_agent import QLearningAgent

# --- Colores ---
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO_PISO = (255, 255, 200)
AMARILLO_LINEAS = (255, 215, 0)
VERDE_AUTO = (34, 139, 34)
GRIS_ASFALTO = (50, 50, 50) # Asfalto más oscuro para contraste
GRIS_OBSTACULO = (80, 80, 80)
AZUL_VENTANA = (173, 216, 230)
ROJO_LUCES = (220, 20, 60)
BLANCO_LUCES = (255, 255, 224)
GRIS_UI = (30, 30, 30, 200)

def lerp(start, end, amount):
    """Función de interpolación lineal para suavizar movimiento"""
    return start + (end - start) * amount

class Simulador:
    def __init__(self):
        pygame.init()
        self.env = CinematicParkingEnv()
        self.screen = pygame.display.set_mode((self.env.width, self.env.height))
        pygame.display.set_caption("Simulador Parking RL - Movimiento Suave")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)
        
        # Cargar IA
        self.agent = QLearningAgent(self.env.get_state_space(), self.env.action_space_size)
        self.ai_loaded = self.agent.load("modelo_parking.pkl")
        
        self.modo = 'MENU'
        self.success = False
        
        # --- VARIABLES PARA SUAVIZADO (Visuales) ---
        # Estas variables persiguen a las variables reales de física
        init_state = self.env.get_state() # Reset implícito
        self.vis_x = self.env.car['x']
        self.vis_y = self.env.car['y']
        self.vis_angle = self.env.car['angle']

    def dibujar_auto_detallado(self):
        car_w = self.env.car_w
        car_l = self.env.car_l
        
        # Superficie del auto
        car_surf = pygame.Surface((car_w, car_l), pygame.SRCALPHA)
        
        # Dibujo del chasis
        points = [
            (car_w * 0.1, car_l * 0.1), (car_w * 0.9, car_l * 0.1),
            (car_w, car_l * 0.3), (car_w, car_l * 0.8),
            (car_w * 0.9, car_l * 0.95), (car_w * 0.1, car_l * 0.95),
            (0, car_l * 0.8), (0, car_l * 0.3)
        ]
        pygame.draw.polygon(car_surf, VERDE_AUTO, points)
        pygame.draw.polygon(car_surf, (0, 80, 0), points, 2)

        # Ventanas y Luces
        pygame.draw.rect(car_surf, AZUL_VENTANA, (car_w * 0.15, car_l * 0.2, car_w * 0.7, car_l * 0.15), border_radius=3)
        pygame.draw.rect(car_surf, AZUL_VENTANA, (car_w * 0.15, car_l * 0.65, car_w * 0.7, car_l * 0.15), border_radius=3)
        pygame.draw.circle(car_surf, BLANCO_LUCES, (car_w * 0.15, car_l * 0.05), 4)
        pygame.draw.circle(car_surf, BLANCO_LUCES, (car_w * 0.85, car_l * 0.05), 4)
        pygame.draw.circle(car_surf, ROJO_LUCES, (car_w * 0.15, car_l * 0.95), 4)
        pygame.draw.circle(car_surf, ROJO_LUCES, (car_w * 0.85, car_l * 0.95), 4)

        # Ruedas
        wheel_w, wheel_h = 8, 16
        for wx, wy in [(0, 10), (car_w-8, 10), (0, car_l-26), (car_w-8, car_l-26)]:
            pygame.draw.rect(car_surf, NEGRO, (wx, wy, wheel_w, wheel_h), border_radius=2)

        # --- ROTACIÓN SUAVIZADA ---
        # Usamos self.vis_angle en lugar de self.env.car['angle']
        angle_deg = math.degrees(self.vis_angle)
        rot_car = pygame.transform.rotate(car_surf, angle_deg + 180)
        
        # --- POSICIÓN SUAVIZADA ---
        # Usamos self.vis_x y self.vis_y
        rect = rot_car.get_rect(center=(self.vis_x + car_w/2, self.vis_y + car_l/2))
        
        self.screen.blit(rot_car, rect.topleft)

    def dibujar(self):
        self.screen.fill(GRIS_ASFALTO)
        
        # Obstáculos
        for obs in self.env.obstacles:
            pygame.draw.rect(self.screen, GRIS_OBSTACULO, (obs['x'], obs['y'], obs['w'], obs['h']), border_radius=5)
            pygame.draw.rect(self.screen, (30,30,30), (obs['x'], obs['y'], obs['w'], obs['h']), 2, border_radius=5)
            
        # Parking Spot
        s = self.env.spot
        pygame.draw.rect(self.screen, AMARILLO_PISO, (s['x'], s['y'], s['w'], s['h']))
        pygame.draw.rect(self.screen, AMARILLO_LINEAS, (s['x'], s['y'], s['w'], s['h']), 4)
        
        # Auto con suavizado
        self.dibujar_auto_detallado()
        
        # UI
        self.dibujar_ui()
        pygame.display.flip()

    def dibujar_ui(self):
        if self.modo == 'MENU':
            # Overlay oscuro
            s = pygame.Surface((self.env.width, self.env.height))
            s.set_alpha(150)
            s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            
            # Panel
            panel = pygame.Rect(50, 150, 300, 250)
            pygame.draw.rect(self.screen, GRIS_UI, panel, border_radius=15)
            pygame.draw.rect(self.screen, AMARILLO_LINEAS, panel, 2, border_radius=15)
            
            self.texto_centrado("SIMULADOR PARKING", -80, color=AMARILLO_LINEAS, size=30)
            self.texto_centrado("Presiona 'M' para Manual", -20)
            self.texto_centrado("Presiona 'A' para Auto (IA)", 20)
            
            status = "MODELO CARGADO" if self.ai_loaded else "MODELO NO ENCONTRADO"
            color_st = VERDE_AUTO if self.ai_loaded else ROJO_LUCES
            self.texto_centrado(status, 80, color=color_st)
        else:
            # HUD simple
            pygame.draw.rect(self.screen, GRIS_UI, (10, 10, 140, 30), border_radius=5)
            lbl = self.font_small.render(f"MODO: {self.modo}", True, BLANCO)
            self.screen.blit(lbl, (20, 15))

        if self.success:
            # Panel de Éxito
            success_panel = pygame.Surface((400, 100), pygame.SRCALPHA)
            success_panel.fill((0, 100, 0, 200)) # Verde semitransparente
            rect_success = success_panel.get_rect(center=(self.env.width/2, self.env.height/2))
            self.screen.blit(success_panel, rect_success.topleft)
            
            msg = self.font.render("¡AUTO ESTACIONADO CORRECTAMENTE!", True, BLANCO)
            sub = self.font_small.render("Presiona 'R' para reiniciar", True, BLANCO)
            
            self.screen.blit(msg, (rect_success.centerx - msg.get_width()/2, rect_success.top + 20))
            self.screen.blit(sub, (rect_success.centerx - sub.get_width()/2, rect_success.top + 60))

    def texto_centrado(self, txt, offset_y, color=BLANCO, size=20):
        font = pygame.font.SysFont("Arial", size, bold=True)
        surf = font.render(txt, True, color)
        rect = surf.get_rect(center=(self.env.width/2, self.env.height/2 + offset_y))
        self.screen.blit(surf, rect)

    def correr(self):
        running = True
        while running:
            # Inputs
            action = 0
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m: 
                        self.modo = 'MANUAL'; self.env.reset(); self.success = False
                    if event.key == pygame.K_a: 
                        self.modo = 'AUTO'; self.env.reset(); self.success = False
                    if event.key == pygame.K_r: 
                        self.env.reset(); self.success = False
                    if event.key == pygame.K_ESCAPE: self.modo = 'MENU'; self.success = False

            # Lógica Física
            if self.success:
                pass # No actualizar física si ya ganó
            elif self.modo == 'MANUAL':
                if keys[pygame.K_UP]: action = 2
                elif keys[pygame.K_DOWN]: action = 1
                if keys[pygame.K_UP] and keys[pygame.K_RIGHT]: action = 5
                if keys[pygame.K_UP] and keys[pygame.K_LEFT]: action = 6
                if keys[pygame.K_DOWN] and keys[pygame.K_RIGHT]: action = 3
                if keys[pygame.K_DOWN] and keys[pygame.K_LEFT]: action = 4
                
                _, reward, done = self.env.step(action)
                if done: 
                    if reward >= 1000:
                        self.success = True
                    else:
                        self.env.reset()
                
            elif self.modo == 'AUTO':
                if self.ai_loaded:
                    state = self.env.get_state()
                    action = self.agent.get_action(state, train=False)
                    _, reward, done = self.env.step(action)
                    if done: 
                        if reward >= 1000:
                            self.success = True
                        else:
                            # Pequeña pausa al terminar para ver el resultado
                            pygame.time.wait(500)
                            self.env.reset()
                else:
                    self.env.step(0)

            # --- SUAVIZADO VISUAL (INTERPOLACIÓN) ---
            # Factor de suavizado (0.1 = lento/muy suave, 0.5 = rápido)
            smooth_factor = 0.2
            
            self.vis_x += (self.env.car['x'] - self.vis_x) * smooth_factor
            self.vis_y += (self.env.car['y'] - self.vis_y) * smooth_factor
            
            # Interpolación angular correcta (evita giros locos de 360 a 0)
            diff_angle = self.env.car['angle'] - self.vis_angle
            while diff_angle > math.pi: diff_angle -= 2*math.pi
            while diff_angle < -math.pi: diff_angle += 2*math.pi
            self.vis_angle += diff_angle * smooth_factor

            self.dibujar()
            self.clock.tick(30) # 60 FPS fluidos
            
        pygame.quit()

if __name__ == "__main__":
    sim = Simulador()
    sim.correr()