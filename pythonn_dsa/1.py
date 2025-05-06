def longest_subscting(s):
    seen=set()
    maxlen=0
    if s =="":
        return 1,seen
    for i in s:
        if i not in seen:
            seen.add(i)
            maxlen+=1

    return maxlen,seen
tests=[
    ("abcabcab",3),
        ("bbbb",1),
        ("pwwkew",3),
        ("",1),
        ("abcdefg",7),
                ("abba",2),
   ]

for string,expected_length in tests:
    result ,seen= longest_subscting(string)
    print(f"input string: {string}| expected_output:{expected_length}|result:{result}| {"pass" if result==expected_length else "Fail"} | seen set is: {seen}")