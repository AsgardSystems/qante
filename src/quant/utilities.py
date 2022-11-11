import sys
import regex as re

##sys.path.append('/Users/mescobar/home/Professional/Business/py/tagger/src')

from .extracterror import handle_error
from .loc import Loc, expand
from .loctuple import subinterval, first, seq_meets, closed_span
from .loctuple import seq_before, intersects, before
from .loclist import  merge_list
from .loctuplelist import groupby
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
   """
   Parameters
   ----------
   in_txt:   text to get column from
   string :  string in column
   
   Returns
   -------
   text locations of column in <inTxt> that contains <string> 
   
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
   """
       Parameters
       ----------
       llist:   list of locations
       Returns
       -------
       create a list of lists from <llist>
       each inner list consists of locations that intersect with at least
       one other location in that list
       ex: llist = [o1,(1,2), o2,(1,3), o3,(4,5), o4,(4,10)]
           result = [ [o1,(1,2), o2,(1,3)],  [o3,(4,5), o4,(4,10)]]
       inner lists are sorted by intrval
       this method ignores the offsets of intervals
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

"""         
def align_cols(cols, categories):

   Parameters
   ----------
   cols : list of columns where each column is a list of locations
          locations are absolute (offset = 0)
   categories : list of categories where each category is a list of locations
                locations are absolute (offset = 0)
   Returns
   -------
   list of columns where each column is a list of absolute locations
  
   this function fixes misalignments between header columns and content columns
   for example, consider the following table with the corresponding <cols>
      header1     header2     header3
      f1      f2          f3
      f4      f5          f6
      cols = [[loc(header1),loc(f1),loc(f4)], 
              [loc(f2),loc(f5)], 
              [loc(header2)], 
              [loc(f3), loc(f6)], 
              [loc(header3)]]
      categories = [ [loc(header1),loc(header2),loc(header3)], 
                     [loc(f1), ..., loc(f6)] ]  
      where loc(f1) denotes the location of f1
   the result would be:
      [[loc(header1),loc(f1),loc(f4)], 
       [loc(header2),loc(f2),loc(f5)], 
       [loc(header3), loc(f3), loc(f6)]]  


   cat_cols = categorize(cols, categories)
   ncols = len(cols)
   # remove empty clusters
   cat_colsWE = [[ccluster for ccluster in catcluster if len(ccluster)>0] \
                for catcluster in cat_cols]
   # compute number of columns in each category
   ncat_cols = [ len([len(ccluster) for ccluster in catcluster])\
               for catcluster in cat_colsWE] 
   if min(ncat_cols) == max(ncat_cols) and min(ncat_cols) != ncols:
      # misaligned header and content columns
      result = []
      for c in range(len(cat_colsWE[0])):
         newcol = []
         for r in range(len(categories)):
            newcol = newcol + cat_colsWE[r][c]
         result.append(sorted(newcol, key=lambda x:x.txt_order()))
      return result
   else:
      return cols
"""  

def get_list_span(locs):
    """
        locs : list of locations
        returns the span of the intervals in <locs>, offsets ignored
    """
    if len(locs) == 0: return None
    start = locs[0].start()
    end = locs[0].end()
    for loc in locs[1:]:
        start = min(start, loc.start())
        end = max(end, loc.end())
    return Loc(start, end)

