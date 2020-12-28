import numpy as np
import cv2
from scipy.spatial import KDTree
import sklearn.cluster

#read image
cap = cv2.VideoCapture("U.mp4")
ret, frame = cap.read()
#frame = cv2.imread("IMG_2779.jpg")
b, g, r = cv2.split(frame)

#edge detection filter
kernel = np.array([[0.0, -1.0, 0.0], 
                [-1.0, 4.0, -1.0],
                [0.0, -1.0, 0.0]])

#filter the source image
b_out = cv2.filter2D(b,-1,kernel)
g_out = cv2.filter2D(g,-1,kernel)
r_out = cv2.filter2D(r,-1,kernel)

#cv2.imshow("", cv2.merge((b_out, g_out, r_out)))

blur = cv2.GaussianBlur(cv2.cvtColor(cv2.merge((b_out, g_out, r_out)), cv2.COLOR_BGR2GRAY),(5,5),0)
ret3,th3 = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)


blurred = cv2.GaussianBlur(th3, (3, 3), 0)
canny = cv2.Canny(blurred, 20, 40)
kernel = np.ones((3,3), np.uint8)
dilated = cv2.dilate(canny, kernel, iterations=2)
(contours, hierarchy) = cv2.findContours(dilated.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

"""cv2.drawContours(frame, contours, -1, (0,255,0), 3)
cv2.imshow("", th3)
cv2.waitKey()"""

hierarchy = hierarchy[0]
candidates = []
center = []

for component in zip(contours, hierarchy):
    contour = component[0]
    curr_hierarchy = component[1]
    
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.05 * peri, True)
    area = cv2.contourArea(contour)

    if len(approx) == 4 and len(cv2.convexHull(approx, returnPoints = False)) == 4 and curr_hierarchy[2] < 0 and area > 1000:
        candidates.append(approx)
"""for i in range(len(candidates)):
    cv2.circle(frame, tuple(candidates[i][0]), 4, (255, 0, 0))
for i in range(len(center)):
    cv2.circle(frame, tuple(center[i][0]), 4, (255, 255, 255))
#cv2.drawContours(th3, candidates, -1, (0, 255, 0), 3)

cv2.namedWindow("a", cv2.WINDOW_NORMAL)
cv2.imshow("a", frame)
cv2.waitKey()"""


c = [50, 300, 350, 600, 650, 900]
corners = []
for x in c:
    for y in c:
        corners.append([x, y, 0])
        corners.append([x, 0, y])
corners = np.float32(corners).reshape(-1,3)

model_points = np.array([(0, 0, 0), (250, 0, 0), (250, 250, 0), (0, 250, 0)], dtype="float32")

camera_matrix = np.array([[frame.shape[1], 0.0, frame.shape[1] / 2], [0.0, frame.shape[1], frame.shape[0] / 2], [0.0, 0.0, 1.0]], dtype = "float32")
dist_coeffs = np.array([[0, 0, 0, 0, 0]], dtype="float32")

angles = []

axis = np.float32([[3,0,0], [0,3,0], [0,0,-3]]).reshape(-1,3)
def draw(img, corners, imgpts):
    corner = tuple(corners[0].ravel())
    img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255,0,0), 5)
    img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0,255,0), 5)
    img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0,0,255), 5)
    return img


for square in candidates:
    sorted_x = square[np.argsort(square[:, 0, 0])]
    sorted_y = square[np.argsort(square[:, 0, 1])]
    top_left = sorted_x[0] if sorted_x[0, 0, 1] < sorted_x[1, 0, 1] else sorted_x[1]
    top_right = sorted_y[0] if sorted_y[0, 0, 0] > sorted_y[1, 0, 0] else sorted_y[1]
    bot_left = sorted_x[0] if sorted_x[0, 0, 1] >= sorted_x[1, 0, 1] else sorted_x[1]
    bot_right = sorted_x[3] if sorted_x[3, 0, 1] >= sorted_x[2, 0, 1] else sorted_x[2]
    square = np.array([top_left, top_right, bot_right, bot_left], dtype="float32")
    ret, rvec, tvec, inliers = cv2.solvePnPRansac(model_points, square, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
    angles.append(np.vstack((rvec, tvec)).flatten())

k = 4
kmeans = sklearn.cluster.KMeans(n_clusters=k)
k_frame = kmeans.fit(angles)
best = np.array(k_frame.cluster_centers_[np.argmax(np.bincount(k_frame.labels_))], dtype="float32")

axis = np.float32([[3,0,0], [0,3,0], [0,0,-3]]).reshape(-1,3)
imgpts, jac = cv2.projectPoints(axis, best[:3].reshape((3, 1)), best[3:].reshape((3, 1)), camera_matrix, dist_coeffs)
print(imgpts)
img = draw(frame, square,imgpts)
cv2.imshow('img',img)
k = cv2.waitKey(0) & 0xff
if k == 's':
    cv2.imwrite(fname[:6]+'.png', img)



imgpts, jac = cv2.projectPoints(corners, best[:3].reshape((3, 1)), best[3:].reshape((3, 1)), camera_matrix, dist_coeffs)

for i in range(len(imgpts)):
    cv2.circle(frame, tuple(imgpts[i][0].astype(int)), 4, (255, 0, 0))

cv2.namedWindow("a", cv2.WINDOW_NORMAL)
cv2.imshow("a", frame)
cv2.waitKey()