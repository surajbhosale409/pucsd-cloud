# Creating zpool
  sudo zpool create <poolname> /dev/loop12  
  [ if need to create a lvm]:
  sudo dd if=/dev/zero of=<filename.img> seek=<size_in_bytes>
  sudo zpool create <poolname> <filename.img>
