string_lists=["eat","tea","tan","ate","nat","bat"]
dict={}
values=[]
for i in string_lists:
    sorted_String = "".join(sorted(i))
    if sorted_String not in dict:
        dict[sorted_String]=[]
    dict[sorted_String].append(i)
        

print(dict)

nums=[1,2,3,4]
prefix=1
res=[1,1,1,1]
for i in range(len(nums)):
    res[i]=prefix
    prefix *= nums[i]

print(res)
postfix=1
for i in reversed(range(len(nums))):
    print(i)
    res[i]=postfix
    postfix*=nums[i]
print(res)


def productexceptSelf(nums):
    res=[1]*len(nums)
    n=len(nums)
    prefix=1
    for i in range(len(res)):
        res[i]=prefix
        prefix*=nums[i]
        
    postfix=1
    for i in range(n-1,-1,-1):
        res[i]*=postfix
        postfix*=nums[i]
    
    return res

print(productexceptSelf([1,2,3,4]))
    
    
sub="Abcd"
print(sub[::-1])