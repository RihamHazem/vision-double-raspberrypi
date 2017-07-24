## IBM CIC Vision-Double
# Mentor: Ahmed S Hassan.
# Code Author: Muhammad S. Masoud
# Description:
#	A stable release version that enables feeding from video/camera, detect motion, and takes snap shots on the frames
#	that include one face or more.
#
#
#



		#Imports Section on top of the program
import os
import cv2
import imutils
import datetime
import thread
import Queue
from modules.detect_blur import DetectBlur
from modules.detect_motion import MotionDetector
from modules.detect_face import DetectFace
from copy import deepcopy
class framecontainer():
	def __init__(self,Image,imgno):
		self.Image=Image
		self.imgno=imgno


if __name__ == "__main__":
	
	# This parameter controls whether the program streams through camera (Normal Mode of Operation)
	# or through a recorded video (Debug Mode of Operation)
	cam_feed = False
	
	# Configuration is hard coded at this stage to avoid conflicts:
	
		# Cascade Classifier trained data
	CascPath="./app/data/haarcascade_frontalface_default.xml"
		# Configuration Parameters for FaceCascade Classifier
	scaleFactor=1.1
	minNeighbors=5
	minSize=(30,30)
		# Configuration Parameters for Face Detection Threading & Image Quality Verification
	FaceDetectionWorkers=4
	haar_thresh=35
	min_zero_thresh=0.01
		# Configuration Parameters for Camera
	rpiCam=True
	cameraNum=0
	width=800
	height=480
	fps=30
		# Configuration Parameters for Video
		# Video File Path:
	VidPath="./app/data/videos/example_03.mp4"

	
	# Initialization Stage of the program:
	if cam_feed:
		# Initialize the setup for Camera.
		# Import only in case of Camera to avoid conflicts on other machines.
		from modules.camera import Camera
		feed=Camera(rpiCam, cameraNum,width,height,fps)
		# Camera parameters are hard coded at this stage.
	else:
		# Initialize setup for video
		feed=cv2.VideoCapture(VidPath)
	
	# Sanity check and Initialization of "snapshots" folder in the data folder
	if not os.path.isdir("./app/data/snapshots"):
		os.mkdir("./app/data/snapshots")


	# First Program Cycle Declarations/Initializations:
		#Frame Number
	imgno=1
		#Initializing the motion detector module
	md=MotionDetector()
			#Configuring the motion detector
	md.motionsense=0
		# Face Detection Service Queue
	frameQ=Queue.Queue()
	verifyQ=Queue.Queue()
		#Initializing the face Cascade modules & FaceDetection Threads
		#Initializing the verification of captured image quality stage (Blur Detection)
	for ID in range(FaceDetectionWorkers):
		FaceCascade =cv2.CascadeClassifier(CascPath)
		thread.start_new_thread(DetectFace,(frameQ,verifyQ,scaleFactor,minNeighbors,minSize,FaceCascade,ID))
		thread.start_new_thread(DetectBlur,(verifyQ,haar_thresh,min_zero_thresh,ID))
	
		#Initializing the live feed GUI
	cv2.namedWindow("Feed")

	


	# The Loop section of the program: (Continous Loop)

	while True:
		

		# Feed code section
		if cam_feed:		
			frame = feed.grabframe()
			imgno+=1
		else:
			(grabbed, frame) = feed.read()
			imgno+=1
			if not grabbed:
				break # Exit at the end of the video


		# Resizing the frame to enhance the performance
		frame = imutils.resize(frame, width=800,height=480)


		# Time stamp the frame
		cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

		# Motion detection section
		motion, boxes = md.detectMotion(frame)
		
		# Handling Frames with Motion section
		if motion:
			md.reset() # Reseting the detector to avoid flooding the system
			
			# New background job for Face Detection Thread
			frameQ.put(framecontainer(deepcopy(frame),imgno))

			# GUI for live feed alert in case of Motion

			for (x, y, w, h) in boxes:
	        		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

	    		cv2.putText(frame, "Motion Detected", (10, 40),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

		
		else:
			# Normal text in case of no motion
			cv2.putText(frame, "No Motion", (10, 40),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)		
		
		# Updating the live feed
		cv2.imshow("Feed", frame)
			
		

		# Program Termination
		key = cv2.waitKey(1) & 0xFF
		if key != 255:
		    break
	#In case of using camera feed, release the resource
	frameQ.join()
	verifyQ.join()
	if cam_feed:
		feed.cleanup()
	#Destroy GUI elements		
	cv2.destroyAllWindows()

	
