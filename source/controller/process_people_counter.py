import threading
import cv2
import time
from source.gui.frm_camera import FrmCamera
import socket
import multiprocessing
import sys
import numpy

from source.utils import const
from source.utils.depthmapCalculator import DepthmapCalculator
from source.utils.videoStreamer import VideoStreamer
from source.utils.backgroundSubtraction import BackgroundSubtraction
from source.utils.ObjectMoving import ObjectMoving
from source.utils.detectObject import DetectMoving
from source.utils.trackingObject import TrackingObj
import numpy as np
import cv2.cv
from source.learningMachine.detect import Detector


class PC_Manager(object):
    def __init__(self, ip_address, threadClient, root_tk, lock, queue_update_pc):
        self.threadClient = threadClient
        self.ip_address = ip_address
        # self.queue_process_to_frm = multiprocessing.Queue()
        self.root = root_tk
        # self.frm_camera = FrmCamera(self.root, lock, self.queue_process_to_frm)
        self.lock = lock

        self.queue_wait_stop = multiprocessing.Queue()
        self.thread_wait_stop = threading.Thread(target = self.wait_value_queue)
        # self.running = True
        # create process
        self.process_pc = Process_People_Counter(self.ip_address, queue_update_pc, self.queue_wait_stop)

    def start(self):
        self.process_pc.start()
        self.thread_wait_stop.start()
        # self.process_pc.join()
        # self.lock.acquire()
        # self.frm_camera.toplevel.after(0, func=lambda: self.frm_camera.update_video())
        # self.lock.release()

    def stop(self):
        try:
            self.queue_wait_stop.close()
            # self.thread_wait_stop.join()
        except Exception,ex:
            print 'STOP thread_wait_stop ' + str(ex)
            pass

        self.process_pc.stop()
        try:
            self.process_pc.terminate()
        except Exception, ex:
            print 'Process terminate exception ' + str(ex)
            pass
        try:
            self.process_pc.join()
        except Exception, ex:
            print 'Process join exception ' + str(ex)
            pass

    def wait_value_queue(self):
            try:
                value = self.queue_wait_stop.get()
                self.threadClient.remove_client(self.ip_address)
            except Exception, ex:
                print 'Thread wait_value_queue ' + str(ex)
                pass


# video recorder


class Process_People_Counter(multiprocessing.Process):
    def __init__(self, ip_address, queue_update_pc, queue_wait_stop):
        multiprocessing.Process.__init__(self)
        self.ip_address = ip_address
        self.queue_update_pc = queue_update_pc
        self.running = True
        self.queue_wait_stop = queue_wait_stop
        # create dgram udp socket
        try:
            self.pi_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            print 'Failed to create socket'
            return

    def stop(self):
        print 'STOP PROCESS START'
        self.running = False
        try:
            self.pi_socket.sendto(const.CMD_DISCONNECT, (self.ip_address, const.PORT))
        except:
            pass
        try:
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(const.CMD_CONNECT, ('localhost', const.PORT))
        except Exception, ex:
            print 'socket.socket Exception ???' + str(ex)
            pass
        try:
            self.pi_socket.close()
        except Exception, ex:
            print 'pi_socket cannot close ???' + str(ex)
        try:
            self.queue_wait_stop.put(const.STOP_PROCESS)
        except:
            pass
        print 'STOP PROCESS END'
        return

    def run(self):
        print "I'm here " + self.ip_address

        # load calibration data to calculate depth map
        depthmapCalculator = DepthmapCalculator('../../data/calibration2')

        # calibrate camera
        calibration = depthmapCalculator.get_calibration()

        # init block matcher (SGBM) to calculate depth map
        block_matcher = depthmapCalculator.get_block_macher()

        # init background subtraction
        backgroundSubtraction = BackgroundSubtraction()

        # init detector
        detector = Detector(min_window_size=(150, 150), step_size=(30, 30), downscale=1)

        # init tracking
        trackObj = TrackingObj(self.queue_update_pc)

        # subtract moving object
        imgObjectMoving = ObjectMoving(150, 150, 30)

        detectMoving = DetectMoving(150)

        # if videoStreamer.connect_pi():
        count = 0
        font = cv2.FONT_HERSHEY_SIMPLEX
        cdetect = 0

        try:
            # Set the whole string
            port = const.PORT
            if ":" in self.ip_address:
                arr = self.ip_address.split(":")
                self.ip_address = arr[0]
                port = int(arr[1])
            self.pi_socket.sendto(const.CMD_CONNECT, (self.ip_address, port))
            self.pi_socket.settimeout(5)
            print 'send ok'

            # CODEC = cv2.cv.CV_FOURCC('M','P','4','V') # MPEG-4 = MPEG-1
            #
            # video_writer_right = cv2.VideoWriter("outputR24.avi", CODEC, 24, (352, 288))
            #
            # video_writer_left = cv2.VideoWriter("outputL24.avi", CODEC, 24, (352, 288))

            while self.running:
                t1 = time.time()
                reply, addr = self.pi_socket.recvfrom(50000)
                try:
                    arr = reply.split('daicahuy')
                    dataRight = numpy.fromstring(arr[0], dtype='uint8')
                    dataLeft = numpy.fromstring(arr[1], dtype='uint8')
                    image_right = cv2.imdecode(dataRight, 1)
                    image_left = cv2.imdecode(dataLeft, 1)
                    # cv2.imshow('SERVER RIGHT', image_right)
                    # cv2.imshow('SERVER LEFT', image_left)
                    # video_writer_right.write(image_right)
                    # video_writer_left.write(image_left)
                    depthmap = depthmapCalculator.calculate(image_left, image_right, block_matcher, calibration)
                    # depthmap = 255 - depthmap
                    cv2.imshow("depthmap", depthmap)
                    # if count % 10 == 0:
                    #     self.queue_update_pc.put(const.TYPE_IN)
                    if count > 1:
                        mask, display = backgroundSubtraction.compute(depthmap)
                        # if np.sum(display) > 100:
                        #     print "capture" + str(count)
                        # cv2.imwrite("capture/" + str(count) + ".jpg", display)

                        cv2.imshow("back1", display)
                        # res,pon1,pon2 = imgObjectMoving.getImgObjectMoving(mask)
                        # if res:
                        #     # cv2.rectangle(display,pon1, pon2,(255,255,255), 2)
                        #     if count>74:
                        #         im_detected = detector.detect(display[pon1[1]:pon2[1],pon1[0]:pon2[0]])
                        #     # cv2.imshow("back", display)
                        #         cv2.imshow("back", im_detected)
                        trackObj.resetTracking()
                        data, data150 = detectMoving.detectObjectInImage(display)
                        # if len(data150) > 0:
                        #     for y in data150:
                        #         # print y
                        #         imgx = display[y[0][1]:y[1][1],y[0][0]:y[1][0]]
                        # cv2.rectangle(image_left,y[0], y[1],(255,255,255), 1)
                        # cv2.imwrite("image/"+str(count)+'.jpg', imgx)

                        if len(data) > 0:
                            for x in data:
                                print x
                                # print x[0], x[1]
                                # print x[1][0] - x[0][0], x[1][1] - x[0][1]
                                # ckObj = trackObj.check_Obj(x[0],x[2])
                                # if ckObj == False:
                                #     cdetect+=1
                                #     print cdetect

                                cv2.rectangle(image_left, x[0], x[1], (255, 255, 255), 1)
                                if detector.detect1(display, x[0], x[1], x[2]):
                                    trackObj.trackingObj(x[0], x[2])
                                    # cv2.rectangle(image_left,x[0], x[1],(255,255,255), 1)
                                    # else:
                                    cv2.rectangle(image_left, x[0], x[1], (255, 255, 255), 5)
                                else:
                                    y = (detectMoving.CheckRectDetect(x[0], x[1], x[2], 352, 288))
                                    imgx = display[y[0][1]:y[1][1], y[0][0]:y[1][0]]
                                    # cv2.imwrite("image/failed/"+str(count)+'.jpg', imgx)
                        trackObj.remove_track()
                        cv2.line(image_left, (0, 144 - 70), (352, 144 - 70), (255, 255, 255), 1)
                        cv2.line(image_left, (0, 144), (352, 144), (255, 255, 255), 1)
                        cv2.line(image_left, (0, 144 + 70), (352, 144 + 70), (255, 255, 255), 1)
                        cv2.putText(image_left, 'In: %i' % trackObj.InSh, (160, 20), font, 0.5, (255, 255, 255), 1)
                        cv2.putText(image_left, 'Out: %i' % trackObj.OutSh, (160, 276), font, 0.5, (255, 255, 255), 1)
                        cv2.imshow("back", image_left)

                    # print "-----------------------------" + str(count)

                    # if res:
                    #     cv2.rectangle(display,pon1, pon2,(255,255,255), 2)
                    # print trackObj.allObj
                    # print 'fps = ' + str(1 / (time.time() - t1))
                    count += 1
                    char = cv2.waitKey(1)

                    if (char == 99):
                        #     count += 1
                        #     cv2.imwrite(str(count)+'.jpg', display)
                        #     video_writer_right.release()
                        #     video_writer_left.release()
                        print trackObj.InSh, trackObj.OutSh

                        cv2.waitKey(0)
                    if (char == 27):
                        break
                except Exception, ex:
                    print 'Thread_Listening_Socket WHILE Exception: ' + str(ex)

        except Exception, ex:
            print 'Thread_Listening_Socket Exception: ' + str(ex)

        self.stop()
