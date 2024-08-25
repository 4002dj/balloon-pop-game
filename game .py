import cv2
import numpy as np
import pygame
import sys
import random

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Balloon Pop')
font = pygame.font.Font(None, 36)

# Initialize score
score = 0

# Balloon settings
num_balloons_per_wave = 5  # Number of balloons per wave
num_waves = 5
current_wave = 0
screen_height = 600
time_in_seconds = 45  # Balloons should float up in 45 seconds

# Adjusted balloon size and speed
balloon_width = 80  # Increased width of the balloon
balloon_height = 100  # Increased height of the balloon
balloon_speed_y = screen_height / (time_in_seconds * 1.5)  # Slower upward speed (1.5x slower)
balloon_speed_x = 2  # Speed at which balloons move sideways
balloon_appear_interval = 1000  # Interval for balloons to appear in milliseconds

# Balloon colors
balloon_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # Including yellow

# Function to create a new balloon with random attributes
def create_balloon():
    return {
        'rect': pygame.Rect(
            random.randint(100, 700), screen_height, balloon_width, balloon_height
        ),
        'color': random.choice(balloon_colors),
        'dx': random.choice([-balloon_speed_x, balloon_speed_x]),  # Random horizontal direction
        'dy': -balloon_speed_y  # Moving upwards
    }

# Initialize Camera
cap = cv2.VideoCapture(0)

def draw_balloon(screen, rect, color):
    pygame.draw.ellipse(screen, color, rect)
    pygame.draw.line(screen, (0, 0, 0), (rect.centerx, rect.bottom), (rect.centerx, rect.bottom + 20), 2)

def initialize_balloons():
    balloons = []
    for _ in range(num_balloons_per_wave):
        balloon = create_balloon()
        while any(b['rect'].colliderect(balloon['rect']) for b in balloons):
            balloon = create_balloon()
        balloons.append(balloon)
    return balloons

# Initialize the first wave of balloons
balloons = initialize_balloons()

# --- Main Game Loop ---
last_balloon_time = pygame.time.get_ticks()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()

    # Capture frame from camera
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define color ranges for detecting white and yellow balls
    lower_white = np.array([0, 0, 200])  # Lower bound for white
    upper_white = np.array([180, 60, 255])  # Upper bound for white
    lower_yellow = np.array([20, 100, 100])  # Lower bound for yellow
    upper_yellow = np.array([30, 255, 255])  # Upper bound for yellow

    # Create masks for detecting white and yellow balls
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    result_white = cv2.bitwise_and(frame, frame, mask=mask_white)
    result_yellow = cv2.bitwise_and(frame, frame, mask=mask_yellow)

    # Combine masks
    mask_combined = cv2.bitwise_or(mask_white, mask_yellow)
    result_combined = cv2.bitwise_and(frame, frame, mask=mask_combined)

    # Find contours
    contours, _ = cv2.findContours(mask_combined, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours and mask on the frame for debugging
    cv2.imshow('Mask White', mask_white)
    cv2.imshow('Mask Yellow', mask_yellow)
    cv2.imshow('Result Combined', result_combined)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # Adjust the threshold as needed
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Detect collision with balloons
            ball_center = (x + w // 2, y + h // 2)
            for balloon in balloons:
                if (balloon['rect'].left < ball_center[0] < balloon['rect'].right and
                    balloon['rect'].top < ball_center[1] < balloon['rect'].bottom):
                    # Increase score based on balloon color
                    if balloon['color'] == (255, 255, 0):  # Yellow
                        score += 10
                    else:
                        score += 5
                    # Remove balloon that was hit
                    balloons.remove(balloon)
                    # Check if all balloons are hit for the wave
                    if not balloons:
                        current_wave += 1
                        if current_wave < num_waves:
                            # Start new wave of balloons
                            balloons = initialize_balloons()
                        else:
                            # Game over or reset after final wave
                            balloons = []
                        break

    # Balloon movement logic
    for balloon in balloons:
        balloon['rect'].x += balloon['dx']
        balloon['rect'].y += balloon['dy']
        # Reset balloon to bottom if it moves off the screen
        if balloon['rect'].bottom < 0:
            balloon = create_balloon()
            while any(b['rect'].colliderect(balloon['rect']) for b in balloons):
                balloon = create_balloon()
            balloon['rect'].center = (random.randint(100, 700), screen_height)

    # Balloons appearing faster
    current_time = pygame.time.get_ticks()
    if current_time - last_balloon_time > balloon_appear_interval:
        if current_wave < num_waves:
            new_balloon = create_balloon()
            while any(b['rect'].colliderect(new_balloon['rect']) for b in balloons):
                new_balloon = create_balloon()
            balloons.append(new_balloon)
            last_balloon_time = current_time

    # Display the camera feed with contours
    cv2.imshow('Ball Detection', frame)

    # --- Update Pygame Display ---
    screen.fill((135, 206, 250))  # Light blue background
    for balloon in balloons:
        draw_balloon(screen, balloon['rect'], balloon['color'])
    score_text = font.render(f'Score: {score}', True, (0, 0, 0))
    screen.blit(score_text, (10, 10))
    pygame.display.flip()

    # Exit the game if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
