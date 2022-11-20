"""Module that implements functions on location lists

merge_list(Loc list, boolean) -> Loc list
shortest(Loc list) -> Loc list
longest(Loc list) -> Loc list
minus(Loc list, Loc list) -> Loc list
rm_intervals(Loc list, Loc list) -> Loc list
"""
from .loctuple import intersects, subinterval, meets, overlaps, during, starts
from .loctuple import finishes, equal
from .loc import merge, Loc
from .extracterror import handle_error

def merge_list(llist, merge_contiguous=False):
   """Returns the result of merging intersecting/contiguous locations in llist
   
   Parameters:
      llist (Loc list) -- list of locations to be merged
      merge_contiguous (boolean) -- whether contiguous locations would be merged
                                    in addition to intersecting location (default False)
    
   It create a new list by merging intersecting locations in llist. If merge_contiguous 
   is True, it also merges contiguous intervals. Intersecting/contiguous locations must 
   have same offset to merge   
   """
   if len(llist) == 0: return llist 
   slist = sorted(llist, key=lambda x: x.order())
   tomerge = slist[0]
   # merge overlapping intervals
   rem = []
   for intrval in slist[1:]:
       if intersects([tomerge, intrval]) and tomerge.offset == intrval.offset:
          tomerge = merge(tomerge, intrval)
       elif merge_contiguous and meets([tomerge, intrval]):
          tomerge = merge(tomerge, intrval)
       else:
          rem.append(tomerge)
          tomerge = intrval
   rem.append(tomerge)
   return rem
def shortest(llist):
    """Returns the subset of llist with the shortest locations
    
    Parameters:
       llist (Loc list): list of locations to get result from
       
    It returns the subset of locations in llist resulting from removing locations 
    that are supersets of other locations in llist
    """
    if len(llist) == 0: return llist
    slist = sorted(llist, key=lambda x: x.order())
    nlist = [slist[0]]
    for elt in slist[1:]:
        if elt.start() != nlist[len(nlist)-1].start():
            nlist.append(elt)
    i = 0
    res = []
    while i < len(nlist):
        j = i+1
        include = True
        while j < len(nlist):
            if subinterval([nlist[j], nlist[i]]):
                include = False
                break
            j += 1
        if include:
            res.append(nlist[i])
        i += 1
    return res
def longest(llist):
   """Returns the subset of llist with the longest locations
   
   Parameters:
      llist (Loc list): list of locations to get result from
      
   It returns the subset of locations in llist resulting from removing locations 
   that are subsets of other locations in llist
   """
   if len(llist) == 0: return llist
   slist = sorted(llist, key=lambda x: x.order(), reverse=True)
   nlist = [slist[0]]
   for elt in slist[1:]:
      if elt.start() != nlist[-1].start():
         nlist.append(elt)
   i = 0
   res = []
   while i < len(nlist):
      j = i+1
      include = True
      while j < len(nlist):
         if subinterval([nlist[i], nlist[j]]):
            include = False
            break
         j += 1
      if include:
         res.append(nlist[i])
      i += 1
   return sorted(res, key=lambda x: x.order())
def binary_search(llist, trg):
   """
      search <trg> in <llist>
      <trg> is an object of type Loc and <llist> is a
      list of Loc objects
      The order of Loc objects is based on fr, to, offset
      if found, it returns True and index of object that is equal to
      <trg>, otherwise it returns False and index j such that
      llist[j] < trg < llist[j+1] 
   """
   lo = 0
   hi = len(llist)-1
   while lo <= hi:
      mid = int( (lo+hi)/2 )
      if trg.order() == llist[mid].order():
         return (True, mid)
      elif trg.order() < llist[mid].order():
         hi = mid-1
      else:
         lo = mid+1
   return (False, hi)
def minus(llist1, llist2):
    """Returns locations in llist1 that are not in llist2
    
    Parameters:
       llist1 (Loc list) -- locations where result locations come from
       llist2 (Loc list) -- locations to be discarded from result
    """
    if len(llist1) == 0 or len(llist2) == 0:
       return llist1
    res = []
    slist = sorted(llist2, key=lambda x: x.order())
    for loc in llist1:
        isIn, indx = binary_search(slist, loc) 
        if isIn:
            continue
        res.append(loc)
    return res 
def rm_intervals(llist1, llist2):
   """Remove locations in llist2 from llist1
   
   Parameters:
      llist1 (Loc list)
      llist2 (Loc list)
      
   It removes locations in llist2 from llist1. if lx is in llist1 and ly is in llist2
   and lx intersect with ly, remove the intersecting part from lx
   """
   mlist1 = merge_list(llist1)
   mlist2 = merge_list(llist2)
   j = 0
   result = []
   while len(mlist1) != 0:
      loc1 = mlist1.pop(0) 
      (s1, e1, o1) = loc1.order()
      # locate first elt in mlist2 that intersects with loc1
      found = False
      i = j
      while i < len(mlist2):
         loc2 = mlist2[i]
         if intersects([loc1, loc2]):
            #or meets([loc2,loc1]) or before([loc2,loc1]): 
            j = i
            found = True
            break
         i += 1
      if not found:
         result.append(loc1)
         continue
      # remove from loc1 intersecting intervals from mlist2      
      include = True
      for k in range(j,len(mlist2)):
         loc2 = mlist2[k]
         if not intersects([loc1, loc2]): break
         (s1, e1, o1) = loc1.order()
         (s2, e2, o2) = loc2.order()
         if o1 != o2:
            handle_error(110901, 'offsets in rm_intervals parameters do not match')
         if overlaps([loc2,loc1]) or starts([loc2,loc1]):
            loc1 = Loc(e2,e1,o1) 
         elif during([loc2, loc1]):
            loc1 = Loc(s1,s2,o1)
            mlist1.insert(0,Loc(e2,e1,o1))
         elif overlaps([loc1,loc2]) or finishes([loc2,loc1]):
            loc1 = Loc(s1, s2,o1)
         elif equal([loc1, loc2]) or during([loc1, loc2]) or starts([loc1, loc2]) \
              or finishes([loc1,loc2]):
            # excludes loc1
            include = False
            break 
      if include:
         result.append(loc1)
   return result
def main():
   l1 = [(1,4), (7,18), (18,26), (30,40)]
   l2 = [(2,3), (7,10), (11,12), (16,18), (25,35)]
   mlist1 = []
   for (s,e) in l1:
      mlist1.append(Loc(s,e))
   mlist2 = []
   for (s,e) in l2:
      mlist2.append(Loc(s,e))
   result = rm_intervals(mlist1, mlist2)
   print('-----------')
   for loc in result:
      print(loc.order())
if __name__ == "__main__":
   main()
