__description__ = \
"""
"""

import numpy as np

class Particle:
    """
    Generic particle.  The particle is defined by three intrinsic
    characteristics: radius, mass and charge.  It
    """

    def __init__(self,x,y,radius=1.0,charge=1.0,kT=1.0,mass=None):

        self._coord = np.array((x,y),dtype=np.float)
        self._radius = radius
        self._charge = charge
        self._kT = kT

        if mass is None:
            self._mass = 4/3*np.pi*(self._radius**3)
        self._velocity = np.random.normal(0,2*self._kT,2)
        self._forces = np.array((0,0),dtype=np.float)

    def advance_time(self,forces=None,dt=1.0):

        if forces is None:
            self._forces = np.array((0.0,0.0),dtype=np.float)

        # dt is defined as 1
        self._accel = self._forces/self._mass
        new_vel = self._accel*dt + self._velocity
        self._coord = (dt*dt)*self._accel/2 + (dt)*(self._velocity + new_vel)/2 + self._coord
        self._velocity = np.copy(new_vel)

    @property
    def radius(self):
        return self._radius

    @property
    def mass(self):
        return self._mass

    @property
    def charge(self):
        return self._charge

    @property
    def coord(self):
        return self._coord

    @property
    def velocity(self):
        return self._velocity
