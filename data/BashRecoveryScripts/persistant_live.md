⚙️ OPTION 1 — Use mkusb (Recommended)
Even from the live session, you can install and use mkusb. You just have to fix networking first.

1. Fix Networking (“Server not found”)
Run:

sudo systemctl restart NetworkManager
ping -c 3 ubuntu.com
If that works, you’re online.

If not, reconnect manually:

Click the network icon → Connect to your Wi-Fi

Or use nmcli device wifi list and nmcli device wifi connect "SSID" password "PASSWORD"

Once you have internet, continue below.

2. Install mkusb (temporarily in RAM)
sudo add-apt-repository ppa:mkusb/ppa
sudo apt update
sudo apt install mkusb mkusb-plug
(This won’t persist after reboot, but that’s fine.)

3. Run mkusb
sudo mkusb
Then follow the prompts:

Choose your Ubuntu 24.04.3 ISO

Select Persistent live

Pick your target USB drive

Choose how much space to allocate for persistence (e.g., most of the USB)

Confirm and let it finish

✅ Result: a fully persistent Ubuntu 24.04.3 USB that saves files, settings, and packages.

🧩 OPTION 2 — Manual (No mkusb, No Internet)
If you can’t get internet, you can still make a persistent USB manually using only built-in tools.

Let’s say:

The USB drive is /dev/sdb

You already have ubuntu-24.04.3-desktop-amd64.iso in ~/Downloads

Steps
1. Write the ISO to USB

sudo dd if=~/Downloads/ubuntu-24.04.3-desktop-amd64.iso of=/dev/sdb bs=4M status=progress oflag=sync
(This will erase the USB!)

2. Create a persistence partition
After the ISO is written, open GParted or run:

sudo parted /dev/sdb
Inside parted:

(parted) mkpart primary ext4 4GB 100%
(parted) name 2 persistence
(parted) quit
3. Format the new partition

sudo mkfs.ext4 -L persistence /dev/sdb2
4. Add persistence config
Mount it:

sudo mkdir /mnt/persistence
sudo mount /dev/sdb2 /mnt/persistence
echo "/ union" | sudo tee /mnt/persistence/persistence.conf
sudo umount /mnt/persistence
✅ Now /dev/sdb2 is ready for persistence.

5. Boot with Persistence
When booting from the USB:

At the GRUB menu, highlight “Try Ubuntu without installing”

Press e to edit boot options

Find the line starting with linux and add persistent at the end

Press F10 or Ctrl+X to boot

Your session will now save data to the persistence partition.

Would you like me to give you a fully copy-pasteable script that does this all automatically (dd + partition + persistence setup) — so you can just run one command in your live session?




Attach

Search

Study

No file chosenNo file chosen
ChatGPT can make mistakes. Check important info. See Cookie Preferences.
2025-11-06 
2025-11-06 Trying to update/install apps on a recently installed version of iodeos from my laptop Ubuntu 24.04.3 now the laptop has crashed and I am working on that LUKS lvm so what I want to know is would they the apps only update on laptop 
