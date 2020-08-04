import argparse
import h5py
import nptdms
import numpy as np
import re

from contextlib import ExitStack
from glob import glob
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Match, Pattern

FILE_VERSION: int = 2
VERSION_KEY: str = 'Version'
SLICES_KEY: str = 'Slices'
INDEX_KEY: str = 'Index'
LAYER_START_TIME_KEY: str = 'LayerStartTime'
LAYER_END_TIME_KEY: str = 'LayerEndTime'
PART_START_TIME_KEY: str = 'PartStartTime'
PART_END_TIME_KEY: str = 'PartEndTime'
TDMS_GROUP_NAME_KEY: str = 'TDMS_GroupName'
VERTICES_KEY: str = 'Vertices'

def tdms2h5(input_dir: str, output_dir: str, groups: List[str] = [], verbose: bool = False) -> None:
  glob_pattern = Path(input_dir) / '*.tdms'
  paths: List[str] = glob(str(glob_pattern))
  regex_file: Pattern[AnyStr] = re.compile(r'Slice\d+.tdms$')
  regex_name: Pattern[AnyStr] = re.compile(r'Slice(\d+)')
  
  with ExitStack() as exitStack:
    h5_files: Dict[str, h5py.File] = {}
    slice_indices: List[int] = []

    path: str
    for path in filter(regex_file.search, paths):
      if verbose:
        print(f'Converting \"{path}\"')
      
      input_file_path = Path(path)
      match: Match[AnyStr] = regex_name.search(input_file_path.stem)
      slice_index = int(match.group(1))
      slice_indices.append(slice_index)
      
      with nptdms.TdmsFile(path) as tdmsFile:
        group: nptdms.TdmsGroup
        for group in tdmsFile.groups():
          if groups and group.name not in groups:
            continue
          
          output_file_path = Path(output_dir) / f'{group.name}.h5'
          if group.name not in h5_files:
            h5_files[group.name] = exitStack.enter_context(h5py.File(output_file_path, 'w'))
            h5_file = h5_files[group.name]
            h5_file.attrs[VERSION_KEY] = FILE_VERSION
            h5_group = h5_file.create_group(SLICES_KEY)
            h5_group.attrs[TDMS_GROUP_NAME_KEY] = group.name
          h5_file = h5_files[group.name]
          h5_group: h5py.Group = h5_file[SLICES_KEY].create_group(str(slice_index))

          key: str
          value: Any
          for key, value in tdmsFile.properties.items():
            if key == 'StartTime':
              key = LAYER_START_TIME_KEY
            elif key == 'EndTime':
              key = LAYER_END_TIME_KEY
            if isinstance(value, np.datetime64):
              h5_group.attrs[key] = np.string_(np.datetime_as_string(value, unit='us', timezone='UTC'))
            else:
              h5_group.attrs[key] = value
          
          key: str
          value: Any
          for key, value in group.properties.items():
            if key == 'StartTime':
              key = PART_START_TIME_KEY
            elif key == 'EndTime':
              key = PART_END_TIME_KEY
            if isinstance(value, np.datetime64):
              h5_group.attrs[key] = np.string_(np.datetime_as_string(value, unit='us', timezone='UTC'))
            else:
              h5_group.attrs[key] = value
          
          channel: nptdms.TdmsChannel
          for channel in group.channels():
            h5_group.create_dataset(channel.name, data=channel.data)
    
    for h5_file in h5_files.values():
      total_vertices = 0
      index_dataset = np.zeros((len(slice_indices), 2), dtype=int)
      for i, index in enumerate(slice_indices):
        total_vertices += h5_file[SLICES_KEY][str(index)]['X-Axis'].size
        index_dataset[i][0] = index
        index_dataset[i][1] = h5_file[SLICES_KEY][str(index)].attrs['layerThickness']
      h5_file[SLICES_KEY].attrs[VERTICES_KEY] = total_vertices
      h5_file.create_dataset(INDEX_KEY, data=index_dataset)
    
    if verbose:
      print('\nWrote files:')
      for file_path in h5_files:
        print(f'  \"{file_path}\"')

def main() -> None:
  parser = argparse.ArgumentParser(description='Converts TDMS files to a HDF5 format. Input files must be named in the following regex format \"Slice\\d+.tdms\"')
  parser.add_argument('input_dir', help='Input directory where .tdms files are located')
  parser.add_argument('output_dir', help='Output directory where .h5 files are generated')
  parser.add_argument('-g', '--groups', nargs='+', help='Specifies which TDMS groups should be converted')
  parser.add_argument('-v', '--verbose', action='store_true', help='Prints additional information while converting')
  args = parser.parse_args()

  if args.verbose:
    print('args:')
    print(f'  input_dir = \"{args.input_dir}\"')
    print(f'  output_dir = \"{args.output_dir}\"')
    print(f'  groups = {args.groups}')
    print(f'  verbose = {args.verbose}')
    print('')

  tdms2h5(args.input_dir, args.output_dir, args.groups, args.verbose)

if __name__ == '__main__':
  main()
