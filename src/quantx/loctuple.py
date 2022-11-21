"""Module that implements relations and functions on location tuples

Allen's relations:
   before(Loc tuple) -> boolean
   meets(Loc tuple) -> boolean
   overlaps(Loc tuple) -> boolean
   starts(Loc tuple) -> boolean
   during(Loc tuple) -> boolean
   finishes(Loc tuple) -> boolean
   equal(Loc tuple) -> boolean
Other relations:
   seq_meets(Loc tuple) -> boolean
   seq_before(Loc tuple) -> boolean
   seq_before_meets(Loc tuple) -> boolean
   subinterval(Loc tuple) -> boolean
   intersects(Loc tuple) -> boolean
   dijoint(Loc tuple) -> boolean
   
This module also defines functions that map location tuples into a location or a tuple location
   closed_span(Loc tuple) -> Loc
   open_right_span(Loc tuple) -> Loc
   open_left_span(Loc tuple) -> Loc
   open_span(Loc tuple) -> Loc
   last(Loc tuple) -> Loc
   first(Loc tuple) -> Loc
   in_between(Loc tuple) -> Loc tuple

"""
from .loc import Loc
from .extracterror import handle_error

# ---------------allen's interval relations------------------------
# each pair consists of two locations, 
# each location consists of an offset and an interval
# allen's relations are applied to the intervals
def before(pair):
   """Allen's before relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location appears before second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "before requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return e1 < s2
def meets(pair):
   """Allen's meets relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location meets second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "meets requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return e1 == s2 
def overlaps(pair):
   """Allen's overlaps relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location overlaps second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "overlaps requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return s1 < s2 and s2 < e1 and e1 < e2
def starts(pair):
   """Allen's starts relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location starts second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "starts requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return s1 == s2 and e1 < e2 
def during(pair):
   """Allen's during relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first occurs during second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "during requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return s2 < s1 and e1 < e2
def finishes(pair):
   """Allen's finishes relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location finishes second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "finishes requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return s2 < s1 and e1 == e2
def equal(pair):
   """Allen's equal relation
   
   Parameters:
      pair (Loc tuple) -- tuple with two locations
   
   Locations are represented by offset, start, end. This function returns True
   if first location is equal to second location by considering start and
   end only, disregarding their offset. Otherwise, it returns False

   """
   if len(pair) != 2:
      handle_error(110306, "equal requires a 2-tuple as input parameter")
   s1, e1 = pair[0].intrval
   s2, e2 = pair[1].intrval
   return s1 == s2 and e1 == e2 
# --------------additional interval relations-------------------
def seq_meets(ltuple):
   """This relation extends meets to more than two arguments
      
      Parameters:
         ltuple (Loc tuple): tuple of locations
      
      If ltuple = (l1, ..., ln), it returns meets((l1,l2)) and meets((l2,l3))
      and ... and meets((ln-1,ln))
      
   """
   for i in range(len(ltuple)-1):
       if not meets( [ltuple[i], ltuple[i+1]] ):
           return False
   return True
def seq_before(ltuple):
   """This relation extends before to more than two arguments
      
      Parameters:
         ltuple (Loc tuple): tuple of locations
      
      If ltuple = (l1, ..., ln), it returns before((l1,l2)) and before((l2,l3))
      and ... and before((ln-1,ln))
   """
   for i in range(len(ltuple)-1):
       if not before( [ltuple[i], ltuple[i+1]] ):
           return False
   return True
def seq_before_meets(ltuple):
   """This relation combines before and meets with a disjunction
   
   Parameters:
      ltuple (Loc tuple): tuple of locations
      
   If ltuple = (loc1, ..., locn), it returns (before((l1,l2)) or meets((l1,l2)))
   and (before((l2,l3)) or meets((l2,l3))) and ... and (before((ln-1,ln)) or meets((ln-1,ln)))

   """
   for i in range(len(ltuple)-1):
       if not before( [ltuple[i], ltuple[i+1]] ) and not meets( [ltuple[i], ltuple[i+1]] ):
           return False
   return True
def subinterval(pair):
   """This relation tests whether first interval is a subset or equal to second interval
   
   Parameters:
      pair (Loc tuple): a pair of locations
      
   Locations are represented by offset, start, end. This function returns True
   if interval of first location intersects interval of second location.
   Intervals are determined by start and end of locations, disregarding offset. 
   """
   if len(pair) != 2:
      handle_error(110306, "subinterval requires a 2-tuple as input parameter")
   return starts(pair) or during(pair) or finishes(pair) or equal(pair)
def intersects(pair): 
   """This relation tests whether first interval intersects with second interval
   
   Parameters:
      pair (Loc tuple): a pair of locations
   
   Locations are represented by offset, start, end. This function returns True
   if interval of first location intersects interval of second location.
   Intervals are determined by start and end of locations, disregarding offset. 
   """
   if len(pair) != 2:
      handle_error(110306, "intersects requires a 2-tuple as input parameter")
   rpair = (pair[1], pair[0]) # reverse pair
   ret = overlaps(pair) or starts(pair) or during(pair) or finishes(pair) or \
         overlaps(rpair) or starts(rpair) or during(rpair) or finishes(rpair) \
         or equal(pair)
   return ret
def disjoint(pair):
   """This relation tests whether first interval is dijoint with second interval
   
   Parameters:
      pair (Loc tuple): a pair of locations
   
   Locations are represented by offset, start, end. This function returns True
   if interval of first location does not intersect interval of second location.
   Intervals are determined by start and end of locations, disregarding offset. 
   """
   if len(pair) != 2:
      handle_error(110306, "disjoint requires a 2-tuple as input parameter")
   return not intersects(pair)
def intersect_len(pair):
   s1,e1 = pair[0].intrval
   s2,e2 = pair[1].intrval
   if s1 < s2 and s2 < e1:
      return min(e1,e2)-s2
   elif s2 < s1 and s1 < e2:
      return min(e1,e2)-s1
   elif s1 == s2:
      return min(e2-s2, e1-s1)
   else:
      return 0 
def begins(pair):
   return starts(pair) or equal(pair)
def closed_span(pair):
   """Returns a location that spans from beginning of first location to end of second location
   
   Parameters:
      pair (Loc tuple) -- pair of locations
       
   It raises an exception if two locations in pair have different offset
   """
   if len(pair) != 2:
      handle_error(110306, "closed_span requires a 2-tuple as input parameter")
   offset = pair[0].offset
   if offset != pair[1].offset:   
      msg = "Function closed_span requires locations to have same offset"
      handle_error(110301, msg)
   start = pair[0].start()
   end = pair[1].end()
   
   return Loc(start, end, offset)
def last(ltuple):
   """Returns last location in ltuple
   
   Parameters:
      ltuple (Loc tuple) -- tuple of locations
   """
   n = len(ltuple)
   return ltuple[n-1]
def first(ltuple):
   """Returns first location in ltuple 
   
   Parameters:
      ltuple (Loc tuple) -- tuple of locations
   """
   return ltuple[0]
def open_right_span(pair):
   """Returns a location that spans from start of first location to start of second location
      
      Parameters:
         pair (Loc tuple) -- pair of locations
          
      It raises an exception if two locations in pair have different offset
   """
   if len(pair) != 2:
      handle_error(110306, "open_right_span requires a 2-tuple as input parameter")
   offset = pair[0].offset  
   if pair[1].offset != offset:
      msg = "Function open_right_span requires locations to have same offset"
      handle_error(110302, msg)
   fr = pair[0].start()
   to = pair[1].start()
   return Loc(fr,to,offset)
def open_left_span(pair):
   """Returns a location that spans from end of first location to end of second location
      
      Parameters:
         pair (Loc tuple) -- pair of locations
          
      It raises an exception if two locations in pair have different offset
   """
   if len(pair) != 2:
      handle_error(110306, "open_left_span requires a 2-tuple as input parameter")
   offset = pair[0].offset
   if pair[1].offset != offset:
      msg = "Function open_right_span requires locations to have same offset"
      handle_error(110303, msg)
   fr = pair[0].end()
   to = pair[1].end()
   return Loc(fr,to,offset)
def open_span(pair):
   """Returns a location that spans from end of first location to start of second location
      
      Parameters:
         pair (Loc tuple) -- pair of locations
          
      It raises an exception if two locations in pair have different offset
   """
   if len(pair) != 2:
      handle_error(110306, "open_span requires a 2-tuple as input parameter")
   offset = pair[0].offset
   if pair[1].offset != offset:
      msg = "Function open_span requires locations to have same offset"
      handle_error(110304, msg)
   fr = pair[0].end()
   to = pair[1].start()
   return Loc(fr,to,offset)
def in_between(ltuple):
   """Returns the locations between the locations in ltuple
   
   Parameters:
      ltuple (Loc tuple) -- tuple of locations (loc1, loc2, ..., locn)
      
   Returns tuple of locations: (rloc1, rloc2, ..., rlocn-1) where rloci is the 
   location between loci and loci+1
   It raises an exception if locations in tuple do not have the same offset

   """
   offset = ltuple[0].offset
   fr = ltuple[0].end()
   res = []
   for loc in ltuple[1:]:
      if loc.offset != offset:
         msg = "Function in_between requires locations to have same offset"
         handle_error(110305, msg)
      to = loc.start()
      res.append(Loc(fr,to,offset))
      fr = loc.end()
   return tuple(res)
    
