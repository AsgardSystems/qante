"""Module for error handling

   When an error is found, funcion handle_error must be called
   
   handle_error(int, string, dict)

"""
class ExtractError(Exception):  
   def __init__(self, code, msg):
      self.code = code
      self.msg = msg
      
def handle_error(code, msg, error_loc=None):
   """Function to handle errors
   
   Parameters:
      code (int) -- error code consisting of 6 digits: tammdd
          t is type of error: 
             1 for serious, 
             2 for warning
          a is the application
                1 for qante
          mm is module where it occurred (should be unique within application):
                for tagging
                   01 is tagger
                   02 for loc
                   03 for loctuple
                   04 for loctuplelist
                   05 for utilities
                   06 for query
                   07 for table
                   09 for loclist
          dd is error code within module
      msg (string) -- error message
      error_loc (dict) -- unused                                   
   """  
   if code < 100000 or code > 999999:
      pref = "ERROR: invalid error code and "
   else:
      t = int(code/100000) 
      if t == 1:
         pref = "ERROR[{}]: ".format(code)
         raise ExtractError(code, pref+msg)
      elif t == 2:
         pref = "Warning[{}]: ".format(code)
      else:
         pref = "ERROR: invalid error code and " 
      print(pref + msg)


