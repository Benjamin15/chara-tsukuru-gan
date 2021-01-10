#!/usr/bin/env python

from __future__ import print_function

import numpy
import math

import chainer
from chainer import cuda
import chainer.functions as F
import chainer.links as L


def add_noise(h, sigma=0.2):
    xp = cuda.get_array_module(h.data)
    if chainer.config.train:
        return h + sigma * xp.random.randn(*h.shape)
    else:
        return h


class Generator(chainer.Chain):

    def __init__(self, n_hidden, bottom_width=4, ch=512, wscale=0.02):
        super(Generator, self).__init__()
        self.n_hidden = n_hidden
        self.ch = ch
        self.bottom_width = bottom_width

        with self.init_scope():
            w = chainer.initializers.Normal(wscale)
            self.l0 = L.Linear(self.n_hidden, bottom_width * bottom_width * ch,
                               initialW=w)
            self.dc1 = L.Deconvolution2D(ch, ch // 2, 4, 2, 1, initialW=w)
            self.dc2 = L.Deconvolution2D(ch // 2, ch // 4, 4, 2, 1, initialW=w)
            self.dc3 = L.Deconvolution2D(ch // 4, ch // 8, 4, 2, 1, initialW=w)
            self.dc4 = L.Deconvolution2D(ch // 8, 3, 3, 1, 1, initialW=w)


    def make_hidden(self, batchsize):
        return numpy.random.uniform(-1, 1, (batchsize, self.n_hidden, 1, 1))\
            .astype(numpy.float32)

    def show_hidden(self, batchsize, idx):
        step = 1/(batchsize-1)
        arrInd = range(0, self.n_hidden, 1)
        arr = numpy.zeros((batchsize, self.n_hidden, 1, 1))

        for kdn in range(batchsize):
            arr[kdn, arrInd[idx],0,0] = 4. * step * kdn - 2

        return arr.astype(numpy.float32)

    def walk_hidden(self, batchsize, start, end):
        arr = numpy.zeros((batchsize, self.n_hidden, 1, 1))

        arrStep = end - start
        step = arrStep / (batchsize - 1)

        for kdn in range(batchsize):
            for idx in range(0, self.n_hidden, 1):
                arr[kdn, idx,0,0] = start[idx] + step[idx] * kdn

        return arr.astype(numpy.float32)

    def pan_hidden(self, batchsize, idx):
        step = math.radians(90)/(batchsize-1)
        arrInd = range(0,self.n_hidden,1)
        arr = numpy.zeros((batchsize, self.n_hidden, 1, 1))

        for kdn in range(batchsize):
            arr[kdn, arrInd[idx],0,0] = 4. * math.cos(step * kdn)
            arr[kdn, arrInd[idx+1],0,0] = 4. * math.sin(step * kdn)

        return arr.astype(numpy.float32)

    def __call__(self, z):
        h = F.reshape(F.relu(self.l0(z)),
                      (len(z), self.ch, self.bottom_width, self.bottom_width))
        h = F.relu(self.dc1(h))
        h = F.relu(self.dc2(h))
        h = F.relu(self.dc3(h))
        x = F.sigmoid(self.dc4(h))
        return x


class Discriminator(chainer.Chain):

    def __init__(self, bottom_width=4, ch=512, wscale=0.02):
        w = chainer.initializers.Normal(wscale)
        super(Discriminator, self).__init__()
        with self.init_scope():
            self.c0_0 = L.Convolution2D(3, ch // 8, 3, 1, 1, initialW=w)
            self.c0_1 = L.Convolution2D(ch // 8, ch // 4, 4, 2, 1, initialW=w)
            self.c1_0 = L.Convolution2D(ch // 4, ch // 4, 3, 1, 1, initialW=w)
            self.c1_1 = L.Convolution2D(ch // 4, ch // 2, 4, 2, 1, initialW=w)
            self.c2_0 = L.Convolution2D(ch // 2, ch // 2, 3, 1, 1, initialW=w)
            self.c2_1 = L.Convolution2D(ch // 2, ch // 1, 4, 2, 1, initialW=w)
            self.c3_0 = L.Convolution2D(ch // 1, ch // 1, 3, 1, 1, initialW=w)
            self.l4 = L.Linear(bottom_width * bottom_width * ch, 1, initialW=w)

    def __call__(self, x):
        h = add_noise(x)
        h = F.leaky_relu(add_noise(self.c0_0(h)))
        h = F.leaky_relu(add_noise(self.c0_1(h)))
        h = F.leaky_relu(add_noise(self.c1_0(h)))
        h = F.leaky_relu(add_noise(self.c1_1(h)))
        h = F.leaky_relu(add_noise(self.c2_0(h)))
        h = F.leaky_relu(add_noise(self.c2_1(h)))
        h = F.leaky_relu(add_noise(self.c3_0(h)))
        return self.l4(h)
