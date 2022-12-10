'''
What: Python Pong Tutorial
Where: https://www.youtube.com/watch?v=vVGTZlnnX3U
Why: Needed to learn the tools available in the Python Pygame library.
'''

import time
import struct
import logging
import platform
import ast

import asyncio
import multiprocessing as mp

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from bleak import BleakScanner
from bleak import BleakClient
from bleak import discover

import pygame

# Define BLE Characteristics
BLE_DEVICE_NAME = 'ZSR_Nano33Iot'
BLE_UUID_ACCELEROMETER_SERVICE = '00001101-0000-1000-8000-00805F9B34fB'
BLE_UUID_ACCELEROMETER_X = '00002101-0000-1000-8000-00805F9B34FB'
BLE_UUID_ACCELEROMETER_Y = '00002102-0000-1000-8000-00805F9B34FB'
BLE_UUID_ACCELEROMETER_Z = '00002103-0000-1000-8000-00805F9B34FB'


async def connect_to_BLE_peripheral(ns) :
    address = None
    notFoundZSRNano = True
    while notFoundZSRNano :
        print(' Scanning list of availble Bluetooth devices for ZSR_Nano33IoT... ')
        devices = await BleakScanner.discover()
        for d in devices :
            if d.name == BLE_DEVICE_NAME :
                address = str(d.address) # store address of peripheral
                notFoundZSRNano = False
                print('BLE Connection established')
                break
        if address != None :
            break
        time.sleep(3) # seconds

    async with BleakClient(address) as client :

        # Zeroize all IMU values
        ax_raw = 0
        ay_raw = 0
        az_raw = 0
        ax = 0
        ay = 0
        az = 0

        # Read real-time IMU values
        readIMUValues = True
        while readIMUValues :
            # Read raw byte values and convert to float
            ax_raw = await client.read_gatt_char(BLE_UUID_ACCELEROMETER_X)
            ax = struct.unpack('<f', ax_raw)[0]

            # Initialize dataframe dataframe
            data = {'time': [time.time()], 'ax': [ax]}
            row = pd.DataFrame(data)

            # Append row to dataframe
            ns.df = pd.concat([ns.df, row], ignore_index=True)
            ns.df.reset_index()

            await asyncio.sleep(0.5) # seconds


# Initialize pygame window
pygame.init()

# Define window properties
WIDTH, HEIGHT = 1000, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

FPS = 60

## Colors for window objects
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

PADDLE_WIDTH, PADDLE_HEIGHT = 20, 100
BALL_RADIUS = 7

# Scoreboard properties
SCORE_FONT = pygame.font.SysFont("comicsans", 50)
WINNING_SCORE = 5

class Paddle:
    COLOR = WHITE
    VELOCITY = 4

    def __init__(self, x, y, width, height):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.width = width
        self.height = height

    def draw(self, win):
        pygame.draw.rect(
            win, self.COLOR, (self.x, self.y, self.width, self.height))

    def move(self, up=True):
        if up:
            self.y -= self.VELOCITY
        else:
            self.y += self.VELOCITY

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y


class Ball:
    MAX_VEL = 5
    COLOR = WHITE

    def __init__(self, x, y, radius):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.radius = radius
        self.x_vel = self.MAX_VEL
        self.y_vel = 0

    def draw(self, win):
        pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y
        self.y_vel = 0
        self.x_vel *= -1


def draw(win, paddles, ball, left_score, right_score):
    win.fill(BLACK)

    left_score_text = SCORE_FONT.render(f"{left_score}", 1, WHITE)
    right_score_text = SCORE_FONT.render(f"{right_score}", 1, WHITE)
    win.blit(left_score_text, (WIDTH//4 - left_score_text.get_width()//2, 20))
    win.blit(right_score_text, (WIDTH * (3/4) -
                                right_score_text.get_width()//2, 20))

    for paddle in paddles:
        paddle.draw(win)

    for i in range(10, HEIGHT, HEIGHT//20):
        if i % 2 == 1:
            continue
        pygame.draw.rect(win, WHITE, (WIDTH//2 - 5, i, 10, HEIGHT//20))

    ball.draw(win)
    pygame.display.update()


def handle_collision(ball, left_paddle, right_paddle):
    if ball.y + ball.radius >= HEIGHT:
        ball.y_vel *= -1
    elif ball.y - ball.radius <= 0:
        ball.y_vel *= -1

    if ball.x_vel < 0:
        if ball.y >= left_paddle.y and ball.y <= left_paddle.y + left_paddle.height:
            if ball.x - ball.radius <= left_paddle.x + left_paddle.width:
                ball.x_vel *= -1

                middle_y = left_paddle.y + left_paddle.height / 2
                difference_in_y = middle_y - ball.y
                reduction_factor = (left_paddle.height / 2) / ball.MAX_VEL
                y_vel = difference_in_y / reduction_factor
                ball.y_vel = -1 * y_vel

    else:
        if ball.y >= right_paddle.y and ball.y <= right_paddle.y + right_paddle.height:
            if ball.x + ball.radius >= right_paddle.x:
                ball.x_vel *= -1

                middle_y = right_paddle.y + right_paddle.height / 2
                difference_in_y = middle_y - ball.y
                reduction_factor = (right_paddle.height / 2) / ball.MAX_VEL
                y_vel = difference_in_y / reduction_factor
                ball.y_vel = -1 * y_vel


def handle_paddle_movement(keys, left_paddle, right_paddle):
    if keys[pygame.K_w] and left_paddle.y - left_paddle.VEL >= 0:
        left_paddle.move(up=True)
    if keys[pygame.K_s] and left_paddle.y + left_paddle.VEL + left_paddle.height <= HEIGHT:
        left_paddle.move(up=False)

    if keys[pygame.K_UP] and right_paddle.y - right_paddle.VEL >= 0:
        right_paddle.move(up=True)
    if keys[pygame.K_DOWN] and right_paddle.y + right_paddle.VEL + right_paddle.height <= HEIGHT:
        right_paddle.move(up=False)


def update_plot(interval, ns):
    #Plot Accerlation_X Data
    time = ns.df.loc[:,'time']
    ax = ns.df.loc[:,'ax']

    # Plot Properties
    plt.cla() 
    plt.plot(time, ax, label = 'acceleration_x')
    plt.legend(loc = 'upper center')
    plt.xlabel('Time (sec)')
    plt.ylabel('Acceleration (g)')
    plt.grid()

def animate(ns):
    ani = FuncAnimation(plt.gcf(), update_plot, fargs = (ns,), interval = 500) # ms
    plt.show()


async def connect_to_BLE_peripheral():
    # Initialize Multiprocessing
    manager = mp.Manager()
    
    # Initialize Data namespace
    ns = manager.Namespace()
    ns.df = pd.DataFrame(columns = ['time', 'ax'])
    
    # Multiprocessing
    # p = mp.Process(target = animate, args = (ns,))
    # p.start()
    asyncio.run(connect_to_BLE_peripheral(ns))

# Main ##########################################################################################

def main():

    connect_to_BLE_peripheral()


    run = True
    clock = pygame.time.Clock()

    left_paddle = Paddle(10, HEIGHT//2 - PADDLE_HEIGHT //
                         2, PADDLE_WIDTH, PADDLE_HEIGHT)
    right_paddle = Paddle(WIDTH - 10 - PADDLE_WIDTH, HEIGHT //
                          2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS)

    left_score = 0
    right_score = 0

    while run:
        clock.tick(FPS)
        draw(WIN, [left_paddle, right_paddle], ball, left_score, right_score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        keys = pygame.key.get_pressed()
        handle_paddle_movement(keys, left_paddle, right_paddle)

        ball.move()
        handle_collision(ball, left_paddle, right_paddle)

        if ball.x < 0:
            right_score += 1
            ball.reset()
        elif ball.x > WIDTH:
            left_score += 1
            ball.reset()

        won = False
        if left_score >= WINNING_SCORE:
            won = True
            win_text = "Left Player Won!"
        elif right_score >= WINNING_SCORE:
            won = True
            win_text = "Right Player Won!"

        if won:
            text = SCORE_FONT.render(win_text, 1, WHITE)
            WIN.blit(text, (WIDTH//2 - text.get_width() //
                            2, HEIGHT//2 - text.get_height()//2))
            pygame.display.update()
            pygame.time.delay(5000)
            ball.reset()
            left_paddle.reset()
            right_paddle.reset()
            left_score = 0
            right_score = 0

    pygame.quit()
    # p.join()


if __name__ == '__main__':
    main()