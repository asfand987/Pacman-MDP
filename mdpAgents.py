# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

#count = 0
init = True

class Grid:
         
    # Constructor
    #
    # Note that it creates variables:
    #
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row=[]
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)

        self.grid = subgrid

    # Print the grid out.
    def display(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j],
            # A new line after each line of the grid
            print 
        # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[self.height - (i + 1)][j],
            # A new line after each line of the grid
            print 
        # A line after the grid
        print
        
    # Set and get the values of specific elements in the grid.
    # Here x and y are indices.
    def setValue(self, x, y, value):
        self.grid[y][x] = value

    def getValue(self, x, y):
        return self.grid[y][x]

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)

        self.makeMap(state)
        self.addObjectsToMap(state)
        #self.updateFoodInMap(state)
        #self.map.display()
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"
        #self.map1.prettyDisplay()

    # Creates the two maps that we need to perform value iteration.
    def makeMap(self,state):
        corners = api.corners(state)
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)

        # map is the original/previous state.
        self.map = Grid(width, height)

        # map1 is the updated/next state.
        self.map1 = Grid(width, height)


    # Functions to get the height and the width of the grid.
    #
    # We add one to the value returned by corners to switch from the
    # index (returned by corners) to the size of the grid (that damn
    # "start counting at zero" thing again).
    def getLayoutHeight(self, corners):
        height = -1
        for i in range(len(corners)):
            if corners[i][1] > height:
                height = corners[i][1]
        return height + 1

    def getLayoutWidth(self, corners):
        width = -1
        for i in range(len(corners)):
            if corners[i][0] > width:
                width = corners[i][0]
        return width + 1

    # Functions to manipulate the map.
    #
    # Put every element in the list of wall elements into the map
    # Put every element in the list of food elements into the map
    # Put every element in the list of ghosts elements into the map 
    # Put every element in the list of capsules elements into the map
    def addObjectsToMap(self, state):

        # Add walls to map
        walls = api.walls(state)
        for i in range(len(walls)):
            self.map1.setValue(walls[i][0], walls[i][1], '%')
        
        # Add food to map
        food = api.food(state)
        for i in range(len(food)):
            self.map1.setValue(food[i][0], food[i][1], 1) 
        
        # Add ghosts to map
        ghosts = api.ghosts(state)
        for i in range(len(ghosts)):
            x = int(ghosts[i][0])
            y = int(ghosts[i][1])
            self.map1.setValue(x, y, -100)

        # Add capsules to map
        capsules = api.capsules(state)
        for i in range(len(capsules)):
            self.map1.setValue(capsules[i][0], capsules[i][1], 1)
        
       
    # Create a map with a current picture of the food that exists.
    def initialMap(self, state):

        # After the initial state has run, @ini will be set to False so it can not run again after all ready running.
        global init
        if init == True:
            for i in range(self.map.getWidth()):
                for j in range(self.map.getHeight()):
                    if self.map.getValue(i, j) != '%':
                        self.map.setValue(i, j, 0)
                        self.map1.setValue(i, j, 0)
            init = False
        
    # update the map after each iteration and calculate the utility of each iteration using the bellman equation.
    def updateMap(self, state):

        # First, make all grid elements that aren't walls blank.
        # Each iteration will run 50 times so we can find the optimal values for each state.
        counter = 0
        while counter < 50:

            for i in range(self.map.getWidth()):
                for j in range(self.map.getHeight()):  

                    # Values for Walls, Food and Ghosts will remain unchanged respectively.
                    if self.map.getValue(i, j) != '%' and self.map.getValue(i, j) != 1 and self.map.getValue(i, j) != -100:
                        
                        #store prev utility values of last state for all legal moves.
                        if self.map.getValue(i, j + 1) != '%':
                            prevNorthState = self.map.getValue(i, j + 1)
                        else: 
                            prevNorthState = self.map.getValue(i, j)

                        if self.map.getValue(i + 1, j) != '%':
                            prevEastState = self.map.getValue(i + 1, j)
                        else: 
                            prevEastState = self.map.getValue(i, j)

                        if self.map.getValue(i - 1, j) != '%':
                            prevWestState = self.map.getValue(i - 1, j)
                        else: 
                            prevWestState = self.map.getValue(i, j)
                        
                        if self.map.getValue(i, j - 1) != '%':
                            prevSouthState = self.map.getValue(i, j - 1)
                        else: 
                            prevSouthState = self.map.getValue(i, j)

                        # Calculate the best payoff of each direction.
                        north = (0.8*prevNorthState) + (0.1*prevEastState) + (0.1*prevWestState)
                        east = (0.8*prevEastState) + (0.1*prevNorthState) + (0.1*prevSouthState)
                        west = (0.8*prevWestState) + (0.1*prevNorthState) + (0.1*prevSouthState)
                        south = (0.8*prevSouthState) + (0.1*prevWestState) + (0.1*prevEastState)
                      
                        # if the current utility of the state is negative, this indicates a ghosts is nearby so we give a low reward value for this state. 
                        # Otherwise give a better reward value if there is not a ghosts nearby.
                        if self.map.getValue(i, j) < 0:
                            reward = -100
                        else:
                            reward = 0.04

                        # Calculate the maximum utility of all the legal moves.
                        maxNextUtility = max(north, east, west, south)    

                        # Plug the values into out bellan equation with a discount factor of 0.8.
                        bellman = reward + (0.8*maxNextUtility)

                        # Update the map.
                        self.map1.setValue(i, j, round(bellman,5))  

            # Update the counter for each iteration.               
            counter = counter + 1

        
    # This function calculates the best path to take as pacmans next step.
    def bestPath(self, state):
        # Pacman current state (x, y).
        pacman = api.whereAmI(state)

        # X and Y co-ordinate of current state.
        x = pacman[0]
        y = pacman[1]
        
        # Define all steps we can take as next.
        northPath = 0
        eastPath = 0
        southPath = 0
        westPath = 0

        # Set all the next steps from the preious values of the map.
        # Remember map is the previous state of the map and map1 is the updated state of the map.
        # Check the next steps is legal, i.e., not a wall.
        if self.map.getValue(x, y + 1) != '%':
            northPath = self.map.getValue(x, y + 1) 
       
        if self.map.getValue(x + 1, y) != '%':
            eastPath = self.map.getValue(x + 1, y) 
        
        if self.map.getValue(x, y - 1) != '%':
            southPath = self.map.getValue(x, y - 1)       
        
        if self.map.getValue(x - 1, y) != '%':
            westPath = self.map.getValue(x - 1, y) 
          
        # Find the next step with the max value and then return a string telling us to go to that step.
        maxValue = max(northPath, eastPath, southPath, westPath)
        if maxValue == northPath:
            return "Go North!"
        
        if maxValue == eastPath:
            return "Go East!"
        
        if maxValue == southPath:
            return "Go South!"
        
        if maxValue == westPath:
            return "Go West!"

        # In the event we could not find the next step with a max value i.e., two or more steps have an equal value,
        # We calculate the next step to take manually.
        if eastPath >= max(northPath, southPath, westPath):
            return "Go East!"
        if westPath >= max(eastPath, northPath, southPath):
            return "Go West!"
        if northPath >= max(eastPath, southPath, westPath):
            return "Go North!"
        if southPath >= max(eastPath, northPath, westPath):    
            return "Go South!"
        
        return "Random"
        
    # Function to calculate the range of steps from the positon of ghosts that will make pacman run away.  
    def runFromGhost(self, state):
        ghosts = api.ghostStates(state) 

        # Ghost state, i.e., if the ghost is in a scared state or not.
        ghostState = ghosts[0][1]
        
        # If the ghosts is not in a scared state.
        if ghostState == 0:
            for i in range(self.map.getWidth()):
                for j in range(self.map.getHeight()):
                    for k in range(len(ghosts)):
                           
                        # X and Y co-ordinates of ghosts.
                        x = int(round(ghosts[k][0][0]))
                        y = int(round(ghosts[k][0][1]))

                        # Ghosts will have a range of 4 steps down line of sights where they will have an impact on pacman directly. 
                        steps = 0

                        # Boolean variables to check if we've hit a fall or not for each direction away from the ghost. 
                        n = False
                        e = False
                        s = False
                        w = False

                    
                        while steps < 4:
                            # For each if statement, check if we are in range and current step is not a wall. 
                            # If it is a wall, set appropritate boolean variable to true so the ghost does not have an effect past this wall.
                            if x + steps < self.map.getWidth() - 1 and self.map.getValue(x + steps, y) == '%':
                                e = True
                            elif x + steps < self.map.getWidth() - 1 and self.map.getValue(x + steps, y) != '%' and e == False:
                                self.map.setValue(x + steps, y, -100 + steps)

                            if x - steps > 1 and self.map.getValue(x - steps, y) == '%':
                                w = True
                            elif x - steps > 1 and self.map.getValue(x - steps, y) != '%' and w == False:
                                self.map.setValue(x - steps, y, -100 + steps)

                            if y + steps < self.map.getHeight() - 1 and self.map.getValue(x, y + steps) == '%':
                                n = True
                            elif y + steps < self.map.getHeight() - 1 and self.map.getValue(x, y + steps) != '%' and n == False:
                                self.map.setValue(x, y + steps, -100 + steps)

                            if y - steps > 1 and self.map.getValue(x, y - steps) == '%':
                                s = True
                            elif y - steps > 1 and self.map.getValue(x, y - steps) != '%' and s == False:
                                self.map.setValue(x, y - steps, -100 + steps)

                            steps = steps + 1


    # Main function 
    def getAction(self, state):

        # Create map and map1 (prev state and current state).
        self.makeMap(state)

        # Add objects (Walls, Food, Ghosts and Capsules) to the map.
        self.addObjectsToMap(state)

        # Update the prev map so we can perform our next iteration to find the next states.
        self.map = self.map1
        self.updateMap(state)

        # Sets the impact of ghosts on the map.
        self.runFromGhost(state)

        # Gets the best direction we should move into next.
        direction = self.bestPath(state)

        # Get all legal moves we can take and remove the move STOP if it is inside legal.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        #self.map1.prettyDisplay()
  
        # Check what direction the @bestPath(state) function set for us to go, and then proceed to move into that direction.
        if direction == "Go North!":
            if Directions.NORTH in legal:
                return api.makeMove(Directions.NORTH, legal)
           
        if direction == "Go East!":
            if Directions.EAST in legal:
                return api.makeMove(Directions.EAST, legal)
           
        if direction == "Go South!":
            if Directions.SOUTH in legal:
                return api.makeMove(Directions.SOUTH, legal)
            
        if direction == "Go West!":
            if Directions.WEST in legal:
                return api.makeMove(Directions.WEST, legal)
           
        # If the direction is not legal, perform a random choice that is legal.
        pick = random.choice(legal)
        return api.makeMove(pick, legal)
        


        