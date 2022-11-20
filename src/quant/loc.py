"""Module that implements location

   merge(Loc, Loc) -> Loc
   expand(Loc) -> Loc
   
   Class Loc methods:
      __init__(int, int, int)
      start() -> int
      end() -> int
      order() -> (int, int, int)
      txt_order() -> (int, int)
      length() -> int
"""
from .extracterror import handle_error

class Loc:
   """Location
   
   Constructor Parameters:
      fr (int) -- start position of interval with respect to offset
      to (int) -- end position of interval with respect to offset
      offset (int) -- position in text (default 0)
   """
   def __init__(self, fr, to, offset=0):
       if fr <= to:
           self.intrval = (fr, to) 
           self.offset = offset
       else:
           fmt = "ERROR: invalid interval {} ({}, {})"
           print(fmt.format(offset, fr, to))
           raise Exception
   def start(self):
      """Returns the start position of location"""
      return self.intrval[0]
   def end(self):
      """Returns the end position of location"""
      return self.intrval[1]
   def order(self):
      """Returns (start position, end position, offset) of location"""
      return (self.start(), self.end(), self.offset)
   def txt_order(self):
      """Returns (start position, end position) of location with respect to beginning of text"""
      return (self.offset+self.start(), self.offset+self.end())
   def length(self):
      """Returns lenght of location"""
      return (self.end() - self.start())
#------------------operations on locations--------------------------
def merge(loc1, loc2):
   """Merge two locations into one
   

   Parameters:
      loc1 (Loc) -- one of the locations to merge
      loc2 (Loc) -- the other location to merge

   Returns a new location that covers both loc1 and loc2
   It raises an exception if loc1 and loc2 do not intersect nor are contiguous
   """
   # merge overlapping intervals into one.
   # set offset of new interval to zero if input intervals have different
   # offsets
   s1, e1 = loc1.intrval
   s2, e2 = loc2.intrval
   if e1 < s2 or e2 < s1:
      handle_error(110202, "Location parameters of merge must intersect or meet")   
   offset1 = loc1.offset
   offset2 = loc2.offset
   if offset1 == offset2:
       offset = offset1
   else:
       fmt = "locations {}{}, {}{} must have same offset to be merged"
       msg= fmt.format(loc1.offset, loc1.intrval, loc2.offset, \
                        loc2.intrval)
       handle_error(110201, msg)
   return Loc(min(s1, s2), max(e1, e2), offset)
def expand(loc):
   """Converts loc to a location with offset zero
   
   Parameters:
      loc (Loc): location to be converted
      
      It translates loc into its corresponding absolute location (offset = 0)
      it returns absolute location
   """
   offset = loc.offset
   start = loc.start() + offset
   end = loc.end() + offset
   return Loc(start, end)
    
