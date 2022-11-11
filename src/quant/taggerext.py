#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 12:47:10 2022

@author: mescobar
"""
from .tagger import Tagger
from .loctuple import subinterval
from .extracterror import handle_error
class TaggerExt(Tagger):
   def contains_tags(self, ref_tag, tag_list):
      """
      Function that select tuples where first element contain the other
      elements and first element is in <ref_tag> and the rest are in <tag_list>
      Parameters
      ----------
      ref_tag :  tag
      tag_list : list of tags [tag_1, ..., tag_n]

      Returns
      -------
      a tuple of n+1 locations [loc_1, ..., loc_n+1], 
      where loc_1 is in <tag> AND 
            loc_2, ..., loc_n+1 are in tag_1, ..., tag_n respectively AND
            loc_2, ..., loc_n+1 are each subintervals of loc_1

      """
      def contains(in_tuple):
         in_list = list(in_tuple)
         fstloc = in_list[0]
         for loc in in_list[1:]:
            if not subinterval((loc, fstloc)):
               return False
         return True
      tuples = self.select(contains, [ref_tag]+tag_list)
      return tuples
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
