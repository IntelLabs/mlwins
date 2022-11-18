# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shard descriptor for CARLA."""

import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from openfl.interface.interactive_api.shard_descriptor import ShardDataset
from openfl.interface.interactive_api.shard_descriptor import ShardDescriptor
import subprocess

from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import glob
import os

import sys
import xml.etree.ElementTree as ET
import cv2
import time
from envoy_dai_2dbb_VOC import Envoy
import shutil

i = 1
# veh = 0
# all_imgs = []

class CARLAShardShardDataset(ShardDataset):
    """CARLA Shard Dataset class."""

    def __init__(self, X):
        """Initialize CARLAShardDataset."""
        self.X = X

    def __len__(self):
        """Count number of sequences."""
        return len(self.X)

    def __getitem__(self, index: int):
        """Return an item by the index."""
        return self.X[index]


class CARLAShardDescriptor(ShardDescriptor):
    """CARLA Shard descriptor class."""

    def __init__(self, envoy_name: str = '', port: int = 2000, tm_port: int = 8000, town_map: str = '') -> None:
        """Initialize CARLAShardDescriptor."""
        super().__init__()
        
        self.envoy_name = envoy_name
        # child_process = subprocess.Popen(['python3', 'envoy_dai_2dbb_VOC.py', '--name', envoy_name])
        # self.envoy = Envoy(envoy_name, port, tm_port, town_map)
        
        
    def get_dataset(self, dataset_type='train', labels=['vehicle', 'traffic light', 'traffic sign']):
        """Return a dataset."""
        if dataset_type == 'train':          
            ann_dir = '../_out/' + self.envoy_name + '/annotations/'
            img_dir = '../_out/' + self.envoy_name + '/images/'
            # for m in range(200):
            #     self.envoy.envoy_tick(m)
            global i
        else:
            ann_dir = '../' + dataset_type + '/' + self.envoy_name + '/annotations/'
            img_dir = '../' + dataset_type + '/' + self.envoy_name + '/images/'
            # another map Town01
            # ann_dir = '../' + dataset_type + '/annotations/'
            # img_dir = '../' + dataset_type + '/images/'

        all_imgs = []
        seen_labels = {}      
        veh = 0
        ann_list = os.listdir(ann_dir)
        if dataset_type == 'train':  
            ann_list.sort(key=lambda x: int(x[:-4]))
            if i > 10:
                ann_list = ann_list[(i-10)*100:i*100]
            else:
                ann_list = ann_list[:i*100]
        # img_list = os.listdir(img_dir)
        # img_list.sort(key=lambda x: int(x[:-4]))
        # if len(ann_list) > 1000:
        #     for files in ann_list[:len(ann_list)-1000]:
        #         os.remove(ann_dir+files)
        #     for files in img_list[:len(img_list)-1000]:
        #         os.remove(img_dir+files)
        for ann in ann_list:
            img = {'object':[]}

            if not os.path.exists(ann_dir+ann):
                print('ann_skip')
                continue
            tree = ET.parse(ann_dir + ann)
            
            for elem in tree.iter():
                if not os.path.exists(img_dir+ann[:-4]+'.jpg'):
                    print('img_skip')
                    continue 
                if 'filename' in elem.tag:
                    img['filename'] = os.path.abspath(img_dir) + '/' + elem.text #cv2.imread(img_dir + elem.text)
                if 'width' in elem.tag:
                    img['width'] = int(elem.text)
                if 'height' in elem.tag:
                    img['height'] = int(elem.text)
                if 'object' in elem.tag or 'part' in elem.tag:
                    obj = {}
                    
                    for attr in list(elem):
                        if 'name' in attr.tag:
                            obj['name'] = attr.text

                            if obj['name'] in seen_labels:
                                seen_labels[obj['name']] += 1
                            else:
                                seen_labels[obj['name']] = 1
                            
                            if len(labels) > 0 and obj['name'] not in labels:
                                break
                            else:
                                img['object'] += [obj]
                                veh += 1
                                
                        if 'bndbox' in attr.tag:
                            for dim in list(attr):
                                if 'xmin' in dim.tag:
                                    obj['xmin'] = int(round(float(dim.text)))
                                if 'ymin' in dim.tag:
                                    obj['ymin'] = int(round(float(dim.text)))
                                if 'xmax' in dim.tag:
                                    obj['xmax'] = int(round(float(dim.text)))
                                if 'ymax' in dim.tag:
                                    obj['ymax'] = int(round(float(dim.text)))

            if len(img['object']) > 0:
                all_imgs += [img] 
        if all_imgs == []:
            print('No objects captured, try again ...')
            test
            # i += 1
            return self.get_dataset()
        print('number of total images:', len(all_imgs))
        print('number of total objects:', veh)
        with open('../_out/' + dataset_type + self.envoy_name+'_count_imgs.txt', 'a') as fp_1:
            fp_1.write(str(len(all_imgs))+',')
        with open('../_out/' + dataset_type + self.envoy_name+'_count_objs.txt', 'a') as fp_2:
            fp_2.write(str(veh)+',')
        if dataset_type == 'train':    
            i += 1
        return all_imgs, seen_labels    
        
        # dirs = '../_out/'+self.envoy_name
        # images = []
        # for filename in glob.glob(dirs + '/*.png'):
        #     if not os.path.exists(filename):
        #         continue
        #     images.append(np.array(Image.open(filename).convert('RGB')))
        # print('Image loading done!')
        # print(len(images))

        # labels = []
        # for filename in glob.glob(dirs + '/*.xml'):
        #     if not os.path.exists(filename):
        #         continue
        #     labels.append(np.array(Image.open(filename).convert('RGB')))
        # print('Label loading done!')
        # print(len(labels))

        # return CARLAShardShardDataset(
        #     np.array(images)
        # )

        # import generate_tfrecord
        # parent_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
        # image_dir = '../_out/'+self.envoy_name + '/images'
        # output_path = '../_out/'+self.envoy_name + '/annotations/train.record'
        # labels_path = '../label_map.pbtxt'
        # generate_tfrecord.main(image_dir, output_path, labels_path)

    @property
    def sample_shape(self):
        """Return the sample shape info."""
        return ['600', '800', '3']

    @property
    def target_shape(self):
        """Return the target shape info."""
        return ['1']

    @property
    def dataset_description(self) -> str:
        """Return the dataset description."""
        return f'Dataset from {self.envoy_name} by CARLA'

    @staticmethod
    def load_data(path):
        """Load text file, return list of words."""
        file = open(path, 'r', encoding='utf8').read()
        data = re.findall(r'[a-z]+', file.lower())
        return data

    @staticmethod
    def get_sequences(data):
        """Transform words to sequences, for X transform to vectors as well."""
        # spacy en_core_web_sm vocab_size = 10719, vector_size = 96
        x_seq = []
        y_seq = []

        # created with make_vocab.py from
        # https://gist.github.com/katerina-merkulova/e351b11c67832034b49652835b14adb0
        NextWordShardDescriptor.download_vectors()
        vectors = pd.read_feather('keyed_vectors.feather')
        vectors.set_index('index', inplace=True)

        for i in range(len(data) - 3):
            x = data[i:i + 3]  # make 3-grams
            y = data[i + 3]
            cur_x = [vectors.vector[word] for word in x if word in vectors.index]
            if len(cur_x) == 3 and y in vectors.index:
                x_seq.append(cur_x)
                y_seq.append(vectors.index.get_loc(y))

        x_seq = np.array(x_seq)
        y_seq = np.array(y_seq)
        y = np.zeros((y_seq.size, 10719))
        y[np.arange(y_seq.size), y_seq] = 1
        return x_seq, y

    @staticmethod
    def download_data(title):
        """Download text by title form Github Gist."""
        url = ('https://gist.githubusercontent.com/katerina-merkulova/e351b11c67832034b49652835b'
               '14adb0/raw/5b6667c3a2e1266f3d9125510069d23d8f24dc73/' + title.replace(' ', '_')
               + '.txt')
        filepath = Path.cwd() / f'{title}.txt'
        if not filepath.exists():
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
        return filepath

    @staticmethod
    def download_vectors():
        """Download vectors."""
        if Path('keyed_vectors.feather').exists():
            return None

        output = 'keyed_vectors.zip'
        if not Path(output).exists():
            url = 'https://drive.google.com/uc?id=1QfidtkJ9qxzNLs1pgXoY_hqnBjsDI_2i'
            gdown.download(url, output, quiet=False)

        with zipfile.ZipFile(output, 'r') as zip_ref:
            zip_ref.extractall(Path.cwd())

        Path(output).unlink()  # remove zip
