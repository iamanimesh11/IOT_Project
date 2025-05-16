
def bubble_Sort(arr):    
    iterate=0
    while iterate<len(arr):    
        swapped=False
        for i in range(len(arr)-1):
                if arr[i]>arr[i+1]:
                    arr[i],arr[i+1]=arr[i+1],arr[i]
                print(arr)
        iterate+=1
        if not swapped:
            break
 
arr=[5,3,8,4,2]   
# print(f" final:{bubble_Sort(arr)}")
def selection_sort(arr):
    n = len(arr)
    for arr_index in range(n):
        # Assume the current index holds the minimum value
        min_index = arr_index
        for i in range(arr_index + 1, n):  # Compare with the rest of the array
            if arr[i] < arr[min_index]:
                min_index = i  # Update the index of the minimum value
                print(f"min index:{min_index}, arr_index: {arr_index}")
        # Swap the found minimum element with the current element
        arr[arr_index], arr[min_index] = arr[min_index], arr[arr_index]
        print(f"Step {arr_index + 1}: {arr}")  # Print the array after each step
    return arr

# Test the function
arr = [5, 3, 8, 4, 2]
print(f"Sorted array: {selection_sort(arr)}")