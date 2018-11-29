

face_stacks = pyfx.find_face_stacks(img_list,"shape_predictor_68_face_landmarks.dat")
left_eye_coord = face_stacks[0].get_centroid("left_eye")[1][0]
right_eye_coord = face_stacks[0].get_centroid("right_eye")[1][0]

left_eye_sprite = pyfx.sprites.GlowingParticle(radius=4)
right_eye_sprite = pyfx.sprites.GlowingParticle(radius=4)

left_eye_coord = {}
right_eye_coord = {}
for f in face_stacks:

    r = f.get_centroid("right_eye")

    rt = r[0]
    rc = r[1][0]

    for i in range(len(rt)):
        to_write = (rc[i,1],rc[i,0])
        try:
            right_eye_coord[rt[i]].append(to_write)
        except KeyError:
            right_eye_coord[rt[i]] = [to_write]

    l = f.get_centroid("left_eye")

    lt = l[0]
    lc = l[1][0]

    for i in range(len(lt)):
        to_write = (lc[i,1],lc[i,0])
        try:
            left_eye_coord[lt[i]].append(to_write)
        except KeyError:
            left_eye_coord[lt[i]] = [to_write]
