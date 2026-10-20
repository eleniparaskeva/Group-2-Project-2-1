def get_camera_position(position, camera_offset_y_cm):
    if position is None:
        return None

    x, y, z = position

    # Distance must be positive
    if z <= 0:
        return None

    # Converting webcam coordinates to Panda3D's default coordinates
    camera_x = x
    camera_y = -z
    camera_z = y + camera_offset_y_cm 

    return camera_x, camera_y, camera_z

def get_lens_settings(camera_position, screen_width_cm, screen_height_cm):
    if camera_position is None:
        return None

    camera_x, camera_y, camera_z = camera_position

    film_size = (screen_width_cm, screen_height_cm)
    film_offset = (-camera_x, -camera_z)
    focal_length = -camera_y  # Distance from your eyes to the screen in cm

    return film_size, film_offset, focal_length

def apply_parallax(camera, lens, position, screen_width_cm,
                   screen_height_cm, camera_offset_y_cm):
    camera_position = get_camera_position(
        position, camera_offset_y_cm
    )

    if camera_position is None:
        return False

    film_size, film_offset, focal_length = get_lens_settings(
        camera_position,
        screen_width_cm,
        screen_height_cm
    )

    camera.setPos(*camera_position)
    camera.setHpr(0, 0, 0)

    lens.setFilmSize(*film_size)
    lens.setFocalLength(focal_length)
    lens.setFilmOffset(*film_offset)

    return True