#!/usr/bin/env python
from __future__ import division
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import pyaudio

import threading
from Queue import Queue
import time
import sys
from numpy import *
from scipy import *
import scipy.signal as signal
from rtlsdr import RtlSdr
from numpy.fft import *
import cPickle



def recordSamples(sdr, idx, N_samples, y, chunk_size=1024):
    """
    Records the samples in chunked acquisitions.
    """
    samples_acquired = 0
    # Acquire the samples from an SDR
    while samples_acquired < N_samples:
        print "SDR %d: Acquired %d samples." % (idx, samples_acquired)
        y.put(sdr.read_samples(chunk_size))
        samples_acquired += chunk_size

    print "SDR %d: Acquired %d samples." % (idx, samples_acquired)
    sdr.close()
    print "SDR %d: Closed." % idx


def acquireSamplesAsync(fs, fc, t_total, chunk_size=1024, num_SDRs=3, gain=36):
    """
    Asynchronously acquire samples and save them.
    """

    assert type(t_total) == int, "Time must be an integer."
    N_samples = 1024000*t_total #1024000 256000 3.2e6
    SDRs = []

    # Initialize the SDRs
    for i in xrange(num_SDRs):
        sdr_i = RtlSdr(device_index=i)
        sdr_i.sample_rate = fs
        sdr_i.center_freq = fc
        sdr_i.gain = gain
        SDRs.append(sdr_i)

    # Setup the output queues
    output_queues = [Queue() for _ in xrange(num_SDRs)]

    rec_thrds = []

    # Create the thread objects for acquisition
    for i, sdr_i in enumerate(SDRs):
        y = output_queues[i]
        sdr_rec = threading.Thread(target=recordSamples, \
                          args=(sdr_i, i, N_samples, y, N_samples))
        rec_thrds.append(sdr_rec)

    # Start the threads
    for rec_thread in rec_thrds:
        rec_thread.start()


    # Wait until threads are done
    while any([thrd.is_alive() for thrd in rec_thrds]):
        time.sleep(1)
        """
        for i, size in enumerate(last_size):
            curr_size = output_queues[i].qsize()
            if not done_arr[i] and size == curr_size:
                #rec_thrds[i].terminate()
                done_arr[i] = True
            else:
                last_size[i] = curr_size
        """

    # For DEBUG
    samples = []
    for i, q in enumerate(output_queues):
        print "Printing Queue %d" % i
        print "\t- Queue size: %d" % q.qsize()
        samples.append([])
        while not q.empty():
            print q.qsize()
            samples[i] += list(q.get())

        print "Done"

    np.save('demo.npy',samples)
    for i in range(num_SDRs-1):
        assert len(samples[i]) == len(samples[i+1])

    return samples


if __name__ == "__main__":
    acquireSamplesAsync(fs=1e6, fc=434.1e6, t_total=1, gain=1, num_SDRs=2)
