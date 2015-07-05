#!/bin/bash
print_msg() {
  case $1 in
      "red" )
          msg="\e[1;31m $2" ;;
      "green" )
          msg="\e[1;32m $2" ;;
      "cyan" )
          msg="\e[1;36m $2" ;;
      *) 
          msg="\e[1;37m $2" ;;
  esac  
  echo -e "$msg \e[0m"
}


INST_DIR="/usr/local/bombo"

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   print_msg "red" "This script must be run as root" 1>&2
   exit 1
fi

if [ -d "$INST_DIR" ]; then
  print_msg "red" "The folder $INST_DIR already exists"
  print_msg "cyan" "Do you want to clean it up? (y/n)"

  read answ
  if [ "$answ" != "y" ]; then
   print_msg "red" "Exiting"
   exit
  fi

  rm -rf "$INST_DIR"
fi

CURR_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


print_msg "cyan" "Identifying OS..."
if [ -f /etc/debian_version ]; then
   OS=Debian
   VER=$(cat /etc/debian_version)
elif [ -f /etc/redhat-release ]; then
   OS=RedHat
   VER=$(cat /etc/debian_version)
fi;
print_msg "cyan" "OS $OS Version $VER"


print_msg "cyan" "Install pip for $OS"
if [ "$OS" == "Debian" ]; then
    sudo apt-get install -y python-pip
    sudo pip install --upgrade pip
elif [ "$OS" == "RedHat" ]; then
    yum -y install python-pip
fi;


print_msg "cyan" "Installing dependencies"
pip install redis boto

print_msg "cyan" "Copying files to $INST_DIR"
cp -R $CURR_DIR $INST_DIR

print_msg "cyan" "Removing git info"
rm -rf "$INST_DIR/.git"

print_msg "cyan" "Changing permissions to $INST_DIR"
chmod 755 -R $INST_DIR

print_msg "cyan" "Updating bin link"
rm -rf "/usr/bin/bombo"
ln -s "${INST_DIR}/bombo" "/usr/bin/bombo"

print_msg "green" "DONE! ;-)"
