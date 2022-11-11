"""
   Module that defines a tagged text object and its methods
   
   Class Tagger Methods:
      __init__(string, boolean [optional])
      tagRE(string, string, int, boolean [optional])
      display_matches()
      tag_loc(string, Loc)
      project(string, string) -> Loc list
      tag_list(string. Loc list)
      tag_lists(string, list of Loc lists)
      not_in(Loc list, int pair) -> Loc list
"""
import regex as re

from .extracterror import handle_error
from .loc import Loc, expand
from .loctuple import subinterval
from .loclist import binary_search, merge_list

def lit( str_to_match):
   """
      Returns a literal object for input parameter
   """
   return {'literal': str_to_match}
class Tagger:
   """
      Tagged text: text and mappings from tags to locations in text
      
      Constructor parameters
         text (string):        text to be tagged
         lower_case (boolean): convert text to lower case 
      
      Locations associated with a tag are always sorted by fr,to,offset
   """
   def __init__(self, text, lower_case=True):
      if lower_case:
         self.text = text.lower()
      else:
         self.text = text
      self.spans   = {} # tag --> [ (from, to), ...]
   def tagRE(self, tag, regexp, group=0, overlapped=False):
      """
         Tag strings in text matching regexp with tag
         
         Parameters
            tag (string):         tag
            regexp (string):      regular expression
            group (int):          match group within the regular expression
            overlapped (boolean): whether regular expression matches overlap
         
         Raises an exception if tag already exists
      """
      if tag in self.spans:
         msg = "Tag {} already in. Did not overwrite".format(tag)
         handle_error(110101, msg)
      self.spans[tag] = [Loc(i[0], i[1]) \
                         for i in self._findpatt(regexp,group,overlapped)]
   def _findpatt(self, pattern,group=0,overlapped=False):
      """
         Returns start and end positions of strings in self.text that match <pattern>
      """
      res = []
      for m in re.finditer(pattern, self.text, overlapped=overlapped):
         fr,to = m.span(group)
         res.append(m.span(group))
      return res
   def display_matches(self):
      """ Prints tagged strings with their respective tags"""
      for tag in self.spans:
         print("{}".format(tag))
         for span in self.spans[tag]:
            offset = span.offset
            fr = offset + span.start()
            to = offset + span.end()
            print("match: {}---".format(self.text[fr:to]))
   def tag_loc(self, tag, loc):
      """
         Tag loc  with tag
         
         Parameters
            loc (Loc):    location object
            tag (string): tag
            
         Raises a warning if loc is already tagged with tag
      """
      if tag not in self.spans:
         self.spans[tag] = []
      # binary search on whole interval including offset
      found, indx = binary_search(self.spans[tag],loc)
      if not found:
         self.spans[tag] = self.spans[tag][:indx+1] + [loc] + \
                           self.spans[tag][indx+1:]
      else:
         msg = "Tag {} already has location {}"
         handle_error(210102, msg.format(tag, loc.txt_order()))
   def project(self, tag, ref_tag):
      """
         Converts tag locations to be relative to the beginning of strings tagged as ref_tag
         
         Parameters
            tag (string):     tag of locations to be converted
            ref_tag (string): reference tag
            
         Exclude locations in tag that are not part of a location in ref_tag.
         Offset of converted locations is first position of corresponding ref_tag location.
         Returns converted locations sorted by (start, end, offset)
      """
      result = []
      taglocs = self.get_locs(tag)
      reftaglocs = self.get_locs(ref_tag)
      for t in taglocs:
         for r in reftaglocs:
            if subinterval([t, r]):
               offset = r.start()
               start = t.start() - offset
               end = t.end() - offset
               result.append(Loc(start, end, offset))
               break
      return sorted(result, key=lambda x: x.order())
   def between(self, startTag, endTag, distance):
      # more efficient than seq_before
      # --- HAS NOT BEEN TESTED ---
      def locateIn(ilist, start):
         """
            locate <start> in <ilist>
            if multiple intervals in <ilist> have <start> as the beginning
            of the interval, returns the index of the first one
            if no interval in <ilist> have <start> as the beginning of 
            interval, returns index i such that <start> is between
            start of ilist[i] and ilist[i+1]
         """
         lo = 0
         hi = len(ilist)-1
         while lo <= hi:
            mid = int( (lo+hi)/2 )
            if start == ilist[mid].start():
               while mid >=0 and start == ilist[mid].start():
                  mid -= 1
               return mid+1
            elif start < ilist[mid].start():
               hi = mid-1
            else:
               lo = mid+1
         return lo
      lower = self.get_locs(startTag)
      upper = self.get_locs(endTag)
      res = []
      for intrval in lower:
         b = locateIn(upper, intrval.end())
         e = locateIn(upper, intrval.end()+distance)
         for indx in range(b, e+1):
            d = upper[indx].start()-intrval.end()
            if d <= distance and d > 0:
               res.append( Loc(intrval.end(), upper[indx].start()) )
      return res
   def tag_list(self, tag, locs):
      """
         Tag locs with tag
         
         Parameters:
            tag (string):       tag
            locs (list of Loc): locations to be tagged
      """
      for l in locs:
         self.tag_loc(tag, l)
   def tag_lists(self, prefix_tag, loc_lists):
      """
          Tags lists in loc_lists with prefix_tag_0,..., prefix_tag_n 
          where n=len(loc_lists)-1
          
          Parameters:
             prefix_tag (string):           prefix of tags to be used
             loc_lists (list of Loc lists): lists to be tagged
      """
      for i,llist in enumerate(loc_lists):
         self.tag_list("{}_{}".format(prefix_tag,i),llist)
   def select(self, relation, tags, aggfn=lambda x:x):
      """
         select intervals tagged by <tags> list that satisfy relation
         apply <aggfn> to selected intervals
         output is not sorted
      """
      result = []
      nrargs = len(tags)
      maxindx = []
      locs = [] # list of locations lists
      for tag in tags:
         col = self.get_locs(tag)
         if len(col) == 0:
             return result
         locs.append(col)
         maxindx.append(len(col) - 1)
      indx = [0]*nrargs # current indices for each array ints
      while indx[0] <= maxindx[0]:
         # get tuple of intervals from arrays in ints
         # one from each array
         args = tuple([locs[i][indx[i]] for i in range(nrargs)])
         if relation(args):
            result.append(aggfn(args))
         # get next indices
         j = nrargs-1
         while j > 0 and indx[j] == maxindx[j]:
            j -= 1 
         indx[j] += 1
         for k in range(j+1, nrargs):
            indx[k] = 0
      return result

   def not_in(self, tags, refint=None):
      """
         Get text locations not tagged by tags.
         
         Parameters
            tags (string list): list of tags
            refint (int pair):  start and end location of text to consider
                                if unspecified, consider all text
                                
         Returns list of locations in text not tagged by any of the tags in 
         parameter tags. If refint is specified, returned locations are
         limited to text[refint[0]:refint[1]]. Returned list is sorted by
         from,to, offset and all offsets are zero.
      """
      if type(tags) is not list:
         handle_error(110104, 'parameter of <not_in> must be a list of tags' )
      if refint == None:
         refint=(0,len(self.text))
      # find intervals to discard
      discard = []
      for tag in tags:
         discard = discard + self.get_locs(tag)
      if len(discard) == 0: return [Loc(0, len(self.text))]
      rem = [expand(loc) for loc in merge_list(discard)]
      
      # build list of locations in <refint> that do not overlap <rem>
      res = []
      point = refint[0]
      for elt in rem:
         loc = expand(elt)
         if loc.start() < point: continue
         if loc.start() >= refint[1]: break
         if point != loc.start():
             res.append(Loc(point, loc.start()))
         point = loc.end()
      if point != refint[1]:
         res.append(Loc(point, refint[1]))
      return sorted(res, key=lambda x: x.order())
   def apply_tags(self, tags):
      """
         show text resulting from replacing text associated with tags 
         in list <tags> by the corresponding tags enclosed by char ~
      """
      txt = self.text
      for tag in self.spans:
         if tag not in tags: continue
         for intrval in self.spans[tag]:
            fr = intrval.start() + intrval.offset
            to = intrval.end() + intrval.offset
            origLen = to-fr
            fill = origLen - len(tag)
            if fill < 0:
               tags = tag[:origLen]
            else:
               tags = tag
            beforeF = int(fill/2)
            afterF = fill - beforeF
            txt = txt[:fr] + '~'*beforeF+ tags + '~'*afterF +txt[to:]
      return txt
   def get_locs(self, tag, overlapped=False):
      """
         get list of locations associated with <tag>
      """
      if isinstance(tag, dict) and 'literal' in tag:
         # literal
         stag = tag['literal']
         stag = stag.replace('(', '\(').replace(')','\)').replace('.', '\.')
         stag = stag.replace('[', '\[').replace(']','\]').replace('$', '\$')
         stag = stag.replace('^', '\^').replace('?','\?')
         res = [Loc(fr,to) for (fr,to) in self._findpatt(stag,0,overlapped)] 
      elif isinstance(tag, str):
         if tag not in self.spans:
            res = []
         else:
            res = self.spans[tag]
      else:
         handle_error(110105, 'first parameter of get_locs is tag of literal' )        
      return res
   def in_tag(self, loc, tagList):
      """
         returns first tag in <tagList> that contains <loc>, if any
         otherwise returns None
      """
      for tag in tagList:
         if tag not in self.spans: continue
         # binary search on whole interval
         isIn, indx = binary_search( self.spans[tag], loc )
         if isIn: return tag
      return None
   def replace_tag(self, tag, string):
      """
         return text resulting by replacing text associated with <tag> by 
         <string>
      """
      result = self.text
      locs = merge_list(self.get_locs(tag))
      for indx in range(len(locs)-1, -1, -1):
         fr, to = locs[indx].intrval
         offset = locs[indx].offset
         fr = fr + offset
         to = to + offset
         result = result[:fr] + string + result[to:]
      return result

   def display_doc(self):
      """
         display entire text of the document
      """
      print(self.text)
   def display_tag(self, tag):
      """
         display text associated with <tag>
      """
      ints = self.get_locs(tag)
      for intrval in ints:
         absint = expand(intrval)
         s = absint.start()
         e = absint.end()
         print(self.text[s:e])
   def get_text_loc(self, loc):
      """
         get text in location <loc>
      """
      absloc = expand(loc)
      s = absloc.start()
      e = absloc.end()
      return self.text[s:e]
   def get_text_list(self, llist):
      """

      Parameters
      ----------
      llist : list of locations [loc1, ..., locn]

      Returns
      -------
      res : list of texts [txt1, ..., txtn]
            txti is the text in the document located at loci

      """
      res = []
      absllist = [expand(loc) for loc in llist]
      slist = sorted(absllist, key=lambda x:x.order())
      for loc in slist:
         res.append(self.get_text_loc(loc)) 
      return res
   def get_text_tag(self, tag):
      """
      Parameters
      ----------
      tag : string of byte
      
      Gets the locations associated with tags and returns the
      list of texts located on these locations

      Returns
      -------
      a list of texts: [txt1, ..., txtn]
      one for each location associated with <tag>
      """
      return self.get_text_list(self.get_locs(tag))
   def del_tag(self, tag):
      """
      tag : a string representing tag to be removed
      """
      if tag not in self.spans:
         handle_error(210103, 'Tag {} to remove does not exist'.format(tag))
      else:
         del self.spans[tag]

    
