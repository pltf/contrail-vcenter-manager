from unittest import TestCase

from mock import Mock
from pyVmomi import vim  # pylint: disable=no-name-in-module
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


class TestVirtualNetworkModel(TestCase):
    def setUp(self):
        self.vmware_vn = Mock()

    def test_populate_vlans(self):
        entry_1 = self._create_pvlan_map_entry_mock('isolated', 2, 3)
        entry_2 = self._create_pvlan_map_entry_mock('promiscuous', 2, 3)
        entry_3 = self._create_pvlan_map_entry_mock('isolated', 3, 4)
        self.vmware_vn.config.distributedVirtualSwitch.config.pvlanConfig = [entry_1, entry_2, entry_3]
        self.vmware_vn.config.defaultPortConfig = self._create_pvlan_port_config_mock(3)

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertEqual(vn_model.isolated_vlan_id, 3)
        self.assertEqual(vn_model.primary_vlan_id, 2)

    def test_populate_vlans_no_p_found(self):
        """ No primary vlan corresponding to isolated vlan in vlan map. """
        entry = self._create_pvlan_map_entry_mock('isolated', 4, 5)
        self.vmware_vn.config.distributedVirtualSwitch.config.pvlanConfig = [entry]
        self.vmware_vn.config.defaultPortConfig = self._create_pvlan_port_config_mock(3)

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertEqual(vn_model.isolated_vlan_id, 3)
        self.assertEqual(vn_model.primary_vlan_id, None)

    def test_populate_vlans_not_p(self):
        """
        default_port_config.vlan is instance of
        vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec.
        VlanType = VLAN.
        """
        self.vmware_vn.config.defaultPortConfig = self._create_vlan_port_config_mock(3)

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertEqual(vn_model.isolated_vlan_id, 3)
        self.assertEqual(vn_model.primary_vlan_id, 3)

    def test_populate_vlans_inv_spec(self):
        """ Sometimes vlan_spec is of invalid type, e.g. TrunkVlanSpec. """
        self.vmware_vn.config.defaultPortConfig.vlan = Mock(spec=vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec)

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertIsNone(vn_model.primary_vlan_id)
        self.assertIsNone(vn_model.isolated_vlan_id)

    def test_populate_vlans_no_map(self):
        """ Private vlan not configured on dvSwitch. """
        self.vmware_vn.config.distributedVirtualSwitch.config.pvlanConfig = None

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertIsNone(vn_model.primary_vlan_id)
        self.assertIsNone(vn_model.isolated_vlan_id)

    def test_populate_vlans_no_spec(self):
        """
        vn_model.default_port_config has no vlan field.
        Invalid port setting.
        """
        entry = self._create_pvlan_map_entry_mock('isolated', 2, 3)
        self.vmware_vn.config.distributedVirtualSwitch.config.pvlanConfig = [entry]
        self.vmware_vn.config.defaultPortConfig = None

        vn_model = VirtualNetworkModel(self.vmware_vn, None, None)

        self.assertIsNone(vn_model.primary_vlan_id)
        self.assertIsNone(vn_model.isolated_vlan_id)

    @staticmethod
    def _create_pvlan_port_config_mock(pvlan_id):
        default_port_config = Mock()
        default_port_config.vlan = Mock(spec=vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec)
        default_port_config.vlan.pvlanId = pvlan_id
        return default_port_config

    @staticmethod
    def _create_vlan_port_config_mock(vlan_id):
        default_port_config = Mock()
        default_port_config.vlan = Mock(spec=vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec)
        default_port_config.vlan.vlanId = vlan_id
        return default_port_config

    @staticmethod
    def _create_pvlan_map_entry_mock(pvlan_type, primary_id, secondary_id):
        entry = Mock()
        entry.pvlanType = pvlan_type
        entry.primaryVlanId = primary_id
        entry.secondaryVlanId = secondary_id
        return entry
