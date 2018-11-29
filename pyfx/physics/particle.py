
import numpy as np

class Particle:
    """
    Generic particle.  The particle is defined by three intrinsic
    characteristics: radius, mass and charge.  It has two main coordinates:
    x,y coordinates; x,y velocities.
    """

    def __init__(self,coord=(0.0,0.0),velocity=(0.0,0.0),
                 radius=1.0,charge=1.0,density=1.0):

        self._coord = np.array(coord,dtype=np.float)
        self._velocity = np.array(velocity,dtype=np.float)
        self._radius = radius
        self._charge = charge
        self._density = density

        self._mass = 4/3*np.pi*(self._radius**3)*self._density

        self._forces = np.array((0,0),dtype=np.float)

    def advance_time(self,forces=None,dt=1.0):

        if forces is None:
            self._forces = np.array((0.0,0.0),dtype=np.float)
        else:
            self._forces = np.copy(forces)

        # dt is defined as 1
        self._accel = self._forces/self._mass
        new_vel = self._accel*dt + self._velocity
        self._coord = (dt*dt)*self._accel/2 + (dt)*(self._velocity + new_vel)/2 + self._coord
        self._velocity = np.copy(new_vel)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self,radius):
        self._radius = radius

    @property
    def density(self):
        return self._density

    @density.setter
    def density(self,density):
        self._density = density

    @property
    def mass(self):
        return self._mass

    @property
    def charge(self):
        return self._charge

    @charge.setter
    def charge(self,charge):
        self._charge = charge

    @property
    def coord(self):
        return self._coord

    @coord.setter
    def coord(self,coord):
        self._coord = np.array(coord)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self,velocity):
        self._velocity = np.array(velocity)
