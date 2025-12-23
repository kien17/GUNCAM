import cv2
import random
import time
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandGunGame:
    def __init__(self):
        # 1. Khởi tạo Mediapipe
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=4,
            min_hand_detection_confidence=0.5
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20), (5, 9), (9, 13), (13, 17)
        ]

        # 2. Cấu hình Màn hình
        self.w_game, self.h_game = 1280, 720
        self.cam_small_w, self.cam_small_h = 320, 180
        
        # Vị trí Camera phụ (Giữa dưới cùng)
        # Y bắt đầu từ 520 (720 - 180 - 20)
        self.cam_x = (self.w_game - self.cam_small_w) // 2
        self.cam_y = self.h_game - self.cam_small_h - 20
        
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
        
        self.cur_pos_p1 = [self.w_game // 4, self.h_game // 2]
        self.cur_pos_p2 = [self.w_game * 3 // 4, self.h_game // 2]
        
        self.target_left = {'x': 0, 'y': 0}
        self.target_right = {'x': 0, 'y': 0}
        self.reset_target('left')
        self.reset_target('right')

    def reset_target(self, side):
        margin = 60
        while True:
            if side == 'left':
                x_min, x_max = margin, self.w_game // 2 - margin
            else: 
                x_min, x_max = self.w_game // 2 + margin, self.w_game - margin
            
            tx = random.randint(x_min, x_max)
            ty = random.randint(margin, self.h_game - margin)
            
            # Tránh camera phụ (Vùng cấm: X[440-840], Y[500-720])
            in_cam_x = self.cam_x - 50 < tx < self.cam_x + self.cam_small_w + 50
            in_cam_y = self.cam_y - 50 < ty < self.h_game
            
            if not (in_cam_x and in_cam_y):
                if side == 'left': self.target_left = {'x': tx, 'y': ty}
                else: self.target_right = {'x': tx, 'y': ty}
                break

    def draw_menu(self, img):
        overlay = img.copy()
        cv2.rectangle(overlay, (0,0), (self.w_game, self.h_game), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Đẩy chữ lên cao hơn (Y < 500) để tránh Cam phụ ở Y=520
        cv2.putText(img, "GAME MENU", (450, 150), 2, 2.5, (0, 255, 255), 3)
        cv2.putText(img, "1. Endless Mode (1 Player)", (350, 280), 2, 1, (255, 255, 255), 2)
        cv2.putText(img, "2. Battle Mode (2 Players)", (350, 360), 2, 1, (255, 255, 255), 2)
        cv2.putText(img, "Press '1' or '2' to Start", (400, 480), 2, 1.2, (0, 255, 0), 2)

    def draw_results(self, img):
        overlay = img.copy()
        cv2.rectangle(overlay, (0,0), (self.w_game, self.h_game), (0,0,0), -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
        
        cv2.putText(img, "TIME'S UP!", (480, 120), 2, 2.5, (0, 0, 255), 3)
        cv2.putText(img, f"P1 (LEFT): {self.score_left}", (200, 250), 2, 1.5, (255, 255, 0), 2)
        cv2.putText(img, f"P2 (RIGHT): {self.score_right}", (800, 250), 2, 1.5, (0, 165, 255), 2)
        
        winner = "DRAW"
        if self.score_left > self.score_right: winner = "P1 WINS!"
        elif self.score_right > self.score_left: winner = "P2 WINS!"
        
        # Đẩy chữ Winner và hướng dẫn lên cao
        cv2.putText(img, winner, (480, 380), 2, 3, (0, 255, 0), 4)
        cv2.putText(img, "Press 'M' for Menu", (500, 480), 2, 1.2, (255, 255, 255), 2)

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, 1280)
        cap.set(4, 720)

        while cap.isOpened():
            success, frame = cap.read()
            if not success: break
            frame = cv2.flip(frame, 1)
            h_orig, w_orig = frame.shape[:2]
            debug_frame = frame.copy()

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = self.detector.detect_for_video(mp_image, int(time.time() * 1000))

            game_screen = np.zeros((self.h_game, self.w_game, 3), dtype=np.uint8)
            game_screen[:] = (255, 190, 100) 
            cv2.rectangle(game_screen, (0, 600), (self.w_game, self.h_game), (100, 200, 100), -1)

            # Vẽ xương tay cho cam phụ
            if results.hand_landmarks:
                for landmarks in results.hand_landmarks:
                    for s, e in self.connections:
                        cv2.line(debug_frame, (int(landmarks[s].x*1280), int(landmarks[s].y*720)), 
                                 (int(landmarks[e].x*1280), int(landmarks[e].y*720)), (0, 255, 0), 2)

            if self.state == 'MENU':
                self.draw_menu(game_screen)
                
            elif self.state == 'PLAYING':
                if self.mode == 'BATTLE':
                    cv2.line(game_screen, (self.w_game//2, 0), (self.w_game//2, self.h_game), (0, 0, 255), 5)
                    cv2.line(debug_frame, (w_orig//2, 0), (w_orig//2, h_orig), (0, 0, 255), 5)
                    
                    cv2.circle(game_screen, (self.target_left['x'], self.target_left['y']), 40, (0, 0, 255), -1)
                    cv2.circle(game_screen, (self.target_right['x'], self.target_right['y']), 40, (0, 0, 255), -1)
                    
                    remain_time = int(self.time_limit - (time.time() - self.start_time))
                    if remain_time <= 0: self.state = 'RESULT'
                    cv2.putText(game_screen, f"{remain_time}", (self.w_game//2 - 25, 60), 2, 2, (0,0,255), 3)
                else: 
                    cv2.circle(game_screen, (self.target_left['x'], self.target_left['y']), 40, (0, 0, 255), -1)

                if results.hand_landmarks:
                    for h_idx, landmarks in enumerate(results.hand_landmarks):
                        itip = landmarks[8]
                        raw_x = itip.x 
                        is_p1 = raw_x < 0.5
                        
                        target_ix, target_iy = 0, 0
                        target_obj = None
                        color = (0,0,0)

                        if is_p1:
                            tx = ((itip.x * 2 - 0.5) * self.sensitivity + 0.5) * (self.w_game // 2)
                            target_ix = np.clip(tx, 0, self.w_game // 2 - 20)
                            target_obj = self.target_left
                            color = (255, 255, 0)
                        else:
                            tx = (((itip.x - 0.5) * 2 - 0.5) * self.sensitivity + 0.5) * (self.w_game // 2) + self.w_game // 2
                            target_ix = np.clip(tx, self.w_game // 2 + 20, self.w_game)
                            target_obj = self.target_right
                            color = (0, 255, 255)

                        target_iy = ((itip.y - 0.5) * self.sensitivity + 0.5) * self.h_game

                        # Smoothing
                        if is_p1:
                            self.cur_pos_p1[0] += (target_ix - self.cur_pos_p1[0]) * self.smoothing
                            self.cur_pos_p1[1] += (target_iy - self.cur_pos_p1[1]) * self.smoothing
                            ix, iy = int(self.cur_pos_p1[0]), int(self.cur_pos_p1[1])
                        else:
                            self.cur_pos_p2[0] += (target_ix - self.cur_pos_p2[0]) * self.smoothing
                            self.cur_pos_p2[1] += (target_iy - self.cur_pos_p2[1]) * self.smoothing
                            ix, iy = int(self.cur_pos_p2[0]), int(self.cur_pos_p2[1])

                        cv2.drawMarker(game_screen, (ix, iy), color, cv2.MARKER_CROSS, 40, 2)

                        # Bắn
                        thumb_down = landmarks[4].y > landmarks[3].y
                        if thumb_down and self.thumb_was_up.get(h_idx, True):
                            if time.time() - self.last_shot_time.get(h_idx, 0) > self.shoot_delay:
                                self.last_shot_time[h_idx] = time.time()
                                dist = ((ix - target_obj['x'])**2 + (iy - target_obj['y'])**2)**0.5
                                
                                is_hit = False
                                if dist < 40:
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
                        color = (0, 0, 255) if s.get('miss') else (0, 255, 255)
                        cv2.circle(game_screen, (int(s['x']), int(s['y'])), 40, color, -1)

                if self.mode == 'BATTLE':
                    cv2.putText(game_screen, f"P1: {self.score_left}", (50, 80), 2, 1.5, (255, 255, 0), 2)
                    cv2.putText(game_screen, f"P2: {self.score_right}", (self.w_game-200, 80), 2, 1.5, (0, 255, 255), 2)
                else:
                    cv2.putText(game_screen, f"SCORE: {self.score_left + self.score_right}", (50, 80), 2, 1.5, (255, 255, 255), 2)

            elif self.state == 'RESULT':
                self.draw_results(game_screen)

            # --- CAM PHỤ ---
            cam_small = cv2.resize(debug_frame, (self.cam_small_w, self.cam_small_h))
            border_color = (0, 0, 255) if self.mode == 'BATTLE' and self.state == 'PLAYING' else (255, 255, 255)
            cv2.rectangle(game_screen, (self.cam_x-2, self.cam_y-2), 
                          (self.cam_x+self.cam_small_w+2, self.cam_y+self.cam_small_h+2), border_color, 2)
            game_screen[self.cam_y:self.cam_y+self.cam_small_h, self.cam_x:self.cam_x+self.cam_small_w] = cam_small

            cv2.imshow("Gun Battle Split Screen", game_screen)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            
            if self.state == 'MENU':
                if key == ord('1'):
                    self.mode = 'ENDLESS'
                    self.state = 'PLAYING'
                    self.init_game_vars()
                elif key == ord('2'):
                    self.mode = 'BATTLE'
                    self.state = 'PLAYING'
                    self.start_time = time.time()
                    self.init_game_vars()
            elif self.state == 'RESULT':
                if key == ord('m'): self.state = 'MENU'

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    game = HandGunGame()
    game.run()