import pygame
import math
import sys

# Initialize game and screen
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Planet Simulation")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
HIGHLIGHT = (200, 200, 200) # For button hover
LABEL_BG = (0, 0, 0, 128)  # Semi-transparent black

# Simulation parameters
G = 6.6743e-11 # Gravity Constant
SCALE = 2.5e-11 # Zoomed out scale
ZOOM_SCALE = 1e-10 # Zoomed in scale
DT = 3600 # Time step, 1 hour
AU = 1.496e11 # Astronomical Unit
zoomed = False # Keeps track of zoom state

# Camera variables
camera_x, camera_y = 0, 0
panning = False
last_mouse_pos = None

# UI elements
font = pygame.font.SysFont("arial", 12)
reset_button = pygame.Rect(10, 10, 100, 30)
reset_text = font.render("Reset", True, WHITE)

class Body:
    def __init__(self, x, y, vx, vy, mass, radius, color, name="Body"):
        """
                Initialize a body.
                :param x: initial X position
                :param y: initial Y position
                :param vx: initial X velocity (m/s)
                :param vy: initial Y velocity (m/s)
                :param mass: Mass of the body (kg)
                :param radius: Radius of the body (for visualization)
                :param color: RGB color of body
                :param name: Name of the body
                """
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.mass, self.radius, self.color = mass, radius, color
        self.name = name
        self.trail = [] # List of coordinated for the trail

    def update_position(self, bodies): # Updates the position of the body
        fx, fy = 0, 0 # Force components
        for other in bodies:
            if other != self:
                dx = other.x - self.x # X distance to other body
                dy = other.y - self.y # Y distance to other body
                r = math.sqrt(dx ** 2 + dy ** 2) # Distance between the bodies
                if r > 1e3: # Dont use unrealistic forces and avoid zero division
                    # Gravitational force - F = G * m1 * m2 / r^2
                    f = G * self.mass * other.mass / (r ** 2)
                    fx += f * dx / r # Add force components, normalized by distance
                    fy += f * dy / r

        # Acceleration: a = F/m
        ax = fx / self.mass
        ay = fy / self.mass
        # Update velocity: v = v + a * dt
        self.vx += ax * DT
        self.vy += ay * DT
        # Update pos: x = x + v * dt
        self.x += self.vx * DT
        self.y += self.vy * DT

        # Convert pos to screen coordinates
        current_scale = ZOOM_SCALE if zoomed else SCALE
        screen_x = int(self.x * current_scale + WIDTH // 2 - camera_x)
        screen_y = int(self.y * current_scale + HEIGHT // 2 - camera_y)
        self.trail.append((screen_x, screen_y)) # Add trail
        if len(self.trail) > 200: # Limit trail to 200 points
            self.trail.pop(0)

    def draw(self, mouse_pos): # Draw the body and trail and label if mouse is near
        current_scale = ZOOM_SCALE if zoomed else SCALE
        # Current screen coordinated
        screen_x = int(self.x * current_scale + WIDTH // 2 - camera_x)
        screen_y = int(self.y * current_scale + HEIGHT // 2 - camera_y)

        # Draw trail
        if len(self.trail) > 1:
            pygame.draw.lines(screen, (50, 50, 50), False, self.trail, 1)

        # Draw body
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), max(self.radius, 2)) # min radius 2

        # Draw label only if mouse is near the planet
        mouse_distance = math.sqrt((mouse_pos[0] - screen_x) ** 2 + (mouse_pos[1] - screen_y) ** 2)
        if mouse_distance < 30:  # Show label if mouse is within 30 pixels
            # Calculate distance to sun
            sun = bodies[0]
            dist = math.sqrt((self.x - sun.x) ** 2 + (self.y - sun.y) ** 2) / AU
            # Render label with name and distance
            label = font.render(f"{self.name}: {dist:.2f} AU", True, WHITE)
            label_rect = label.get_rect(center=(screen_x, screen_y - self.radius - 15))
            pygame.draw.rect(screen, LABEL_BG, label_rect, border_radius=5) # Background for label
            screen.blit(label, label_rect)

# Data for all the planets!
planets_data = [
    (0, 0, 1.989e30, 8, (255, 255, 0), "Sun"),
    (5.791e10, 0.2056, 3.301e23, 2, (169, 169, 169), "Mercury"),
    (1.082e11, 0.0067, 4.867e24, 3, (255, 165, 0), "Venus"),
    (1.496e11, 0.0167, 5.972e24, 4, (0, 100, 255), "Earth"),
    (2.279e11, 0.0934, 6.39e23, 3, (255, 100, 0), "Mars"),
    (7.785e11, 0.0489, 1.898e27, 6, (200, 150, 100), "Jupiter"),
    (1.429e12, 0.0565, 5.683e26, 5, (250, 200, 100), "Saturn"),
    (2.871e12, 0.0463, 8.681e25, 4, (100, 200, 255), "Uranus"),
    (4.498e12, 0.0086, 1.024e26, 4, (0, 0, 255), "Neptune"),
    (5.906e12, 0.2488, 1.309e22, 2, (150, 100, 50), "Pluto"),
]

def get_initial_conditions(a, e, mass, radius, color, name, central_mass=1.989e30):
    """Calculate initial position and velocity for a body at perihelion"""
    r = a * (1 - e)
    x = r # Place along x-axis
    y = 0
    if a == 0:
        return Body(0, 0, 0, 0, mass, radius, color, name)
    # Velocity at perihelion: v = sqrt(G * M * (1 + e) / (a * (1 - e)))
    v = math.sqrt(G * central_mass * (1 + e) / (a * (1 - e)))
    vx = 0
    vy = v # Tangential velocity along y-axis
    return Body(x, y, vx, vy, mass, radius, color, name)

def reset_simulation():
    """Reset simulation to initial conditions"""
    global bodies, camera_x, camera_y, zoomed
    bodies = [get_initial_conditions(*data) for data in planets_data]
    camera_x, camera_y = 0, 0
    zoomed = False

# Initialize bodies
bodies = [get_initial_conditions(*data) for data in planets_data]

# Main game loop!
running = True
trail_reset = False # Flag to reset trails on camera or zoom change
while running:
    mouse_pos = pygame.mouse.get_pos() # Current mouse position
    reset_hovered = reset_button.collidepoint(mouse_pos) # If current mouse pos hovers over reset button

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                zoomed = not zoomed # Toggle zoom, z key pressed
                trail_reset = True
            elif event.key == pygame.K_LEFT:
                camera_x -= 50 # pan left
                trail_reset = True
            elif event.key == pygame.K_RIGHT:
                camera_x += 50 # pan right
                trail_reset = True
            elif event.key == pygame.K_UP:
                camera_y -= 50 # pan up
                trail_reset = True
            elif event.key == pygame.K_DOWN:
                camera_y += 50 # pan down
                trail_reset = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if reset_button.collidepoint(event.pos):
                    reset_simulation()
                    trail_reset = True
                else:
                    panning = True
                    last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                panning = False
        elif event.type == pygame.MOUSEMOTION and panning:
            current_pos = event.pos
            camera_x += (last_mouse_pos[0] - current_pos[0])
            camera_y += (last_mouse_pos[1] - current_pos[1])
            last_mouse_pos = current_pos
            trail_reset = True

    screen.fill(BLACK) # Clear screen

    # Draw reset button
    pygame.draw.rect(screen, HIGHLIGHT if reset_hovered else GRAY, reset_button)
    screen.blit(reset_text, (reset_button.x + 10, reset_button.y + 5))

    # Draw simulation info
    zoom_text = font.render(f"Zoom: {'In' if zoomed else 'Out'}", True, WHITE)
    time_text = font.render(f"Time Step: {DT/3600:.1f} hr", True, WHITE)
    screen.blit(zoom_text, (120, 10))
    screen.blit(time_text, (120, 30))

    for body in bodies:
        body.update_position(bodies) # Update position and velocity
        if trail_reset:
            body.trail = [] # Clear trail on bodies
        body.draw(mouse_pos)

    trail_reset = False
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()