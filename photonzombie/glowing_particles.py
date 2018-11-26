
def _random_pareto(a,minimum=1,maximum=np.inf):
    """
    Sample from a pareto distribution, forcing output to be between minimum
    and maximum.
    """

    b = np.random.pareto(a) + minimum
    if b > maximum:
        b = maximum

    return b


class GlowingParticleSprite:

    def __init__(self,
                 radius=1,
                 intensity=1,
                 hue=0.5,
                 num_rings=8,
                 expansion_factor=1.3,
                 alpha=1,
                 alpha_decay=1):
        """
        radius: particle radius
        intensity: how brightly the particle glows (0 to 1 scale)
        hue: hue (0 to 1 scale)
        num_rings: how many rings to expand out from the point source
        expansion_factor: how much bigger each ring is than the previous ring
        alpha: maximum alpha for center of particle (0 to 1 scale)
        alpha_decay: multiply alpha by this value for each new ring
        """

        if radius <= 0:
            err = "radius must be positive\n"
            raise ValueError(err)
        self._radius = radius

        if intensity < 0 or intensity > 1:
            err = "intensity must be between 0 and 1\n"
            raise ValueError(err)
        self._intensity = intensity

        if hue < 0 or hue > 1:
            err = "hue must be between 0 and 1\n"
            raise ValueError(err)
        self._hue = hue

        if num_rings < 1:
            err = "num_rings must be 1 or more.\n"
            raise ValueError(err)
        self._num_rings = num_rings

        if expansion_factor <= 1:
            err = "expansion factor must be > 1.\n"
            raise ValueError(err)
        self._expansion_factor = expansion_factor

        if alpha < 0 or alpha > 1:
            err = "alpha must be between 0 and 1\n"
            raise ValueError(err)
        self._alpha = alpha

        if alpha_decay <= 0:
            err = "alpha decay must be larger than 0\n"
            raise ValueError(err)
        self._alpha_decay = alpha_decay

        self._out_of_frame = False


    def _build_sprite(self):
        """
        Construct a bitmap representation of this particle.
        """

        # Create mini array to draw object
        size = self._radius*(self._expansion_factor**(self._num_rings - 1)) + 3
        self._size = int(np.ceil(size))
        img = np.zeros((2*self._size + 1,2*self._size + 1),dtype=np.float)

        # Find center of mini array for drawing
        center = self._size
        # Draw num_rings circles, expanding radius by expansion_factor each time
        # and dropping the alpha value by alpha_decay
        alpha = self._alpha
        radius = self._radius
        for i in range(self._num_rings):
            rr, cc = draw.circle(center,center,
                                 radius=radius)
            img[rr,cc] += alpha

            alpha = alpha*self._alpha_decay
            radius = int(round(radius*self._expansion_factor))

        # Normalize the array so it ranges from 0 to 1
        img = img/np.max(img)*self._intensity

        # Hue is set by user, value fixed at one, saturation is determined by
        # intensity
        hue =   np.ones(img.shape,dtype=np.float)*self._hue
        value = np.ones(img.shape,dtype=np.float)
        saturation = 1 - img

        col = np.stack((hue,saturation,value),2)
        rgb = np.array(255*matplotlib.colors.hsv_to_rgb(col),dtype=np.uint8)

        # Create output image, RGBA
        self._sprite = np.zeros((img.shape[0],img.shape[1],4),dtype=np.uint8)
        self._sprite[:,:,:3] = 255*matplotlib.colors.hsv_to_rgb(col)
        self._sprite[:,:,3] = self._alpha*255*img

    def write_to_image(self,img_matrix):
        """
        Write the sprite to an image.
        """

        # Now figure out where this should go in the output matrix
        x_min = int(np.round(self._coord[0] - self._size - 1))
        x_max = x_min + self.sprite.shape[0]
        y_min = int(np.round(self._coord[1] - self._size - 1))
        y_max = y_min + self.sprite.shape[1]

        i_min = 0
        i_max = self.sprite.shape[0]
        j_min = 0
        j_max = self.sprite.shape[1]

        # Deal with x/i-bounds
        if x_min < 0:

            i_min = abs(x_min)
            if i_min >= self.sprite.shape[0]:
                self._out_of_frame = True
                return img_matrix
            x_min = 0

        if x_max >= img_matrix.shape[0]:

            i_max = i_max - (x_max - img_matrix.shape[0])
            if i_max <= 0:
                self._out_of_frame = True
                return img_matrix
            x_max = img_matrix.shape[0]

        # Deal with y/j-bounds
        if y_min < 0:

            j_min = abs(y_min)
            if j_min >= self.sprite.shape[1]:
                self._out_of_frame = True
                return img_matrix
            y_min = 0

        if y_max >= img_matrix.shape[1]:

            j_max = j_max - (y_max - img_matrix.shape[1])
            if j_max <= 0:
                self._out_of_frame = True
                return img_matrix
            y_max = img_matrix.shape[1]

        # Update output matrix with the new output
        new_alpha = np.zeros((x_max-x_min,y_max-y_min),dtype=np.uint16)
        new_alpha[:,:] += img_matrix[x_min:x_max,y_min:y_max,3]
        new_alpha[:,:] += self.sprite[i_min:i_max,j_min:j_max,3]
        new_alpha[new_alpha>255] = 255

        img_matrix[x_min:x_max,y_min:y_max,:3] += self.sprite[i_min:i_max,j_min:j_max,:3]
        img_matrix[x_min:x_max,y_min:y_max,3] = new_alpha

        return img_matrix

    @property
    def sprite(self):
        return self._sprite

    @property
    def out_of_frame(self):
        return self._out_of_frame



class ParticleCollection:
    """
    """

    def __init__(self,
                 hue=0.5,
                 dimensions=(1080,1920),
                 radius_pareto=1.0,
                 radius_max=100,
                 intensity_pareto=1.0,
                 intensity_max=100):

        self._hue = hue
        self._dimensions = np.array(dimensions,dtype=np.int)
        self._radius_pareto = radius_pareto
        self._radius_max = radius_max
        self._intensity_pareto = intensity_pareto
        self._intensity_max = intensity_max

        self._num_particles = 0
        self._particles = []
        self.potentials = []

    def construct_particles(self,num_particles=50,use_potential=0,
                            num_equilibrate_steps=0):
        """
        Populate list of particles.

        num_particles: how many particles to create
        use_potential: which potential to sample from to generate x,y
                       coordinates of the particles. If less than one,
                       do not use a potential -- choose randomly.  If there
                       is no potential loaded, also sample randomly.
        """

        self._num_particles = num_particles

        for i in range(self._num_particles):

            radius = _random_pareto(self._radius_pareto,maximum=self._radius_max)
            intensity = _random_pareto(self._intensity_pareto,maximum=self._intensity_max)
            intensity = intensity/self._intensity_max

            if len(self.potentials) > 0 and use_potential >= 0:
                x, y = self.potentials[use_potential].sample_coord()
            else:
                x = np.random.choice(range(self._dimensions[0]))
                y = np.random.choice(range(self._dimensions[1]))

            p = physics.Particle(x,y,radius=radius)
            sprite = GlowingParticleSprite(radius,intensity,self._hue)

            self._particles.append((p,sprite))

        # equilibrate
        for i in range(num_equilibrate_steps):
            self.advance_time()

    def advance_time(self,dt=1.0):

        for p in self._particles:

            forces = np.array([0.0,0.0],dtype=np.float)
            for pot in self.potentials:
                forces += pot.get_forces(p[0].coord)
            p.advance_time(forces,dt)

    def write_out(self):
        """
        Write out sprites to an image array.
        """

        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particles:
            out_array = p.write_to_image(out_array)

        return out_array
