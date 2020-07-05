
import pygame, sys
import time
from pygame.locals import *
import random
from math import log
from itertools import chain
from operator import itemgetter
import pprint
from inspect import getsourcefile
from os.path import abspath, join
from os import sep, listdir

vec=pygame.math.Vector2

def load_image(name):
    image = pygame.image.load(name)
    return pygame.transform.scale(image, (10, 10))

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
CYAN =(0,255,255)
YELLOW= (255,255,0)
LIGHTGRAY= (150,150,150)

MAX_ROBOT_SPEED=1.6
MAX_FORCE=0.4
FLEE_RADIUS=20 # closest permissible distance between robot and player
SEEK_FORCE=0.1 # limits the amount by which the robot can change directions
APPROACH_RADIUS=5

# This sets the WIDTH and HEIGHT of each grid location
GRID_WIDTH = 20
GRID_HEIGHT = 20

# This sets the margin between each cell
MARGIN = 5

# Create a 2 dimensional array. A two dimensional
# array is simply a list of lists.

grid = []
tup = []
for row in range(6):
    # Add an empty array that will hold each cell
    # in this row
    grid.append([])
    for column in range(6):
        grid[row].append(0)  # Append a cell
        #print (grid)
# Set row 1, cell 5 to one. (Remember rows and
# column numbers start at zero.)
#grid[1][5] = 1

# Initialize pygame
pygame.init()
pyjoy = pygame.joystick.Joystick(0)
pyjoy.init()

#Here we're going to set up the refresh rate, giving out game a max fps, so it doesn't run too often.
FPS = 50
fpsClock = pygame.time.Clock()

pywindow = pygame.display.set_mode((155, 155))
pygame.display.set_caption('Moving Image!')

gameExit= False

# RENAME BOTH OF THESE
record=[0]*10 #creates a list of ten elements each of them 0
rec=[0]*10

#.................Loading the image from the home directory.............
playerImg = load_image('squirtle.png')
robotImg= load_image('apple.png')

#................. Initializing Player and Robot variables

player_x = 80
player_y = 80
player_switch_state=0
first_destroyed=0
second_destroyed=0


robot_x = 70
robot_y = 70
robot_pos=vec(70,70)

robot_vel=vec(0,0)
robot_acc=vec(0,0)
robot_target=vec(145,145)

# Constants for possible states
STATE_VICTORY = 0
STATE_TARGET_1 = 1
STATE_TARGET_2 = 2

robot_state = STATE_TARGET_1 # targets tower 1 by default

i=0 # RENAME THIS
j=0 # RENAME THIS

############## ROBOT MOTION METHODS ..............................................................................................................................

# Check player position to see if fleeing is necessary
# TODO may use position prediction here
def should_flee():
    return (robot_pos-vec(player_x,player_y)).length() < FLEE_RADIUS

# Method for robot to flee from a certain target
def flee(target):
    steer = vec(0,0)
    dist=robot_pos-target
    dist=dist+vec(-2,1)
    # TODO can use predicted player position to determine direction to go to here?
    desired=dist.normalize()*MAX_ROBOT_SPEED

    steer=desired-robot_vel
    if steer.length() != 0 and steer.length()< MAX_FORCE:
        try:
            steer.scale_to_length(MAX_FORCE)
        except ValueError:
            # print("ValueError raised")
            # print('steer', steer, steer.length())
            # print('desired', desired)
            # print('robot_vel', robot_vel)
            pass
    return steer

# Method for robot to seek a certain target. Slows down when near
def seek_with_approach(target):
    desired=(target-robot_pos)
    dist=desired.length()
    desired=desired.normalize()
    if dist<APPROACH_RADIUS:
        desired*=dist/APPROACH_RADIUS * MAX_ROBOT_SPEED
    else:
        desired*=MAX_ROBOT_SPEED
    steer=desired-robot_vel
    if steer.length()> SEEK_FORCE:
        steer.scale_to_length(SEEK_FORCE)
    return steer

# Central method for robot movement
def get_robot_acc():
    if should_flee():
        return flee(vec(player_x, player_y))
    else:
        return seek_with_approach(robot_target)

##############...............................................................................................................................

'''
# Set the HEIGHT and WIDTH of the screen
WINDOW_SIZE = [255, 255]
screen = pygame.display.set_mode(WINDOW_SIZE)

# Set title of screen
pygame.display.set_caption("Array Backed Grid")
playerImg = load_image('squirtle.png')
player_x = 120
player_y = 120


# Loop until the user clicks the close button.
done = False

# Used to manage how fast the screen updates
clock = pygame.time.Clock()
'''

done =False

hspace={}
stm_size=7
pp = pprint.PrettyPrinter(indent=4)

#############................................Making powerset functions using a generator to save memory......................................

def is_set_bit(num, bit):
    return (num & (1 << bit) > 0 )

def xuniqueCombinations(items, n):
    if n==0: yield ()
    else:
        for i in range(len(items)):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield (items[i],)+cc

def powersetNoEmpty(iterable):
    '''
        powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
        returns as a generator
    '''
    for i in range(1, (1 << len(iterable))):
        yield tuple((iterable[bit] if is_set_bit(i, bit) else '*' for bit in range(len(iterable)-1, -1, -1) ))
##############...............................................................................................................................


#############.................................Observe..................................................

def observe(hspace,stm,observation):
    hspace_keys=powersetNoEmpty(stm)
    for key in hspace_keys:
        pspace=hspace.setdefault(key,{})
        pspace.setdefault(observation, 0)
        pspace[observation]+=1

    return hspace

#############.........................................................................................



#############..............................Making the definiton of the reliable entropy......................................................

def reliableEntropy(pspace):
    '''
    Entropy with an additional false positive to remove the bias towards low
    frequency hypothesis
    Returns the reliable entropy
    '''
    total_frequency = 0

    for freq in pspace.values():
        total_frequency += freq

    total_frequency += 1.0

    h_rel = -((1.0/total_frequency) * log(1.0/total_frequency, 2))

    for frequency in pspace.values():
        tmp = frequency/total_frequency
        h_rel -= tmp * log(tmp, 2)

    return h_rel
#############.............................................................................


#############.................................Pruning............................................
def prune(hspace, h_thresh):
    '''
    Prune the hypothesis space using the entropy as a threshold
    Returns a pruned hypothesis space
    '''
    for key in list(hspace.keys()):
        #if reliableEntropy((key, hspace[key])) > h_thresh:
        if reliableEntropy(hspace[key]) > h_thresh:
            hspace.pop(key)
    return hspace
############................................................................................


#############.................................Prediction............................................

def predict(hspace, stm):
    '''
    Given a short term memory and hypothesis space, make a prediction.
    Returns the prediction, STM item used to make the prediction, and entropy
    '''
    stm_matches = [hspace[p] for p in powersetNoEmpty(stm) if p in hspace]
    if len(stm_matches) == 0:
        return None, float('inf')

    lowest_entropy = min(stm_matches, key=reliableEntropy)
    h = reliableEntropy(lowest_entropy)
    prediction = max(lowest_entropy.items(), key=itemgetter(1))
    return  prediction[0],list(lowest_entropy.items()) , h
#############.........................................................................................


#############.................................Predicting row and the column number............................................

# Following 1-indexing. Top left is (1,1)
def predict_row_and_column(x,y):
    a=0
    b=0
    for i in range (51):
        if (25*i)-x > 0:
            a=i
            break
    for j in range(51):
        if (25*j)-y > 0:
            b=j
            break
    return (a,b)
#############.........................................................................................


# -------- Main Program Loop -----------
while (1):
    # Draw window
    pywindow.fill(LIGHTGRAY)

    # Draw towers
    pygame.draw.rect(pywindow, RED, [0,0,10,10])
    pygame.draw.rect(pywindow, RED, [0,145,10,10])
    pygame.draw.rect(pywindow, GREEN, [145,0,10,10])
    pygame.draw.rect(pywindow, GREEN, [145,145,10,10])
#.............................................................................................................................................
'''
   if pyjoy.get_axis(0) > 0:
        if should_flee()== True:
            player_x-=0.1
        else:
            player_x += 1
        if player_x > 145: #This is to keep my image inside my window. Erase these lines
            player_x = 145 
        
         #to allow the image to move freely outside the display.
    if pyjoy.get_axis(0) < 0:
        if should_flee()== True:
            player_x+=0.1
        else:
            player_x -= 1
        if player_x < 0: #This is to keep my image inside my window. Erase these lines
            player_x = 0
    


    if pyjoy.get_axis(1) > 0:
        if should_flee()== True:
            player_y+=0.1
        else:
            player_y += 1
        if player_y >145: #This is to keep my image inside my window. Erase these lines
            player_y = 145
    


    if pyjoy.get_axis(1) < 0:
        if should_flee()== True:
            player_y-=0.1
        else:
            player_y -= 1
        if player_y <0: #This is to keep my image inside my window. Erase these lines
            player_y = 0
'''



    player_x-=1
    player_y-=1
    if player_x < 0: #This is to keep my image inside my window. Erase these lines
        player_x = 0
    if player_y < 0: #This is to keep my image inside my window. Erase these lines
        player_y = 0




    if ((player_x,player_y)==(0,0)):
        player_x-=0
        player_y+=1
        if player_y >145: #This is to keep my image inside my window. Erase these lines
            player_y = 145
        
        if player_x < 0: #This is to keep my image inside my window. Erase these lines
            player_x = 0






    
    if ((player_x,player_y)==(0,0)) and (player_switch_state==0):
        player_switch_state=1
        first_destroyed=1
        

    if ((player_x,player_y)==(0,145)) and (player_switch_state==1):
        player_switch_state=0
        second_destroyed=1
        

    if ((player_x,player_y)==(0,0)) and (player_switch_state==1):
        player_switch_state=0
        first_destroyed=1
        

    if ((player_x,player_y)==(0,145)) and (player_switch_state==0):
        player_switch_state=1
        second_destroyed=1
        
    human_result=first_destroyed+second_destroyed
    #print (human_result)
    #print ((player_x,player_y))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.JOYAXISMOTION and i<10:

            rec[i]=predict_row_and_column(player_x, player_y)

            #print (rec)
            i+=1
        #print (rec)
        if i>=10:
            i=0
    # Set the screen background

    # Draw the grid
    for row in range(6):
        for column in range(6):
            color = WHITE
            #if grid[row][column] == 1:
                #color = GREEN
            pygame.draw.rect(pywindow,
                             color,
                             [(MARGIN + GRID_WIDTH) * column + MARGIN,
                              (MARGIN + GRID_HEIGHT) * row + MARGIN,
                              GRID_WIDTH,
                              GRID_HEIGHT])
#.................................................................................................................................................................................

    # Check robot_state to determine target or victory

    if human_result==2:
        print("human wins")
        
        pygame.quit()
        sys.exit()

    elif robot_state == STATE_VICTORY:
        # victory
        print ("robot wins")
        
        pygame.quit()
        sys.exit()

        pygame.quit()
        sys.exit()
    elif robot_state == STATE_TARGET_1:
        # target tower 1
        if robot_target != vec(145,145):
            robot_target = vec(145,145)
    elif robot_state == STATE_TARGET_2:
        # target tower 2
        if robot_target != vec(145,0):
            robot_target = vec(145,0)


    

    # Robot motion code
    robot_vel += get_robot_acc()

    if robot_vel.length() > MAX_ROBOT_SPEED:
        robot_vel.scale_to_length(MAX_ROBOT_SPEED)

    robot_pos += robot_vel

    # Conditions to keep robot inside window
    if robot_pos.x >145:
        robot_pos.x=145

    if robot_pos.x <0:
        robot_pos.x=0

    if robot_pos.y > 145:
        robot_pos.y=145

    if robot_pos.y<0:
        robot_pos.y=0

    # Update robot_x and robot_y
    robot_x, robot_y = (robot_pos)

    record[j]= (robot_x,robot_y)
    #print (record)
    j+=1

    if j>9:
        #print(observe(hspace, record[3:10], (player_x,player_y)))
        #print(prune(observe(hspace, rec[3:10], (player_x,player_y)),h_thresh=1.0))
        #print(predict(prune(observe(hspace, rec[3:10], predict_row_and_column(player_x,player_y)),1.5),rec[3:10]))
        #print(type((predict(prune(observe(hspace, rec[3:10], predict_row_and_column(player_x,player_y)),1.5),rec[3:10]))[1]))
        temp_prediction = predict(prune(observe(hspace, rec[3:10], predict_row_and_column(player_x,player_y)),1.1),rec[3:10])
        if temp_prediction != (None, float('inf')):
            if 0.7<temp_prediction[-1] < 1.0:
                '''tup.append((predict(prune(observe(hspace, rec[3:10], predict_row_and_column(player_x,player_y)),1.5),rec[3:10])))
                print(tup)'''
                # tup.append(temp_prediction)
                print(temp_prediction)
                with open(("HRI_new_1_output.txt"),'a') as out:
                    out.write(str(temp_prediction))
                    out.write("\n")
                #f= open("HRI_new_1_output.txt",'w')

        j=0

    # Check if target met, and robot_state needs to be changed
    # TODO use pygame.Rect to check for overlap rather than using coordinates

    if robot_x == 145 and robot_y == 145:
        robot_state = STATE_TARGET_2

    if robot_x == 145 and robot_y == 0:
        robot_state = STATE_VICTORY

#..............................................................................................................................................................

    # Limit to 60 frames per second

    #print(predict_row_and_column(player_x,player_y))

    pywindow.blit(playerImg,(player_x,player_y))
    pywindow.blit(robotImg, (robot_x, robot_y))
    pygame.display.update()
    fpsClock.tick(FPS)

    #screen.blit(playerImg,(player_x,player_y))

    