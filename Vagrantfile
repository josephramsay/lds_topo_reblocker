# -*- mode: ruby -*-
# vi: set ft=ruby :

################################################################################
#
# Copyright 2013 Crown copyright (c)
# Land Information New Zealand and the New Zealand Government.
# All rights reserved
#
# This program is released under the terms of the new BSD license. See the
# LICENSE file for more information.
#
################################################################################

#
### CONFIGURATION SECTION
#

Vagrant.require_version ">= 1.8.0"

box = "bento/ubuntu-14.04"

# Canonical cloud box.
# box = "trusty-canonical"
# box_url_base = "http://cloud-images.ubuntu.com/vagrant/trusty/current"
# box_url_name = "trusty-role-cloudimg-amd64-vagrant-disk1.box"
# box_url = box_url_base + "/" + box_url_name

require 'socket'
require 'open-uri'
require 'uri'

# if corp_address then on corp network
# if on corp network then read proxy_address
#   use proxy_address to fetch cntlm.deb
#   flag virtuals to install/use cntlm

CNTLM32 = "https://sourceforge.net/projects/cntlm/files/cntlm/cntlm%200.92.3/cntlm_0.92.3_i386.deb"
CNTLM64 = "https://sourceforge.net/projects/cntlm/files/cntlm/cntlm%200.92.3/cntlm_0.92.3_amd64.deb"
CNTLMXX = "deploy/packages/cntlm.deb"

# LINZ IP address
corp_address = Socket.ip_address_list.find { |ai| ai.ip_address.start_with?('10.80.','144.66.') }.ip_address
print "LOCip=",corp_address,"\n"
if corp_address && ENV['http_proxy']
    #handle proxy vars of the form http://xxx{4}..:pppp/ or xxx{4}..:pppp
    proxy_array = ENV['http_proxy'].scan(URI.regexp)[0]
    proxy_address = "%{h}:%{p}" % {:h=>proxy_array[3], :p=>proxy_array[4]} if proxy_array[0].start_with?('http')
    proxy_uri = URI.parse("http://%{pa}/" % {:pa=>proxy_address})
    print "PXYip=",proxy_address,"\n"
    if !File.exist?(CNTLMXX)
        File.open(CNTLMXX,"wb") do |saved_file|
            open(CNTLM64,"rb",:proxy=>proxy_uri) do |read_file|
                saved_file.write(read_file.read)
            end
        end
    end
end

PASSWD = "ansible-password.txt"
#IFACE = "enp0s3"
IFACE = "eth1"
PROJ = "vagrant"
ROLES = {
    "basic" => {
        "memory" => "512",
        "ports" => [
            ["1111", "11111"],
        ],
        "count" => "1",
    },    

    "database" => {
        "memory" => "2048",
        "ports" => [
            ["5432", "15432"],
        ],
        "count" => "1",
    },

    "webclient" => {
        "memory" => "512",
        "ports" => [
            ["1111", "11111"],
        ],
        "count" => "1",
    },
        
    "webserver" => {
        "memory" => "512",
        "ports" => [
            ["80", "8080"],
        ],
        "count" => "1",
    },
}

#
### DON'T CHANGE ANYTHING UNDER THIS LINE
#

Vagrant.configure(2) do |config|

    # config.vm.box_url = box_url
    config.vm.box = box

    config.ssh.forward_agent = true
    config.vm.synced_folder '.', '/vagrant'

    # loop over all configured roles
    ROLES.select{|k,v| k!="basic"}.each do | (role, cfg) |
        print "Building role #{role}"
        
        insts = Array.new

        # loop over all role instances`(defined by role count)
        (1..cfg["count"].to_i).each do |i|

            if i == 1
                host = "#{role}"
            else
                host = "#{role}-#{i}"
            end
            
            config.vm.define host do |inst|

                insts.push(host)

                # IP address
                inst.vm.network "private_network", type: "dhcp"

                # hostname
                inst.vm.hostname = host

                # ports forwarding
                cfg["ports"].each do | port |
                    inst.vm.network "forwarded_port",
                        guest: port[0],
                        host: port[1],
                        auto_correct: true
                end
            
                # PROXY SHELL PROVISIONER
                inst.vm.provision "shell", inline: <<-SHELL
                    dpkg -s cntlm >/dev/null 2>&1
                    if [ $? -eq 1 ]; then
                        dpkg -i #{'/vagrant/'+CNTLMXX}
                    fi
                SHELL


                ### PRODUCTION DEPLOYMENT
                inst.vm.provision "deploy", type: "ansible" do |ansible|
                    ansible.playbook = "deploy/#{role}.yml"
                    ansible.limit = "all"
                    ansible.verbose = "vv"
                    ansible.groups = {
                        "#{role}" => insts,
                    }
                    ansible.extra_vars = {
                        HOST_NAME: "#{host}",
                        PROJECT_NAME: PROJ,
                        ROLE_NAME: "#{role}",
                        SYSTEM_NETWORK_DEVICE: IFACE,
                        SYSTEM_INTERFACE_ADDRESS: corp_address,
                        SYSTEM_PROXY_ADDRESS: proxy_address,
                    }
                    # load password from file if exists
                    if File.exist?(PASSWD)
                        ansible.vault_password_file = PASSWD
                    else
                        ansible.ask_vault_pass = true
                    end
                end
            end #config.vm.define host do |inst|
        end #(1..cfg["count"].to_i).each do |i|
    end #ROLES.each do | (role, cfg) |
end #Vagrant.configure(2)
