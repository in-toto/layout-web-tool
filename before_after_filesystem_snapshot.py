def snapshot(before_dict, after_dict):
  '''before_after_snapshot is a simple function that returns which files were
    unchanged, modified, added or removed from an input dictionary (before_dict)
    and an output dictionary (after_dict). Both these dictionaries have file
    names as the keys and their hashes as the values.'''

  unchanged_files = []
  modified_files = []
  added_files = []
  removed_files = []
  for key in before_dict:
    if key in after_dict:
      if before_dict[key] == after_dict[key]:
        # Matching the hashes to check if file was unchanged
        unchanged_files.append(key)
      else:
        modified_files.append(key)
    else:
      removed_files.append(key)
  for key in after_dict:
    if key not in before_dict:
      # Looking for new files
      added_files.append(key)

  # Returning the snapshot of the new file system
  return (sorted(unchanged_files), sorted(modified_files), sorted(added_files),
  sorted(removed_files))
