from os import walk
import pygame

def import_folder(path: str):
    surface_list = []

    for _, __, img_files in walk(path):
        for img in img_files:
            full_path = path + '/' + img
            img_surf = pygame.image.load(full_path).convert_alpha()
            surface_list.append(img_surf)

    return surface_list

def import_folder_dict(path):
    surface_dict = {}

    for _, __, img_files in walk(path):
        for img in img_files:
            full_path = path + '/' + img
            img_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[img.split('.')[0]] = img_surf

    return surface_dict
