from .loc import Loc
from .extracterror import handle_error

# ---------------allen's interval relations------------------------
# each pair consists of two locations, 
# each location consists of an offset and an interval
# allen's relations are applied to the intervals
def before(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return e1 < s2
def meets(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return e1 == s2 
def overlaps(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return s1 < s2 and s2 < e1 and e1 < e2
def starts(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return s1 == s2 and e1 < e2 
def during(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return s2 < s1 and e1 < e2
def finishes(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return s2 < s1 and e1 == e2
def equal(pair):
    s1, e1 = pair[0].intrval
    s2, e2 = pair[1].intrval
    return s1 == s2 and e1 == e2 
# --------------additional interval relations-------------------
def seq_meets(ltuple, error=0):
    """
        meets with room for error
        <error> indicates the max number of characters between consecutive
        intervals
    """
    for i in range(len(ltuple)-1):
        if not meets( [ltuple[i], ltuple[i+1]] ) and \
           ( not before( [ltuple[i], ltuple[i+1]] ) or \
             ltuple[i+1].start() - ltuple[i].end() > error ):
            return False
    return True
def seq_before(ltuple, distance=None):
    """
        before with limited distance between consecutive intervals
        <before> is the maximum number of chars between consecutive intervals
    """
    for i in range(len(ltuple)-1):
        if not before( [ltuple[i], ltuple[i+1]] ):
            return False
        elif distance != None and \
            ltuple[i+1].start() - ltuple[i].end() > distance:
            return False
    return True
def seq_before_meets(ltuple):
    for i in range(len(ltuple)-1):
        if not before( [ltuple[i], ltuple[i+1]] ) and not meets( [ltuple[i], ltuple[i+1]] ):
            return False
    return True
def subinterval(lpair):
    return starts(lpair) or during(lpair) or finishes(lpair) or equal(lpair)
def intersects(pair): 
    rpair = (pair[1], pair[0]) # reverse pair
    ret = overlaps(pair) or starts(pair) or during(pair) or finishes(pair) or \
          overlaps(rpair) or starts(rpair) or during(rpair) or finishes(rpair) \
          or equal(pair)
    return ret
def disjoint(pair):
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
def closed_span(ltuple):
    """
        combines tuple of locations into a single location consisting of
        the span from first to last location in tuple
        all locations in tuple must have the same offset, otherwise it raises
        an exception
    """
    n = len(ltuple)
    first = ltuple[0]
    last = ltuple[n-1]
    offset = first.offset
    for i in range(1, len(ltuple)):
        if offset != ltuple[i].offset:
           msg = "Function closed_span requires locations to have same offset"
           handle_error(110301, msg)
    start = first.start()
    end = last.end()
    return Loc(start, end, offset)
def last(ltuple):
   """
      returns last location in tuple <ltuple>
   """
   n = len(ltuple)
   return ltuple[n-1]
def first(ltuple):
   """
      returns first location in tuple <ltuple>
   """
   return ltuple[0]
def open_right_span(ltuple):
   """
      combines tuple of locations into a single location consisting of
      the span from first to last location in tuple, excluding the last
      all locations in tuple must have the same offset, otherwise it raises
      an exception
   """
   offset = ltuple[0].offset
   fr = ltuple[0].start()
   for loc in ltuple[1:]:
       if loc.offset != offset:
          msg = "Function open_right_span requires locations to have same offset"
          handle_error(110302, msg)
   to = ltuple[-1].start()
   return Loc(fr,to,offset)
def open_left_span(ltuple):
   """
      combines tuple of locations into a single location consisting of
      the span from first to last location in tuple, excluding the first
      all locations in tuple must have the same offset, otherwise it raises
      an exception
   """
   offset = ltuple[0].offset
   fr = ltuple[0].end()
   for loc in ltuple[1:]:
       if loc.offset != offset:
          msg = "Function open_right_span requires locations to have same offset"
          handle_error(110303, msg)
   to = ltuple[-1].end()
   return Loc(fr,to,offset)
def open_span(ltuple):
   """
      combines tuple of locations into a single location consisting of
      the span from first to last location in tuple, excluding first and last
      all locations in tuple must have the same offset, otherwise it raises
      an exception
   """
   offset = ltuple[0].offset
   fr = ltuple[0].end()
   for loc in ltuple[1:]:
      if loc.offset != offset:
         msg = "Function open_span requires locations to have same offset"
         handle_error(110304, msg)
   to = ltuple[-1].start()
   return Loc(fr,to,offset)
def in_between(ltuple):
   """
   Parameters
   ----------
      ltuple : tuple of locations (loc1, loc2, ..., locn)
   Raises
   ------
      Exception if locations in tuple do not have the same offset
   Returns
   -------
      tuple of locations: (rloc1, rloc2, ..., rlocn-1)
      where rloci is the location between loci and loci+1

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
    
