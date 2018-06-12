import uuid
from unittest import TestCase

from mock import Mock, patch
from vnc_api.vnc_api import Project, SecurityGroup

from cvm.models import (ID_PERMS, VirtualMachineInterfaceModel,
                        VirtualMachineModel, VirtualNetworkModel, VlanIdPool,
                        find_virtual_machine_ip_address)
from tests.utils import (create_dpg_mock, create_port_mock,
                         create_vmware_vm_mock)


class TestFindVirtualMachineIpAddress(TestCase):
    def setUp(self):
        self.vm = Mock()

    def test_standard_case(self):
        desired_portgroup, expected_ip = 'second', '10.7.0.60'
        self.vm.guest.net = [
            self._create_mock(
                network='first',
                ipAddress=['1.1.1.1', 'fe80::257:56ff:fe90:d265'],
            ),
            self._create_mock(
                network=desired_portgroup,
                ipAddress=['fe80::250:56ff:fe90:d265', expected_ip],
            ),
        ]

        result = find_virtual_machine_ip_address(self.vm, desired_portgroup)

        self.assertEqual(result, expected_ip)

    def test_unmatched_portgroup_name(self):
        desired_portgroup, expected_ip = 'non-existent', None
        self.vm.guest.net = [
            self._create_mock(
                network='first',
                ipAddress=['1.1.1.1', 'fe80::257:56ff:fe90:d265'],
            ),
            self._create_mock(
                network='second',
                ipAddress=['fe80::250:56ff:fe90:d265', expected_ip],

            ),
        ]

        result = find_virtual_machine_ip_address(self.vm, desired_portgroup)

        self.assertEqual(result, expected_ip)

    def test_unmatched_ip_type(self):
        desired_portgroup, expected_ip = 'second', None
        self.vm.guest.net = [
            self._create_mock(
                network='first',
                ipAddress=['1.1.1.1', 'fe80::257:56ff:fe90:d265'],
            ),
            self._create_mock(
                network=desired_portgroup,
                ipAddress=['fe80::250:56ff:fe90:d265'],
            ),
        ]

        result = find_virtual_machine_ip_address(self.vm, desired_portgroup)

        self.assertEqual(result, expected_ip)

    def test_missing_field(self):
        desired_portgroup, expected_ip = 'irrelevant', None
        self.vm.guest = None

        result = find_virtual_machine_ip_address(self.vm, desired_portgroup)

        self.assertEqual(result, expected_ip)

    def test_missing_field_in_network(self):
        desired_portgroup, expected_ip = 'second', '10.7.0.60'
        self.vm.guest.net = [
            None,
            self._create_mock(
                network=desired_portgroup,
                ipAddress=['fe80::250:56ff:fe90:d265', expected_ip],
            ),
        ]

        result = find_virtual_machine_ip_address(self.vm, desired_portgroup)

        self.assertEqual(result, expected_ip)

    @staticmethod
    def _create_mock(**kwargs):
        mock = Mock()
        for kwarg in kwargs:
            setattr(mock, kwarg, kwargs[kwarg])
        return mock


class TestVirtualMachineModel(TestCase):
    def setUp(self):
        self.vmware_vm, self.vm_properties = create_vmware_vm_mock()

    def test_init(self):
        vm_model = VirtualMachineModel(self.vmware_vm, self.vm_properties)

        self.assertEqual(self.vmware_vm, vm_model.vmware_vm)
        self.assertEqual('d376b6b4-943d-4599-862f-d852fd6ba425', vm_model.uuid)
        self.assertEqual('VM', vm_model.name)
        self.assertTrue(vm_model.is_powered_on)
        self.assertTrue(vm_model.tools_running)

    def test_to_vnc(self):
        vm_model = VirtualMachineModel(self.vmware_vm, self.vm_properties)
        vm_model.vm_properties['config.instanceUuid'] = 'd376b6b4-943d-4599-862f-d852fd6ba425'
        vm_model.vrouter_uuid = 'vrouter_uuid'

        vnc_vm = vm_model.vnc_vm

        self.assertEqual(vm_model.uuid, vnc_vm.name)
        self.assertEqual(vm_model.uuid, vnc_vm.uuid)
        self.assertEqual([vm_model.uuid], vnc_vm.fq_name)
        vrouter_annotation = vnc_vm.get_annotations().get_key_value_pair()[0]
        self.assertEqual('vrouter_uuid', vrouter_annotation.value)

    def test_update(self):
        vm_model = VirtualMachineModel(self.vmware_vm, self.vm_properties)
        vmware_vm = Mock()
        vmware_vm.summary.runtime.host = None
        vmware_vm.config.hardware.device = []
        new_properties = {
            'config.instanceUuid': '52073317-45b6-c3ee-596f-63dd49dd689e',
            'name': 'VM',
            'runtime.powerState': 'poweredOff',
            'guest.toolsRunningStatus': 'guestToolsNotRunning',
        }

        vm_model.update(vmware_vm, new_properties)

        self.assertEqual(vmware_vm, vm_model.vmware_vm)
        self.assertEqual('52073317-45b6-c3ee-596f-63dd49dd689e', vm_model.uuid)
        self.assertEqual('VM', vm_model.name)
        self.assertFalse(vm_model.is_powered_on)
        self.assertFalse(vm_model.tools_running)


class TestVirtualMachineInterfaceModel(TestCase):
    def setUp(self):
        self.project = Project()
        self.security_group = SecurityGroup()

        vmware_vm, vm_properties = create_vmware_vm_mock()
        device = Mock()
        device.backing.port.portgroupKey = '123'
        device.macAddress = 'c8:5b:76:53:0f:f5'
        vmware_vm.config.hardware.device = [device]
        self.vm_model = VirtualMachineModel(vmware_vm, vm_properties)
        self.vm_model.vm_properties['config.instanceUuid'] = 'd376b6b4-943d-4599-862f-d852fd6ba425'
        self.vm_model.vrouter_uuid = '192.168.0.10'

        vmware_vn = create_dpg_mock(name='VM Network', key='123')
        vnc_vn = Mock(uuid='d376b6b4-943d-4599-862f-d852fd6ba425')
        vnc_vn.name = 'VM Network'
        self.vn_model = VirtualNetworkModel(vmware_vn, vnc_vn, VlanIdPool(0, 100))

    def test_to_vnc(self):
        vmi_model = VirtualMachineInterfaceModel(self.vm_model, self.vn_model, self.project, self.security_group)

        vnc_vmi = vmi_model.to_vnc()

        self.assertEqual(vnc_vmi.name, vmi_model.uuid)
        self.assertEqual(vnc_vmi.parent_name, self.project.name)
        self.assertEqual(vnc_vmi.display_name, vmi_model.display_name)
        self.assertEqual(vnc_vmi.uuid, vmi_model.uuid)
        self.assertEqual(vnc_vmi.virtual_machine_interface_mac_addresses.mac_address, [vmi_model.mac_address])
        self.assertEqual(vnc_vmi.get_id_perms(), ID_PERMS)

    @patch('cvm.models.find_vm_mac_address')
    @patch('cvm.models.VirtualMachineInterfaceModel.to_vnc')
    @patch('cvm.models.VirtualMachineInterfaceModel._should_construct_instance_ip')
    def test_construct_instance_ip(self, should_construct, to_vnc_mock, _):
        should_construct.return_value = True
        to_vnc_mock.return_value.uuid = 'd376b6b4-943d-4599-862f-d852fd6ba425'

        vmi_model = VirtualMachineInterfaceModel(self.vm_model, self.vn_model, None, None)
        vmi_model.construct_instance_ip()
        instance_ip = vmi_model.vnc_instance_ip

        self.assertEqual('d376b6b4-943d-4599-862f-d852fd6ba425',
                         instance_ip.virtual_machine_interface_refs[0]['uuid'])
        self.assertEqual(
            str(uuid.uuid3(uuid.NAMESPACE_DNS,
                           'ip-' + self.vn_model.name + '-' + self.vm_model.name)),
            instance_ip.uuid
        )


class TestVlanIdPool(TestCase):
    def setUp(self):
        self.vlan_id_pool = VlanIdPool(0, 100)

    def test_reserve(self):
        self.vlan_id_pool.reserve(0)

        self.assertNotIn(0, self.vlan_id_pool._available_ids)

    def test_reserve_existing(self):
        self.vlan_id_pool.reserve(0)

        self.vlan_id_pool.reserve(0)

        self.assertNotIn(0, self.vlan_id_pool._available_ids)

    def test_get_first_available(self):
        self.vlan_id_pool.reserve(0)

        result = self.vlan_id_pool.get_available()

        self.assertEqual(1, result)
        self.assertNotIn(1, self.vlan_id_pool._available_ids)

    def test_no_available(self):
        for i in range(4095):
            self.vlan_id_pool.reserve(i)

        result = self.vlan_id_pool.get_available()

        self.assertIsNone(result)

    def test_free(self):
        self.vlan_id_pool.reserve(0)

        self.vlan_id_pool.free(0)

        self.assertIn(0, self.vlan_id_pool._available_ids)

    def test_free_and_get(self):
        self.vlan_id_pool.reserve(0)

        self.vlan_id_pool.free(0)
        next_id = self.vlan_id_pool.get_available()

        self.assertEqual(1, next_id)


class TestVirtualNetworkVlans(TestCase):
    def setUp(self):
        self.dpg = create_dpg_mock(name='DPG1', key='dvportgroup-20')
        self.ports = []
        self.dvs = Mock()
        self.dpg.config.distributedVirtualSwitch = self.dvs
        self.dvs.FetchDVPorts.side_effect = self._check_criteria

    def test_sync_vlan_ids(self):
        self.ports.append(create_port_mock(1))
        self.ports.append(create_port_mock(2))

        vn_model = VirtualNetworkModel(self.dpg, None, VlanIdPool(0, 100))

        self.assertNotIn(1, vn_model.vlan_id_pool._available_ids)
        self.assertNotIn(2, vn_model.vlan_id_pool._available_ids)

    def test_vmi_vlan_id_aquisition(self):
        self.ports.append(create_port_mock(0))
        self.ports.append(create_port_mock(1))
        vn_model = VirtualNetworkModel(self.dpg, None, VlanIdPool(0, 100))
        vm_model = VirtualMachineModel(*create_vmware_vm_mock([self.dpg]))
        vmi_model = VirtualMachineInterfaceModel(vm_model, vn_model, None, None)

        vmi_model.acquire_vlan_id()

        self.assertEqual(2, vmi_model.vlan_id)

    def _check_criteria(self, criteria):
        if criteria.portgroupKey == 'dvportgroup-20' and criteria.inside:
            return self.ports
        return None
