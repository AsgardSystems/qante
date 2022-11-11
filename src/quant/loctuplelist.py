from .extracterror import handle_error

def groupby(tuplelist, groupindex, outindex):
    """
        group <tuplelist> by <groupindex>
        for each value of <groupindex>, takes tuples with that value and
        creates a list of values of <outindex> in these tuples
        for example, consider the following tuplelist where ik are locations
        and on, (sm, em) is an expansion of a location --offset,(start,end)
            tuplelist: i1, o1,(s1,e1), i3
                       i4, o3,(s2,e2), i6
                       i7, o2,(s1,e1), i8
                       i9, o4,(s2,e2), i10
            groupindex = 1
            outindex = 2
            result: [ [i3, i8], [i6, i10] ]
    """
    if len(tuplelist) == 0:
       return []
    maxindx = len(tuplelist[0])-1
    if groupindex > maxindx or groupindex < 0 or outindex > maxindx or \
       outindex < 0:
       fmt = "Parameters groupindex [{}] and outindex [{}] are out of range [0,{}]"
       msg = fmt.format(groupindex, outindex, maxindx)
       handle_error(110401, msg)   
    result = {}
    for ltuple in tuplelist:
        gloc = ltuple[groupindex]
        oloc = ltuple[outindex]
        if gloc.intrval not in result:
           result[gloc.intrval] = []
        result[gloc.intrval].append(oloc)
    return [value for key,value in result.items()]
        
