# -*- coding: utf-8 -*-
"""Module to extract tables from text
This module relies on columns being aligned. If columns are misaligned, function
get_table tries to get desired results based on the parameters passed. However,
there will be cases of misaligned colums that this function won't get desired 
results
 
get_table(string, int, boolean, int)

Table class methods:
   __init__(string, int, string)
   get_cols()
   get_headers_text(int) 
   get_rows()
   get_row(Loc) -> Loc list
   get_colnumbers(row) -> int list
   untag_rows()
"""
import regex as re

from .extracterror import handle_error
from .loc import expand, Loc
from .loctuple import intersect_len
from .loctuple import first, subinterval, before, intersects, seq_before, meets
from .loclist import binary_search
from .tagger import Tagger
from .loctuplelist import groupby
from . import utilities as ut
class Table: 
   """Table object
   Constructor Parameters:
      text (string) -- text where table is
      hlinecnt (int) -- number of lines in the table header
      fieldRE (string) -- regular expression that matches fields in the table (default ut.FIELD)
   Set data member tagged to define tags on text
   """
   def __init__(self, text, hlinecnt, fieldRE = ut.FIELD):
      non_empty = []
      for m in re.finditer(ut.LINE, text):
         if re.search('\S', m.group()) != None:
            # line with non-space characters           
            if hlinecnt == 0 or len(non_empty) == hlinecnt-1:
               non_empty.append((m.span()[0],len(text)))
               break
            else:
               non_empty.append(m.span())
      if hlinecnt != 0 and len(non_empty) != hlinecnt:
         fmt = "Table does not have enough header lines: {}"
         handle_error(110701, fmt.format(text))
      table_text = ''
      for fr,to in non_empty:
         table_text = table_text + text[fr:to]
      self.hlinecnt = hlinecnt
      self.tagged = Tagger(table_text)
      self.tagged.tagRE('LINE', ut.LINE)                  # line
      self.tagged.tagRE('FIELD', fieldRE, 2)              # field
      # get headers -- first <hlinecnt> lines
      locs = self.tagged.get_locs('LINE')
      if hlinecnt > 0:
         self.tagged.tag_list('lHDER', locs[:hlinecnt] )  # header line
      self.tagged.tag_list('lCONT', locs[hlinecnt:])      # content line
      # project fields to beginning of line
      # (i.e. relative to beginning of line)
      locs = self.tagged.project('FIELD', 'LINE')
      self.tagged.tag_list('pFIELD', locs)                # projected field
      tuples = self.tagged.select(subinterval, ['FIELD', 'lHDER'])
      hdr_field = list(map(first, tuples))
      tuples = self.tagged.select(subinterval, ['FIELD', 'lCONT'])
      cont_field = list(map(first, tuples))
      self.tagged.tag_list('cFIELD', cont_field)          # content field
      self.tagged.tag_list('hFIELD', hdr_field)           # header field
      locs = self.tagged.project('cFIELD', 'LINE')
      self.tagged.tag_list('pcFIELD', locs )              # projected content field
      locs = self.tagged.project('hFIELD', 'LINE')
      self.tagged.tag_list('phFIELD', locs)               # projected header field
   def get_cols(self):
      """Get columns from table

      Set the following data members:
         cols_count -- number of columns in table 
         cols_lengths -- list of column lengths
         cont_cols_count -- number of content columns
         cont_cols_lengths -- list of content column lengths
         hdr_cols_count -- number of header columns
         hdr_cols_lengths -- list of header column lengths 
      Tag columns as 'COL_0', 'COL_1', ....
      """
      self.cols = ut.cluster(self.tagged.get_locs('pFIELD'))
      self.abs_cols = [sorted(list(map(expand, column)), key=lambda x:x.order()) \
                       for column in self.cols] 
      # tags columns as COL_0, COL_1, ...
      self.tagged.tag_lists('COL', self.abs_cols)
      self.cols_count = len(self.cols)
      self.cols_lengths = [len(col) for col in self.cols]

      self.cont_cols = ut.cluster(self.tagged.get_locs('pcFIELD'))
      self.cont_cols_count = len(self.cont_cols)
      self.cont_cols_lengths = [len(col) for col in self.cont_cols]
 
      self.hdr_cols = ut.cluster(self.tagged.get_locs('phFIELD'))
      self.hdr_cols_count = len(self.hdr_cols)
      self.hdr_cols_lengths = [len(col) for col in self.hdr_cols] 
   
   def split_cont_cols(self):
      """
      split a content column that align with 2 or more headers
      """
      def get_col_to_split():
         cont_spans = [ut.get_list_span(col) for col in self.cont_cols]
         hdr_spans = [ut.get_list_span(col) for col in self.hdr_cols]
         score = []
         hdr_cols = {}
         for cc in range(self.cont_cols_count):
            cont_span = cont_spans[cc]
            if cont_span is None:
               score.append(-1)
               continue
            hdr_cols[cc] = []
            for hc in range(self.hdr_cols_count):
               if intersects( (cont_span, hdr_spans[hc]) ):
                  hdr_cols[cc].append(hc)
            if len(hdr_cols[cc]) < 2: 
               score.append(-1)
               continue
            len_cont_span = cont_span.length()
            int_perc = sum([intersect_len((cont_span, hdr_spans[j])) \
                            for j in hdr_cols[cc]]) / len_cont_span 
            score.append(1-int_perc)
         max_score = max(score)
         if max_score < 0: return None, None
         cc_best = [k for k in range(self.cont_cols_count) if score[k] == max_score][0]
         hdr_spans = [ut.get_list_span(self.hdr_cols[col]) for col in hdr_cols[cc_best]]
         return cc_best, hdr_spans
      def partition(cont_loc, hdr_spans, j):
         if j == len(hdr_spans)-1 or not intersects((cont_loc, hdr_spans[j+1])):
            return cont_loc, []
         cont_txt = self.tagged.get_text_loc(cont_loc)
         space_at = [i for i,ch in enumerate(cont_txt) if ch == ' ']
         for i in space_at:
            curr_loc = Loc(cont_loc.start(), cont_loc.start()+i, cont_loc.offset)
            next_loc = Loc(cont_loc.start()+i+1, cont_loc.end(), cont_loc.offset)
            if not intersects((next_loc, hdr_spans[j])) and intersects((next_loc, hdr_spans[j+1])):
               return curr_loc, [next_loc]
         return cont_loc, []
      def split_cont_col(col2split,hdr_spans ):
         """
            split content column nr col2split into n columns where n is the
            number of elements in hdr_spans
            hdr_spans are the spans of headears that align with column col2split
            
         """
         cols = [ [] for i in range(len(hdr_spans)) ] # cols to replace self.cont_cols[cc_best]
         if len(self.tagged.get_locs('TOSPLIT')) != 0:
            self.tagged.del_tag('TOSPLIT')
         self.tagged.tag_list('TOSPLIT', [expand(elt) for elt in self.cont_cols[col2split]])
         pairs =  self.tagged.select(subinterval, ['TOSPLIT', 'LINE'])
         # group content fields by line
         rows = groupby(pairs, 1, 0)
         for row in rows:
            # process one line
            self.tagged.del_tag('TOSPLIT')
            self.tagged.tag_list('TOSPLIT',row)
            locs = self.tagged.project('TOSPLIT','LINE')
            used_hdr = set([])
            pending = []
            i = 0
            while i < len(locs):
               cont_loc = locs[i]
               found = False
               for k in range(2):
                  for j in range(len(cols)):
                     #if j in used_hdr and max(cont2hdr[i]) > j: continue
                     if k==0 and j in used_hdr: continue
                     if intersects((cont_loc, hdr_spans[j])):
                        curr_loc, next_loc = partition(cont_loc, hdr_spans, j)
                        cols[j].append(curr_loc)
                        locs = locs[:i+1] + next_loc + locs[i+1:]
                        found = True
                        used_hdr.add(j)
                        break
                  if k == 1 and not found:
                     pending.append(cont_loc)
                  elif found:
                     break
               i += 1
            cont_spans = [ut.get_list_span(col) for col in cols]
            for cont_loc in pending:
               found = False
               scores = {}
               for j in range(len(cols)):
                  if cont_spans[j] == None: continue
                  if intersects((cont_loc, cont_spans[j])):
                     found = True
                     scores[j] = intersect_len((cont_loc, cont_spans[j]))
               if found:
                  max_score = max(list(scores.values()))
                  indx = [j for j in scores.keys() if scores[j] == max_score][0]
                  cols[indx].append(cont_loc)
               else:
                  fmt = "Couldn't find column for content {}"
                  handle_error(210708, fmt.format(self.tagged.get_text_loc(cont_loc)))
               cont_spans = [ut.get_list_span(col) for col in cols]
         return cols
      col2split,hdr_spans = get_col_to_split()
      if col2split == None: return False
      cols = split_cont_col(col2split,hdr_spans )
      # replace  self.cont_cols[cc_best] with cols
      self.cont_cols = self.cont_cols[:col2split] + cols + self.cont_cols[col2split+1:]
      self.cont_cols_count = len(self.cont_cols)
      self.cont_cols_lengths = [len(col) for col in self.cont_cols]              
      return True     
   def adjust_content(self, col_count=None):
      changed = True
      while col_count != None and self.cont_cols_count < col_count and changed:
         changed = self.split_cont_cols() 
      # propagage changes 
      cont_field = [expand(loc) for col in self.cont_cols for loc in col]
      self.tagged.del_tag('cFIELD')
      self.tagged.tag_list('cFIELD', cont_field)
      locs = self.tagged.project('cFIELD', 'LINE')
      self.tagged.del_tag('pcFIELD')
      self.tagged.tag_list('pcFIELD', locs)               
      # update fields
      hdr_field = self.tagged.get_locs('hFIELD')
      self.tagged.del_tag('FIELD')
      self.tagged.tag_list('FIELD', hdr_field + cont_field)
      # update cols
      locs = self.tagged.project('FIELD', 'LINE')
      self.tagged.del_tag('pFIELD')
      self.tagged.tag_list('pFIELD', locs)
      if self.hdr_cols_count == self.cont_cols_count:
         self.cols = [self.hdr_cols[i]+self.cont_cols[i] for i in range(self.hdr_cols_count)]
      else:
         self.cols = ut.cluster(self.tagged.get_locs('pFIELD'))
      # update abs_cols
      self.abs_cols = [sorted(list(map(expand, column)), key=lambda x:x.order()) \
                       for column in self.cols]  
      self.cols_count = len(self.cols)
      self.cols_lengths = [len(col) for col in self.cols]
             
   def adjust_header(self, col_count=None):
      """
      Split columns in header if the number of columns in header 
      is smaller than the number of columns in content
      
      Merge columns in header i the number of columns in header
      is larger than the number of columns in content
      """
      split = False
      changed = True
      cont_spans = [ut.get_list_span(col) for col in self.cont_cols]
      while ((col_count == None and self.cont_cols_count > self.hdr_cols_count) or \
            (col_count != None and self.hdr_cols_count < col_count)) and \
            changed: 
         #print(self.cont_cols_count, self.hdr_cols_count)
         #print( [self.tagged.get_text_list(elt) for elt in self.hdr_cols] )
         hdr_spans  = [ut.get_list_span(col) for col in self.hdr_cols]
         # find header that covers two columns
         changed = False
         for i in range(len(cont_spans)-1):
            if intersects( ( cont_spans[i], hdr_spans[i] ) ) and \
               intersects( ( cont_spans[i+1], hdr_spans[i] ) ) :
               changed = self.split_hdr_col(i, cont_spans[i], cont_spans[i+1])
               if changed:
                  split = True
                  break  
      merged = False
      changed = True
      #print("merging...")
      while ((col_count == None and self.cont_cols_count < self.hdr_cols_count) or \
            (col_count != None and self.hdr_cols_count > col_count)) and \
            changed: 
         #print(self.cont_cols_count, self.hdr_cols_count)
         #print( [self.tagged.get_text_list(elt) for elt in self.hdr_cols] )
         hdr_spans  = [ut.get_list_span(col) for col in self.hdr_cols]
         # find 2 header that covers one column
         changed = False
         for i in range(len(hdr_spans)-1):
            if i >= len(cont_spans)-1:
               continue
            #perc_1 = intersect_len( ( cont_spans[i], hdr_spans[i] ) ) / \
            #         hdr_spans[i].length()
            perc_2 = intersect_len( ( cont_spans[i], hdr_spans[i+1] ) ) / \
                     hdr_spans[i+1].length()
            perc_3 = intersect_len( ( cont_spans[i+1], hdr_spans[i+1] ) ) / \
                     hdr_spans[i+1].length()
            if perc_2 > 0 and perc_2 > perc_3 :
               # merge headers
               merged_hdrs = self.hdr_cols[i] + self.hdr_cols[i+1]
               self.hdr_cols = self.hdr_cols[:i]+[merged_hdrs]+self.hdr_cols[i+2:]
               self.hdr_cols_count = len(self.hdr_cols)
               self.hdr_cols_lengths = [len(col) for col in self.hdr_cols]  
               merged = True
               changed = True
               break  
      # propage changes in hdr_columns to cols, abs_cols, fields, hdr_fields
      if split or merged:
         # update hdr_field related tags
         hdr_field = [expand(loc) for col in self.hdr_cols for loc in col]
         self.tagged.del_tag('hFIELD')
         self.tagged.tag_list('hFIELD', hdr_field)
         locs = self.tagged.project('hFIELD', 'LINE')
         self.tagged.del_tag('phFIELD')
         self.tagged.tag_list('phFIELD', locs)               
         cont_field = self.tagged.get_locs('cFIELD')
         # update fields
         self.tagged.del_tag('FIELD')
         self.tagged.tag_list('FIELD', hdr_field + cont_field)
         # update cols
         locs = self.tagged.project('FIELD', 'LINE')
         self.tagged.del_tag('pFIELD')
         self.tagged.tag_list('pFIELD', locs)
         if self.hdr_cols_count == self.cont_cols_count:
            self.cols = [self.hdr_cols[i]+self.cont_cols[i] for i in range(self.hdr_cols_count)]
         else:
            self.cols = ut.cluster(self.tagged.get_locs('pFIELD'))
         # update abs_cols
         self.abs_cols = [sorted(list(map(expand, column)), key=lambda x:x.order()) \
                          for column in self.cols]  
         self.cols_count = len(self.cols)
         self.cols_lengths = [len(col) for col in self.cols]
         
   def align_content_cols(self):
      """
      Aligns misaligned content cells
      """
      def get_triple(loc):
         return loc.start(), loc.end(), loc.offset
      # find content column withoud header
      for colnr in range(len(self.abs_cols)):
         col = self.abs_cols[colnr]
         col_proj = self.cols[colnr]
         # does <col> have a header?
         col_pos = [elt.order() for elt in col]
         hdr_pos = [elt.order() for elt in self.tagged.get_locs('hFIELD')]
         if set(col_pos).intersection(set(hdr_pos)):
            continue
         # <col> does not have a header, move elements to other cols
         for loc in col:
            loc_proj = [cell for cell in col_proj if expand(cell).order() == loc.order()][0]
            # get row of loc
            row = self.get_row(loc)
            row_colnrs = self.get_colnumbers(row)
            indx = [i for i in range(len(row_colnrs)) if row_colnrs[i]==colnr][0]
            newcol = None
            if indx > 0:
               prev_colnr = row_colnrs[indx-1]
               if prev_colnr < colnr-1:
                  newcol = colnr-1
            elif indx < len(row_colnrs):
               next_colnr = row_colnrs[indx+1]
               if next_colnr > colnr+1:
                  newcol = colnr+1
            if newcol == None:
               handle_error(110702, "table content columns could not be aligned")
            else:
               # move loc to column newcol
               found, i = binary_search(self.abs_cols[newcol], loc) 
               if found:
                  handle_error(110703, "location in two columns: {}".format(loc))
               self.abs_cols[newcol] = self.abs_cols[newcol][:i+1]+[loc]+\
                                       self.abs_cols[newcol][i+1:]
               # move loc_proj to column newcol
               found, i = binary_search(self.cols[newcol], loc_proj) 
               if found:
                  handle_error(110704, "location in two columns: {}".format(loc))
               self.cols[newcol] = self.cols[newcol][:i+1]+[loc_proj]+\
                                   self.cols[newcol][i+1:]
         # remove <col>, <col_proj>
         self.abs_cols = self.abs_cols[:colnr]+self.abs_cols[colnr:]
         self.cols = self.cols[:colnr]+self.cols[colnr:]
      self.cols_count = len(self.cols)
      self.cols_lengths = [len(col) for col in self.cols]
            
   def split_hdr_col(self, i, first_span, second_span):
      """
      i :           header column number
      first_span :  span of first content column covered by header i
      second_span : span of second content column covered by header i
      
      For each element in header column i, find out whether element aligns
      with first or second content column or element needs to be split into
      two strings that align with first and second content columns
      
      update self.hdr_cols, self.hdr_cols_count, and self.hdr_cols_lengths   
      """
      bef_meet = lambda pair: before(pair) or meets(pair)
      first = []
      second = []
      for hdr in self.hdr_cols[i]:
         if before((hdr, second_span)) and intersects((hdr, first_span)):
             first.append(hdr)
         elif before((first_span, hdr)) and intersects((hdr, second_span)):
             second.append(hdr)
         elif intersects((hdr, first_span)) and intersects((hdr, second_span)):
            # split hdr, it intersects with both content columns
            hdr_text = self.tagged.get_text_loc(hdr)
            #print("header",hdr_text)
            split = False
            # try splitting hdr at word boundary (e.g. ' ') 
            space_at = [i for i,ch in enumerate(hdr_text) if ch == ' ']
            # compute score for each possibility based on satisfied conditions
            satisfied = []
            for left_len in space_at:
               left_hdr = Loc(hdr.start(), hdr.start()+left_len, hdr.offset)
               right_hdr = Loc(hdr.start()+left_len+1, hdr.end(), hdr.offset)
               satisfied.append((intersects((left_hdr, first_span)),
                                 intersects((right_hdr, second_span)),
                                 bef_meet((left_hdr, second_span)),
                                 bef_meet((first_span, right_hdr)))) 
            if len(satisfied) == 0:
               # hdr is a single word, no spaces
               if len(self.hdr_cols[i]) > 1:
                  # multiple fields in header
                  # put hdr where it intersects the most
                  left_perc = intersect_len( (hdr, first_span) )/hdr.length()
                  right_perc = intersect_len( (hdr, second_span) )/hdr.length()
                  if left_perc <= right_perc:
                     left_hdr = hdr
                     right_hdr = None
                  else:
                     left_hdr = None
                     right_hdr = hdr
                  split = True
            else:
               score = [(o1+o2)*10+b1+b2 for (o1, o2, b1, b2) in satisfied]
               # get best possibility, if any
               max_score = max(score)
               if max_score > 20:
                  index = [i for i in range(len(score)) if score[i] == max_score][0]
                  left_len = space_at[index]
                  left_hdr = Loc(hdr.start(), hdr.start()+left_len, hdr.offset)
                  right_hdr = Loc(hdr.start()+left_len+1, hdr.end(), hdr.offset)
                  split = True
            if not split:
               # split in the middle between first_span and second_span
               # compute half point between cont[i] and cont[i+1]
               half_point = int((second_span.start() + first_span.end())/2)
               left_hdr = Loc(hdr.start(), half_point, hdr.offset)
               right_hdr = Loc(half_point+1, hdr.end(), hdr.offset)
            if left_hdr is not None:
               first.append(left_hdr)
            if right_hdr is not None:
               second.append(right_hdr)
         elif seq_before((first_span, hdr, second_span)):
            # header is between content columns
            # put hdr in closest column, if equidistant put in left
            left_dist = hdr.start() - first_span.end()
            right_dist = second_span.start() - hdr.end()
            if left_dist <= right_dist:
               first.append(hdr)
            else:
               second.append(hdr)
         else:
            handle_error(110705, 'Non-implemented case for split header')
      if len(first) == 0 or len(second) == 0:
          handle_error(110706, 'Could not split header')
      self.hdr_cols = self.hdr_cols[:i]+[first]+[second]+self.hdr_cols[i+1:]
      self.hdr_cols_count = len(self.hdr_cols)
      self.hdr_cols_lengths = [len(col) for col in self.hdr_cols]
      if len(first) > 0 and len(second) > 0:
         return True
      return False

   def align_cols(self):
      """
      this function fixes misalignments between header columns and content columns
      for example, consider the following table with the corresponding <cols>
         header1     header2     header3
         f1      f2          f3
         f4      f5          f6
         abs_cols = [[loc(header1),loc(f1),loc(f4)], 
                    [loc(f2),loc(f5)], 
                    [loc(header2)], 
                    [loc(f3), loc(f6)], 
                    [loc(header3)]]
         categories = [ [loc(header1),loc(header2),loc(header3)], 
                        [loc(f1), ..., loc(f6)] ]  
         where loc(f1) denotes the location of f1
      the result would be to change abs_cols to:
         [[loc(header1),loc(f1),loc(f4)], 
          [loc(header2),loc(f2),loc(f5)], 
          [loc(header3), loc(f3), loc(f6)]]  
      """
      cols = self.abs_cols
      categories = [self.tagged.get_locs('hFIELD'), self.tagged.get_locs('cFIELD')]
      cat_cols = ut.categorize(cols, categories)
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
         self.abs_cols = result
        
   def get_headers_text(self, hlinecnt):
      """Get text of each header column
      
      Set data member headers to a list of text, one for each header column
      """
      self.headers = []
      # creates headers for each column
      if hlinecnt > 0:
         # split columns into header and content
         cont_field = self.tagged.get_locs('cFIELD')
         hdr_field = self.tagged.get_locs('hFIELD') 
         cat_cols = ut.categorize(self.abs_cols, [hdr_field, cont_field])   
         # select header columns
         hdr_cols = cat_cols[0]
         # join text of each header column to create a header for the column
         self.headers = [' '.join(self.tagged.get_text_list(col)) for col in hdr_cols]

   def get_rows(self):
      """Get rows from table
      
      Tag content rows in table as 'ROW_0', 'ROW_1', ...
      """
      pairs =  self.tagged.select(subinterval, ['cFIELD', 'LINE'])
      # group content fields by line
      self.rows = groupby(pairs, 1, 0)
      self.rows_count = len(self.rows)
      self.rows_lengths = [len(row) for row in self.rows]
      self.tagged.tag_lists('ROW', self.rows)
   def get_row(self, loc):
      """Finds row where Loc is
      Parameters:
         loc (Loc) -- location to search
      Returns row (Loc list) where loc is
      """
      abs_loc = expand(loc)
      for row in self.rows:
         row_pos = [elt.order() for elt in row]
         if abs_loc.order() in row_pos:
            return row
   def get_colnumbers(self, row):
      """Get column numbers of elements in row
      
      Parameters:
         row (Loc list): list of locations
      For each location in row, it finds its column number
      Returns the list of column numbers, one for each element of row 
      """
      result = []
      colnr = 0
      for loc in row:
         found = False
         for c in range(colnr,self.cols_count):
            col_loc = [elt.order() for elt in self.abs_cols[c]]
            if loc.order() in col_loc:
               colnr = c+1
               result.append(c)
               found = True
               break
         if not found:
            handle_error(110709, "Row element is not in any column")
      return result
   def untag_rows(self):
      """Remove tags 'ROW_0', 'ROW_1', from tagged"""
      for rownr in range(self.rows_count):
         self.tagged.del_tag("ROW_{}".format(rownr))
   def untag_cols(self):
      """Remove tags 'COL_0', 'COL_1', from tagged"""
      for colnr in range(self.cols_count):
         self.tagged.del_tag("COL_{}".format(colnr))
      
def get_table(text, hlinecnt, sparse=False, col_count=None):
   """Extract table from text
   
   Parameters
      text (string) -- text where table comes from
      hlinecnt (int) -- number of lines 
      sparse (bool) -- True, if there are empty cells in table (default False)
      col_count -- number of columns in table (default None, the function will
                                               determine the number of columns)
      
   The first hlinecnt lines in text that contain non-space characters are considered
   headers, the rest are considered content
   
   Returns a list of dictionaries, one for each content row. Each dictionary maps
   a header to the value in the row.
   """
   table = Table(text, hlinecnt)
   table.get_cols()
   table.get_rows()
   orig_cols_count = table.cols_count
   if col_count != None and table.cols_count != col_count:
      for i in range(2):
         if hlinecnt != 0 and col_count != table.hdr_cols_count:
            table.adjust_header(col_count)
         if col_count != table.cont_cols_count:
            table.adjust_content(col_count)
         if col_count == table.cont_cols_count and col_count == table.hdr_cols_count:
            break
         table = Table(text, hlinecnt, ut.altFIELD)
         table.get_cols()
         table.get_rows() 
   else:
      if not sparse:
         if max(table.rows_lengths) > table.hdr_cols_count:
            # check whether a single header column is covering 2 content columns 
            # if so, fix it
            table.adjust_header()
         elif max(table.rows_lengths) == table.hdr_cols_count and \
            table.cont_cols_count > table.hdr_cols_count and \
            table.cols_count > table.hdr_cols_count:
            # columns in content are misaligned
            table.align_content_cols()
      if table.hdr_cols_count == table.cont_cols_count and \
         table.cont_cols_count < table.cols_count:
         # check if header columns are misaligned with content columns
         table.align_cols()
   table.get_headers_text(hlinecnt)
   table.untag_rows()
   table.get_rows()
   # reset columns
   table.untag_cols()
   table.tagged.tag_lists('COL', table.abs_cols)
   # ------------------------------------------------------------------
   #      build table represented as a list of dictionaries 
   #      each dictionary maps a column header to a content field text
   result = []
   column_tags = ["COL_{}".format(c) for c in range(table.cols_count)]
   for rnr in range(table.rows_count):
        # get intervals in row
        locs = table.tagged.get_locs("ROW_{}".format(rnr))
        row = {}
        for loc in locs:
            # get column where loc is
            tag = table.tagged.in_tag(loc, column_tags)
            if tag == None:
               fmt = "Content field [{}] in table does not belong to any column"
               msg = fmt.format(table.tagged.get_text_loc(loc))
               handle_error(110507, msg)
            colnr = int(tag[4:]) # column nr
            if colnr >= len(table.headers) or table.headers[colnr] == '':
               if column_tags[colnr] not in row:
                  row[column_tags[colnr]] = table.tagged.get_text_loc(loc)
               else:
                  row[column_tags[colnr]] += ' ' +table.tagged.get_text_loc(loc)
            else:
               if table.headers[colnr] not in row:
                  row[table.headers[colnr]] = table.tagged.get_text_loc(loc)
               else:
                  row[table.headers[colnr]] += ' ' +table.tagged.get_text_loc(loc)
        result.append(row)
   return result
