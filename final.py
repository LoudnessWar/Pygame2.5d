import sys
from array import array
import random
import pygame
import pygame.font
import moderngl
import numpy as np

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height), pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface((screen_width, screen_height))
ctx = moderngl.create_context()

screen.fill((200, 100, 100))
clock = pygame.time.Clock()

img = pygame.image.load('assets\grid.png')

quad_buffer = ctx.buffer(data=array('f', [
    # position (x, y), uv coords (x, y)
    -1.0, 1.0, 0.0, 0.0,  # top left
    1.0, 1.0, 1.0, 0.0,  # top right
    -1.0, -1.0, 0.0, 1.0,  # bottom left
    1.0, -1.0, 1.0, 1.0,  # bottom right
]))

vert_shader = '''
#version 330 core

uniform vec3 camera_pos;  // Camera position in world space
uniform vec3 camera_orientation;  // Camera orientation as Euler angles
uniform float K;  // Perspective constant

in vec2 vert;
in vec2 textcoord;
out vec3 uvq;

// Function to calculate the intersection point of two lines
vec3 intersectLines(vec3 p1, vec3 p2, vec3 q1, vec3 q2) {
    vec3 p1p2 = p2 - p1;
    vec3 q1q2 = q2 - q1;
    vec3 p1q1 = q1 - p1;
    float t = dot(cross(q1q2, p1p2), p1q1) / dot(cross(p1p2, q1q2), cross(p1p2, q1q2));
    return p1 + p1p2 * t;
}

void main() {
    
    mat3 rotationMatrix = mat3(
        cos(camera_orientation.y) * cos(camera_orientation.z), -cos(camera_orientation.y) * sin(camera_orientation.z), sin(camera_orientation.y),
        cos(camera_orientation.x) * sin(camera_orientation.z) + sin(camera_orientation.x) * sin(camera_orientation.y) * cos(camera_orientation.z), 
        cos(camera_orientation.x) * cos(camera_orientation.z) - sin(camera_orientation.x) * sin(camera_orientation.y) * sin(camera_orientation.z), 
        -sin(camera_orientation.x) * cos(camera_orientation.y),
        sin(camera_orientation.x) * sin(camera_orientation.z) - cos(camera_orientation.x) * sin(camera_orientation.y) * cos(camera_orientation.z), 
        sin(camera_orientation.x) * cos(camera_orientation.z) + cos(camera_orientation.x) * sin(camera_orientation.y) * sin(camera_orientation.z), 
        cos(camera_orientation.x) * cos(camera_orientation.y)
    );
    
    // Apply rotation to world position
    vec3 world_pos = vec3(vert.x, vert.y, 0.0);  // Assume points lie on xz plane (y=0)
    vec3 rotated_pos = rotationMatrix * world_pos;
    
    vec3 to_camera = rotated_pos - camera_pos;
    float z_dist = to_camera.z;
    vec2 screen_pos = vec2(to_camera.x / (z_dist * K), to_camera.y / (z_dist * K));
    
    // Calculate intersection point of diagonals
    vec3 diag_intersection = intersectLines(vec3(-1.0, 1.0, 0.0), vec3(1.0, -1.0, 0.0), vec3(1.0, 1.0, 0.0), vec3(-1.0, -1.0, 0.0));
    
    // Calculate distances from intersection point to each vertex
    float d0 = distance(diag_intersection, vec3(-1.0, 1.0, 0.0));
    float d1 = distance(diag_intersection, vec3(1.0, 1.0, 0.0));
    float d2 = distance(diag_intersection, vec3(-1.0, -1.0, 0.0));
    float d3 = distance(diag_intersection, vec3(1.0, -1.0, 0.0));
    
    // Calculate perspective-corrected uvq using screen position
    uvq = vec3(textcoord, 1.0) * (d2 / (d0 + d2)) * (1.0 / z_dist);  // Perspective-corrected uvq
    
    gl_Position = vec4(screen_pos, 0.0, 1.0);
}

'''

frag_shader = '''
#version 330 core

uniform sampler2D tex;

in vec3 uvq;  // Interpolated uvq including perspective correction
out vec4 f_color;

void main() {
    // Perform perspective division
    vec2 tex_coords = uvq.xy / uvq.z;
    
    // Sample texture
    f_color = texture(tex, tex_coords);
}

'''

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'textcoord')])
print(program.extra)

camera_pos = [0.0, 0.0, -10.0]
camera_orientation = [0.0, 0.0, 0.0]
K = 0.1

def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex

t = 0

def text(screen):
    font = pygame.font.SysFont(None, 48)
    text = font.render("Title Text", True, pygame.Color("Red"))
    text_rect = text.get_rect(center=(screen.get_width() // 2, 100))
    screen.blit(text, text_rect)

scaled_img = pygame.transform.scale(img, (screen_width, screen_height))

camera_speed = 0.1
camera_rotation_speed = 0.1

def circle_surf(radius, color):
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf

particles = []



while True:
    display.fill((0, 0, 0))
    display.blit(scaled_img, (0, 0))

    text(screen=display)

    mx_change, my_change = pygame.mouse.get_rel()

    # Adjust camera orientation based on mouse movement
    camera_orientation[0] += my_change * camera_rotation_speed * 0.01
    camera_orientation[1] += mx_change * camera_rotation_speed * 0.01

    # Ensure camera orientation stays within a certain range
    camera_orientation[0] = max(min(camera_orientation[0], 90), -90)

    # mx, my = pygame.mouse.get_pos()
    # particles.append([[mx, my], [random.randint(0, 20) / 10 - 1, -5], random.randint(6, 11)])

    # for particle in particles:
    #     particle[0][0] += particle[1][0]
    #     particle[0][1] += particle[1][1]
    #     particle[2] -= 0.1
    #     particle[1][1] += 0.15
    #     pygame.draw.circle(display, (255, 150, 0), [int(particle[0][0]), int(particle[0][1])], int(particle[2]))

    #     radius = particle[2] * 2
    #     display.blit(circle_surf(radius, (20, 20, 200)), (int(particle[0][0] - radius), int(particle[0][1] - radius)), special_flags=pygame.BLEND_RGB_ADD)

    #     if particle[2] <= 0:
    #         particles.remove(particle)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        camera_pos[2] += camera_speed
    if keys[pygame.K_s]: 
        camera_pos[2] -= camera_speed
    if keys[pygame.K_a]:
        camera_pos[0] -= camera_speed
    if keys[pygame.K_d]:
        camera_pos[0] += camera_speed
    if keys[pygame.K_q]:
        K -= camera_speed/10
    if keys[pygame.K_e]:
        K += camera_speed/10

    if keys[pygame.K_UP]:
        camera_orientation[0] += camera_rotation_speed
    if keys[pygame.K_DOWN]:
        camera_orientation[0] -= camera_rotation_speed
    if keys[pygame.K_LEFT]:
        camera_orientation[1] += camera_rotation_speed
    if keys[pygame.K_RIGHT]:
        camera_orientation[1] -= camera_rotation_speed

    screen.fill((0, 0, 0))
    ctx.clear(depth=True)

    frame_tex = surf_to_texture(display)
    frame_tex.use(0)
    program['tex'] = 0
    program['camera_pos'] = camera_pos
    program['camera_orientation'] = camera_orientation
    program['K'] = K
    render_object.render(mode=moderngl.TRIANGLE_STRIP)



    pygame.display.flip()

    
    frame_tex.release()
    
    clock.tick(60)
