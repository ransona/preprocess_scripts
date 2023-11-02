import numpy as np
import matplotlib.pyplot as plt

# Create a random 100x100 matrix with values between 0 and 1
matrix = np.random.rand(100, 100)

# Plot the image of the matrix
plt.imshow(matrix, cmap='gray')  # You can change the colormap if needed. For example, 'viridis', 'plasma', etc.
plt.colorbar()
plt.title('Image of a Random 100x100 Matrix')
plt.show()