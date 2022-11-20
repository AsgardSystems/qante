"""Module with common regular expressions and useful functions:

Regular Expressions:
   LINE
   INT
   DECIMAL
   FIELD
   altFIELD
   PAGE
Functions:   
   get_column(string, string) -> Loc list
   cluster(Loc list) -> List of Loc lists
   get_list_span(Loc list) -> Loc
"""

##sys.path.append('/Users/mescobar/home/Professional/Business/py/tagger/src')

from .extracterror import handle_error
from .loc import Loc, expand
from .loctuple import subinterval
from .loctuple import intersects
from .tagger import Tagger, lit

#-------------------- regular expressions --------------------
NEWPAGE = chr(12).encode('ascii')     # new page character as a byte
NEWLINE = b'\n'
PDEL = '($|^|{})'.format(chr(12))     # page delimiter
PCONT = '[^{}]*'.format(chr(12))      # page content
PAGE = '('+PCONT+')' + PDEL
LCONT = '[^\n^{}]*'.format(chr(12))   # line content
LDEL = '(\n|$|^|{})'.format(chr(12))  # line delimiter
LINE = '('+LCONT+')' +LDEL            # line enclosed by line separators
WDEL = '(\n|^|$|{}| )'.format(chr(12))# word delimiter
WORD = '[^\n^{}^ ]+'.format(chr(12))  # word
FIELD = WDEL + '((' + WORD + ' )*' + WORD + ')' # field
DECIMAL = '[0-9,]+(\.[0-9]*){0,1}'  # decimal number with commas
INT = '[0-9,]+'
altFIELD = WDEL + '(' + WORD + ')'            # alternative field
#-------------------- literals ---------------------

def get_column(in_txt, string):
   """Get column in in_text that contains string
   
   Parameters:
      in_txt (string) --  text to get column from
      string (string) --  string in column
   
   Returns text locations of column in in_txt that contains <string>    
   """
   tagged = Tagger(in_txt)
   tagged.tagRE('#FIELD', FIELD, 2, True)
   tagged.tagRE('#LINE', LINE, 1)
   locs = tagged.project('#FIELD', '#LINE')
   tagged.tag_list('#pFIELD', locs)
   tagged.tag_list('#REF', tagged.get_locs(lit(string)))
   cols = cluster(tagged.get_locs('#pFIELD'))
   abs_cols = [list(map(expand, column)) for column in cols] 
   tagged.tag_lists('#COL', abs_cols)
   ncols = len(abs_cols)
   res = []
   for c in range(ncols):
      pair_list = tagged.select(subinterval, ['#REF', '#COL_{}'.format(c)])
      if len(pair_list) > 0:
         res.append(c)
   if len(res) != 1:
      msg = "There is more than one column with text {}".format(string)
      handle_error(110501, msg)
   return (abs_cols[res[0]])

def cluster(llist):
   """Clusters locations in llist into intersecting locations
   
   Parameters:
      llist (Loc list) -- locations to cluster
   
   It creates a list of clusters from llists, where each cluster consists of 
   locations that intersect with at least one other location in that cluster.
   ex: llist = [o1,(1,2), o2,(1,3), o3,(4,5), o4,(4,10)]
       result = [ [o1,(1,2), o2,(1,3)],  [o3,(4,5), o4,(4,10)]]
   Locations in clusters are sorted by (start, end)
   This function ignores the offsets of intervals
   It returns the list of clusters
   """
   clusters = []
   if len(llist) == 0: return clusters
   curr = [llist[0]]
   lo = llist[0].start()
   hi = llist[0].end()
   for t in llist[1:]:
       if intersects([Loc(lo,hi), t]):
           lo = min(lo, t.start())
           hi = max(hi, t.end())
           curr.append(t)
       else:
           clusters.append(curr)
           curr = [t]
           lo = t.start()
           hi = t.end()
   clusters.append(curr)
   return clusters

def categorize(clusters, categories ):
   """
   Parameters
   ----------
   clusters :  a list of clusters (locations lists)
               each cluster is sorted by txt_order()
               clusters = [ cluster_1, .... , cluster_n ] where
               cluster_i = [loc_1, ...., loc_o]
   categories : a list of categories (locations lists)
                each category is sorted by txt_order()
                categories = [ category_1, ... , category_m ]
                category_j = [loc_1, ..., loc_l]

   Returns
   -------
   a list of categorized clusters, one for each category:
      result = [ categorized_clusters_1, ...., categorized_clusters_m]
   each categorized clusters is a list of clusters:
      categorized_clusters_i = [ ccluster_1, ..., ccluster_p]
      ccluster_j = [loc_1, ...., loc_q]
      each loc_k in ccluster_j is a location in cluster_j that is also
      in category_i
      each ccluster_j is sorted by txt_order()

   """
   result = []
   for category in categories:
      categorized_clusters = []
      for cluster in clusters:
         cat = 0
         clu = 0
         ccluster = []
         while cat < len(category) and clu < len(cluster):
            if cluster[clu].txt_order() == category[cat].txt_order():
               ccluster.append(cluster[clu])
               clu += 1
               cat += 1
            elif cluster[clu].txt_order() < category[cat].txt_order():
               clu += 1
            else:
               cat += 1
         categorized_clusters.append(ccluster)
      result.append(categorized_clusters)
   return result
 

def get_list_span(locs):
   """Gets span of all locations in loc
   
   Parameters:
      locs (Loc list) -- locations to get the span from
      
   It returns the span of the intervals in locs, offsets ignored
   """
   if len(locs) == 0: return None
   start = locs[0].start()
   end = locs[0].end()
   for loc in locs[1:]:
      start = min(start, loc.start())
      end = max(end, loc.end())
   return Loc(start, end)

