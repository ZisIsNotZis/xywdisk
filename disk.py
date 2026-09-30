import os
import numpy as np
from scipy.optimize import lsq_linear
from pymodbus.client import ModbusTcpClient
from socket import create_connection
from time import sleep

# Device endpoints were hard-coded to a private bench network. They are now
# read from the environment so the code can be published and re-pointed.
HEAT_HOST = os.getenv("HEAT_HOST", "localhost")
HEAT_PORT = int(os.getenv("HEAT_PORT", "502"))
PTM_HOST = os.getenv("PTM_HOST", "localhost")
PTM_PORT = int(os.getenv("PTM_PORT", "502"))
SENSOR_HOST = os.getenv("SENSOR_HOST", "localhost")
SENSOR_PORT = int(os.getenv("SENSOR_PORT", "9090"))
DATA_PATH = os.getenv("DISK_DATA", "real4.47f,34f")

def F(x, t=10, eps=.02):
    print(x)
    X[I] = x
    heat.write_registers(5, (x[:7]*100).astype('H').tolist())
    ptm.write_registers(4085, (x[:7]*400).astype('H').tolist())
    ptm.write_register(4211, 65535)
    y = []
    while len(y)<t or abs(y[-1]-y[-t]).max()>eps:
        sleep(1.1)
        sensr.send(b'GetData')
        y += [np.array(sensr.recv(999)[:-1].split(b',')[-34:],'f')]
    y = sum(y[-t:])/t
    print(y.mean(), 3*y.std())
    Y[I] = y-120.1
    I[()] += 1
    return Y[I-1]
heat = ModbusTcpClient(HEAT_HOST, port=HEAT_PORT)
heat.connect()
print('heat ok')
heat.write_register(801, 12000)
ptm = ModbusTcpClient(PTM_HOST, port=PTM_PORT)
ptm.connect()
print('ptm ok')
sensr = create_connection((SENSOR_HOST, SENSOR_PORT))
print('sensr ok')

class Jac:
    def __init__(s, X, Y, x, y, inv=0, k=.5):
        if inv:
            X,Y,x,y = Y,X,y,x
        s._ = np.exp(np.linalg.norm(X-x,axis=1,keepdims=1)**k/-.5**k)
        s._ = np.linalg.lstsq((X-x)*s._,(Y-y)*s._)[0]
        if not inv:
            s._ = s._.T
    def __call__(s, x, y, root=0, mi=0, ma=3):
        return lsq_linear(s._,y.astype('d'),(x-ma,x-mi)).x if root else y@s._
    def step(s, dx, dy, inv=0, eps=1e-9):
        s._ += (s._@dx)[:,None]*(dx-dy@s._)/(dy@s._@dx+eps)if inv else(dy-s._@dx)[:,None]*dx/(np.linalg.norm(dx)+eps)
class Line:
    _ = 1
    def __call__(s, x, g, y, J, eps=1e-9):
        return x-min(y@J@g/(np.linalg.norm(J@g)+eps),s._)*g
    def step(s, dx, y, J, l, dl):
        _ = (np.linalg.norm(y+J@dx)-l)/dl
        print('line', s._, _)
        if _>.25:
            if _>.75:
                s._ *= 2
            return 1
        s._ *= .25
class Jit:
    _ = .1
    def __call__(s, x):
        return x+s._*np.random.randn(len(x))*x.clip(.1)
    def step(s, dl):
        print('jit', s._)
        s._ *= .96
def lsq1(a, b, mi, ma):
    x = min(max(a@b/np.linalg.norm(a)**2, mi), ma)
    return x, np.linalg.norm(a*x-b)
def root(f, X, Y, I=None, mi=0, ma=3, epoch=128, it=1, R=.1):
    i = np.linalg.norm(Y[:I],axis=1).argmin()
    x = X[i]
    y = Y[i]
    l = np.linalg.norm(y)
    line = Line()
    jit = Jit()
    for i in range(epoch):
        J = Jac(X[:I], Y[:I], x, y)
        for j in range(it):
            g = J(x, y)
            x_ = jit(line(x, g, y, J._)).clip(mi, ma)
            y_ = f(x_)
            l_ = np.linalg.norm(y_)
            J.step(x_-x, y_-y)
            jit.step(l_-l)
            if line.step(x_-x, y, J._, l, l_-l):
                x,y,l = x_,y_,l_
    return l

X = np.memmap(DATA_PATH, '47f,34f', shape=9999)
Y = X['f1']
X = X['f0']
I = np.array(Y.any(1).argmin())
Y[I:] = 0
for i in range(I, 47):
    F(np.array([2*(j==i)for j in range(47)]))
if I==48:
    F(np.ones(47))
raise
i = np.linalg.norm(Y[:I], axis=1).argmin()
x = X[i]
y = Y[i]
w = JFit(X[:I], Y[:I], x, y).T
while True:
    ks = [lsq1(w,y,-x,3-x)for x,w in zip(x,w)]
    print(ks)
    i,(k,s) = min(enumerate(ks), key=lambda iks:iks[1][1]+np.random.rand()*.03)
    # k = np.sign(k)*max(abs(k), x[i]*.1)
    print(I, i, x[i], k, s)
    x[i] = (x[i]+k).clip(0,3)
    y,y_ = F(x),y
    w[i] = (y-y_)/k
# root(F, X, Y, I)