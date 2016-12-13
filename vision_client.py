import socket
import time
# import the necessary packages
from collections import deque
import numpy as np
import argparse
import imutils
import cv2

#global xCoord
xCoord = 0
#global yCoord
yCoord = 0

originCoord = (0,0)
displacedCoord = (0,0)

def runEverything():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video",
        help="path to the (optional) video file")
    ap.add_argument("-b", "--buffer", type=int, default=64,
        help="max buffer size")
    args = vars(ap.parse_args())

    # define the lower and upper boundaries of the "green"
    # ball in the HSV color space, then initialize the
    # list of tracked points
    greenLower = (29, 86, 6)
    greenUpper = (64, 255, 255)
    pts = deque(maxlen=args["buffer"])
    global xCoord
    global yCoord
    timeout = time.time() + 5 # 5 seconds from now
     
    # if a video path was not supplied, grab the reference
    # to the webcam
    if not args.get("video", False):
        camera = cv2.VideoCapture(0)
        # USB webcam on Linux
        #camera = cv2.VideoCapture(1)
     
    # otherwise, grab a reference to the video file
    else:
        camera = cv2.VideoCapture(args["video"])
        
    # keep looping
    while True:
        # grab the current frame
        (grabbed, frame) = camera.read()
     
        # if we are viewing a video and we did not grab a frame,
        # then we have reached the end of the video
        if args.get("video") and not grabbed:
            break
     
        # resize the frame, blur it, and convert it to the HSV
        # color space
        frame = imutils.resize(frame, width=600)
        # blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
     
        # construct a mask for the color "green", then perform
        # a series of dilations and erosions to remove any small
        # blobs left in the mask
        mask = cv2.inRange(hsv, greenLower, greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None
     
        # only proceed if at least one contour was found
        if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
     
            # only proceed if the radius meets a minimum size
            if radius > 10:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(frame, (int(x), int(y)), int(radius),
                    (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
     
        # update the points queue
        pts.appendleft(center)
        
        # loop over the set of tracked points
        for i in xrange(1, len(pts)):
            # if either of the tracked points are None, ignore
            # them
            if pts[i - 1] is None or pts[i] is None:
                continue
            
            # update coordinates
            xCoord = pts[i][0]
            yCoord = pts[i][1]
     
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
            cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
        # print coordinates to the screen
        cv2.putText(frame, "x: {}, y: {}".format(xCoord, yCoord), (10,frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        # show the frame to our screen
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        #really hack
        if time.time() > timeout:
            break
     
        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            break
     
    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
host = socket.gethostname();
port = 8888;
try:
    s.connect((host, port))
except Exception as e:
    print "It's all buggered! Exception is %s" % e
finally:
    while True:
        inp = s.recv(1024)
        print "Received Command:", inp
        if ("ipos" in inp):
            runEverything()
            originCoord = (xCoord, yCoord)
            print "x: %d y: %d" % originCoord
            s.sendall(str(originCoord))
        elif ("fpos" in inp):
            runEverything()
            displacedCoord = (xCoord, yCoord)
            print "x: %d y: %d" % displacedCoord
            s.sendall(str(originCoord))
            s.sendall("moving")
            

    #s.close