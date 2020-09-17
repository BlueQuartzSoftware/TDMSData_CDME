import argparse
import h5py
import nptdms
import numpy as np
import re

from contextlib import ExitStack
from pathlib import Path
from typing import Any, AnyStr, Dict, Generator, List, Match, Pattern

FILE_VERSION: int = 3
VERSION_KEY: str = 'Version'
SLICES_KEY: str = 'TDMSData'
INDEX_KEY: str = 'Index'
LAYER_START_TIME_KEY: str = 'LayerStartTime'
LAYER_END_TIME_KEY: str = 'LayerEndTime'
PART_START_TIME_KEY: str = 'PartStartTime'
PART_END_TIME_KEY: str = 'PartEndTime'
TDMS_GROUP_NAME_KEY: str = 'TDMS_GroupName'
VERTICES_KEY: str = 'Vertices'

def _write_tdms_properties(h5_group: h5py.Group, tdms_dict: Dict[str, Any], replacements: Dict[str, str]) -> None:
  key: str
  value: Any
  for key, value in tdms_dict.items():
    if key in replacements:
      key = replacements[key]
    if isinstance(value, np.datetime64):
      h5_group.attrs[key] = str(np.datetime_as_string(value, unit='us', timezone='UTC'))
    else:
      h5_group.attrs[key] = value

def tdms2h5(input_dir: Path, output_dir: Path, prefix: str, area_offset: int, intensity_offset: int, laser_offset: int, groups: List[str] = [], verbose: bool = False) -> None:
  largest_offset = max(area_offset, intensity_offset)

  if not output_dir.exists():
    if verbose:
      print(f'Creating directory \"{output_dir}\"')
    output_dir.mkdir(parents=True)

  paths_generator: Generator[(Path, None, None)] = input_dir.glob('*.[Tt][Dd][Mm][Ss]')
  regex_name: Pattern[AnyStr] = re.compile(fr'{prefix}(\d+)')

  with ExitStack() as exitStack:
    h5_files: Dict[str, h5py.File] = {}
    slice_indices: List[int] = []

    path: Path
    for path in filter(lambda item: regex_name.search(item.stem), paths_generator):
      if verbose:
        print(f'Converting \"{path}\"')

      match: Match[AnyStr] = regex_name.search(path.stem)
      slice_index = int(match.group(1))
      slice_indices.append(slice_index)

      with nptdms.TdmsFile(path) as tdmsFile:
        bitgain_os_1: float = tdmsFile.properties['Bitgain OS 1']
        bitgain_os_2: float = tdmsFile.properties['Bitgain OS 2']

        group: nptdms.TdmsGroup
        for group in tdmsFile.groups():
          if groups and not any(re.match(pattern, group.name) for pattern in groups):
            continue
          
          output_file_path = output_dir / f'{group.name}.h5'
          if group.name not in h5_files:
            h5_files[group.name] = exitStack.enter_context(h5py.File(output_file_path, 'w'))
            h5_file = h5_files[group.name]
            h5_file.attrs[VERSION_KEY] = FILE_VERSION
            h5_group = h5_file.create_group(SLICES_KEY)
            h5_group.attrs[TDMS_GROUP_NAME_KEY] = group.name
          h5_file = h5_files[group.name]
          h5_group: h5py.Group = h5_file[SLICES_KEY].create_group(str(slice_index))

          layer_replacements = {
            'StartTime' : LAYER_START_TIME_KEY,
            'EndTime' : LAYER_END_TIME_KEY
          }
          _write_tdms_properties(h5_group, tdmsFile.properties, layer_replacements)

          part_replacements = {
            'StartTime' : PART_START_TIME_KEY,
            'EndTime' : PART_END_TIME_KEY
          }
          _write_tdms_properties(h5_group, group.properties, part_replacements)

          # LaserTTL only uses laser_offset. The end has to be adjusted to make the resulting array consistent
          laser_channel: nptdms.TdmsChannel = group['LaserTTL']
          laser_end_index: int = len(laser_channel) - (laser_offset)
          h5_group.create_dataset(laser_channel.name, data=laser_channel[laser_offset : laser_end_index])

          # Intensity and Area use laser_offset
          area_channel: nptdms.TdmsChannel = group['Area']
          # At this point for illustrative purposes, since the laser_offset is always the largest
          end_index: int = len(area_channel) - (area_offset)
          h5_group.create_dataset(area_channel.name, data=area_channel[area_offset : end_index])

          intensity_channel: nptdms.TdmsChannel = group['Intensity']
          end_index: int = len(intensity_channel) - (intensity_offset)          
          h5_group.create_dataset(intensity_channel.name, data=intensity_channel[intensity_offset : end_index])

          # Have not figured out how to correlate parameter to the actual parameter used, just use the same as Laser TTL since it is a machine setting
          parameter_channel: nptdms.TdmsChannel = group['Parameter']
          h5_group.create_dataset(parameter_channel.name, data=parameter_channel[:])

          # X and Y channels just adjust the maximum
          x_channel: nptdms.TdmsChannel = group['X-Axis']
          x_dataset = h5_group.create_dataset(x_channel.name, data=(x_channel[:] / bitgain_os_1), dtype=np.float32)
          x_dataset.attrs['Units'] = 'μm'

          y_channel: nptdms.TdmsChannel = group['Y-Axis']
          y_dataset = h5_group.create_dataset(y_channel.name, data=(y_channel[:] / bitgain_os_2), dtype=np.float32)
          y_dataset.attrs['Units'] = 'μm'

          # Resulting slices will be aligned with the same number of data points for each channel

    slice_indices = sorted(slice_indices)

    for h5_file in h5_files.values():
      index_dataset = np.zeros((len(slice_indices), 3), dtype=np.int64)
      for i, index in enumerate(slice_indices):
        index_dataset[i][0] = index
        index_dataset[i][1] = h5_file[SLICES_KEY][str(index)].attrs['layerThickness']
        index_dataset[i][2] = h5_file[SLICES_KEY][str(index)]['X-Axis'].size
      dataset: h5py.Dataset = h5_file.create_dataset(INDEX_KEY, data=index_dataset)
      dataset.attrs['Column0'] = 'SliceIndex'
      dataset.attrs['Column1'] = 'LayerThickness (μm)'
      dataset.attrs['Column2'] = 'NumVertices'

    if verbose:
      print('\nWrote files:')
      h5_file: h5py.File
      for h5_file in h5_files.values():
        print(f'  \"{h5_file.filename}\"')

def main() -> None:
  parser = argparse.ArgumentParser(description='Converts TDMS files to a HDF5 format. Input files must be named in the following regex format \"[prefix]\\d+.tdms\"')
  parser.add_argument('input_dir', type=Path, help='Input directory where .tdms files are located')
  parser.add_argument('output_dir', type=Path, help='Output directory where .h5 files are generated')
  parser.add_argument('prefix', help='Specifies the file prefix to search for as regex.')
  parser.add_argument('-g', '--groups', nargs='+', help='Specifies which TDMS groups should be converted')
  parser.add_argument('-v', '--verbose', action='store_true', help='Prints additional information while converting')
  parser.add_argument('-a', '--area-offset', type=int, default=0, help='Area index offset (CamOffset)')
  parser.add_argument('-i', '--intensity-offset', type=int, default=0, help='Intensity index offset (PhdOffset)')
  parser.add_argument('-l', '--laser-offset', type=int, default=0, help='Laser index offset')
  args = parser.parse_args()

  if args.verbose:
    print('args:')
    print(f'  input_dir = \"{args.input_dir}\"')
    print(f'  output_dir = \"{args.output_dir}\"')
    print(f'  prefix = \"{args.prefix}\"')
    print(f'  groups = {args.groups}')
    print(f'  verbose = {args.verbose}')
    print(f'  area-offset = {args.area_offset}')
    print(f'  intensity-offset = {args.intensity_offset}')
    print(f'  laser-offset = {args.laser_offset}')
    print('')

  tdms2h5(args.input_dir, args.output_dir, args.prefix, args.area_offset, args.intensity_offset, args.laser_offset, args.groups, args.verbose)

if __name__ == '__main__':
  main()
