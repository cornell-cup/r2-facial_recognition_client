"""
Heavily drawn from https://pypi.org/project/face-recognition/
"""
import os
from typing import Mapping, Tuple, Union

import numpy
import face_recognition

CACHE_LOCATION = '.cache'
IMG_EXTs = ['.jpg', '.jpeg', '.png']


def load_images(path: str, mappings: Mapping[str, numpy.ndarray] = None,
                cache: bool = True, cache_location: str = CACHE_LOCATION) -> \
                Union[Tuple[str, numpy.ndarray], Mapping[str, numpy.ndarray]]:
    """
    Loads in the image(s) from the given path.

    PARAMETERS
    ----------
    path
        The path to the image or directory.
    mappings
        The mappings to update with the added filenames
    cache
        Whether to cache the files as they are loaded.
    cache_location
        The directory of the cache to check, default specified by
        CACHE_LOCATION

    RETURNS
    -------
        A Mapping of names to encodings if path is a directory, a single
        Tuple of name & encoding if the path is a file, and raises an exception
        otherwise.
    """
    mappings = {} if mappings is None else mappings

    def check_and_add(path_, file_):
        filename_ = file_[:file_.rindex('.')]
        if cache:
            # Following EAFP idiom.
            try:
                mappings[filename_] = get_cached(file_, cache_location)
            except OSError:
                # DNE in cache
                encoding = face_recognition.face_encodings(
                    face_recognition.load_image_file(os.path.join(path_, file_))
                )[0]
                add_cache(filename_, encoding, cache_location)
                mappings[filename_] = encoding

        else:
            mappings[filename_] = face_recognition.face_encodings(
                face_recognition.load_image_file(os.path.join(path_, file_))
            )[0]

    if os.path.isdir(path):
        for _, _, files in os.walk(path):
            for file in files:
                ext_idx = file.rindex('.')
                if file[ext_idx+1] in IMG_EXTs:
                    print(f'{file} was loaded in as a recognized face.')
                    filename = file[:file.rindex('.')]
                    check_and_add(path, filename)
    elif os.path.isfile(path):
        ext_idx = path.rindex('.')
        if path[ext_idx+1] not in IMG_EXTs:
            print('Warning: file being explicitly loaded does not have .jpg '
                  'extension. Make sure this is actually an image file.')
        # os.path.split should return head and tail, path and filename
        # respectively
        check_and_add(*os.path.split(path))
    else:
        raise RuntimeError(f'The path given ({path}) is not a directory or '
                           f'file.')
    return mappings


def get_cached(name: str, cache_location: str = CACHE_LOCATION):
    return numpy.load(os.path.join(cache_location, f'{name}.encoding'),
                      allow_pickle=False)


def add_cache(name: str, encoding: numpy.ndarray,
              cache_location: str = CACHE_LOCATION):
    with open(os.path.join(cache_location, f'{name}.encoding'), 'rb+') as f:
        f.seek(0)
        f.truncate()
        f.write(encoding.tobytes())


def check_faces(img: numpy.ndarray, mappings: Mapping[str, numpy.ndarray]):
    ordered_map = list(mappings.items())
    known_encodings = map(lambda x: x[1], ordered_map)
    unknown_face_locations = face_recognition.face_locations(img)
    unknown_face_encodings = face_recognition.face_encodings(
        img, unknown_face_locations)

    identities = []
    for unknown_face in unknown_face_encodings:
        matches = face_recognition.compare_faces(known_encodings, unknown_face)
        face_distances = face_recognition.face_distance(known_encodings,
                                                        unknown_face)
        closest_idx = numpy.argmin(face_distances)
        distance = face_distances[closest_idx]
        name = ordered_map[closest_idx][0] if matches[closest_idx] else \
            'Unknown'
        print(f'Face was {distance} away from {name}.')

        identities.append(name)
    return identities, unknown_face_locations