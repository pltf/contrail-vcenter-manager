EVENTS_TO_OBSERVE = [
    'VmCreatedEvent',
    'VmClonedEvent',
    'VmDeployedEvent',
    'VmPoweredOnEvent',
    'VmPoweredOffEvent',
    'VmSuspendedEvent',
    'VmRenamedEvent',
    'VmMacChangedEvent',
    'VmMacAssignedEvent',
    'VmReconfiguredEvent',
    'VmMigratedEvent',
    'VmRemovedEvent',
]

VNC_ROOT_DOMAIN = 'default-domain'
VNC_VCENTER_PROJECT = 'vCenter'
VNC_VCENTER_IPAM = 'vCenter-ipam'
VNC_VCENTER_DEFAULT_SG = 'default'
VNC_VCENTER_DEFAULT_SG_FQN = VNC_ROOT_DOMAIN + ':' + VNC_VCENTER_PROJECT + ':' + VNC_VCENTER_DEFAULT_SG
