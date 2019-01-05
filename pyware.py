# Copyright (c) 2018, Ryan Westlund.
# This code is under the BSD 3-Clause license.

import sys,random

class Button(object):
  def __init__(self,window,pos,size,image,color,border_color,str_color='default',nodraw=False):
    self.window=window
    self.pos=pos
    self.size=size
    self.image=image
    self.color=color
    self.border_color=border_color
    if str_color=='default':str_color=border_color
    self.str_color=str_color
    self.__down__=False
    if not nodraw:self.draw()
  def draw(self):
    self.window.fill(self.color,self.pos+self.size)
    if self.down:
      pygame.draw.line(self.window,self.border_color,[self.pos[0],self.pos[1]],[self.pos[0],self.pos[1]+self.size[1]-1])
      pygame.draw.line(self.window,self.border_color,[self.pos[0],self.pos[1]],[self.pos[0]+self.size[0]-1,self.pos[1]])
    else:
      pygame.draw.line(self.window,self.border_color,[self.pos[0],self.pos[1]+self.size[1]],[self.pos[0]+self.size[0],self.pos[1]+self.size[1]])
      pygame.draw.line(self.window,self.border_color,[self.pos[0]+self.size[0],self.pos[1]],[self.pos[0]+self.size[0],self.pos[1]+self.size[1]])
    if self.image.__class__==str:write(self.window,[self.pos[0]+2,self.pos[1]+2],self.image,self.str_color,end=self.pos[0]+self.size[0])
    if self.image.__class__==dict:
      self.center=[self.pos[0]+int(self.size[0]/2),self.pos[1]+int(self.size[1]/2)]
      for pixel in self.image:self.window.set_at([self.center[0]+pixel[0],self.center[1]+pixel[1]],self.image[pixel])
  def test(self,pos):
    if pos[0]>=self.pos[0] and pos[0]<=self.pos[0]+self.size[0] and pos[1]>=self.pos[1] and pos[1]<=self.pos[1]+self.size[1]:return True
    return False
  @property
  def down(self):
    return self.__down__
  @down.setter
  def down(self,val):
    self.__down__=val
    self.draw()

class File(object):
  def __init__(self,filename):
    self.file=open(filename,'a+')
    self.dict={}
    self.file.seek(0)
    line=self.file.readline()
    while line:
      colonpoint=line.find(':')
      key=line[:colonpoint]
      value=line[colonpoint+1:]
      if value[-1]=='\n':value=value[:-1]
      self.dict[key]=value
      line=self.file.readline()
  def read(self,key):
    def get_type(data):
      if data[0] in {"'",'"'}:return 'str'
      if data[0] in {'0','1','2','3','4','5','6','7','8','9','.','-'}:return 'num'
      if data[0]=='[':return 'list'
      if data[0]=='{':return 'dict'
      if data[0]=='(':return 'tup'
      print('type error with:',data);sys.exit()
    def scan_str(data):
      string=''
      length=1
      init=data[0]
      data=data[1:]
      backslashed=False
      for character in data:
        length+=1
        if backslashed:
          backslashed=False
          if character=='\\':string+='\\'
          if character=='n':string+='\n'
          if character=='t':string+='\t'
          if character=='v':string+='\v'
          if character=='r':string+='\r'
          continue
        if character=='\\':backslashed=True;continue
        if character==init:break
        string+=character
        backslashed=False
      return string,length
    def scan_num(data):
      string=''
      length=0
      for character in data:
        if character in {'1','2','3','4','5','6','7','8','9','0','.','-'}:length+=1;string+=character
        else:break
      try:return int(string),length
      except:return float(string),length
    def scan_list(data):
      seq=[]
      length=1
      while True:
        character=data[length]
        if character in {"'",'"'}:
          seg=scan_str(data[length:])
          seq+=[seg[0]]
          length+=seg[1]
        elif character in {'1','2','3','4','5','6','7','8','9','0','.','-'}:
          seg=scan_num(data[length:])
          seq+=[seg[0]]
          length+=seg[1]
        elif character=='[':
          seg=scan_list(data[length:])
          seq+=[seg[0]]
          length+=seg[1]
        elif character=='{':
          seg=scan_dict(data[length:])
          seq+=[seg[0]]
          length+=seg[1]
        elif character=='(':
          seg=scan_tup(data[length:])
          seq+=[seg[0]]
          length+=seg[1]
        elif character==']':length+=1;break
        elif character in {',',' '}:length+=1
      return seq,length
    def scan_dict(data):
      dictionary={}
      length=1
      while True:
        character=data[length]
        if character in {"'",'"'}:
          element=scan_str(data[length:])
          key=element[0]
          length+=element[1]
        elif character in {'1','2','3','4','5','6','7','8','9','0','.','-'}:
          element=scan_num(data[length:])
          key=element[0]
          length+=element[1]
        elif character=='{':
          element=scan_dict(data[length:])
          key=element[0]
          length+=element[1]
        elif character=='(':
          element=scan_tup(data[length:])
          key=element[0]
          length+=element[1]
        elif character=='}':length+=1;break
        elif character in {',',' '}:length+=1;continue
        length+=1 # this is to account for the colon
        if data[length]==' ':length+=1
        character=data[length]
        if character in {"'",'"'}:
          element=scan_str(data[length:])
          value=element[0]
          length+=element[1]
        elif character in {'1','2','3','4','5','6','7','8','9','0','.','-'}:
          element=scan_num(data[length:])
          value=element[0]
          length+=element[1]
        elif character=='[':
          element=scan_list(data[length:])
          value=element[0]
          length+=element[1]
        elif character=='{':
          element=scan_dict(data[length:])
          value=element[0]
          length+=element[1]
        elif character=='(':
          element=scan_tup(data[length:])
          value=element[0]
          length+=element[1]
        dictionary[key]=value
      return dictionary,length
    def scan_tup(data):
      seq=()
      length=1
      while True:
        character=data[length]
        if character in {"'",'"'}:
          seg=scan_str(data[length:])
          seq+=(seg[0],) # have to put these commas here otherwise the parentheses will be interpreted as simply a precedence specifier and not as a tuple
          length+=seg[1]
        elif character in {'1','2','3','4','5','6','7','8','9','0','.','-'}:
          seg=scan_num(data[length:])
          seq+=(seg[0],)
          length+=seg[1]
        elif character=='[':
          seg=scan_list(data[length:])
          seq+=(seg[0],)
          length+=seg[1]
        elif character=='{':
          seg=scan_dict(data[length:])
          seq+=(seg[0],)
          length+=seg[1]
        elif character=='(':
          seg=scan_tup(data[length:])
          seq+=(seg[0],)
          length+=seg[1]
        elif character==')':length+=1;break
        elif character in {',',' '}:length+=1
      return seq,length

    data=self.dict[key]
    type=get_type(data)
    if type is True:return True
    if type=='str':return scan_str(data)[0]
    if type=='num':return scan_num(data)[0]
    if type=='list':return scan_list(data)[0]
    if type=='dict':return scan_dict(data)[0]
    if type=='tup':return scan_tup(data)[0]
  def set(self,key,value):
     if value.__class__==str:self.dict[key]="'"+value+"'"
     else:self.dict[key]=str(value)
  def delete(self,key):
    del self.dict[key]
  def write(self):
    self.file.seek(0)
    self.file.truncate()
    for key in self.dict:self.file.write(key+':'+self.dict[key]+'\n')
  def close(self):
    self.file.close()

class Bar(object):
  def __init__(self,window,pos,size,fcolor,ecolor,bcolor,max,fill=-1): #fcolor, ecolor, bcolor; fill, empty, and border colors
    self.window=window
    self.pos=pos
    self.size=size
    self.fcolor=fcolor
    self.ecolor=ecolor
    self.bcolor=bcolor
    self.max=max
    if fill<0:fill=0
    self.__fill__=fill
    if self.max==0:self.max=1;self.fill=1
    self.draw()
  def draw(self):
    level=int((self.fill/self.max)*self.size[0])
    pygame.draw.rect(self.window,self.ecolor,(self.pos[0]+level,self.pos[1],self.size[0]-level+1,self.size[1]),0)
    if level>0:pygame.draw.rect(self.window,self.fcolor,(self.pos[0],self.pos[1],level+1,self.size[1]),0)
    pygame.draw.rect(self.window,self.bcolor,(self.pos[0]-1,self.pos[1]-1,self.size[0]+3,self.size[1]+2),1)
  @property
  def fill(self):
    return self.__fill__
  @fill.setter
  def fill(self,level):
    if level>self.max:level=int(str(self.max)[:])
    if level<0:level=0
    self.__fill__=level
    self.draw()

def average(*nums):
  total=0
  for num in nums:total+=num
  return total/len(nums)

def randomize(data):
  new=()
  while data:
    index=random.randint(0,len(data)-1)
    new+=(data[index],)
    del data[index]
  return new

def wait(keys,clock):
  done=False
  key=None
  while not done:
    clock.tick(10)
    for event in pygame.event.get():
      if event.type==pygame.KEYDOWN:
        for key in keys:
          if event.key==key:done=True;key=event.key;break
      elif event.type==pygame.QUIT:sys.exit()
  return key

def between(lowerbound,midpoint,upperbound):
  if midpoint>=lowerbound and midpoint<=upperbound:return True
  return False

def rangebetween(lowerbound,lowerpoint,upperpoint,upperbound):
  if between(lowerbound,lowerpoint,upperbound) and between(lowerbound,upperpoint,upperbound):return True
  return False

def rangeoverlap(lowerbound,lowerpoint,upperpoint,upperbound):
  if between(lowerbound,lowerpoint,upperbound) or between(lowerbound,upperpoint,upperbound) or between(lowerpoint,lowerbound,upperpoint) or between(lowerpoint,upperbound,upperpoint):return True
  return False

