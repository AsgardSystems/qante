"""Module for tagged text. It keeps track of mappings from tags to locations in text
   
   lit(string) -> literal
   
   Class Tagger Methods:
      __init__(string, boolean)
      tagRE(string, string, int, boolean)
      tag_loc(string, Loc)
      tag_list(string. Loc list)
      tag_lists(string, list of Loc lists)
      del_tag(string)     
      display_matches()
      display_doc()
      display_tag(string)
      display_tuples(list of Loc tuples)
      get_locs(string/literal, boolean) -> Loc list
      get_text_loc(Loc) -> string
      get_text_tuple(Loc tuple) -> string tuple
      get_text_list(Loc list) -> string list
      get_text_tag(string) -> string list
      in_tag(Loc, string list) -> string
      not_in(Loc list, int pair) -> Loc list
      project(string, string) -> Loc list
      replace_tag(string, string) -> string
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
      
   Constructor parameters:
      text (string) -- text to be tagged
      lower_case (boolean) -- if True, convert text to lower case (default True) 
      
   Locations associated with a tag are always sorted by fr,to,offset
   """
   def __init__(self, text, lower_case=True):
      if lower_case:
         self.text = text.lower()
      else:
         self.text = text
      self.spans   = {} # tag --> [ (from, to), ...]
   def tagRE(self, tag, regexp, group=0, overlapped=False):
      """Tag strings in text matching regexp with tag
         
      Parameters:
         tag (string) -- tag
         regexp (string) -- regular expression
         group (int) -- match group within the regular expression (default 0)
         overlapped (boolean) -- whether regular expression matches overlap (default False)
      
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
   def display_tuples(self, ltuples):
      """Display text associated with list of location tuples"""
      for t in ltuples:
         print(self.get_text_tuple(t))
   def tag_loc(self, tag, loc):
      """Tag loc  with tag
         
      Parameters:
         loc (Loc) -- location 
         tag (string) -- tag
         
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
      """Converts tag locations to be relative to the beginning of strings tagged as ref_tag
         
      Parameters:
         tag (string) -- tag of locations to be converted
         ref_tag (string) -- reference tag
         
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
      """Tag locs with tag
         
      Parameters:
         tag (string) -- tag
         locs (list of Loc) -- locations to be tagged
      """
      for l in locs:
         self.tag_loc(tag, l)
   def tag_lists(self, prefix_tag, loc_lists):
      """Tags lists in loc_lists with prefix_tag_0,..., prefix_tag_n 
      where n=len(loc_lists)-1
          
      Parameters:
         prefix_tag (string) -- prefix of tags to be used
         loc_lists (list of Loc lists) -- lists to be tagged
      """
      for i,llist in enumerate(loc_lists):
         self.tag_list("{}_{}".format(prefix_tag,i),llist)
   def _select(self, pred, tuples, tags, schema):
      """
          select locations tuples from <tuples> and <tags> that satisfy 
          <pred>
          
          pred:   a boolean function on a tuple of locations
          tuples: list of locations tuples
          tags:   list of tags
          schema: a dictionary specifying the column numbers of pred 
                  arguments and tuples 
             'pred':   [i1, ..., ir]
             'tuples': [j1, ..., jt]
             'tags':   [k1, ..., kg]
          output: a list of locations tuples and its schema (col numbers):
             [(loc1, ..., locn), ...] where n=t+g 
             columns in <output> are sorted by column number
          
          creates cartesian product of tuples and locations in tags
          apply <pred> to each element of the cartesian product 
          and output the element if <pred> is True
                  
      """
      def get_pred_args(args, stuples, stags, spred):
         """
            This function extract locations from args to pass as arguments
            of predicate
            
            <args> has the locations to get pred args from:
            args =  [ (l1,...,lt), loc1, ..., locg ]
            <stuples> has column numbers of first element in <args>
            stuples = [j1,...,jt]
            <stags> has column numbers of the other elements in <args>
            stags =               [ k1, ...,  kg]
            <spred> has column numbers of predicate arguments
            spred = [cn1,...,cnr]
         """
         result = []
         if len(stuples) > 0:
            loc_tuple = args[0]
         for col in spred:
            indices = [i for i in range(len(stuples)) if stuples[i] == col ] 
            if len(indices) != 0:
               indx_tuple = indices[0]
               result.append(loc_tuple[indx_tuple])
               continue
            indices = [i for i in range(len(stags)) if stags[i] == col ] 
            indx_tag = indices[0]
            result.append(args[indx_tag+1])
         return tuple(result)
        
      def get_out_tuple(args, stuples, stags, soutput):
         result = []
         if len(stuples) > 0:
            loc_tuple = args[0]
         for col in soutput:
            indices = [i for i in range(len(stuples)) if stuples[i] == col ] 
            if len(indices) != 0:
               indx_tuple = indices[0]
               result.append(loc_tuple[indx_tuple])
               continue
            indices = [i for i in range(len(stags)) if stags[i] == col ] 
            indx_tag = indices[0]
            result.append(args[indx_tag+1])
         return tuple(result)
       
      def check_schema(schema):
         # -------verify constraints-----------
         stuples = []; stags = []; spred = []
         if 'tuples' in schema:
            stuples = schema['tuples']
         if 'pred' in schema:
            spred = schema['pred']
         if 'tags' in schema:
            stags = schema['tags']
         # stuples, stags, and spred must be sets
         if len(stuples) != len(set(stuples)) or len(spred) != len(set(spred)) \
            or len(stags) != len(set(stags)):
            fmt = "Column numbers in schemas must not have duplicates: {},{},{}"
            handle_error(110801, fmt.format(stuples,stags,spred))
         stags_derived = set(spred).difference(set(stuples))
         if stags_derived != set(stags):
            fmt = "Invalid column numbers for tags: {}"
            handle_error(110802, fmt.format(stags))
         # predicate columns come from tuples and tags
         soutput = sorted(stuples + stags)
         return (stuples, stags, spred, soutput)       
      stuples, stags, spred, soutput = check_schema(schema)
      result = []
      nrargs = len(tags)+1      
      locs = [tuples] # list of locations lists
      maxindx = [len(tuples)-1]
      for tag in tags:
          col = self.get_locs(tag)
          if len(col) == 0:
              return (soutput, result) 
          locs.append(col)
          maxindx.append(len(col) - 1)
      indx = [0]*nrargs # current indices for each array ints
      while indx[0] <= maxindx[0]:
          # get tuple of intervals from arrays in ints
          # one from each array
          args = [ locs[i][indx[i]] for i in range(nrargs) ]
          pargs = get_pred_args(args, stuples, stags, spred)
          if pred(pargs):
             otuple = get_out_tuple(args, stuples, stags, soutput)
             result.append(otuple)
          # get next indices
          j = nrargs-1
          while j > 0 and indx[j] == maxindx[j]:
              j -= 1 
          indx[j] += 1
          for k in range(j+1, nrargs):
              indx[k] = 0
      return (soutput, result) 
   def select(self, relation, tags, aggfn=lambda x:x):
      """
         select intervals tagged by <tags> list that satisfy relation
         apply <aggfn> to selected intervals
         output is not sorted
         
         superseded by Query module
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
      """Get text locations not tagged by tags.
         
      Parameters:
         tags (string list) -- list of tags
         refint (int pair) -- start and end location of text to consider (default None)
                             
      Returns list of locations in text not tagged by any of the tags in 
      parameter tags. If refint is not None, returned locations are
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
      """Returns Loc list of text tagged with tag
         
      Parameters:
         tag (string/literal) -- tag or literal
         overlapped (boolean) -- whether string matches overlap when tag is a literal 
                                 (default False)
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
         handle_error(110105, 'first parameter of get_locs must be a tag or a literal' )        
      return res
   def in_tag(self, loc, tag_list):
      """Returns first tag in tag_list that includes loc, if any, otherwise returns None
         
      Parameters:
         loc (Loc) -- location
         tag_list (string list) -- list of tags
      """
      for tag in tag_list:
         if tag not in self.spans: continue
         # binary search on whole interval
         isIn, indx = binary_search( self.spans[tag], loc )
         if isIn: return tag
      return None
   def replace_tag(self, tag, replacement):
      """Returns text resulting from replacing strings tagged with tag with replacement
         
      Parameters:
         tag (string) -- tag of strings to be replaced
         replacement (string) -- replacement string
      """
      result = self.text
      locs = merge_list(self.get_locs(tag))
      for indx in range(len(locs)-1, -1, -1):
         fr, to = locs[indx].intrval
         offset = locs[indx].offset
         fr = fr + offset
         to = to + offset
         result = result[:fr] + replacement + result[to:]
      return result

   def display_doc(self):
      """display entire text"""
      print(self.text)
   def display_tag(self, tag):
      """Display strings tagged with tag
      
      Parameters:
         tag (string/literal) -- tag name or literal
      """
      ints = self.get_locs(tag)
      for intrval in ints:
         absint = expand(intrval)
         s = absint.start()
         e = absint.end()
         print(self.text[s:e])
   def get_text_loc(self, loc):
      """Returns string in location loc
      
      Parameters:
         loc (Loc) -- location
      """
      absloc = expand(loc)
      s = absloc.start()
      e = absloc.end()
      return self.text[s:e]
   def get_text_list(self, llist):
      """Returns list of strings in locations llist
         
      Parameters:
         llist (Loc list) -- list of locations
      """
      res = []
      absllist = [expand(loc) for loc in llist]
      slist = sorted(absllist, key=lambda x:x.order())
      for loc in slist:
         res.append(self.get_text_loc(loc)) 
      return res
   def get_text_tuple(self, ltuple):
      """Returns tuple of strings in locations ltuple
         
      Parameters:
         ltuple (Loc tuple) -- tuple of locations
      """
      res = []
      for loc in ltuple:
         res.append(self.get_text_loc(loc)) 
      return tuple(res)
   def get_text_tag(self, tag):
      """Returns list of strings tagged by tag
         
      Parameters:
         tag (string) -- tag
      """
      return self.get_text_list(self.get_locs(tag))
   def del_tag(self, tag):
      """Delete tag
      
      Parameters:
         tag (string) -- tag to be deleted
      """
      if tag not in self.spans:
         handle_error(210103, 'Tag {} to remove does not exist'.format(tag))
      else:
         del self.spans[tag]

    
