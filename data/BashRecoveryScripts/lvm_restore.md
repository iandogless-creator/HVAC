# ======== HVAC System Backup Commands ========

# 1. Unlock the encrypted system partition
sudo cryptsetup open /dev/nvme0n1p3 cryptroot

# 2. Activate the LVM volume group
sudo vgchange -ay ubuntu-vg

# 3. Mount the root filesystem
sudo mkdir -p /mnt/ubuntu
sudo mount /dev/ubuntu-vg/ubuntu-lv /mnt/ubuntu

# 4. Mount the external backup drive
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
sudo cryptsetup open /dev/sdd1 hvacbackup
sudo mkdir -p /mnt/HVACbak
df -h | grep HVACbak
sudo mount /dev/mapper/hvacbakup /media/ubuntu/HVACbak

# 5. Backup home directory (replace 'youruser' with your actual username)
sudo rsync -aAXHv --progress /mnt/ubuntu/home/youruser/ /mnt/HVACbak/home-backup/

# 6. Optional: Create a date-stamped backup folder (uncomment if desired)
# DATE=$(date +%F)
# sudo rsync -aAXHv --progress /mnt/ubuntu/home/youruser/ /mnt/HVACbak/home-backup-$DATE/

# 7. Cleanly unmount everything when done
sudo umount /mnt/HVACbak
sudo umount /mnt/ubuntu
sudo vgchange -an ubuntu-vg
sudo cryptsetup close cryptroot

# ============================================
2025-11-06 
2025-11-06 I imported my phone no from Samsung galaxy a16 to this! Pixel 7 pro running on iodeos the no are not working would I have to change to +44 for instance!



