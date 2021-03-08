

# defining error and warning handling

def say ( ) :
  input ( "Press enter to continue" )

def warning ( msg ) :
  print ( "Warning :", msg )
  say ( )

def error ( msg ) :
  print ( "Error :", msg )
  exit ( )



# checking the version of Python

from sys import version_info as v

if v.major < 3 :
  error ( "You are running old version of Python, 3.X is required!" )
elif v.minor < 9 :
  warning ( "You are running an outdated version of Python, 3.9 is recommended.")



# arguments handling

from sys import argv

if argv [ -1 ] == "modules" :
  print ( "Required modules :" )
  print ( "- opencv-python, used as cv2" )
  print ( "- numpy" )



# importing additional modules

try :
  from numpy import array as np, uint8
  import cv2
except :
  error ( "Some modules could not be imported! Use argument 'modules' to list them" )

from random import randint, randrange
from os import system
from pathlib import Path
from platform import system as s

# settings of display

SHOW_STAT = 1
MAKE_STAT_VIDEO = 0
SHOW_DISPLAY = 1
MAKE_DISPLAY_VIDEO = 0
DISPLAY_VIDEO_NAME = "gen.mp4"
STAT_VIDEO_NAME = "stat.mp4"


if s ( ) == "Windows" :
  if SHOW_DISPLAY :
    warning ( "Windows console usually does not support color codes" )



# field registration
#
# field [ y ] [ x ] = a
#
# a - Kind of reservation
#      0 - empty
#      1 - cell
#      2 - food
#      3 - poison

FIELD_SIZE = [ 20, 30 ] # height, width
LIGHT_HEIGHT = 5
SPAWN = [ LIGHT_HEIGHT - 2, FIELD_SIZE [ 1 ] // 2 ] # y, x
POISON_CHANCE = 16
GRAVITY_CYCLE = 8 # ticks amount to perform gravity
field = [ [ 0 ] * FIELD_SIZE [ 1 ] for i in range ( FIELD_SIZE [ 0 ])]



DISPLAY_FACTOR = 400
dim = ( DISPLAY_FACTOR, int ( DISPLAY_FACTOR * FIELD_SIZE [ 0 ] / FIELD_SIZE [ 1 ]))
if MAKE_DISPLAY_VIDEO : video = cv2.VideoWriter ( DISPLAY_VIDEO_NAME, cv2.VideoWriter_fourcc( *'mp4v' ), 120, dim )

PER = [ 100, 100 ]
STAT_FACTOR = 3
dim_stat = ( STAT_FACTOR * PER [ 0 ], STAT_FACTOR * PER [ 1 ])
if MAKE_STAT_VIDEO :
  video_stat = cv2.VideoWriter ( STAT_VIDEO_NAME, cv2.VideoWriter_fourcc( *'mp4v' ), 120, dim_stat )
  frame_stat = [ [ [ 0, 0, 0 ] for i in range ( PER [ 0 ])] for j in range ( PER [ 1 ])]

# cell structure
#
# cell [ a ] [ b ] [ c ]
#
# a - which cell to operate with
#
# b - values
#      energy - energy in % ( int )
#      cords - coordinates ( int, int )
#      exec_pl - current execution place ( int )
#      kind - energy consume kind
#          0 - fotosynth
#          1 - organics
#          2 - carnivorous
#      gen_seq - genetic sequence ( len * int )
#
# c - genetic code place
#
#      relations
#         0 - up left
#         1 - up
#         2 - up right
#         3 - right
#         4 - bottom right
#         5 - bottom
#         6 - bottom left
#         7 - left
#
#
#      0-7 - take energy according to relations
#
#      8-15 - prove according to relations
#          empty - +1
#          cell - +2
#          food - +3
#          poison - +4
#
#      16-23 - move or convert poison to organics according to relations
#
#      24-31 - give energy to cell according to relations
#
# energy count
#
#       genetic code execution = -2
#       fotosynthesis = +5
#       eating organics = +10
#       eating cell = + cell energy

GEN_ALG_LEN = 64
STD_GEN_SEQ = [ 0 ] * GEN_ALG_LEN
#STD_GEN_SEQ = [ randrange ( 32 ) * randrange ( 2 ) for _ in range ( GEN_ALG_LEN )]
STD_CELL_KIND = 0
cells = [ ]
MUT_CHANCE = 3 # mutation = not randrange ( MUT_CHANCE )
EVO_CHANCE = 4 # evolution
MUL_CHANCE = 1 # parallel execution
CAN_DEVOLUTE = 4 # possibility to get lower kind



# create Cell class

class Cell :
  def __init__ ( self, energy = 50, cords = SPAWN, exec_pl = 0, kind = STD_CELL_KIND, gen_seq = STD_GEN_SEQ ) :
    self.energy = energy
    self.cords = cords
    self.exec_pl = exec_pl
    self.kind = kind
    self.gen_seq = gen_seq
    self.age = 0
    self.killed = False
    field [ cords [ 0 ]] [ cords [ 1 ]] = 1



# init all genetic codes

def code ( gen_code, cell ) :
  if cell.energy <= 0 : return
  if cell.killed : return
  cell.exec_pl = ( cell.exec_pl + 1 ) % GEN_ALG_LEN
  relations = [ [ -1, -1 ], [ -1, 0 ], [ -1, 1 ], [ 0, 1 ], [ 1, 1 ], [ 1, 0 ], [ 1, -1 ], [ 0, -1 ]]
  if cell.energy >= 100 :
    for dy, dx in relations :
      x = ( cell.cords [ 1 ] + dx ) % FIELD_SIZE [ 1 ]
      y = cell.cords [ 0 ] + dy
      if not 0 <= y < FIELD_SIZE [ 0 ] : continue
      if field [ y ] [ x ] == 0 :
        gen_seq = cell.gen_seq [ : ]
        if not randrange ( MUT_CHANCE ) :
          pl = randrange ( GEN_ALG_LEN - 1 )
          gen_seq [ pl ] = randint ( 0, 31 )
        kind = cell.kind
        if not randrange ( EVO_CHANCE ) :
          new_kind = randint ( 0, 2 )
          if CAN_DEVOLUTE or new_kind > kind : kind = new_kind
        exec_pl = 0
        if not randrange ( MUL_CHANCE ) :
          exec_pl = ( cell.exec_pl + 1 ) % GEN_ALG_LEN
        cells.append ( Cell ( energy = cell.energy // 2, cords = [ y, x ], exec_pl = exec_pl, kind = kind, gen_seq = gen_seq ))
        break
    cell.energy //= 2

  cell.energy -= 2
  code_kind, mod = divmod ( gen_code, 8 )
  dx, dy = relations [ mod ]
  x = ( cell.cords [ 1 ] + dx ) % FIELD_SIZE [ 1 ]
  y = cell.cords [ 0 ] + dy

  if not 0 <= y and ( code_kind or cell.kind ) : return
  if not y < FIELD_SIZE [ 0 ] : return

  f = field [ y ] [ x ]

  if code_kind == 0 : # getting energy
    if cell.kind == 0 :
      if cell.cords [ 0 ] == 0 or ( y <= LIGHT_HEIGHT and field [ cell.cords [ 0 ] - 1 ] [ cell.cords [ 1 ]] == 0 ) :
        cell.energy += 5
    elif f == 3 :
      cell.energy = 0
    elif cell.kind == 1 :
      if f == 2 :
        field [ y ] [ x ] = 0
        cell.energy += 10
    elif cell.kind == 2 :
      if f == 1 :
        for i in cells :
          if i.cords == [ y, x ] :
            cell.energy += i.energy
            i.energy = 0
            i.killed = True
            break
  elif code_kind == 1 : # proving places
    e = cell.exec_pl
    cell.exec_pl = ( e + f ) % GEN_ALG_LEN
  elif code_kind == 2 : # move or unpoison
    if f == 3 : field [ y ] [ x ] = 2
    elif f == 0 :
      field [ cell.cords [ 0 ]] [ cell.cords [ 1 ]] = 0
      cell.cords = [ y, x ]
      field [ y ] [ x ] = 1
  elif code_kind == 3 : # spend energy
    if f == 1 :
      for i in cells :
        if i.cords == [ y, x ] :
          cell.energy -= 10
          i.energy += 10
          break

# setting up first cell

cells.append ( Cell ( ))

# creating display

print ( "\x1b[?25l", end = "" )

def display ( ) :
  print ( "\x1b[1;1H( WORKING )" )
  if MAKE_DISPLAY_VIDEO or SHOW_DISPLAY :
    frame = [ ]
    for i in range ( len ( field )) :
      frame_row = [ ]
      for j in range ( len ( field [ i ])) :
        f = field [ i ] [ j ]
        # choose colored cell for graphics
        graphic = "--"
        if f == 0 : # water
          if ( i <= LIGHT_HEIGHT ) :
            graphic = "\x1b[38;2;40;40;255m" # light
            frame_row.append ( [ 200, 200, 120 ])
          else :
            graphic = "\x1b[38;2;0;0;200m" # shadow
            frame_row.append ( [ 120, 120, 60 ])
        elif f == 1 : # cell
          for k in cells :
            if k.cords == [ i, j ] :
              if k.kind == 0 : # fotosynth
                graphic = "\x1b[38;2;0;255;0m"
                frame_row.append ( [ 80, 180, 80 ])
              elif k.kind == 1 : # organics
                graphic = "\x1b[38;2;255;200;0m"
                frame_row.append ( [ 70, 200, 200 ])
              elif k.kind == 2 : # carnivorous
                graphic = "\x1b[38;2;255;0;0m"
                frame_row.append ( [ 20, 20, 120 ])
              break
        elif f == 2 : # food
          graphic = "\x1b[38;2;100;100;100m"
          frame_row.append ( [ 150, 150, 150 ])
        elif f == 3 : # posion
          graphic = "\x1b[38;2;200;0;255m"
          frame_row.append ( [ 250, 50, 250 ])
        if SHOW_DISPLAY : print ( graphic + "@@", end = "" )
      frame.append ( frame_row )
      if SHOW_DISPLAY : print ( )
  if MAKE_DISPLAY_VIDEO :
    npframe = cv2.resize ( np ( frame, dtype = uint8 ), dim, interpolation = cv2.INTER_AREA )
    video.write ( npframe )
  if SHOW_STAT or MAKE_DISPLAY_VIDEO or MAKE_STAT_VIDEO : print ( "\x1b[0m\x1b[J" )
  if MAKE_DISPLAY_VIDEO :
    print ( "Display video\n- size :", round ( Path ( DISPLAY_VIDEO_NAME ).stat ( ).st_size / 1000000, 2 ), "MB\n- duration :", cycle // 120, "s" )
  if MAKE_STAT_VIDEO :
    print ( "Statistics video\n- size :", round ( Path ( STAT_VIDEO_NAME ).stat ( ).st_size / 1000000, 2 ), "MB\n- duration :", cycle // 120, "s" )
  if SHOW_STAT or MAKE_STAT_VIDEO :
    print ( "\nLife cycle : ", cycle )
    print ( "Amount of cells : ", len ( cells ))
    age = [ 0 ]
    for i in cells : age.append ( i.age )
    print ( "\nLongest living cell\n- Age : ", max ( age ))
    gen_s = [ ]
    kind = 0
    for i in cells :
      if i.age == max ( age ) :
        gen_s = i.gen_seq
        kind = i.kind
        break
    print ( "- Kind :", kind )
    print ( "- Agorithm :" )
    print ( "  ", gen_s )
    amount = [ 0, 0, 0 ]
    for i in [ 0, 1, 2 ] :
      for j in cells :
        if j.kind == i :
          amount [ i ] += 1
      print ( i, "- Amount :", amount [ i ])
    gray = 0
    pink = 0
    for i in range ( len ( field )) :
      for j in range ( len ( field [ i ])) :
        f = field [ i ] [ j ]
        if f == 2 : gray += 1
        elif f == 3 : pink += 1
    print ( "food - Amount :", gray )
    print ( "posion - Amount :", pink )
    if MAKE_STAT_VIDEO :
      for i in range ( PER [ 0 ]) :
        new = [ 0, 0, 0 ]
        for j in range ( PER [ 1 ]) [ : : -1 ] :
          new, frame_stat [ i ] [ j ] = frame_stat [ i ] [ j ], new
      if pink : frame_stat [ -1 - int ( pink / ( FIELD_SIZE [ 0 ] * FIELD_SIZE [ 1 ]) * PER [ 0 ])] [ -1 ] = [ 250, 50, 250 ]
      if gray : frame_stat [ -1 - int ( gray / ( FIELD_SIZE [ 0 ] * FIELD_SIZE [ 1 ]) * PER [ 0 ])] [ -1 ] = [ 150, 150, 150 ]
      if amount [ 0 ] : frame_stat [ -1 - int ( amount [ 0 ] / ( FIELD_SIZE [ 0 ] * FIELD_SIZE [ 1 ]) * PER [ 0 ])] [ -1 ] = [ 80, 180, 80 ]
      if amount [ 1 ] : frame_stat [ -1 - int ( amount [ 1 ] / ( FIELD_SIZE [ 0 ] * FIELD_SIZE [ 1 ]) * PER [ 0 ])] [ -1 ] = [ 70, 200, 200 ]
      if amount [ 2 ] : frame_stat [ -1 - int ( amount [ 2 ] / ( FIELD_SIZE [ 0 ] * FIELD_SIZE [ 1 ]) * PER [ 0 ])] [ -1 ] = [ 20, 20, 120 ]
      npframe = cv2.resize ( np ( frame_stat, dtype = uint8 ), dim_stat, interpolation = cv2.INTER_AREA )
      video_stat.write ( npframe )

def clean ( ) :
  print ( "\x1b[?25h" )
  display ( )
  if MAKE_DISPLAY_VIDEO : video.release ( )
  if MAKE_STAT_VIDEO : video_stat.release ( )
  print ( "( END )" )
  exit ( )


if s ( ) == "Windows" : system ( "cls" )
else : system ( "clear" )

# life begins here

cycle = 0

try :
  while True :
    dead = [ ]
    for i in range ( len ( cells )) :
      x = cells [ i ].exec_pl
      gen_code = cells [ i ].gen_seq [ x ]
      code ( gen_code, cells [ i ] )
      cells [ i ].energy = min ( 100, cells [ i ].energy )
      if ( cells [ i ].energy <= 0 ) : # dead
        dead.append ( i )
      cells [ i ].age += 1

    for i in dead [ : : -1 ] :
        y, x = cells [ i ].cords
        if cells [ i ].killed or cells [ i ].energy < -15 : field [ y ] [ x ] = 0
        else : field [ y ] [ x ] = 2
        cells.pop ( i )

    cycle += 1

    if not ( cycle % GRAVITY_CYCLE ) :
      l = len ( field ) - 1
      for i in range ( len ( field [ l ])) :
        if not ( field [ l ] [ i ] == 1 ) :
          field [ l ] [ i ] = 0
      for i in range ( l ) [ : : -1 ] :
        for j in range ( len ( field [ i ])) :
          if field [ i + 1 ] [ j ] == 0 and not field [ i ] [ j ] == 1 :
            field [ i + 1 ] [ j ] = field [ i ] [ j ]
            field [ i ] [ j ] = 0
      if not randrange ( POISON_CHANCE ) :
        y = randrange ( l )
        x = randrange ( len ( field [ 0 ]))
        if ( field [ y ] [ x ] == 0 ) :
          field [ y ] [ x ] = 3
    if not len ( cells ) : clean ( )
    display ( )
except :
  clean ( )
