import re
import subprocess
import os
import shutil
import time
import libvirt

def populate_domain(domain):
 pass
def grab_mac(domain):
  #THIS FUNCTION NEEDS TO HAVE AN EXCEPTION WRAPPER 
  create_call = subprocess.Popen(['virsh dumpxml ' + domain], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  stdout = create_call.communicate()[0]
  regex_str = '<interface type=.network.>\n      <mac address=.(..:..:..:..:..:..)./>'
  unparsed_mac = re.findall(regex_str, stdout)
  return unparsed_mac[0]
def find_open_ip(network):
  #THIS FUNCTION NEEDS AN EXCEPTION WRAPPER
  create_call = subprocess.Popen(['virsh net-dumpxml ' + network], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  stdout1 = create_call.communicate()[0]
  regex_str1 = '<range start=.\d\d\d.\d\d\d.\d\d\d.(\d{1,3}). end=\'\d\d\d.\d\d\d.\d\d\d.\d{1,3}./>'
  regex_str2 ='<host mac=...:..:..:..:..:... name=.*? ip=\'\d\d\d.\d\d\d.\d\d\d.\d{1,3}./>'
  find_bottom = re.findall(regex_str1, stdout1)
  hosts_list = re.findall(regex_str2, stdout1)
#  hosts_list.append(['ubuntu14.04'])
  used_ips = []
  used_ips_ints = []
  regex_str3 = '\d\d\d.\d\d\d.\d\d\d.(\d{1,3})'
  regex_str4 = '\d\d\d.\d\d\d.\d\d\d.\d{1,3}'
#  network_ip = re.findall(regex_str4, hosts_list[0])[0]
  network_ip = '192.168.122.'
  for x in hosts_list:
    if re.findall(regex_str3, x):
      used_ips.append(re.findall(regex_str3, x))
  for y in used_ips:
    used_ips_ints.append(int(y[0]))
  print used_ips_ints
  for a in range(2, int(find_bottom[0])):
    for y in used_ips_ints:
      if y == a:
        break
    else:
      yield network_ip + str(a)
class kvm_domain():
  #I'M SURE THIS IS GOING TO GET EXTENDED - Used for Cloud API
  def __init__(self, name, disk='none', network='default', description='TestVM', os='Ubuntu14.04',os_t='Linux',
  ram='4096', cpu='2', exists=0, ipconfig='rc', running='off', ip='None', conn=[], dom=[]):
    self.name = name
    self.disk = disk
    self.network = network
    self.description = description
    self.os = os
    self.os_t = os_t
    self.ram = ram
    self.cpu = cpu
    self.exists = exists
    self.ipconfig = ipconfig
    self.conn = conn
    self.dom = dom
  def get_libvirt_conn(self):
    conn2=libvirt.open("qemu:///system")
    self.conn.append(conn2)
    print self.conn
  def create_domain(self):
    #REFACTOR THIS INTO SOMETHING MORE GENERIC
    if self.exists == 1:
      print 'domain already exists'
      return 0
    create_call = subprocess.Popen(['virt-install -n ' + self.name + ' --description ' + self.description +
    ' --os-type=' + self.os_t + ' --os-variant=' + self.os +  ' --ram ' + self.ram +  ' --vcpus=' + self.cpu +  ' --disk path=' + self.disk +
    ' --graphics spice' +  ' --network ' + self.network + ' --import --video qxl --channel spicevmc  --wait=0'],
    shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = create_call.communicate()[0]
    if self.exists == 0:
      self.exists = 1
    print stdout
    return 1
  def start_domain(self):
     create_call = subprocess.Popen(['virsh start ' + self.name], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
     stdout = create_call.communicate()[0]
     print 'starting domain'
  def destroy_domain(self):
     create_call = subprocess.Popen(['virsh destroy ' + self.name], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
     stdout = create_call.communicate()[0]
     print 'destroying domain'

  def get_libvirt_self(self):

    #NEEDS TRY EXCEPT FOR WHEN I FORGET TO HANDLE THE CONNECTION PROPERLY

    if self.conn:
      dom2 = self.conn[0].lookupByName(self.name)
      self.dom.append(dom2)
    else:
      self.get_libvirt_conn()
      dom2 = self.conn[0].lookupByName(self.name)
      self.dom.append(dom2)
      print 'conn on else'



  def consistency_check(self):
    pass
  def check_run_state(self):
    pass
  def set_domain_ip(self):

    #REFACTOR THIS FOLLOWING CHECK_RUN_STATE BEING CODED

    if self.ipconfig == 'rc':
      mac =  grab_mac(self.name)
      open_ip_addr = find_open_ip('default')
      print mac
      open_ip_addr = open_ip_addr.next()
      print open_ip_addr
      self.check_mac(mac, open_ip_addr)
      self.destroy_domain()
      time.sleep(15)
      self.start_domain()
      self.ip = open_ip_addr
  def undefine_and_cleanup(self):
    create_call = subprocess.Popen(['virsh undefine ' + self.name], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = create_call.communicate()[0]
  def check_mac(self, mac, openIPADDR):
    create_call = subprocess.Popen(['virsh net-dumpxml ' + self.network], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = create_call.communicate()[0]
    regex_str = mac
    if re.findall(regex_str, stdout):
      print 'Mac Is Already Present'
    else:
      create_call = subprocess.Popen(['virsh net-update --network default --command add --section ip-dhcp-host --xml "<host mac=\'' + mac + '\' name=\'' + self.name + '\' ip=\'' + openIPADDR + '\'/>" --live --config'], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
      stdout = create_call.communicate()[0]
      print('Assigned Mac to ip address ' + openIPADDR)
  def snap_domain(self, snap='lame', setactive=0):

    #MAKE SURE THIS WORKS ON ODD CASES MAYBE INCLUDE SOME NICE WRAPPERS

    if setactive == 0:
      create_call = subprocess.Popen(['virsh snapshot-create ' +self.name +' --disk-only --no-metadata'], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
      stdout = create_call.communicate()[0]
      regex_str = 'Domain snapshot (.*?) created'
      print stdout
      snapname = re.findall(regex_str, stdout)
      return snapname[0]
    elif setactive == 1:
      snap__current = self.snap_target(snap)
      regex_str = '/var/lib/libvirt/images/(.*?)'
      active_disk = re.findall(regex_str, snap__current)
      active_disk = active_disk[0]
      print active_disk
      print active_disk
      create_call2 = subprocess.Popen(['virsh snapshot-create-as --domain ' +self.name +' --name ' + active_disk +'.active  --disk-only --no-metadata'], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
      stdout = create_call2.communicate()[0]

  def grab_xml_domain(self):

    #Included for a planned refactor - low priority
    pass

  def find_snap_current(self):

    #NEEDS EXCEPTION HANDLING AND CASE HANDLING
    #NEEDS TO BE SETUP FOR MULTI CASE
    #INVESTIGATE OPTIONS IN THE LIBVIRT API FOR CHECKPOINTING

    list_o_xml = os.listdir('/etc/libvirt/qemu')
    regex_str5 = self.name
    file_name = 'nah'
    for item2 in list_o_xml:
      lame3 =  re.findall(regex_str5, item2)
      if lame3:
        file_name = item2
        file_path = ('/etc/libvirt/qemu/' + file_name)
        if os.path.isfile(file_path):
          with open(file_path, 'r') as f:
            read_data = f.read()
            re_str = '<disk type=\'file\' device=\'disk\'>.*?<source file=\'(.*?)\'/>.*?<target dev=\'vda\' bus=\'virtio\'/>'
            temp2 = re.findall(re_str, read_data, re.DOTALL)
            if temp2[0]:
              print 'temp2'+temp2[0]
              print temp2[0]
              return temp2[0]
            else:
              pass
  def snap_target(self, snap1):

    #THIS FUNCTION NEEDS CONFLICT RESOLUTION! DON'T FORGET POTENTIALLY CLIENT SIDE IMPACT

    list_o_targets = os.listdir('/var/lib/libvirt/images/')
    regex_str5 = str(snap1)
    file_name = 'nah'
    for item2 in list_o_targets:
      lame3 =  re.findall(regex_str5, item2)
      if lame3:
        print lame3
        print 'double cool'
        return '/var/lib/libvirt/images/'+item2

  def revert_domain(self, snap2, setactive=1):
    list_o_xml = os.listdir('/etc/libvirt/qemu')
    regex_str6 = self.name
    file_path_xml = ''
    file_name_xml = 'nah'
    for item3 in list_o_xml:
      lame4 =  re.findall(regex_str6, item3)
      if lame4:
        if lame4[0]:
          file_path_xml = '/etc/libvirt/qemu/' + item3
    #REFACTOR THIS FOLLOWING THE IMPLIMENTATION OF PONDER - HIGH PRIORITY
    #REFACTOR THIS FOR FULL USAGE OF PYTHON BINDINGS ON CUT OVER TO LIBVIRT API INSTEAD OF STRING PARSING


    create_call = subprocess.Popen(['virsh autostart ' +self.name +' --disable'], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = create_call.communicate()[0]
    self.destroy_domain()
    target = self.snap_target(snap2)
    print 'Targetis='+target
    current = self.find_snap_current()
    replacexml = ''
    print 'current='+current
    with open(file_path_xml, 'r') as f:
      read_data = f.read()
      replacexml = re.sub(current, target, read_data)
    with open('/root/python/tmp.xml', 'w') as fo:
      fo.write(replacexml)
    self.get_libvirt_self()
    self.dom[0].undefine()
    shutil.copy2('/root/python/tmp.xml', file_path_xml)
    self.conn[0].defineXML(replacexml)
    #create_call7 = subprocess.Popen(['virsh define ' + self.name /root/python/tmp.xml], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    #stdout = create_call7.communicate()[0]

 #   self.snap_domain(snap=snap2 ,setactive=1)
 #   self.start_domain()
  def list_snaps(self):
    pass

  def check_existence(self):
    list_d = Get_Domains()
    list_a = [self.name]
    value = listCompare(list_d, list_a)
    if value == 1:
      return 0
    else:
      return 1
  def Create_Base_VM(self):
    name = Decide_Name()
    self.name = name
    disk_path = '/var/lib/libvirt/images/' + name + '.img'
    self.Clear_DHCP()
    if os.path.isfile(disk_path):
      pass
    else:
      shutil.copy2('/var/lib/libvirt/golden/ubuntu14.04.Golden.img', disk_path)
      self.disk = disk_path
      self.exists = self.check_existence()
    if self.exists == 0:
      self.create_domain()
      self.set_domain_ip()
      print 'Domain Created'
    else:
      print 'Domain Exists'


  def Clear_DHCP(self):
    domain_list = Get_Domains()
    domain_list.append('ubuntu14.04')
    print domain_list
    regex_str = '<host mac=\'..:..:..:..:..:..\' name=\'(.*?)\' ip=\'.*?\'/>'
    create_call = subprocess.Popen(['virsh net-dumpxml ' + self.network], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout = create_call.communicate()[0]
    list_e_DHCP = re.findall(regex_str, stdout)
    list_e_DHCP.append('')
    s1 = set(domain_list)
    s2 = set(list_e_DHCP)
    s3 = s2 - s1
    print s3
    for item in s3:
      regex_str1 = '(<host mac=\'..:..:..:..:..:..\' name=\'' + item + '\' ip=\'.*?\'/>)'
      temp = re.findall(regex_str1, stdout)
      print 'virsh net-update --network default --command delete --section ip-dhcp-host --xml \"' + temp[0] +'\"   --live --config'
      create_call2 = subprocess.Popen(['virsh net-update --network default --command delete --section ip-dhcp-host --xml \"' + temp[0] +'\"  --live --config'],
      shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
      stdout2 = create_call2.communicate()[0]
      print stdout2

class domain_snap_tree():
  def __init__(self, name):
    self.name = name

class domain_snap_object():
  def __init__(self, domain, name):
    self.domain = domain
    self.name = name

def Decide_Name():
  List_d = Get_Domains()
  Base_Name = 'UbuntuSnapTest'
  list_a = ['']
  a = 0
  b = 0
  while a != 1:
    list_a.pop()
    Attempt_Name = list_a.append(Base_Name + str(b))
    a = listCompare(List_d, list_a)
    b = b + 1
  return list_a[0]

def listCompare(list1, list2):
  if [item for item in list1 if item in list2]:
    return 0
  else:
    return 1 #Does not exist

def Get_Domains():
  create_call = subprocess.Popen(['virsh list --all --name'], shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  stdout = create_call.communicate()[0]
  regex_str = '(.*?)\n'
  List_of_domains = re.findall(regex_str, stdout)
  return List_of_domains


#list_o_snaps = []
#TestVM = kvm_domain('blah')
#TestVM.Create_Base_VM()
#TestVM.snap_domain()
Blah = kvm_domain('UbuntuSnapTest4')
Blah.snap_domain()
#Blah.revert_domain('UbuntuSnapTest4.img')


#dom = TestVM.get_libvirt_self()
#print dom
#conn = TestVM.get_libvirt_conn()
