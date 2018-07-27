from mock import patch
from pyVmomi import vim

from cvm.clients import VCenterAPIClient


def test_set_vlan_id(vcenter_api_client, dvs, vcenter_port):
    vcenter_port.vlan_id = 10

    with patch('cvm.clients.SmartConnectNoSSL'):
        with patch.object(VCenterAPIClient, '_get_dvswitch', return_value=dvs):
            with vcenter_api_client:
                vcenter_api_client.set_vlan_id(vcenter_port)

    dvs.ReconfigureDVPort_Task.assert_called_once()
    spec = dvs.ReconfigureDVPort_Task.call_args[1].get('port', [None])[0]
    assert spec is not None
    assert spec.key == '8'
    assert spec.configVersion == '1'
    assert spec.setting.vlan.vlanId == 10


def test_enable_vlan_override(vcenter_api_client, portgroup):
    with patch('cvm.clients.SmartConnectNoSSL'):
        with vcenter_api_client:
            vcenter_api_client.enable_vlan_override(portgroup=portgroup)

    portgroup.ReconfigureDVPortgroup_Task.assert_called_once()
    config = portgroup.ReconfigureDVPortgroup_Task.call_args[0][0]
    assert config.policy.vlanOverrideAllowed is True
    assert config.configVersion == '1'


def test_set_vlan_trunk(vcenter_api_client, portgroup):
    with patch('cvm.clients.SmartConnectNoSSL'):
        with vcenter_api_client:
            vcenter_api_client.set_vlan_trunk(portgroup=portgroup)

    portgroup.ReconfigureDVPortgroup_Task.assert_called_once()
    vlan_config = portgroup.ReconfigureDVPortgroup_Task.call_args[0][0].defaultPortConfig.vlan
    assert isinstance(vlan_config, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec)
    assert isinstance(vlan_config.vlanId[0], vim.NumericRange)
    assert vlan_config.vlanId[0].start == 0
    assert vlan_config.vlanId[0].end == 4094


def test_get_vlan_id(vcenter_api_client, dvs, vcenter_port, dv_port):
    dv_port.config.setting.vlan.vlanId = 10
    dv_port.config.setting.vlan.inherited = False

    with patch('cvm.clients.SmartConnectNoSSL'):
        with patch.object(VCenterAPIClient, '_get_dvswitch', return_value=dvs):
            with vcenter_api_client:
                result = vcenter_api_client.get_vlan_id(vcenter_port)

    assert result == 10


def test_restore_vlan_id(vcenter_api_client, dvs, vcenter_port):
    with patch('cvm.clients.SmartConnectNoSSL'):
        with patch.object(VCenterAPIClient, '_get_dvswitch', return_value=dvs):
            with vcenter_api_client:
                vcenter_api_client.restore_vlan_id(vcenter_port)

    dvs.ReconfigureDVPort_Task.assert_called_once()
    spec = dvs.ReconfigureDVPort_Task.call_args[1].get('port', [None])[0]
    assert spec is not None
    assert spec.key == '8'
    assert spec.configVersion == '1'
    assert spec.setting.vlan.inherited is True


def test_get_reserved_vlan_ids(vcenter_api_client, dvs_1):
    with patch('cvm.clients.SmartConnectNoSSL'):
        with patch.object(VCenterAPIClient, '_get_dvswitch', return_value=dvs_1):
            with vcenter_api_client:
                vlans_1 = vcenter_api_client.get_reserved_vlan_ids('vrouter_uuid_1')
                vlans_2 = vcenter_api_client.get_reserved_vlan_ids('vrouter_uuid_2')

    assert vlans_1 == [10, 7]
    assert vlans_2 == [5]