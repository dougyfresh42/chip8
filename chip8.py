# imports
import sys
import pygame
import random
import struct
import numpy as np

# debug
debug = False

# load rom into memory
memory = [0] * 4096
if len(sys.argv) < 2:
  print("No")

with open(sys.argv[1], "rb") as f:
    #byte = int.from_bytes(f.read(1), byteorder='big')
    byte = f.read(1)
    index = 512
    while byte:
      print(byte)
      # Do stuff with byte.
      memory[index] = int.from_bytes(byte, byteorder='big')
      index = index + 1

      #byte = int.from_bytes(f.read(1), byteorder='big')
      byte = f.read(1)

    print(f"{index} bytes read")

# load default sprites into memory
def_sprites = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
               0x20, 0x60, 0x20, 0x20, 0x70, # 1
               0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
               0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
               0x90, 0x90, 0xF0, 0x10, 0x10, # 4
               0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
               0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
               0xF0, 0x10, 0x20, 0x40, 0x40, # 7
               0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
               0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
               0xF0, 0x90, 0xF0, 0x90, 0x90, # A
               0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
               0xF0, 0x80, 0x80, 0x80, 0xF0, # C
               0xE0, 0x90, 0x90, 0x90, 0xE0, # D
               0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
               0xF0, 0x80, 0xF0, 0x80, 0x80] # F

for i, s in enumerate(def_sprites):
  memory[i] = s

# set up graphics
pygame.init()
screen = pygame.display.set_mode((640,320))

drawn_pixels = [[False]*32 for _ in range(64)]
def debug_pix():
  global drawn_pixels
  for x in range(64):
    for y in range(32):
      print(int(drawn_pixels[x][y]), end="")
    print()

def draw_pixel(inx, iny):
  global drawn_pixels
  x = inx % 64
  y = iny % 32

  already_drawn = drawn_pixels[x][y]
  
  drawn_pixels[x][y] = not already_drawn

  return already_drawn

def draw_byte(byte, x, y):
  collision = False

  pixels = [0] * 8
  for i in range(8):
    drawn = byte & (1<<i)
    pixels[-1-i] = 1 if drawn else 0

  for i in range(8):
    if pixels[i]:
      collision = draw_pixel(x+i, y) or collision

  return collision

def draw_sprite(length, x, y):
  global memory, Iregister
  collision = False
  for i in range(length):
    byte = memory[Iregister + i]
    collision = draw_byte(byte, x, y+i) or collision

  #draw to screen
  colors = np.array([[0,0,0],[255,255,255]])
  indices = np.asarray(drawn_pixels).astype(int)
  surface = pygame.surfarray.make_surface(colors[indices])
  surface = pygame.transform.scale(surface, (640,320))
  screen.blit(surface, (0, 0))
  pygame.display.flip()

  return collision

def cls():
  global screen, drawn_pixels
  for i in range(len(drawn_pixels)):
    for j in range(len(drawn_pixels[i])):
      drawn_pixels[i][j] = False
  screen.fill((0,0,0))

keys_pressed = [0] * 16
keys_key = [pygame.K_x, pygame.K_1, pygame.K_2,
            pygame.K_3, pygame.K_q, pygame.K_w,
            pygame.K_e, pygame.K_a, pygame.K_s,
            pygame.K_d, pygame.K_z, pygame.K_c,
            pygame.K_4, pygame.K_r, pygame.K_f,
            pygame.K_v]

def get_input():
  global keys_pressed, keys_key

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit(); sys.exit();  

  downkeys = pygame.key.get_pressed()
  for i, k in enumerate(keys_key):
    keys_pressed[i] = downkeys[k]

# set up registers
registers = [0] * 16
Iregister = 0

def lr(reg):
  global registers
  return registers[reg]

def sr(reg, v):
  global registers
  registers[reg] = v & 0xFF

delay = 0
sound = 0

pc = 512

stack = [0] * 16
sp = -1

# begin execution
running = True

def interpret(inst):
  global memory, Iregister, pc, sp, keys_pressed, delay, sound
  #CLS
  if inst == 0x00e0:
    cls()
  #RET
  elif inst == 0x00ee:
    pc = stack[sp] - 2
    sp = sp - 1

  #JP
  elif inst & 0xF000 == 0x1000:
    pc = (inst & 0xFFF) - 2

  #CALL
  elif inst & 0xF000 == 0x2000:
    sp = sp + 1
    stack[sp] = pc
    pc = (inst & 0xFFF) - 2

  #SE
  elif inst & 0xF000 == 0x3000:
    compreg = (inst & 0xF00) >> 8
    if lr(compreg) == inst & 0xFF:
      pc = pc + 2

  #SNE
  elif inst & 0xF000 == 0x4000:
    compreg = (inst & 0xF00) >> 8
    if lr(compreg) != inst & 0xFF:
      pc = pc + 2

  #SE
  elif inst & 0xF000 == 0x5000:
    compreg = (inst & 0xF00) >> 8
    compreg2 = (inst & 0xF0) >> 4
    if lr(compreg) == lr(compreg2):
      pc = pc + 2

  #LD
  elif inst & 0xF000 == 0x6000:
    ldreg = (inst & 0xF00) >> 8
    sr(ldreg, inst & 0xFF)

  #ADD
  elif inst & 0xF000 == 0x7000:
    addreg = (inst & 0xF00) >> 8
    sr(addreg, lr(addreg) + (inst & 0xFF))

  #xy family
  elif inst & 0xF000 == 0x8000:
    regx = (inst & 0xF00) >> 8
    regy = (inst & 0xF0) >> 4
    switch = inst & 0xF
    #LD
    if switch == 0:
      sr(regx, lr(regy))
    #OR
    elif switch == 1:
      sr(regx, lr(regx) | lr(regy))
    #AND
    elif switch == 2:
      sr(regx, lr(regx) & lr(regy))
    #XOR
    elif switch == 3:
      sr(regx, lr(regx) ^ lr(regy))
    #ADD
    elif switch == 4:
      result = lr(regx) + lr(regy)
      sr(0xF, result > 255)
      sr(regx, result & 0xFF)
    #SUB
    elif switch == 5:
      sr(0xF, lr(regx) > lr(regy))
      sr(regx, lr(regx) - lr(regy))
    #SHR
    elif switch == 6:
      sr(0xF, lr(regx) & 0x1)
      sr(regx, lr(regx) >> 1)
    #SUBN
    elif switch == 7:
      sr(0xF, lr(regy) > lr(regx))
      sr(regx, lr(regy) - lr(regx))
    #SHL
    elif switch == 0xE:
      #sr(0xF, (lr(regx) & 0x8000) >> 12)
      sr(0xF, (lr(regx) & 0x80) >> 7)
      sr(regx, (lr(regx) << 1) & 0xFF)

  #SNE
  elif inst & 0xF000 == 0x9000:
    regx = (inst & 0xF00) >> 8
    regy = (inst & 0xF0) >> 4
    if lr(regx) != lr(regy):
      pc = pc + 2

  #LD I, addr
  elif inst & 0xF000 == 0xA000:
    Iregister = inst & 0xFFF

  #JP V0, addr
  elif inst & 0xF000 == 0xB000:
    pc = (inst & 0xFFF) + lr(0)

  #RND Vx, byte
  elif inst & 0xF000 == 0xC000:
    #random.choice(range(256))
    reg = (inst & 0xF00) >> 8
    sr(reg, random.choice(range(256)) & inst)

  #DRW
  elif inst & 0xF000 == 0xD000:
    regx = (inst & 0xF00) >> 8
    regy = (inst & 0xF0) >> 4
    length = inst & 0xF

    collision = draw_sprite(length, lr(regx), lr(regy))
    sr(0xF, collision)

  elif inst & 0xF000 == 0xE000:
    regx = (inst & 0xF00) >> 8
    pressed = keys_pressed[lr(regx)]
    if (inst & 0xFF == 0x9E) and pressed:
      pc = pc + 2
    elif (inst & 0xFF == 0xA1) and not pressed:
      pc = pc + 2

  #x family
  elif inst & 0xF000 == 0xF000:
    regx = (inst & 0xF00) >> 8
    
    switch = inst & 0xFF
    if switch == 0x07:
      sr(regx, delay)
    elif switch == 0x0A:
      pressed = False
      current = [k for k in keys_pressed]
      while not pressed:
        get_input()
        for i in range(len(keys_pressed)):
          if current[i] < keys_pressed[i]:
            sr(0xF, i)
            pressed = True
            break
          elif current[i] > keys_pressed[i]:
            current[i] = keys_pressed[i]
      #pressed = False
      #while not pressed:
      #  get_input()
      #  for k in keys_pressed:
      #    pressed = pressed or k
      #  pygame.time.wait(10)
    elif switch == 0x15:
      delay = lr(regx)
    elif switch == 0x18:
      sound = lr(regx)
    elif switch == 0x1E:
      Iregister = Iregister + lr(regx)
    elif switch == 0x29:
      Iregister = 5 * lr(regx)
    elif switch == 0x33:
      num = lr(regx)
      memory[Iregister]   = (num % 1000) // 100
      memory[Iregister+1] = (num % 100) // 10
      memory[Iregister+2] = (num % 10) // 1
    elif switch == 0x55:
      for i in range(regx+1):
        memory[Iregister + i] = lr(i)
    elif switch == 0x65:
      for i in range(regx+1):
        sr(i, memory[Iregister + i])

current_time = pygame.time.get_ticks()
while(running):
  # get instruction
  instruction = (memory[pc] << 8) | memory[pc+1]

  # do instruction
  #print(pc)
  #print(f"{hex(memory[pc])}, {hex(memory[pc+1])}")
  #print(f"{hex(instruction)}")

  interpret(instruction)

  # decrement timer registers
  new_time = pygame.time.get_ticks()
  if new_time - current_time > 16 or new_time < current_time:
    delay = max(delay - 1, 0)
    sound = max(sound - 1, 0)
    current_time = new_time

  # increment pc
  pc = pc + 2

  # check for quit
  # get input
  get_input()
  #print(keys_pressed)

  # debug
  if(debug):
    print("Registers: ")
    for i, reg in enumerate(registers):
      print(f"{i}: {reg}")
    print(f"PC: {pc}")
    print(f"SP: {sp}")
    debug = False

  pygame.time.delay(0)
