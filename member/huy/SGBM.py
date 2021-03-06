from stereovision.calibration import StereoCalibration
import cv2
import numpy as np

def nothing(x):
    pass
#
video1 = cv2.VideoCapture('outputR.avi') #right
video1.set(3,352)
video1.set(4,288)

video2 = cv2.VideoCapture('outputL.avi')
video2.set(3,352)
video2.set(4,288)

# This assumes you've already calibrated your camera and have saved the
# calibration files to disk. You can also initialize an empty calibration and
# calculate the calibration, or you can clone another calibration from one in
# memory
calibration = StereoCalibration(input_folder='./data')


cv2.namedWindow('Tuner')
cv2.createTrackbar('minDisparity','Tuner',0,255,nothing) #### 78
cv2.createTrackbar('numDisparities','Tuner',1,16,nothing) # divide by 16 = 2
cv2.createTrackbar('SADWindowSize','Tuner',1,21,nothing) #old number
cv2.createTrackbar('P1','Tuner',0,255,nothing) # 25
cv2.createTrackbar('P2','Tuner',0,255,nothing) # P2>P1 84
cv2.createTrackbar('disp12MaxDiff','Tuner',0,255,nothing)
cv2.createTrackbar('preFilterCap','Tuner',0,255,nothing)
cv2.createTrackbar('uniquenessRatio','Tuner',0,25,nothing)
cv2.createTrackbar('speckleWindowSize','Tuner',0,200,nothing)
cv2.createTrackbar('speckleRange','Tuner',0,32,nothing) # multiplied by 16

# cv2.namedWindow('Post filter')
# cv2.createTrackbar('medianBlur','Post filter', 0, 21, nothing())
# cv2.createTrackbar('inpaint','Post filter', 0, 21, nothing())
# cv2.createTrackbar('bilateralFilter','Post filter', 0, 21, nothing())
# cv2.createTrackbar('GaussianBlur','Post filter', 0, 21, nothing())

minDisparity = 8
numDisparities = 3 *16
SADWindowSize = 1 #old number
P1 = 35
P2 = 89
disp12MaxDiff = 0
# preFilterCap =
# uniquenessRatio =
# speckleWindowSize =
# speckleRange =
fullDP = True


while 1:
    ret1, frame1 = video1.read()
    ret2, frame2 = video2.read()

    imgL = cv2.cvtColor(frame1,cv2.COLOR_RGB2GRAY)
    imgR = cv2.cvtColor(frame2,cv2.COLOR_RGB2GRAY)

    # Now rectify two images taken with your stereo camera. The function expects
    # a tuple of OpenCV Mats, which in Python are numpy arrays
    rectified_pair = calibration.rectify((imgL, imgR))
    # rectified_pair = calibration.rectify((frame2, frame1))

    # minDisparity = cv2.getTrackbarPos('minDisparity','Tuner')
    # numDisparities = cv2.getTrackbarPos('numDisparities','Tuner')
    # if numDisparities == 0:
    #     numDisparities = 1
    # numDisparities = numDisparities *16
    # SADWindowSize = cv2.getTrackbarPos('SADWindowSize','Tuner')
    # if SADWindowSize%2 == 0:
    #     SADWindowSize = SADWindowSize + 1
    # P1 = cv2.getTrackbarPos('P1','Tuner')
    # P2 = cv2.getTrackbarPos('P2','Tuner')
    # disp12MaxDiff = cv2.getTrackbarPos('disp12MaxDiff','Tuner')
    preFilterCap = cv2.getTrackbarPos('preFilterCap','Tuner')
    uniquenessRatio = cv2.getTrackbarPos('uniquenessRatio','Tuner')
    speckleWindowSize = cv2.getTrackbarPos('speckleWindowSize','Tuner')
    speckleRange = cv2.getTrackbarPos('speckleRange','Tuner')
    # fullDP = True

    block_matcher = cv2.StereoSGBM(minDisparity, numDisparities, SADWindowSize, P1, P2,disp12MaxDiff,preFilterCap, uniquenessRatio, speckleWindowSize,speckleRange,fullDP)
    disparity = block_matcher.compute(rectified_pair[0], rectified_pair[1])

    display = cv2.normalize(disparity,disparity, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    cv2.imshow("Before filter", display)
    (T, mask) = cv2.threshold(display, 0, 255, cv2.THRESH_BINARY_INV)

    # mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
    # display = cv2.inpaint(display, mask, 5, cv2.INPAINT_TELEA)
    display = cv2.medianBlur(display, 5)

    # detector = cv2.SimpleBlobDetector()
    # keypoint = detector.detector.detect(display)
    # img_keypoint = cv2.drawKeypoints(display, keypoint, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # display = cv2.bilateralFilter(display,5,55,55)
    # display = cv2.GaussianBlur(display, (5,5), 0.1)
    # display = cv2.blur(display, (5,5))
    # display = cv2.bitwise_and(display,display,None,mask)
    cv2.imshow("Tuner", display)
    # cv2.imshow("mask", img_keypoint)
    # cv2.imshow("res",rectified_pair[0])
    # cv2.imshow("res2",rectified_pair[1])
    char = cv2.waitKey(10)
    if (char == 27):
        break

cv2.destroyAllWindows()