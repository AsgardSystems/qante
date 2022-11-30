#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module that processes queries on tagged objects
   
   Class Query methods:
      __init__(string/literal list, string, Tagger object, int list, boolean)
      execute() -> list of Loc tuples
      UDP(string, lambda)

"""
import regex as re

from .extracterror import handle_error
from .loctuple import subinterval, seq_before, meets, starts
from .loctuple import before, seq_meets, equal, intersects, disjoint
from .loctuple import overlaps, seq_before_meets, during, finishes

def rm_dups(tuples):
   included = set([])
   sresult = []
   for r in tuples:
      if r in included: continue
      sresult.append(r)
      included.add(r)
   return sresult
def merge_results(prev, new):
   """
      prev : list of schema-tuples pairs
      new :  list of schema-tuples pairs

      updates prev to include new
      if prev already includes tuples for a schema in new, it add new tuples

   """
   for schema, tuples in new:
      found = False
      for i, (osch, otup) in enumerate(prev):
         if schema == osch:
            found = True
            prev[i] = (osch, rm_dups(otup + tuples))
            break
      if not found:
          prev.append( (schema, tuples))
def natural_inner_join(sch_tuples1, sch_tuples2):
   """
      applies natural inner join to tuples1 and tuples2
      schemas of tuples1 and tuples2 must intersect

      sch_tuples1 : pair (sch1,tuples1) where sch1 is a list of integers
                    denoting column number, and tuples1 is a list of location
                    tuples that follow sch1
      sch_tuples2 : pair (sch2,tuples2) where sch2 is a list of integers
                    denoting column number, and tuples2 is a list of location
                    tuples that follow sch2

      Returns a pair (sch, tuples) where sch is the sorted union of sch1 and sch2 and
                    tuples is the result of applying natural join to tuples1 and
                    tuples2 and follows schema sch
   """
   sch1, tuples1 = sch_tuples1
   sch2, tuples2 = sch_tuples2
   overlap = list(set(sch1).intersection(set(sch2)))
   if len(overlap) == 0:
      handle_error(110601, 'schemas in natural_inner_join must intersect')
   if len(sch1) != len(set(sch1)) or len(sch2) != len(set(sch2)):
      handle_error(110602, 'schema has duplicate column number')
   # overlap column number to sch1 index
   over2sch1 = {}
   for o in overlap:
      over2sch1[o] =[i for i in range(len(sch1)) if sch1[i] == o][0]
   # overlap column number to sch2 index
   over2sch2 = {}
   for o in overlap:
      over2sch2[o] =[i for i in range(len(sch2)) if sch2[i] == o][0]
   # sort tuples by overlapping columns
   stuples1 = sorted(tuples1, key=lambda t: tuple( [t[over2sch1[o]].order() for o in overlap] ))
   stuples2 = sorted(tuples2, key=lambda t: tuple( [t[over2sch2[o]].order() for o in overlap] ))
   t1 = 0
   t2 = 0
   joinres = []
   joinsch = sch1 + [col for col in sch2 if col not in overlap]
   # compute join
   while t1 < len(stuples1) and t2 < len(stuples2):
      tuple1 = stuples1[t1]
      tuple2 = stuples2[t2]
      key1 = tuple([tuple1[over2sch1[o]].order() for o in overlap])
      key2 = tuple([tuple2[over2sch2[o]].order() for o in overlap])
      if key1 < key2:
         t1 += 1
      elif key1 > key2:
         t2 += 1
      else:
         i = t1
         while i < len(stuples1):
            j = t2
            while j < len(stuples2):
               tuple1 = stuples1[i]
               tuple2 = stuples2[j]
               k1 = tuple([tuple1[over2sch1[o]].order() for o in overlap])
               k2 = tuple([tuple2[over2sch2[o]].order() for o in overlap])
               if k1 == key1 and k2 == key2:
                  l2 = [tuple2[col] for col in range(len(sch2)) if sch2[col] not in overlap]   
                  joinres.append(tuple(list(tuple1)+l2))
                  j += 1
               else:
                  break
            i += 1
         t1 += 1
         t2 += 1
   # sort columns in joinres so that first column is the one with the lowest
   # column number, then next corresponds to next column number, and so forth
   scols = sorted(joinsch)
   colsmap = []
   for col in scols:
      indx = [i for i in range(len(joinsch)) if joinsch[i] == col][0]
      colsmap.append(indx)
   stuples =[] 
   for t in joinres:
      new_t = [t[indx] for indx in colsmap]
      stuples.append(tuple(new_t))
   return (scols, stuples)
def cartesian_prod(tuples, ptuples, schema):
   """
      tuples :      list of location tuples
      ptuples :     list of location tuples
      schema :      dictionary 
         {'pred':   [c1, ..., cp] : column numbers in ptuples
          'tuples': [d1, ..., dt] : column numbers in tuples
          'tags':   unused

      Computes cartesian product of tuples x ptuples and sorts
      columns in cartesian product by column number
      returns column numbers of result, sorted cartesian product
   """ 
   spred = schema['pred']
   stuples = schema['tuples']
   # verify that schema['pred'] and schema['tuples'] are disjoint
   if len(set(spred).intersection(set(stuples))) != 0:
      fmt = 'schemas of cartesian product operands must be disjoint: {} {}'
      handle_error(110603, fmt.format(spred, stuples))
   # column numbers of result
   soutput = sorted(spred+stuples)
   # mapping column number in result to where it comes from
   col2src = {}
   for col in soutput:
      if col in spred:
         src = 'p'
         indx = [i for i in range(len(spred)) if spred[i] == col][0]
      else:
         src = 't'
         indx = [i for i in range(len(stuples)) if stuples[i] == col][0]
      col2src[col] = (src, indx)  
   result = []
   for ttuple in tuples:
      for ptuple in ptuples:
         rtuple = []
         for col in soutput:
            src,indx = col2src[col]
            if src == 'p':
               rtuple.append(ptuple[indx])
            else:
               rtuple.append(ttuple[indx])
         result.append(tuple(rtuple))
   return soutput,result  
def project(prev_result, oschema):
    """
        prev_result : a schema-tuples pair, where schema is a list of columns
                      and tuples is a list of tuples following the schema
        oschema :     list of colums to project prev_result on
        
        takes tuples in prev_result and project on columns in oschema
        
        Returns a pair new_sch, new_tuples
           new_sch :    list of columns
           new_tuples : list of tuples
    """
    prev_sch, prev_tuples = prev_result
    new_sch = sorted(list(set(prev_sch).intersection(set(oschema))))
    if new_sch == prev_sch:
        return prev_result
    indices = [i for i in range(len(prev_sch)) if prev_sch[i] in new_sch]
    new_tuples = []
    for ptuple in prev_tuples:
        ltuple = list(ptuple)
        new_tuple = tuple( [ltuple[i] for i in range(len(ltuple)) if i in indices] )
        new_tuples.append(new_tuple)
    return new_sch, new_tuples
class Node:
   def __init__(self, op):
      self.op = op          # operator: predicate or booleans AND, OR
      self.result = []      # result so far, list of (schema,[(loc1, ..., locn),...])
      self.children = []    # children, if any
      self.params = []      # parameters as list of column numbers, if leaf
      self.ecount = None    # number of tuples to consider in computation
      self.done = False     # whether computation of node was completed
      self.processed =[]
   def print_node(self, pref, tm, fd=None):
      if fd == None:
         print(pref,self.op)
         if len(self.result) > 0:
            print(pref+"Current result")
            for schema, tuples in self.result:
               print(pref+"schema: {}, {} tuples".format(schema, len(tuples)))
               tm.display_tuples(tuples)
               if self.result not in self.processed:
                  self.processed.append(self.result)
         if len(self.children) == 0:
            print(pref+"leaf")
         if self.done:
            print(pref+"DONE")
         else:
            print(pref+"params: ",self.params)
            print(pref+"estimate of computation count: ",self.ecount)
            print(pref+"pending")
      else:
         line = ["{}{}---params: {}".format(pref,self.op,self.params)]
         if self.done:
            for schema, tuples in self.result:
               line.append(pref+"schema: {}, actual count {} tuples".format(schema, len(tuples)))
         else:
            for schema, tuples in self.result:
               line.append(pref+"schema: {}, current count {} tuples".format(schema, len(tuples)))
            line.append(pref+"estimate count {} tuples".format(self.ecount))
         for l in line: 
            fd.write(l)
            fd.write('\n')

class Query:
   """Class for querying tagged text

   Constructor Parameters:

      tags (string/literal list) -- list of tags or literals used by query

      query (string) -- query to be executed. It must follow this syntax:
         query  ::= '(' query ')' | conj | disj | term
         conj   ::= term 'and' query
         disj   ::= term 'or' query

         term   ::= pred '(' params ')'
         params ::= int ',' params | int

         term   ::= 'dist(' int ',' int ')' relop int
         relop  ::= '<' | '>' | '=' | '<=' | '>=' | '!='

         pred   ::= allen_relation | other-relation

         allen-relation ::= 'before' | 'meets'
            | 'during' | 'finishes' | 'starts' | 'equal' | 'overlaps'

         other-relation ::= 'subinterval' | 'intersects' | 'disjoint'
            | 'seq_before' | 'seq_before_meets' | 'seq_meets'

      tagger (Tagger Object) -- tagged text to apply query

      project (int list) --
         list of indices in tags to include in result (default [])

      log_on (boolean) -- whether to log query execution
         on file query_exec_log.txt (default False)
   """
   FSAdist = {0:[('[(]',1,'token')],
          1:[('[0-9]+', 2, 'token')],
          2:[(',',3,'token')],
          3:[('[0-9]+', 4, 'token')],
          4:[('[)]',5,'token')],
          5:[('[<>=!]', 6, None)],
          6:[('=',7,'combine2'), ('[0-9]+', 8, '2tokens')],
          7:[('[0-9]+', 8, 'token')]}
   def __init__(self, tags, query, tagger, project = [], log_on=False):
      self.PREDS = {'subinterval': subinterval, 
               'seq_before': seq_before,
               'meets': meets,
               'during': during,
               'finishes': finishes,
               'starts': starts,
               'before': before,
               'equal': equal,
               'intersects': intersects,
               'disjoint': disjoint,
               'overlaps': overlaps,
               'seq_before_meets': seq_before_meets,
               'seq_meets': seq_meets}
      if log_on:
         self.fd = open("query_exec_log.txt",'a')
      else:
         self.fd = None
      self.root = None
      self.tagger = tagger
      # subinterval(1, 0) and subinterval(4, 3) and seq_before(0, 2, 3)
      self.query = query 
      self.tokens = []
      # tags considered in this query and number of locations associated with each
      self.qtags = {i:tags[i] for i in range(len(tags))}
      self.count = {i:len(tagger.get_locs(tags[i])) for i in range(len(tags))}
      empty_tags = [self.qtags[i] for i in self.count.keys() if self.count[i] == 0]
      if len(empty_tags) != 0:
          handle_error(210604, 'Tags in query are empty: {}'.format(empty_tags))
      # list of estimated counts of leaves that have not been computed
      self.ecounts = []
      self.project = project
      if len(set(project).difference(set(range(len(self.qtags))))) != 0:
          fmt = "Invalid project columns in query: {}"
          handle_error(110605, fmt.format(project))
   def __del__(self):
      if self.fd != None:
         self.fd.close()
   def UDP(self, pred_name, pred_function):
      """User Defined Predicate
      
      Parameters:
         pred_name (string) -- name of predicate
         pred_function (lambda) -- boolean function to apply when predicate is invoked. 
         
      Defines a new predicate to be included in queries
      """
      self.PREDS[pred_name] = pred_function
   def tokenize(self):
      def parse_dist(i, tokens):
         """
             Verify that next tokens follow this pattern: ( n1 , n2 ) op n3
             where op is a single token (<,>,=) or two tokens(< =, > =, ! =)
             If so, return the following list: ( n1 , n2 ) op n3 where op
             is a single token (tokens < =, > =, ! = are comvined into <=, >=, != )
         """
         token_list = []
         state = 0
         for j in range(i,len(tokens)):
            if state == 8:
               return (j, token_list)
            found = False
            for (pattern, state, op) in Query.FSAdist[state]:
               m = re.search('^{}$'.format(pattern), tokens[j])
               if m != None: 
                  found = True                 
                  break
            if found:
               if op == 'token':
                  token_list.append(tokens[j])
               elif op == 'combine2':
                  token_list.append(tokens[j-1]+tokens[j])
               elif op == '2tokens':
                  token_list.append(tokens[j-1])
                  token_list.append(tokens[j])
            else:
               fmt = 'Invalid expression: {}'
               handle_error(110606, fmt.format(' '.join(tokens[i-1:j+1])))
         if state == 8:
            return (j+1, token_list)
         else:
            fmt = 'Invalid expression: {}'
            handle_error(110607, fmt.format(' '.join(self.tokens[i-1:j+1])))
      if len(self.tokens) > 0:
         fmt = "Query was already tokenized: {}"
         handle_error(210608, fmt.format(self.tokens))
         
      word_patt = '[\w]+'
      delim_patt = '[)(,><=!]'
      pattern = "({})|({})".format(word_patt, delim_patt)
      tokens = []
      for m in re.finditer(pattern, self.query):
         tokens.append(m.group())
      # --------
      # replace dist(n1, n2) op n3, where op in [<. >, =, <=, >=, !=]
      # with dist_pred(_n(n1, n2) where
      # dist_pred_n = lambda t: t[0].offset == t[1].offset and 
      #                         t[1].start() >= t[0].end() and 
      #                         t[1].start()-t[0].end()) op n3
      # --------
      self.tokens = []
      i = 0
      while i < len(tokens):
         if tokens[i] == 'dist':
            n = len(self.PREDS.keys())
            fn_str = 'dist_pred_{}'.format(n)
            self.tokens.append(fn_str)
            i,token_list = parse_dist(i+1, tokens)
            self.tokens = self.tokens + token_list[:-2]
            fmt = "lambda t: (t[0].offset == t[1].offset) and " + \
                  "(t[1].start() >= t[0].end()) and " + \
                  "(t[1].start()-t[0].end()) {} {}"
            lambda_fn = fmt.format( token_list[-2], token_list[-1])
            self.PREDS[fn_str] = eval( lambda_fn )
         else:
            self.tokens.append(tokens[i])
            i += 1
            
   def parse(self):
      """
         Processes list of tokens in self.tokens to compute a parse tree
         It sets self.root to the root of the parse tree
      """
      def is_bop(token):
         # is token a boolean operator?
         return token == 'and' or token == 'or'
      def get_pred_params(i):
         """
            i: next index in self.tokens after predicate name
            
            parses "(c1, .., cn)" after predicate name

            Returns pair (params, i) where
               params : list [c1, ..., cn]
               i: index in self.tokens of closing parenthesis ')' after cn
         """
         nxt = 'open_paren'
         params = []
         while i < len(self.tokens) and self.tokens[i] != ')':
            if (nxt == 'num' and re.search('^[0-9]+$', self.tokens[i]) == None) or \
               (nxt == 'comma' and self.tokens[i] != ',') or \
               (nxt == 'open_paren' and self.tokens[i] != '('):
               fmt = "Invalid syntax in query: {} - Error while parsing parameters at: {}"
               handle_error(110609, fmt.format(self.query, self.tokens[i]))
            if nxt == 'num':
               val = int(self.tokens[i])
               if val < 0 or val >= len(self.qtags):
                  fmt = 'Parameter {} of predicate out of range. In query: {}'
                  handle_error(110610, fmt.format(val, self.query))
               params.append(val)
               nxt = 'comma'
            else:
               nxt = 'num'
            i += 1
         return params, i
      def get_subtree(bool_ops, preds, token):
         """
            bool_ops: stack of boolean operators 'and' and 'or'
            preds: stack of predicates or roots of subtrees
            token: token being processed and is
            used in the error message if an error is found
            
            builds subtree with top of bool_ops as the parent and 
            top two elements of preds as the children
            
            pushes resulting msubtree into preds stack
         """
         op = bool_ops.pop()
         if len(preds) < 2:
            fmt = "Invalid syntax in query: {} - {}"
            handle_error(110611,fmt.format(self.query, token))
         child1 = preds.pop()
         child2 = preds.pop()
         node = Node(op)
         node.children = [child1, child2]
         preds.append(node)
      def get_tree(start_index, open_paren):
         """
            start_index : index in self.tokens where the parsing begins
            open_paren: boolean indicating this function was called as a
            result of finding an open parenthesis
            
            builds a parse tree from tokens starting at index star_index
            if open_paren is True, then stops when the closing parenthesis
            is found, otherwise it stops at the end of self.tokens
       
            Returns the root of the tree
         """
         i = start_index
         bool_ops = []
         preds = []
         nxt_type = 'pred'
         while i < len(self.tokens):
            token = self.tokens[i]
            # check for parsing errors
            if (nxt_type == 'pred' and is_bop(token)) or \
               (nxt_type == 'bool_op' and not is_bop(token) and token != ')') or \
               (token == ')' and not open_paren):
               fmt = "Invalid syntax in query: {} - {}"
               handle_error(110612,fmt.format(self.query, token))
            # pushes a boolean operator (and/or) into bool_ops stack
            if is_bop(token):
               bool_ops.append(token)
               nxt_type = 'pred'
               i += 1
            # parses subexpression starting at '(' by making a recursive call
            elif token == '(':
               root, index = get_tree(i+1, True)
               preds.append(root)
               nxt_type = 'bool_op'
               i = index
            # finishes parsing of subexpression ending at ')'
            elif  token == ')':
               while len(bool_ops) > 0:
                  get_subtree(bool_ops, preds, token)
               return preds.pop(), i+1
            # creates node with predicate and its parameters
            # pushes node into preds stack
            else:
               # get predicate
               if token not in self.PREDS:
                  fmt = "Invalid predicate in query; {}"
                  handle_error(110613, fmt.format(token))
               function = self.PREDS[token]
               node = Node(function)
               node.params, i = get_pred_params(i+1)
               preds.append(node)
               # create subtree if top of bool_ops is 'and' with 'and' as parent
               # and top two elements in preds stack as children
               # pop 'and' and top two elements
               # push subtree into preds stack
               if len(bool_ops) > 0 and bool_ops[-1] == 'and':
                  get_subtree(bool_ops, preds, token)
               nxt_type = 'bool_op'
               i += 1
         while len(bool_ops) > 0:
            get_subtree(bool_ops, preds, "")
         if len(preds) == 0:
            fmt = "Invalid query; {}"
            handle_error(110614, fmt.format(self.query))
         return preds.pop()
      self.root = get_tree(0, False)
   def flatten_tree(self):
      """
         combine contiguous 'and' or 'or' nodes into a single node
         ex:
            Original Tree:
                           and
                            |
                        --------
                        |      |
                       and     or
                        |      |
                     ------  -----
                     |    |  |   |
                     x    y  z   w
          Transformed Tree:
                          and
                           |
                     -----------
                     |   |     |   
                     x   y     or
                               |
                             -----
                             |   |
                             z   w
                  
      """
      def depth_first(ptr):
         if ptr.op == 'and' or ptr.op == 'or':
            to_rm = []
            bool_op = ptr.op
            for indx, child in enumerate(ptr.children):
               if child.op == bool_op:
                  to_rm.append(indx)
                  for grandchild in child.children:
                     ptr.children.append(grandchild)
            for r in range(len(to_rm)-1, -1, -1):
               ptr.children = ptr.children[:to_rm[r]]+ptr.children[to_rm[r]+1:]
            for child in ptr.children:
               depth_first(child)
      depth_first(self.root)
   def find_ecount(self, ecount):
     lo = 0
     hi = len(self.ecounts)-1
     while lo <= hi:
        mid = int( (lo+hi) / 2)
        if self.ecounts[mid] == ecount:
           return (True, mid)
        elif self.ecounts[mid] < ecount:
           lo = mid+1
        else:
           hi = mid-1
     return (False, hi)
   def delete_ecount(self, ecount):
      found, indx = self.find_ecount(ecount) 
      if not found:
         fmt = 'Trying to delete unexistent ecount {} in {}'
         handle_error(110615,fmt.format(ecount), self.ecounts)
      self.ecounts = self.ecounts[:indx]+self.ecounts[indx+1:]
   def update_ecount(self, oldcnt, newcnt):
      # delete oldcnt
      self.delete_ecount(oldcnt)
      # insert newcnt
      found, indx = self.find_ecount(newcnt) 
      self.ecounts = self.ecounts[:indx+1]+[newcnt]+self.ecounts[indx+1:] 
   def add_ecount(self, newcnt):
      found, indx = self.find_ecount(newcnt) 
      self.ecounts = self.ecounts[:indx+1]+[newcnt]+self.ecounts[indx+1:]           
   def update_tree(self):
      """
         traverse tree to update results of 'and'/'or' nodes if computation of
         their children was completed. 
         it traverses the tree depth-first and updates the nodes when returning
         to the node after visiting all its descendants
         moves up the results to update 'and' nodes results 
         update ecount of leaves
      """
      def update_node(ptr, parent):
         """
            ptr :    inner node
            parent : parent of <ptr>
            
            check whether all children of <ptr> have completed their computation
            if so, update <ptr> and <parent> states
         """
         # check whether all children are done
         ptr.done = sum([1 for child in ptr.children if not child.done]) == 0
         if ptr.done:
            # this node is done, update and stop recursion
            # move result one level up
            if parent != None:
               if parent.op == 'and':
                  if len(parent.result) == 0:
                     parent.result = ptr.result
                  elif len(ptr.result) == 0:
                     msg = "Result of conjunction is empty, it should include a schema"
                     handle_error(110616, msg )
                  else:
                     # apply join AQUI -- parent.result = naturaljoin(parent.result,ptr.result)
                     new_parent_result =[]
                     for s1,t1 in parent.result:
                        for s2,t2 in ptr.result:
                           schema_inter = set(s1).intersection(set(s2))
                           if len(schema_inter) > 0:
                              schema,tuples = natural_inner_join((s1,t1), (s2,t2))
                           else:
                              schema,tuples = cartesian_prod(t1, t2, schema={'tuples':s1,'pred':s2})
                           new_schema = True
                           for i, pair in enumerate(new_parent_result):
                              s,t = pair
                              if schema == s:
                                 new_parent_result[i] = (s, rm_dups(t + tuples))
                                 new_schema = False
                                 break
                           if new_schema:
                              new_parent_result.append((schema,tuples))  
                     parent.result = new_parent_result      
               else:
                  # parent is 'or', append result
                  merge_results(parent.result, ptr.result)
      def depth_first(ptr, parent, prev_res):
         if len(ptr.children) == 0:
            # a leaf
            if not ptr.done:
               prev_ecount = ptr.ecount
               if prev_res == None:
                  ptr.ecount = 1
                  for col in ptr.params:
                     ptr.ecount = ptr.ecount * self.count[col]
               else:
                  ptr.ecount = 0
                  for cols, tuples in prev_res:
                     extra_cols = [col for col in ptr.params if col not in cols]
                     if extra_cols == ptr.params:
                        cnt = 1
                     else:
                        cnt = len(tuples)
                     for col in extra_cols:
                        cnt = cnt * self.count[col]
                     ptr.ecount += cnt
               # update self.ecounts
               if prev_ecount == None:
                  self.add_ecount(ptr.ecount)
               else:
                  self.update_ecount(prev_ecount, ptr.ecount)
         else:
            # inner node
            if not ptr.done:
               if ptr.op == 'and' and len(ptr.result) > 0:
                  # and's current results move down
                  prev_res = ptr.result
               for child in ptr.children:
                  depth_first(child, ptr, prev_res)
               update_node(ptr, parent)
      depth_first(self.root, None, None)
        
   def print_tree(self):
      def depth_first(ptr, pref):
         ptr.print_node(pref,self.tagger, self.fd)
         if len(ptr.children) > 0:
            pref = pref + "---"
            for child in ptr.children:
               depth_first(child, pref)
      depth_first(self.root,"")
      if self.fd == None:
         print("\n\n")
      else:
         self.fd.write('\n\n')
         self.fd.flush()
   def print_result(self, result):
      for cols,tuples in result:
         print('===')
         for t in tuples:
            print('---')
            for i in range(len(t)):
               f = t[i]
               print(self.tagger.get_text_loc(f), '\n...')
            
   def compute_leaf(self):
      """
         Traverse tree depth-first until it finds leaf with lowest value of ecount
         When going down the tree and finding an 'and' node, take the result of
         'and' node and push down as previous result. when a new 'and' node is
         found the previous result is updated with the result of new 'and' node
         When leaf with lowest value is found, it uses previous result to compute the
         result of the leaf and updates the result of the leaf parent.
         if leaf parent is 'and', it overwrites its result with computed result
         if leaf parent is 'or', it appends computed result to its result
      """
      def project(tuples, schema, outcols):
         """
            tuples:  list of location tuples
            schema:  column numbers for each elt in tuple
            outcols: columns to include in output

            returns projection of tuples on outcols
         """
         res = []
         indices = [ i for i in range(len(schema)) if schema[i] in outcols]
         for ltuple in tuples:
            res.append(tuple([ltuple[i] for i in indices]))
         return res 
      def sort_columns(schema, tuples):
         """
            sort columns in tuples by column number
         """
         newres = []
         sschema = sorted(schema)
         for ltuple in tuples:
            t = []
            for col in sschema:
               index = [i for i in range(len(schema)) if schema[i] == col][0]
               t.append(ltuple[index])
            newres.append(tuple(t))
         return sschema, newres      
      def depth_first(ptr,ecount,prev_res,parent):
         found = False
         if len(ptr.children) == 0:
            # a leaf
            if not ptr.done and ptr.ecount == ecount: 
               found = True
               """
               schema:
                  'pred': leaf predicate parameters
                  'tuples': schema (tags) of previous results
                  'tags': 'pred'-'tuples'
               """
               schema = {'pred': ptr.params} 
               new_res = []
               if prev_res != None:
                  # schemas of prev results and predicate params are disjoint
                  disjoint = True
                  partial_newres = []
                  # computation limited with previous results
                  for cols,tuples in prev_res:
                     schema['tuples'] = cols
                     # new columns to add with this predicate
                     schema['tags'] = list(set(ptr.params).difference(set(cols)))
                     if set(schema['tags']) == set(schema['pred']):
                        # leaf predicate's parameters and prev result's tags are disjoint
                        tags = [ self.qtags[i] for i in ptr.params ]
                        partial_newres = partial_newres + self.tagger.select(ptr.op, tags)
                        newschema, newres = cartesian_prod(tuples, partial_newres, schema)
                     else:
                        disjoint = False
                        tags = [ self.qtags[i] for i in schema['tags'] ]
                        newschema, newres = self.tagger._select(ptr.op, tuples, tags, schema)
                     new_res.append((newschema, rm_dups(newres)))
                  if disjoint:
                     ptr.result = [(ptr.params, rm_dups(partial_newres))]
                  else:
                     # project on params and save result in leaf node
                     res = []
                     for cols, tuples in new_res:
                        res = res + project(tuples, cols, ptr.params)
                     ptr.result = [(ptr.params, rm_dups(res))]
               else:
                  # no previous results
                  tags = [self.qtags[col] for col in ptr.params]
                  # get results with columns not sorted
                  newres_unsorted = self.tagger.select(ptr.op, tags)
                  # sort columns
                  newsch, newres = sort_columns(ptr.params, newres_unsorted)
                  new_res = [ (newsch, newres) ]
                  ptr.result = [ (newsch.copy(), newres.copy()) ]
               self.delete_ecount(ecount)
               ptr.done = True
               ptr.ecount = len(ptr.result[0][1])
               # move up new_res to parent
               if parent != None:
                  if parent.op == 'and':
                     # overwrite
                     parent.result = new_res
                  else:
                     # parent is 'or', append result
                     merge_results(parent.result, new_res)
         else:
            # inner node
            if ptr.op == 'and' and len(ptr.result) > 0:
               # and's current results move down
               prev_res = ptr.result
            for child in ptr.children:
               found = depth_first(child, ecount, prev_res, ptr) 
               if found: break
         return found
      min_ecount = self.ecounts[0]
      depth_first(self.root, min_ecount, None, None)
   def execute(self):       ## dab 2022-11-07
      """Execute query
      
      Returns the list of tuple locations that satisfy the query. The number 
      of elements in each tuple is determined from parameters tags and project
      in the constructor. Each tuple has n elements where n is the number
      of elements in project, if project is not [], or the number of elements in tags,
      if project is [].
      """
      self.tokenize()      # partition query into tokens
      self.parse()         # create parse tree
      self.flatten_tree()  # reduce height of tree
      self.update_tree()   # estimate counts of tuples to be evaluated by leaf nodes
      if self.fd != None: self.print_tree()
      while not self.root.done:
         self.compute_leaf() # evaluate leaf with lowest number of tuples to evaluate
         self.update_tree()  # update tree with results of leaf
         if self.fd != None: self.print_tree()
      if len(self.project) == 0:
          oschema = list(range(len(self.qtags)))
      else:
          oschema = self.project
      # project results to oschema
      for i in range(len(self.root.result)):
          self.root.result[i] = project(self.root.result[i], oschema)
      # complete result with cartesian products, if needed
      result = []
      all_true = lambda x: True
      for sch, tuples in self.root.result:
        tags = [self.qtags[oschema[i]] for i in range(len(oschema)) if oschema[i] not in sch]
        if len(tags) == 0:
            result = result + tuples
            continue
        psch = [oschema[i] for i in range(len(oschema)) if oschema[i] not in sch]
        schema = {'tuples': sch, 'pred': psch}
        ptuples = self.tagger.select(all_true, tags)       
        result = result + cartesian_prod(tuples, ptuples, schema)[1]
      # remove duplicates
      sresult = []
      included = set([])
      for r in result:
         if r in included: continue
         sresult.append(r)
         included.add(r)
      return sresult



