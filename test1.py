import numpy as np

# Assume 'arr' is your 2D numpy array
arr = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])

# Split the array into two arrays based on odd and even indices
arr_even = arr[:, ::2]  # Columns at even indices
arr_odd = arr[:, 1::2]  # Columns at odd indices

print("Original array:\n", arr)
print("Array with even indices:\n", arr_even)
print("Array with odd indices:\n", arr_odd)
