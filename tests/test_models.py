from unittest import TestCase

from mock import Mock
from vnc_api.vnc_api import Project, SecurityGroup

from cvm.models import (ID_PERMS, VirtualMachineInterfaceModel,
                        VirtualMachineModel, VirtualNetworkModel)


class TestVirtualMachineModel(TestCase):
    def setUp(self):
        self.vmware_vm = Mock()
        self.vmware_vm.summary.runtime.host.vm = []

    def test_to_vnc(self):
        vm_model = VirtualMachineModel(self.vmware_vm)
        vm_model.uuid = 'd376b6b4-943d-4599-862f-d852fd6ba425'
        vm_model.vrouter_ip_address = '192.168.0.10'

        vnc_vm = vm_model.to_vnc()

        self.assertEqual(vnc_vm.name, vm_model.uuid)
        self.assertEqual(vnc_vm.uuid, vm_model.uuid)
        self.assertEqual(vnc_vm.display_name, vm_model.vrouter_ip_address)
        self.assertEqual(vnc_vm.fq_name, [vm_model.uuid])


class TestVirtualNetworkModel(TestCase):
    def test_construct_alloc_pool(self):
        ip_range = '192.168.1.1#20'
        start_ip = '192.168.1.1'
        end_ip = '192.168.1.20'

        allocation_pool = VirtualNetworkModel._construct_alloc_pool(ip_range)

        self.assertEqual(allocation_pool.start, start_ip)
        self.assertEqual(allocation_pool.end, end_ip)

    def test_construct_alloc_pool_list(self):
        self.assertEqual(VirtualNetworkModel._construct_alloc_pool_list(None), None)
        self.assertEqual(VirtualNetworkModel._construct_alloc_pool_list(1), [1])


class TestVirtualMachineInterfaceModel(TestCase):
    def setUp(self):
        self.project = Project()
        self.security_group = SecurityGroup()

        vmware_vm = Mock()
        vmware_vm.summary.runtime.host.vm = []
        vmware_vm.config.hardware.device = []
        self.vm_model = VirtualMachineModel(vmware_vm)
        self.vm_model.uuid = 'd376b6b4-943d-4599-862f-d852fd6ba425'
        self.vm_model.vrouter_ip_address = '192.168.0.10'

        vmware_vn = Mock()
        vmware_vn.config.key = '123'
        vnc_vn = Mock(name='VM Network', uuid='d376b6b4-943d-4599-862f-d852fd6ba425')
        self.vn_model = VirtualNetworkModel(vmware_vn, vnc_vn, None)

    def test_to_vnc(self):
        vmi_model = VirtualMachineInterfaceModel(self.vm_model, self.vn_model, self.project, self.security_group)

        vnc_vmi = vmi_model.to_vnc()

        self.assertEqual(vnc_vmi.name, vmi_model.uuid)
        self.assertEqual(vnc_vmi.parent_name, self.project.name)
        self.assertEqual(vnc_vmi.display_name, vmi_model.display_name)
        self.assertEqual(vnc_vmi.uuid, vmi_model.uuid)
        self.assertEqual(vnc_vmi.virtual_machine_interface_mac_addresses.mac_address, [vmi_model.mac_address])
        self.assertEqual(vnc_vmi.get_id_perms(), ID_PERMS)
