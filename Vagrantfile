# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # online documentation at https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty64"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder "../", "/home/vagrant/shared"

  # Provider-specific configuration so you can fine-tune various backing providers for Vagrant. These expose provider-specific options.
  config.vm.provider "virtualbox" do |vb|
    vb.name = "mu-pypy"

    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

    # Customize the amount of memory on the VM:
    vb.memory = 2048
    vb.cpus = 2
  end

  # assumes that ../ contatins .ssh/ .gitconfig .gitignore_global
  config.vm.provision "shell", inline: <<-SHELL
    mkdir -p /home/vagrant/.dotfiles
    cp -r /home/vagrant/shared/.ssh /home/vagrant/shared/.gitconfig /home/vagrant/
    cp /home/vagrant/shared/.gitignore_global /home/vagrant/.dotfiles

    eval `ssh-agent`
    chmod -R 700 /home/vagrant/.ssh
    ssh-add

    echo 'deb https://dl.bintray.com/sbt/debian /' | sudo tee -a /etc/apt/sources.list.d/sbt.list
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 642AC823
    apt-get update
    apt-get install -y git gcc clang make libffi-dev pkg-config libz-dev libbz2-dev libsqlite3-dev libncurses-dev libexpat1-dev libssl-dev libgdbm-dev tk-dev libgc-dev pypy openjdk-7-jdk scala sbt python2.7 python-pip python-pytest
    apt-get upgrade -y

    echo '"\\e[A": history-search-backward' >> /home/vagrant/.inputrc
    echo '"\\e[B": history-search-forward' >> /home/vagrant/.inputrc
    echo 'export JAVA_HOME=$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")' >> /home/vagrant/.bashrc
    echo 'export MU=/home/vagrant/mu-impl-ref2' >> /home/vagrant/.bashrc
    echo 'export LD_LIBRARY_PATH=$MU/cbinding:$LD_LIBRARY_PATH' >> /home/vagrant/.bashrc
    echo 'export LIBRARY_PATH=$MU/cbinding:$LIBRARY_PATH' >> /home/vagrant/.bashrc
    echo 'export PYTHONPATH=$MU/pythonbinding:$MU/tools:$PYTHONPATH' >> /home/vagrant/.bashrc

    git clone https://gitlab.anu.edu.au/mu/mu-impl-ref2 /home/vagrant/mu-impl-ref2
    cd /home/vagrant/mu-impl-ref2
    sbt compile
    cd cbinding
    make

    chown vagrant:vagrant -R /home/vagrant
  SHELL
end
