from kvcache import KVCache
import pytest

## TODO: AWH - test bad key names

def test_simple():

    c=KVCache()
    c.set_val("a", "zzz")
    assert c.get("a").decode()=='zzz'
    c.expire("a", 0)
    assert c.get("a") is None
    c.set_val("a", "zzz")
    import time
    time.sleep(6)
    assert c.get("a") is None
    c.set_val("aa", "aa")
    c.set_val("b_b", "b_b")
    c.set_val("bb", "bb")
    c.set_val("ab", "ab")
    c.set_val("ac", "ac")
    print(c.keys("b_*"))
    print(c.keys("a*"))
