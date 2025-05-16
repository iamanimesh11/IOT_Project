string_lists=["eat","tea","tan","ate","nat","bat"]
dict={}
values=[]
for i in string_lists:
    sorted_String = "".join(sorted(i))
    if sorted_String not in dict:
        dict[sorted_String]=[]
    dict[sorted_String].append(i)
        

print(dict)