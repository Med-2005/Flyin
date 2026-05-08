def twoSum(nums, target):
    seen = {}

    for i, l in enumerate(nums):
        needed = target - l

        if needed in seen:
            return [seen[needed], i]

        seen[l] = i

print(twoSum([2,7,11,15], 9))
