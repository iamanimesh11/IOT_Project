def prefix_sum_subarrays(nums,k):
    count=0
    prefix_sum=0
    prefix_sum_dict= {0:1}

    for num in nums:
        prefix_sum+=num
        s=prefix_sum-k
        if  s  in prefix_sum_dict:
            count+=prefix_sum_dict[s]
        prefix_sum_dict[prefix_sum]=prefix_sum_dict.get(prefix_sum,0) + 1

    return count



# nums=[1,2,1,2,1]
# k=3
# print(prefix_sum_subarrays(nums,3))

def get_equal_target_indices(arr,target):
    """ """
    complement=0
    map={}
    for i in range(len(arr)):
        complement=target-arr[i]
        if complement  not in map:
            map[arr[i]]=i
        else:
            
            
    

arr=[2,7,11,15]
target =9
print(get_equal_target_indices(arr,target))