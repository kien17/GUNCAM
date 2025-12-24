import cv2
import pygame
import random
import time
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- CẤU HÌNH PYGAME ---
WINDOW_W, WINDOW_H = 1280, 720
CAM_W, CAM_H = 320, 180
FPS = 60

# --- MÀU SẮC ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
BG_COLOR = (20, 20, 40)

class HandGunGame:
    def __init__(self):
        # 1. Khởi tạo Pygame
        pygame.init()
        pygame.display.set_caption("Hand Gun Battle - Skeleton Mode")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 40)
        self.font_small = pygame.font.SysFont("Arial", 24)

        # 2. Khởi tạo Mediapipe
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=4,
            min_hand_detection_confidence=0.5
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # Định nghĩa các đường nối xương tay (Mediapipe connections)
        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20), (5, 9), (9, 13), (13, 17)
        ]
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)

        # 3. Thông số Game
        self.cam_x = (WINDOW_W - CAM_W) // 2
        self.cam_y = WINDOW_H - CAM_H - 20
        self.sensitivity = 2.0
        self.smoothing = 0.15
        
        self.state = 'MENU'
        self.mode = 'ENDLESS'
        self.time_limit = 60
        self.start_time = 0
        
        self.init_game_vars()

    def init_game_vars(self):
        self.score_left = 0
        self.score_right = 0
        self.target_radius = 45
        
        self.thumb_was_up = {}
        self.last_shot_time = {}
        self.shoot_delay = 0.3
        self.active_shots = []
        
        self.cur_pos_p1 = [WINDOW_W // 4, WINDOW_H // 2]
        self.cur_pos_p2 = [WINDOW_W * 3 // 4, WINDOW_H // 2]
        
        self.target_left = {'x': 0, 'y': 0}
        self.target_right = {'x': 0, 'y': 0}
        self.reset_target('left')
        self.reset_target('right')

    def reset_target(self, side):
        margin = 60
        while True:
            if side == 'left':
                x_min, x_max = margin, WINDOW_W // 2 - margin
            else:
                x_min, x_max = WINDOW_W // 2 + margin, WINDOW_W - margin
            
            tx = random.randint(x_min, x_max)
            ty = random.randint(margin, WINDOW_H - margin)
            
            in_cam_x = self.cam_x - 50 < tx < self.cam_x + CAM_W + 50
            in_cam_y = self.cam_y - 50 < ty < WINDOW_H
            
            if not (in_cam_x and in_cam_y):
                if side == 'left': self.target_left = {'x': tx, 'y': ty}
                else: self.target_right = {'x': tx, 'y': ty}
                break

    def draw_text_centered(self, text, font, color, y_pos):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WINDOW_W // 2, y_pos))
        self.screen.blit(surf, rect)

    def draw_menu(self):
        self.screen.fill(BG_COLOR)
        self.draw_text_centered("GAME MENU", self.font_big, CYAN, 150)
        self.draw_text_centered("1. Endless Mode (1 Player)", self.font_med, WHITE, 280)
        self.draw_text_centered("2. Battle Mode (2 Players)", self.font_med, WHITE, 360)
        self.draw_text_centered("Press '1' or '2' to Start", self.font_small, GREEN, 480)

    def draw_results(self):
        s = pygame.Surface((WINDOW_W, WINDOW_H))
        s.set_alpha(200)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))

        self.draw_text_centered("TIME'S UP!", self.font_big, RED, 120)
        
        t1 = self.font_med.render(f"P1 (LEFT): {self.score_left}", True, YELLOW)
        t2 = self.font_med.render(f"P2 (RIGHT): {self.score_right}", True, CYAN)
        self.screen.blit(t1, (200, 250))
        self.screen.blit(t2, (800, 250))

        winner = "DRAW"
        if self.score_left > self.score_right: winner = "P1 WINS!"
        elif self.score_right > self.score_left: winner = "P2 WINS!"
        
        self.draw_text_centered(winner, self.font_big, GREEN, 380)
        self.draw_text_centered("Press 'M' for Menu", self.font_med, WHITE, 480)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: running = False
                    
                    if self.state == 'MENU':
                        if event.key == pygame.K_1:
                            self.mode = 'ENDLESS'
                            self.state = 'PLAYING'
                            self.init_game_vars()
                        elif event.key == pygame.K_2:
                            self.mode = 'BATTLE'
                            self.state = 'PLAYING'
                            self.start_time = time.time()
                            self.init_game_vars()
                    elif self.state == 'RESULT':
                        if event.key == pygame.K_m: self.state = 'MENU'

            # --- XỬ LÝ HÌNH ẢNH & MEDIAPIPE ---
            success, frame = self.cap.read()
            if not success: break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            results = self.detector.detect_for_video(mp_image, int(time.time() * 1000))

            # --- VẼ XƯƠNG TAY (SKELETON) TRỰC TIẾP LÊN ẢNH ---
            if results.hand_landmarks:
                for landmarks in results.hand_landmarks:
                    # Vẽ các khớp nối (Xương)
                    for s, e in self.connections:
                        pt1 = (int(landmarks[s].x * WINDOW_W), int(landmarks[s].y * WINDOW_H))
                        pt2 = (int(landmarks[e].x * WINDOW_W), int(landmarks[e].y * WINDOW_H))
                        cv2.line(frame_rgb, pt1, pt2, (0, 255, 0), 2) # Xanh lá
                    
                    # Vẽ các đầu ngón tay (Tròn)
                    for i in [4, 8, 12, 16, 20]:
                        pt = (int(landmarks[i].x * WINDOW_W), int(landmarks[i].y * WINDOW_H))
                        cv2.circle(frame_rgb, pt, 5, (255, 0, 0), -1) # Đỏ

            # --- VẼ GIAO DIỆN GAME ---
            self.screen.fill(BG_COLOR)

            if self.state == 'PLAYING':
                if self.mode == 'BATTLE':
                    pygame.draw.line(self.screen, RED, (WINDOW_W//2, 0), (WINDOW_W//2, WINDOW_H), 5)
                    pygame.draw.circle(self.screen, RED, (self.target_left['x'], self.target_left['y']), self.target_radius)
                    pygame.draw.circle(self.screen, WHITE, (self.target_left['x'], self.target_left['y']), self.target_radius, 3)
                    
                    pygame.draw.circle(self.screen, RED, (self.target_right['x'], self.target_right['y']), self.target_radius)
                    pygame.draw.circle(self.screen, WHITE, (self.target_right['x'], self.target_right['y']), self.target_radius, 3)
                    
                    remain_time = int(self.time_limit - (time.time() - self.start_time))
                    if remain_time <= 0: self.state = 'RESULT'
                    timer_surf = self.font_big.render(str(remain_time), True, BLUE)
                    timer_rect = timer_surf.get_rect(center=(WINDOW_W//2, 60))
                    self.screen.blit(timer_surf, timer_rect)
                else:
                    pygame.draw.circle(self.screen, RED, (self.target_left['x'], self.target_left['y']), self.target_radius)
                    pygame.draw.circle(self.screen, WHITE, (self.target_left['x'], self.target_left['y']), self.target_radius, 3)

                if results.hand_landmarks:
                    for h_idx, landmarks in enumerate(results.hand_landmarks):
                        itip = landmarks[8]
                        raw_x = itip.x 
                        is_p1 = raw_x < 0.5
                        
                        target_ix, target_iy = 0, 0
                        target_obj = None
                        color = WHITE

                        if is_p1:
                            tx = ((itip.x * 2 - 0.5) * self.sensitivity + 0.5) * (WINDOW_W // 2)
                            target_ix = np.clip(tx, 0, WINDOW_W // 2 - 20)
                            target_obj = self.target_left
                            color = YELLOW
                        else:
                            tx = (((itip.x - 0.5) * 2 - 0.5) * self.sensitivity + 0.5) * (WINDOW_W // 2) + WINDOW_W // 2
                            target_ix = np.clip(tx, WINDOW_W // 2 + 20, WINDOW_W)
                            target_obj = self.target_right
                            color = CYAN

                        target_iy = ((itip.y - 0.5) * self.sensitivity + 0.5) * WINDOW_H

                        if is_p1:
                            self.cur_pos_p1[0] += (target_ix - self.cur_pos_p1[0]) * self.smoothing
                            self.cur_pos_p1[1] += (target_iy - self.cur_pos_p1[1]) * self.smoothing
                            ix, iy = int(self.cur_pos_p1[0]), int(self.cur_pos_p1[1])
                        else:
                            self.cur_pos_p2[0] += (target_ix - self.cur_pos_p2[0]) * self.smoothing
                            self.cur_pos_p2[1] += (target_iy - self.cur_pos_p2[1]) * self.smoothing
                            ix, iy = int(self.cur_pos_p2[0]), int(self.cur_pos_p2[1])

                        pygame.draw.line(self.screen, color, (ix-20, iy), (ix+20, iy), 3)
                        pygame.draw.line(self.screen, color, (ix, iy-20), (ix, iy+20), 3)

                        thumb_down = landmarks[4].y > landmarks[3].y
                        if thumb_down and self.thumb_was_up.get(h_idx, True):
                            if time.time() - self.last_shot_time.get(h_idx, 0) > self.shoot_delay:
                                self.last_shot_time[h_idx] = time.time()
                                dist = ((ix - target_obj['x'])**2 + (iy - target_obj['y'])**2)**0.5
                                
                                is_hit = False
                                if dist < self.target_radius:
                                    is_hit = True
                                    if is_p1: 
                                        self.score_left += 1
                                        self.reset_target('left')
                                    else: 
                                        self.score_right += 1
                                        self.reset_target('right')
                                
                                self.active_shots.append({'x': ix, 'y': iy, 't': time.time(), 'miss': not is_hit})
                        
                        self.thumb_was_up[h_idx] = not thumb_down

                for s in self.active_shots[:]:
                    if time.time() - s['t'] > 0.2: self.active_shots.remove(s)
                    else: 
                        eff_color = RED if s.get('miss') else YELLOW
                        pygame.draw.circle(self.screen, eff_color, (int(s['x']), int(s['y'])), 40)
                        pygame.mixer.Sound.play(pygame.mixer.Sound('shot.mp3'))

                if self.mode == 'BATTLE':
                    score1_surf = self.font_med.render(f"P1: {self.score_left}", True, YELLOW)
                    self.screen.blit(score1_surf, (50, 50))
                    
                    score2_surf = self.font_med.render(f"P2: {self.score_right}", True, CYAN)
                    score2_rect = score2_surf.get_rect(topright=(WINDOW_W - 50, 50))
                    self.screen.blit(score2_surf, score2_rect)
                else:
                    score_surf = self.font_med.render(f"SCORE: {self.score_left + self.score_right}", True, WHITE)
                    self.screen.blit(score_surf, (50, 50))

            # --- CHUYỂN ĐỔI ẢNH CAM ĐỂ HIỂN THỊ (Đã có xương) ---
            frame_small = cv2.resize(frame_rgb, (CAM_W, CAM_H))
            frame_small = np.rot90(frame_small)
            frame_small = cv2.flip(frame_small, 0)
            
            cam_surf = pygame.surfarray.make_surface(frame_small)
            
            border_color = BLUE if (self.mode == 'BATTLE' and self.state == 'PLAYING') else WHITE
            pygame.draw.rect(self.screen, border_color, (self.cam_x-2, self.cam_y-2, CAM_W+4, CAM_H+4), 2)
            
            self.screen.blit(cam_surf, (self.cam_x, self.cam_y))
            
            if self.mode == 'BATTLE' and self.state == 'PLAYING':
                pygame.draw.line(self.screen, RED, (self.cam_x + CAM_W//2, self.cam_y), 
                                 (self.cam_x + CAM_W//2, self.cam_y + CAM_H), 3)

            if self.state == 'MENU':
                self.draw_menu()
            elif self.state == 'RESULT':
                self.draw_results()

            pygame.display.flip()
            # self.clock.tick(FPS)

        self.cap.release()
        pygame.quit()

if __name__ == "__main__":
    game = HandGunGame()
    game.run()