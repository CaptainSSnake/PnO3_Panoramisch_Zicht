import numpy as np
from mpi4py import MPI
from picamera import PiCamera
import cv2 as cv
from time import time, sleep
from threading import Thread

from stream import Receiver, StreamRecorder, FrameBuffer, send, transform, RESOLUTION, FRAMERATE, running

def senderloop2(camera, comm):
    record_buffer = FrameBuffer()
    transform_buffer = FrameBuffer()
    with StreamRecorder(camera, record_buffer) as recorder:
        camera.start_recording(recorder, 'rgb')
        begin = time()
        transform_thread = Thread(target=transform, args=(record_buffer, transform_buffer))
        send_thread = Thread(target=send, args=(comm, transform_buffer))
        
        transform_thread.start()
        send_thread.start()
        sleep(10)
        running = False
        end = time()
        print(f'time {end-begin}')
        camera.stop_recording()

def senderloop(camera, comm):
    sender = StreamSender(comm)
    camera.start_recording(sender, 'mjpeg')
    begin = time()
    while True:
        sender.send()
        sleep(0.01)
        if time() - begin > 10:
            break
    end = time()
    print(f'time {end-begin}')
    camera.stop_recording()
        
        
def receiverloop(camera, comm):
    with StreamRecorder(camera, comm) as recorder:
        camera.start_recording(recorder, 'rgb')
        recv = Receiver(comm)
        
        while True:
            own_image = recorder.get_frame()
            
            if own_image is not None:
                data = recv.read()
                
#                 t = Thread(target=ShowImages, args = (data,own_image))
#                 t.start()
#                 t.join()
                if data is None:
                    print('stop recording')
                    camera.stop_recording()
                    print('stopped recording')
                    break


def ShowImages(other_image, own_image):
    cv.imshow('andere', other_image)
    cv.imshow('eigen', own_image)
    cv.waitKey(0)

def main():
    print('test')
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    #size = comm.Get_size()
    hostname = MPI.Get_processor_name()
       
    with PiCamera(resolution=RESOLUTION, framerate=FRAMERATE) as camera:
        print('start')
        comm.Barrier()
        if rank == 1:
            senderloop2(camera, comm)
        elif rank == 0:
            receiverloop(camera, comm)

        print('stop')


if __name__ == '__main__':
    main()
