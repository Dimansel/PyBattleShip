from tkinter import *
from tkinter import messagebox
from random import choice
from random import randint

class Ship:        #the class is describing "ship" objects
    def __init__(self, row, col, width, height, parent, color, hidden = False):
        self.parent = parent        #needed to have an access to some variables in game
        self.color = color              #color of the ship
        self.row = row                  #coordinates
        self.col = col                     #in the grid
        self.width = width           #width and
        self.height = height         #height of the ship (measured in grid cells)
        self.dead = False              #indicates wether ship is dead or not
        self.wounds = []               #list of hits
        self.lines = []                     #stores lines that is painted to show "wounded" places
        self.hidden = hidden       #indicates wether ship is hidden or not
        self.rect = None               #rectangle. painted to display not hidden ship
        self.redraw()                    #clears all and paints it again

    def delete(self):
        for line in self.lines:
            self.parent.canvas.delete(line)
        self.parent.canvas.delete(self.rect)

    #checks if given point is near the ship (in radius of 1 cell)  and returns the corresponding result
    def _near(self, row, col):
        for i in range(self.col-1, self.col+self.width+1):
            for j in range(self.row-1, self.row+self.height+1):
                if i == col and j == row: return True
        return False

    #checks if given ship is near the ship and returns the corresponding result
    def isNear(self, ship):
        for i in range(ship.col, ship.col+ship.width):
            for j in range(ship.row, ship.row+ship.height):
                if self._near(j, i): return True
        return False

    #checks if given point hit the ship and return the corresponding result
    def hit(self, row, col):
        if (row, col) in self.wounds: return False        #this place already was hit
        for i in range(self.row, self.row+self.height):
            for j in range(self.col, self.col+self.width):
                if row == i and col == j:
                    self.wounds.append((row, col))        #there's a hit
                    if len(self.wounds) == self.width*self.height:        #the ship is now dead
                        self.dead = True
                        self.hidden = False        #if the ship was hidden we can see it now
                    self.redraw()
                    return True
        return False
    
    def redraw(self):
        self.parent.canvas.delete(self.rect)            #delete rectangle
        for line in self.lines:                                      #delete all the lines
            self.parent.canvas.delete(line)
        for wound in self.wounds:                          #paint "crosses" in places of "wounds"
            x1 = wound[1]*self.parent.cell_size
            y1 = wound[0]*self.parent.cell_size
            cs = self.parent.cell_size
            ccs = cs//10
            self.lines.append(self.parent.canvas.create_line(x1+ccs, y1+ccs, x1+cs-ccs, y1+cs-ccs, fill = self.parent.hitsColor, width = 3))
            self.lines.append(self.parent.canvas.create_line(x1+cs-ccs, y1+ccs, x1+ccs, y1+cs-ccs, fill = self.parent.hitsColor, width = 3))
        if self.hidden: return        #if the ship is not hidden paint it's as a rectangle
        x1 = self.col*self.parent.cell_size
        y1 = self.row*self.parent.cell_size
        x2 = (self.col+self.width)*self.parent.cell_size
        y2 = (self.row+self.height)*self.parent.cell_size
        self.rect = self.parent.canvas.create_rectangle(x1, y1, x2, y2, outline = self.color, width = 3)

class BattleShip(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.master.resizable(width = False, height = False)
        self.pack()                                                       #using the "pack" layout manager
        self.cell_size = 50                                           #width (height) of the cell
        self.master.title('BattleShip')                       #title of the window
        self.qns = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]             #list of the ships' widths
        self.currentShip = None
        self.dots = []
        self.hits = []
        self.uShips = []
        self.bShips = []
        self.color = 'blue'                          #color of the grid, digits, letters and ships
        self.cantStayColor = 'red'            #color of the current ship if it can't stay at it's current position
        self.canStayColor = 'green'          #color of the current ship if it can stay at it's current position
        self.hitsColor = 'red'                     #color of "hits" and "missed shots"
        self.createCanvas()                       #creating Canvas and binding events to it
        self.drawGrid()                              #drawing grid with digits and letters
        self.initGame()                              #initializes new game; i.e., sets all the variables to their's initial values and deleting ships on the Canvas

    def createCanvas(self):
        self.canvas = Canvas(self, width = 24*self.cell_size, height = 12*self.cell_size)
        self.canvas.pack()
        self.canvas.focus_set()
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('n', self.initGame)
        self.canvas.bind('<Button-3>', self.rotate)
        self.canvas.bind('<Motion>', self.mouseMove)

    def drawGrid(self):
        for i in range(1, 24):        #drawing vertical lines
            self.canvas.create_line(i*self.cell_size, 0, i*self.cell_size, 12*self.cell_size, fill = self.color)
        for i in range(1, 12):        #drawing horizontal lines
            self.canvas.create_line(0, i*self.cell_size, 24*self.cell_size, i*self.cell_size, fill = self.color)
        #drawing two rectangles that separate players' fields from background grid
        self.canvas.create_rectangle(self.cell_size, self.cell_size, 11*self.cell_size, 11*self.cell_size, outline = self.color, width = 3)
        self.canvas.create_rectangle(13*self.cell_size, self.cell_size, 23*self.cell_size, 11*self.cell_size, outline = self.color, width = 3)

    def initGame(self, ev = None):
        self.status = 1                                                        #0 - game is inactive, 1 - user is placing ships, 2 - game is active
        self.turn = 0                                                           #0 - user, 1 - Bot
        self.sdead = [0, 0]                                                  #number of destroyed ship. user's and Bot's respectively
        self.deleteAll()                                                       #deletes all the dots (missed shots), ships and current ship (if user hasn't completed ship placing)
        self.dots = []                                                           #stores missed shot object (Canvas create_oval method result)
        self.hits = []                                                            #stores grid coordinates of all shots
        self.wd = (i for i in self.qns)                                  #generator that generates sequence of ship's sizes (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)
        #next 4 variables needed for simple "intelligence" of the Bot
        self.enemyFound = False                                      #indicates wether Bot has shot a user's ship, but not killed. if has this variable stores the first shot
        self.cway = (0, 0)                                                    #current way for next shot (offset of previous shot)
        self.lshot = False                                                    #coordinates of last shot if was successful, otherwise remains "False"
        self.ways = [(-1, 0), (1, 0), (0, 1), (0, -1)]              #possible ways for next shot
        self.currentShip = None                                        #when user is placing his ships this variable stores current ship that will be placed
        self.uShips = []                                                        #contains all the user's ships
        self.bShips = []                                                        #contains all the Bot's ships

    def deleteAll(self):
        if self.currentShip != None: self.currentShip.delete()
        for dot in self.dots: self.canvas.delete(dot)
        for ship in self.uShips+self.bShips: ship.delete()

    def gameOver(self, user):
        s = 'You ' + ('win' if user else 'lose') + '!'
        messagebox.showinfo('Game over', s)

    #next three methods are responsible for current ship when user is placing his ships
    def rotate(self, ev = None):        #to rotate a ship simply swap it's width and height
        if self.currentShip == None: return
        ow = self.currentShip.width
        self.currentShip.width = self.currentShip.height
        self.currentShip.height = ow
        self.updateColor()

    def mouseMove(self, ev = None):        #move current ship on grid when mouse is moving
        x = ev.x//self.cell_size
        y = ev.y//self.cell_size
        if self.status == 1 and self.currentShip != None:
            self.currentShip.row = y
            self.currentShip.col = x
            self.updateColor()
    
    def updateColor(self):        #this method colors the current ship depending wether it can stay at current position or not (by default green and red respectively)
        color = self.canStayColor if self.canStay(self.currentShip, self.uShips, 1, 1, 11, 11) else self.cantStayColor
        self.currentShip.color = color
        self.currentShip.redraw()

    #checks if a given ship can stay at it's position on a field defined by a bounding box coordinates and returns the corresponding result
    def canStay(self, ship, ships, min_row, min_col, max_row, max_col):
        for xship in ships:
            if ship.isNear(xship): return False
        if ship.col < min_col or ship.row < min_row: return False
        if ship.col+ship.width > max_col or ship.row+ship.height > max_row: return False
        return True

    #randomly places ships on the Bot's field
    def placeBotShips(self):
        for i in self.qns:        #first of all, for each size of ship (4, 3, 3, 2, 2, 2, 1, 1, 1, 1) generate random rotation of the ship
            available = []         #then for each cell of the Bot's filed check if ship with this rotation, width and height can stay at this cell and add this cell to available if can
            k = randint(0, 1)
            for a in range(13, 23):
                for b in range(1, 11):
                    test = Ship(b, a, [i, 1][k], [i, 1][1-k], self, self.color, True)
                    if self.canStay(test, self.bShips, 1, 13, 11, 23): available.append((b, a, [i, 1][k], [i, 1][1-k]))
                    test.delete
            p = choice(available)        #choose random cell from list of available cells and place ship
            self.bShips.append(Ship(p[0], p[1], p[2], p[3], self, self.color, True))

    #places current ship at the clicked cell if current ship can stay here. if all ships were placed we need to place Bot's ships and set status value to 2
    def placeShip(self, hitx, hity):
        if self.currentShip != None:
            if not self.canStay(self.currentShip, self.uShips, 1, 1, 11, 11): return
            self.currentShip.color = self.color
            self.currentShip.redraw()
            self.uShips.append(self.currentShip)
        if len(self.uShips) == len(self.qns):        #all the ships have been placed
            self.status = 2
            self.placeBotShips()
            self.currentShip = None
            return
        self.currentShip = Ship(hity, hitx, next(self.wd), 1, self, self.canStayColor)
        self.updateColor()

    #makes a shot at hitx, hity coordinates. takes also "list of ships" and boolean variable "user" depending on who calls "shot"
    def shot(self, hitx, hity, ships, user):
        self.hits.append((hitx, hity))
        k = 1 if user else 0
        for ship in ships:
            if ship.hit(hity, hitx):        #for each ship in the list checks point at (hitx, hity) "hits" a ship
                if not user:                    #this shot was made by Bot
                    if not self.enemyFound: self.enemyFound = (hitx, hity)        #the first successful hit after last killing (if was)
                    else: self.lshot = (hitx, hity)                                                        #the last succesful hit
                if ship.dead:
                    if not user:
                        self.enemyFound = False        #this ship was killed so Bot don't need to remember first and last hits anymore
                        self.lshot = False
                        self.ways = [(-1, 0), (1, 0), (0, 1), (0, -1)]        #restore possible ways
                    self.sdead[k] += 1        #increase the number of killed ships
                    if self.sdead[k] == len(ships):        #if number if killed ships equal to number of all opponent's ship game is over
                        self.status = 0
                        for shp in self.bShips:        #show all the hidden Bot's ships
                            shp.hidden = False
                            shp.redraw()
                        self.gameOver(user)        #show "game over" messagebox
                        return
                if not user: self.botTurn()        #if Bot's shot was successful he has his turn again
                return
        #next lines will be executed only if shot was missed
        #switch turn and draw a circle at coordinates of missed shot
        self.turn = 1 - self.turn
        x1 = hitx*self.cell_size
        y1 = hity*self.cell_size
        cs = self.cell_size
        ccs = int(cs*0.4)
        self.dots.append(self.canvas.create_oval(x1+ccs, y1+ccs, x1+cs-ccs, y1+cs-ccs, fill = self.hitsColor, outline = ''))
        if user: self.botTurn()

    #here Bot is thinking and making his shot
    def botTurn(self):
        available = []
        for i in range(1, 11):        #find available cells for shot, i.e. such that are not near dead ships and not used earlier
            for j in range(1, 11):
                near = False
                for ship in self.uShips:
                    if ship.dead and ship._near(j, i):
                        near = True
                        break
                if (i, j) not in self.hits and not near:
                    available.append((i, j))
        if self.enemyFound:        #if there was the first hit (at least)
            way = 0
            if self.lshot:        #if the last shot was successful try to make next show in the same "way"
                way = (self.lshot[0]+self.cway[0], self.lshot[1]+self.cway[1])
            if way not in available and (-self.cway[0], -self.cway[1]) in self.ways:        #if last shot was missed or next shot in the same "way" is not available
                self.cway = (-self.cway[0], -self.cway[1])                                                     #it's obvious that we need to make a shot in opposite "way" in this case
                self.ways.remove(self.cway)
                way = (self.enemyFound[0]+self.cway[0], self.enemyFound[1]+self.cway[1])
            while way not in available:        #here we're getting first available "way" if opposite is unavailable
                self.cway = choice(self.ways) #after choosing a "way" simply make a shot
                way = (self.enemyFound[0]+self.cway[0], self.enemyFound[1]+self.cway[1])
                self.ways.remove(self.cway)
            self.shot(way[0], way[1], self.uShips, False)
        else:        #if there wasn't any hit choose random point and shot
            rand_point = choice(available)
            self.shot(rand_point[0], rand_point[1], self.uShips, False)

    #handles "mouse click" event binded to the Canvas
    def click(self, ev = None):
        hitx = ev.x//self.cell_size
        hity = ev.y//self.cell_size
        if self.status == 1:
            self.placeShip(hitx, hity)
        if self.status == 2:
            if hitx < 13 or hitx > 22 or hity < 1 or hity > 10: return
            if (hitx, hity) in self.hits: return
            if self.turn == 0:
                self.shot(hitx, hity, self.bShips, True)

game = BattleShip()
game.mainloop()
