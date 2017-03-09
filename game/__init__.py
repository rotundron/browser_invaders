import random

from browser import document, html, timer, window


SIZE = WIDTH, HEIGHT = 640, 480 # SIZE : size of game area in pixels
SCREEN = None
CTX = None
SHIPSIZE = 30					#SHIPSIZE : size of users ship in pixels

SHIPCOLOR = "#0fd"				#SHIPCOLOR: ship's colour set to light blue
SHOTCOLOR = "#d00"				#SHOTCOLOR: shot set to red
ENEMYCOLOR = "#fff"

images = {}


#Attach ascii codes for keyboard inputs to values
K_LEFT = 37
K_RIGHT = 39
K_UP = 38
K_DOWN = 40
K_SPACE = 32
K_ESCAPE = 27

KEYBOARD_LISTENER = None


def init():
    global SCREEN, CTX
    document.body.append(html.H1("Browser Invaders - a Python adventure")) #display program title to user
    SCREEN = html.CANVAS(width=WIDTH, height=HEIGHT)	#create game screen with set hight and width
    SCREEN.style = {"background": "black"}				#set the screen's background to black
    document.body.append(SCREEN)						
    CTX = SCREEN.getContext("2d")

    #load images for the ship and both enemies,
    #and print an acknowledgement after each load
    for image_name in "ship", "enemy_01", "enemy_02":
        images[image_name] = html.IMG(src="images/{}.png".format(image_name))
        print("loaded {}.png".format(image_name))


def gameover():
    global game # create a new game object for reset
    document.get(selector="h1")[0].text= "Game Over" #tell the user they have failed

#class is used for enemy ships and the player ship
#draws object to screen, updates animation frames, and checks if a ship has been shot
class GameObject:
    def __init__(self, pos=None):
        #create the object with the correct size,position, and start at the correct animation frame
        self.pos = pos
        self.width = SHIPSIZE	#the ship is square resulting in 1 variable "SHIPSIZE" used for height and width
        self.height = SHIPSIZE
        self.update_rect()		#update width and height of image to display

        self.image_counter = 0
        self.image_index = 0
        # Put object animation image names in a "self.image_names" list 
        # and the starting image object in self.image

    def update(self):
        self.update_screen()

        self.image_counter += 1	
        if hasattr(self, "image_names") and not self.image_counter % 40: #if object has animation frames and 40 counts have passed
            self.image_index += 1		#change to the next animation frame
            if self.image_index >= len(self.image_names): #if the new animation frame is past all available animation frames
                self.image_index = 0	#go back to the first animation frame
            self.image = images[self.image_names[self.image_index]]	#update the image with new frame

    def update_screen(self):
        if hasattr(self, "image"):	#if object has an image
            CTX.drawImage(self.image, self.pos[0], self.pos[1])	#draw the image at the correct location
        else:		#otherwise fill space with solid colour
            CTX.fillStyle = self.color
            # call with *self.rect not working with Brython 3.0.2
            CTX.fillRect(self.rect[0], self.rect[1], self.rect[2], self.rect[3])

    def update_rect(self):
        self.rect = (self.pos[0], self.pos[1], self.width, self.height)	#update width and height of image to display

    def intersect(self, other):
        #store the four corners of the image
        left = self.rect[0]
        right = left + self.rect[2]
        top = self.rect[1]
        botton = self.rect[1] + self.rect[3]
        
        #single boolean expression for if the rectangle of self overlaps with the rectangle of the other object	
        return (
            left >= other.rect[0] and left <= other.rect[0] + other.rect[2] or
            right >= other.rect[0] and right <= other.rect[0] + other.rect[2] or
            left <= other.rect[0] and right >= other.rect[0]) and (
                top >= other.rect[1] and top <= other.rect[1] + other.rect[3] or
                botton >= other.rect[1] and botton <= other.rect[1] + other.rect[3] or
                top <= other.rect[1]  and botton >= other.rect[1])

#stores both enemy and user ships bullets
class Shot(GameObject):
    def __init__(self, pos):
        pos = [pos[0] - SHIPSIZE / 8, pos[1] - SHIPSIZE] #bullet fires from 7/8 of the ship height
        self.speed = -15								 
        self.color = SHOTCOLOR
        super(Shot, self).__init__(pos)
        self.width = SHIPSIZE / 4		#bullet is 1/4 the size of the player
        self.update_rect()				#update rectangular image size


    def update(self):
        super(Shot, self).update()
        self.pos[1] += self.speed 	#move bullet to new position by speed pixels
        if self.pos[1] <= 0:		#when the bullet exits the screen
            return False			#remove bullet
        self.update_rect()			#update image position
        return True					#bullet persists

    def hit_any_enemy(self, enemy_list):
        finished = []
        for i, enemy in enumerate(enemy_list):	#in all the enemies on screen
            if self.intersect(enemy):			#check if the bullet_pos intersects with the enemy position
                finished.append(i)				#add enemy to delete list
                enemy.die()						#kill the enemy
        for i in reversed(finished):			#for all the enemies to delete
            del enemy_list[i]					#delete that enemy


#stores invader enemies
class Enemy(GameObject):
    def __init__(self, game, pos, speed=5):
        self.game = game
        self.speed = speed
        self.color = ENEMYCOLOR
        super(Enemy, self).__init__(pos)		
        self.image = images["enemy_01"] 	#load first animation frame as the image
        self.image_names = ["enemy_01", "enemy_02"]	#store both animation frames as available


    def update(self):
        super(Enemy, self).update()	#re-draw enemy
        self.pos[0] += self.speed 	#move enemy
        if self.pos[0] + self.width > WIDTH or self.pos[0] < 0:	#if the enemy hits the screen walls
            self.speed = -self.speed #reverse direction
            self.pos[0] += self.speed #move in new direction to offset movement outside wall
            self.pos[1] += SHIPSIZE * 2 	#drop down a layer
        if self.pos[1] >= HEIGHT:	#if the invader drops below the screen
            self.game.gameover()	#player loses
        self.update_rect()

    def die(self):
        self.game.score += 100	#when the player shoots the invaders they gain 100pts

#store player ship
class Ship(GameObject):
    def __init__(self, game):
        global KEYBOARD_LISTENER #watch for user input from keyboard
        self.game = game
        pos = [(WIDTH - SHIPSIZE) / 2, HEIGHT - SHIPSIZE]	#start ship at bottom middle of screen

        super(Ship, self).__init__(pos)

        self.aceleration = 2
        self.speed = 0

        self.max_speed = 7	#don't let the users speed beyond 7 pixels

        self.image = images["ship"]	#load player image. does not have an animation
        KEYBOARD_LISTENER = self.keypress 
        document.body.addEventListener("keydown", KEYBOARD_LISTENER) #add input listener to the window

    def update(self):
        super(Ship, self).update()

        self.speed *= 0.95	#decrease speed by a factor of 19/20 every update...stops player from stopping immediately

        if self.speed > self.max_speed: #if the player is moving too fast
            self.speed = self.max_speed 
        elif self.speed < -self.max_speed: #if the player is moving to fast in the opposite direction
            self.speed = - self.max_speed

        self.pos[0] += self.speed
        if self.pos[0] > WIDTH - SHIPSIZE: 	#if the player hits the right wall
            self.speed = 0					#player is no longer miving
            self.pos[0] = WIDTH - SHIPSIZE  #player is at the boundary limit
        elif self.pos[0] < 0:				#same as above but for the left wall
            self.speed = 0
            self.pos[0] = 0

    def keypress(self, event):
        if event.keyCode == K_RIGHT:		#if the player wants to move right
            self.speed += self.aceleration  #increase speed to the right
        elif event.keyCode == K_LEFT:       #if the player wants to move left
            self.speed -= self.aceleration	#increase speed to the left
        elif event.keyCode == K_UP:			#if player presses up
            self.speed = 0					#stop ship
        elif event.keyCode == K_SPACE and len(self.game.shots) < 3: #if player presses space bar and less than three shots on screen
            self.game.shots.append(Shot((self.pos[0] + SHIPSIZE / 2, self.pos[1]))) #fire shot
        elif event.keyCode == K_ESCAPE: #if player wants to quit
            self.game.gameover()		#kill game

    def remove(self):
        document.body.removeEventListener("keydown", KEYBOARD_LISTENER)

#store current game
class Game:

    high_score = 0 

    def __init__(self):
        self.game_over_marker = False
        self.score = 0

        self.ship = Ship(self)
        self.shots = []
        self.enemies = []
        self.next_enemy_wave = self.enemy_wave_size()
        self.populate_enemies()		#add enemies to screen
        self.scheduled_enemies = False


    def clear_screen(self):
        SCREEN.width = WIDTH

    def display_score(self):
        CTX.fillStyle = SHOTCOLOR
        CTX.font = "bold 40px Sans"
        CTX.fillText("%6d" % self.score, 10, 40) #display current score with 6 digits
        CTX.fillText("%6d" % self.high_score, WIDTH - 200, 40) #display highscore next to current score also with 6 digits

    def main(self):
        self.clear_screen()			#erase all objects from screen
        self.ship.update()	

        for enemy in self.enemies:	#for all the enemies on the screen
            enemy.update()

        finished = []	#list of shots to delete

        for i, shot in enumerate(self.shots):	#for all shots on screen
            if not shot.update():	#if shot no longer on screen
                finished.append(i)	#add to list of shots to delete
            shot.hit_any_enemy(self.enemies)	#check if it has hit any of the remaining enemies

        for i in reversed(finished):	#for shots off screen
            del self.shots[i]			#delete shots

        if not self.enemies and not self.scheduled_enemies: #if all enemies dead and no enemies planned to recreate
            self.scheduled_enemies = True			#planning to repopulate enemies
            timer.set_timeout(self.populate_enemies, 2000) 	#repopulate enemies after 2 seconds

        self.display_score()

        if not self.game_over_marker:			#if game is still going
            timer.set_timeout(self.main, 30)	#update game in 3/100 of a second
        else:									
            self.display_game_over()			#otherwise display game over message

    def enemy_wave_size(self):
        quantity, speed = 12, 4		#initial number of enemies is 12 and their speed is 4 pixels
        while True:
            yield(quantity, speed)	
            quantity += 5			#increase the number of enemy rows by 5
            speed += 2				#increase their speed by 2

    def populate_enemies(self):
        quantity, speed = next(self.next_enemy_wave)	#update number and pixel movement speed of enemies

        #increase acceleration and maximum speed of ship to compensate for more faster enemies
        self.ship.aceleration += 1						
        self.ship.max_speed = max(self.ship.max_speed, speed + 2)

        #draw 10 enemies per line
        enemies_per_line = 10
        x_pos = 20
        y_pos = 60
        x_step = (WIDTH - 20 - SHIPSIZE) / enemies_per_line #space enemies equally
        enemies_current_line = 0
        odd_line = 1
        for i in range(quantity):	#for number of enemies
            self.enemies.append(Enemy(self, [x_pos, y_pos], speed * odd_line)) #create a new enemy	
            print(x_pos, y_pos)	
            x_pos += x_step * odd_line	#update enemy position from left wall
            enemies_current_line += 1	
            if enemies_current_line >= enemies_per_line:	#if there are too many enemies on the current line
                #Start drawing enemies on a new line underneath
                enemies_current_line = 0
                odd_line *= -1
                y_pos += SHIPSIZE * 2
                x_pos = 20 if odd_line == 1 else (WIDTH - 20 - SHIPSIZE)
                print(odd_line, x_pos)

        self.scheduled_enemies = False #a new wave of enemies is no longer planned


    def display_game_over(self):
        
    	#draw a game over message in the middle of the screen that says GAME OVER in bold sans script
    	#with the same colour as the bullet shots
        CTX.font = "bold 80px Sans"
        CTX.fillStyle = SHOTCOLOR
        message = "GAME OVER"
        text_width = CTX.measureText(message).width
        print("tamanho: ", text_width)
        text_left = (WIDTH - text_width) / 2
        text_botton = (HEIGHT / 2) + 40
        CTX.fillText(message, text_left, text_botton)

    def gameover(self):
        self.game_over_marker = True
        self.ship.remove()		#delete player
        if self.score > self.high_score:	#if a new highscore is set
            self.__class__.high_score = self.score 	#update highscore
        document.body.onclick = self.restart #restart after player clicks screen

    def restart(self, event):
        # TODO: remove event listener for game restart
        if self.game_over_marker: #if game is over
            self.__init__() 	#initialize
            self.main()			#and run new game




#initial setup for game 
init()
# menu()
game = Game()
game.main()