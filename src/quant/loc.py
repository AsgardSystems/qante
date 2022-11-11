from .extracterror import handle_error

# class representing interval: [fr, to)
class Loc:
    def __init__(self, fr, to, offset=0):
        if fr <= to:
            # when fr == to, the interval is pointing to an empty string
            # useful to denote empty lines
            self.intrval = (fr, to) 
            self.offset = offset
        else:
            fmt = "ERROR: invalid interval {} ({}, {})"
            print(fmt.format(offset, fr, to))
            raise Exception
    def start(self):
        return self.intrval[0]
    def end(self):
        return self.intrval[1]
    def order(self):
        return (self.start(), self.end(), self.offset)
    def txt_order(self):
        return (self.offset+self.start(), self.offset+self.end())
    def length(self):
        return (self.end() - self.start())
#------------------operations on intervals--------------------------
def merge(loc1, loc2):
    # merge overlapping intervals into one.
    # set offset of new interval to zero if input intervals have different
    # offsets
    s1, e1 = loc1.intrval
    s2, e2 = loc2.intrval
    offset1 = loc1.offset
    offset2 = loc2.offset
    if offset1 == offset2:
        offset = offset1
    else:
        fmt = "locations {}{}, {}{} can't be merged"
        msg= fmt.format(loc1.offset, loc1.intrval, loc2.offset, \
                         loc2.intrval)
        handle_error(110201, msg)
    return Loc(min(s1, s2), max(e1, e2), offset)
def expand(loc):
   """
      loc: a possibly relative location (any offset)
      translates <loc> into its corresponding absolute location (offset = 0
      returns absolute location
   """
   offset = loc.offset
   start = loc.start() + offset
   end = loc.end() + offset
   return Loc(start, end)
    
