import logging
from pyObjectManager.List import List
from pyObjectManager.Int import Int
from pyObjectManager.Real import Real
from pyObjectManager.BitVec import BitVec
from pyObjectManager.Char import Char
from pyObjectManager.String import String
import ast
import pyState

logger = logging.getLogger("pyState:SimFunction:String.rstrip")

def _rstrip(state,newString,chars):

    # Look char by char in reverse order to find target char
    for c in range(newString.length()-1,-1,-1):#[::-1]:
        c = newString[c]
        for f in range(chars.length()):
            f = chars[f]
            # If we must be, pop and move on
            if c.mustBe(f):
                newString.pop()
                break
            # If we CAN be, take both options at once
            elif c.canBe(f):
                state_notEqual = state.copy()
                newString_notEqual = newString.copy()
                newString_notEqual.setState(state_notEqual)
                chars_notEqual = chars.copy()
                chars_notEqual.setState(state_notEqual)
                state_notEqual.addConstraint(f.getZ3Object() != c.getZ3Object())
                
                # Equal side
                newString.pop()
                state_eq = state.copy()
                newString_eq = newString.copy()
                newString_eq.setState(state_eq)
                chars_eq = chars.copy()
                chars_eq.setState(state_eq)
                state_eq.addConstraint(f.getZ3Object() == c.getZ3Object())

                # Take both
                return _rstrip(state_notEqual,newString_notEqual,chars_notEqual) + _rstrip(state_eq,newString_eq,chars_eq)
        else:
            break

    return [newString.copy()]
    


def handle(state,call,chars=None,ctx=None):
    """
    Simulate Python's rstrip string method
    """
    ctx = ctx if ctx is not None else state.ctx
    
    # The root (i.e.: "s" in s.rstrip())
    root = state.resolveObject(call.func.value,ctx=ctx).copy()

    assert len(root) == 1

    root = root.pop()

    assert type(root) is String

    # Resolve the chars
    charsl = state.resolveObject(chars,ctx=ctx) if chars is not None else state.getVar(varName='tempRstripstr',ctx=1,varType=String,kwargs={'string': " ","increment": True})

    # Normalize
    charsl = [charsl] if type(charsl) is not list else charsl

    # Resolve calls if we need to
    retObjs = [x for x in charsl if type(x) is pyState.ReturnObject]
    if len(retObjs) > 0:
        return retObjs

    ret = []
    
    for chars in charsl:

        # According to the docs, this should be String or None
        if type(chars) not in [String, Char]:
            err = "handle: Invalid argument type {0}".format(type(chars))
            logger.error(err)
            raise Exception(err)

        # Change input to always be a String object
        if type(chars) is Char:
            oldChars = chars
            chars = state.getVar(varName='tempRstripstr',ctx=1,varType=String,kwargs={'increment': True})
            chars.append(oldChars)


        # Get new str
        newString = state.getVar('temprStripStr',ctx=1,varType=String,kwargs={'increment':True}).copy()
        
        # Set new str to be the same as the old str
        newString.setTo(root,clear=True)

        # Perform the strip
        ret += _rstrip(state,newString,chars)

    return ret
