echo "Setting up environment for $USER:"
sudo mkdir -p $HOME 
sudo chown $USER:pi $HOME
cp -a /etc/skel/. $HOME/.

echo "Mounting $USER's home directory:"
#ZFS_SERVER_IP=192.168.43.5
ZFS_SERVER_IP=192.168.0.102
sudo mount -t nfs -o port=3049 localhost:/zfs-storage/students/$USER $HOME
#sudo mount -t nfs $ZFS_SERVER_IP:/zfs-storage/students/$USER $HOME
cd $HOME
