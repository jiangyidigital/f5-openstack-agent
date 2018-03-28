# coding=utf-8
# Copyright (c) 2017,2018, F5 Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import mock
import pytest

from f5_openstack_agent.lbaasv2.drivers.bigip import agent_manager
from f5_openstack_agent.lbaasv2.drivers.bigip.tunnels import tunnel as \
    tunnel_mod

import class_tester_base_class
import conftest
import mock_builder_base_class
import test_icontrol_driver
import test_plugin_rpc

from ..tunnels.test import test_network_cache_handler
from ..tunnels.test import test_tunnel


@pytest.fixture
@mock.patch('f5_openstack_agent.lbaasv2.drivers.bigip.agent_manager.'
            'LbaasAgentManager._setup_rpc')
@mock.patch('f5_openstack_agent.lbaasv2.drivers.bigip.agent_manager.'
            'importutils.import_object')
def agent_mgr_setup(mock_importutils, mock_setup_rpc):
    return agent_manager.LbaasAgentManager(mock.MagicMock(name='conf'))


@pytest.mark.skip(reason="Mocked RPC breaks initialization")
@mock.patch('f5_openstack_agent.lbaasv2.drivers.bigip.agent_manager.LOG')
def test_update_fdb_entries(mock_log, agent_mgr_setup):
    '''When func is called in agent_manager, it prooduces a warning message.'''

    agent_mgr_setup.update_fdb_entries('', '')
    warning_msg = "update_fdb_entries: the LBaaSv2 Agent does not handle an " \
        "update of the IP address of a neutron port. This port is generally " \
        "tied to a member. If the IP address of a member was changed, be " \
        "sure to also recreate the member in neutron-lbaas with the new " \
        "address."
    assert mock_log.warning.call_args == mock.call(warning_msg)


class TestLbaasAgentManagerMockBuilder(mock_builder_base_class.MockBuilderBase,
                                       conftest.TestingWithServiceConstructor):
    """Builder class for Mock objects that mock LbaasAgentManager

    This class builds mock-module class objects for isolation of the
    LbaasAgentManager.  As such, all reference to `target` are pointing to
    either an instantiated instance of LbaasAgentManager or is a mocked
    instance of this class.

    Use:
        class Tester(object):
            my_mock_builder = TestLbaasAgentManagerMockBuilder
            standalone = TestLbaasAgentManagerMockBuilder.standalone
            neutron_only = TestLbaasAgentManagerMockBuilder.neutron_only
            bigip_only = TestLbaasAgentManagerMockBuilder.bigip_only
            fully_int = TestLbaasAgentManagerMockBuilder.fully_int
            fixture = my_mock_builder.fixture

            def test_foo(fixture):
                # this then uses the pytest.fixture fixture from MockBuilder
    """
    # non-instantiated
    lbdriver = test_icontrol_driver.TestiControlDriverMockBuilder
    _other_builders = dict(
        _LbaasAgentManager__lbdriver=lbdriver,
        plugin_rpc=test_plugin_rpc.TestPluginRpcMockBuilder,
        network_cache_handler=test_network_cache_handler.
        TestNetworkCacheHandlerMockBuilder)
    _other_builders['_LbaasAgentManager__tunnel_handler'] = \
        test_tunnel.TestTunnelHandlerMockBuilder

    @staticmethod
    def mocked_target(*args):
        """Build a Mock target that totally skips the __init__ method

        This is typically a building block that builds just an instantiated
        instance of target that has limited to no attibute quality that is
        otherwise generated by fully_mocked_target().

        Thus, the return is a partially-completed dead-end Target object
        instance.
        """
        with mock.patch(
                'f5_openstack_agent.lbaasv2.drivers.bigip.agent_manager.'
                'LbaasAgentManager.__init__') as my_init:
            my_init.return_value = None
            conf = mock.Mock()
            new_target = agent_manager.LbaasAgentManager(conf)
            new_target.conf = conf
        return new_target

    def fully_mocked_target(self, mocked_target):
        """Creates a mocked target that mocks all lower other_builders' targets

        This does not mean that the caller's black-box is limited to this
        target, but can drill further using a system of either mocks or
        non-mocks.  Please see conftest.MockBuilder for details.
        """
        # Mock() objects here should be filled in with the appropriate mocks...
        super(TestLbaasAgentManagerMockBuilder, self).fully_mocked_target(
            mocked_target)
        mocked_target.context = 'context'
        mocked_target.serializer = None
        mocked_target.cache = mock.Mock()
        mocked_target.last_resync = mock.Mock()
        mocked_target.needs_resync = False
        mocked_target._LbaasAgentManager__tunnel_rpc = mock.Mock()
        mocked_target._LbaasAgentManager__l2_pop_rpc = mock.Mock()
        mocked_target.state_rpc = mock.Mock()
        mocked_target.pending_services = {}
        mocked_target.service_resync_interval = 5
        mocked_target.agent_host = 'conf.host:agent_hash'
        agent_configurations = (
            {'environment_prefix': 'environment_prefix',
             'environment_group_number': 'environment_group_number',
             'global_routed_mode': 'f5_global_routed_mode'}
        )
        mocked_target.admin_state_up = 'start_agent_admin_state_up'

        mocked_target.agent_state = {
            'binary': 'AGENT_BINARY_NAME',
            'host': mocked_target.agent_host,
            'topic': 'TOPIC_LOADBALANCER_AGENT_V2',
            'agent_type': 'AGENT_TYPE_LOADBALANCERV2',
            'l2_population': 'l2_population',
            'start_flag': True,
            'configurations': agent_configurations
        }
        mocked_target.endpoints = mocked_target
        mocked_target.connection = mock.Mock()
        return mocked_target

    def new_fully_mocked_target(self):
        return self.fully_mocked_target(self.mocked_target())

    def mock_all_get_all_deployed(self, target=None, **kwargs):
        """Modifies target to have at least one purgable item per ref type"""
        if not target:
            target = self.new_fully_mocked_target()
        listing = [
            'get_all_deployed_loadbalancers', 'get_all_deployed_listeners',
            'get_all_deployed_l7_policys',
            'get_all_deployed_health_monitors', 'get_all_deployed_pools']
        for method in listing:
            self.mock_other_builders_method(
                target, method, targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=[],
                **kwargs)

    def mock_all_purges(self, target=None):
        """Performs a basic mock against all purges methods

        Example: purge_orphaned_loadbalancers
        """
        if not target:
            target = self.new_fully_mocked_target()
        self.mock_purge_orphaned_loadbalancers(target)
        self.mock_purge_orphaned_listeners(target)
        self.mock_purge_orphaned_l7_policys(target)
        self.mock_purge_orphaned_pools(target)
        self.mock_purge_orphaned_nodes(target)
        self.mock_purge_orphaned_health_monitors(target)

    def mock_purge_orphaned_loadbalancers(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_loadbalancers method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_loadbalancers', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_listeners(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_listeners method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_listeners', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_l7_policys(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_l7_policys method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_l7_policys', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_pools(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_pools method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_pools', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_nodes(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_nodes method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_nodes', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_health_monitors(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_health_monitors method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_health_monitors', static,
                          call_cnt, expected_args, kwargs)
        return target

    def mock_purge_orphaned_policys(
            self, target=None, call_cnt=1, static=None, expected_args=None,
            **kwargs):
        """Mocks the target's purge_orphaned_policys method

        The given kwargs will be passed to the mock.Mock call

        This will also create a new fully_mocked_target if target is not
        specified.
        """
        if not target:
            target = self.new_fully_mocked_target()
        self._mockfactory(target, 'purge_orphaned_policys', static,
                          call_cnt, expected_args, kwargs)
        return target


# replace the name to LBaasmAgentManagerClassMocker as decided by team
class LBaasAgentManagerMocker(object):
    """To-be Instantiated Mocker class that tracks 'frozen' code space

    This class is meant to be a code-space tracker element that tracks code
    space variables and pointers to keep original code space elements in tact.
    Upon setUp of a test instance, the fixtures here will create and replace
    the code space elements with either mocks or temporary variables.  Upon
    tearDown, these frozen code space elements are restored and mocks and
    temporary variables are restored.

    Using this class's methods should be limited to global-code-space libraries
    imported from Python standard libraries or pip-hosted libraries.  NOT
    F5-controlled libraries within this repo.  Those should be handled and
    built by the appropriate MockBuilder classes within the modules that
    target the class to be mocked.
    """

    @pytest.fixture
    def mock_logger(self):
        """Mocks the target's logger element for caller's use in testing"""
        my_logger = mock.Mock()
        self.freeze_logger = agent_manager.LOG
        self.logger = my_logger
        agent_manager.LOG = my_logger

    def teardown(self):
        """Performs teardown operations dynamically to catch fixtures used"""
        if hasattr(self, 'freeze_logger'):
            agent_manager.LOG = self.freeze_logger


class TestLbaasAgentManager(LBaasAgentManagerMocker,
                            class_tester_base_class.ClassTesterBase):
    """Tester class that tests the AgentManager

    Tests under this tester class should test the code in agent_manager.py and
    encompass both fully-comprehensive white-box tests (fcwb) and some black-
    box tests (bb).  Black-box tests should provide information on where they
    are limited to in the pydoc for the method.
    """
    # this is not instantiated
    builder = TestLbaasAgentManagerMockBuilder
    # fixtures hosted by builder (add more if needed):
    # standalone_builder = TestLbaasAgentManagerMockBuilder.standalone_builder
    # mocked_target = my_builder.mocked_target
    # NOTE: in the above list, do not add mock_{method}'s as these cannot be
    # fixtures because they are instantiated!

    def test_fcwb_clean_orphaned_objects_and_save_device_config(
            self, standalone_builder, fully_mocked_target, mock_logger):
        """Performs fully-comprehensive testing for this method

        White-box test for:
            agent_manager.LBaasAgentManager.\
                clean_orphaned_objects_and_save_device_config
        That verfies grammar and "freezes" logic.
        """
        target = fully_mocked_target

        def no_global_agent_exists(self, builder, target):
            plugin_rpc_get_clusterwide_agent_retval = dict()
            get_clusterwide_agent_expected = \
                tuple([target.conf.environment_prefix,
                       target.conf.environmentgroup_number])
            builder.mock_other_builders_method(
                target, 'get_clusterwide_agent', targets_attr='plugin_rpc',
                call_cnt=1, expected_args=get_clusterwide_agent_expected,
                return_value=plugin_rpc_get_clusterwide_agent_retval)
            assert target.clean_orphaned_objects_and_save_device_config()
            builder.check_mocks(target)

        def global_agent_exists(self, builder, target):
            plugin_rpc_get_clusterwide_agent_retval = \
                dict(host=target.agent_host)
            get_clusterwide_agent_expected = \
                tuple([target.conf.environment_prefix,
                       target.conf.environmentgroup_number])
            builder.mock_other_builders_method(
                target, 'get_clusterwide_agent', targets_attr='plugin_rpc',
                call_cnt=1, expected_args=get_clusterwide_agent_expected,
                return_value=plugin_rpc_get_clusterwide_agent_retval)
            builder.mock_other_builders_method(
                target, 'backup_configuration',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=None)
            builder.mock_all_get_all_deployed(target, return_value=[1])
            builder.mock_all_purges(target)
            assert not target.clean_orphaned_objects_and_save_device_config()
            builder.check_mocks(target)

        def global_agent_with_failure(self, builder, target):
            plugin_rpc_get_clusterwide_agent_retval = dict(host=target.host)
            get_clusterwide_agent_expected = \
                tuple([target.conf.environment_prefix,
                       target.conf.environmentgroup_number])
            builder.mock_other_builders_method(
                target, 'get_clusterwide_agent', targets_attr='plugin_rpc',
                call_cnt=1, expected_args=get_clusterwide_agent_expected,
                return_value=plugin_rpc_get_clusterwide_agent_retval)
            builder.mock_other_builders_method(
                target, 'backup_configuration',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=None)
            builder.mock_all_get_all_deployed(target, return_value=[1])
            builder.mock_all_purges(target)
            builder.mock_purge_orphaned_loadbalancers(
                special_effect=AssertionError)
            assert target.clean_orphaned_objects_and_save_device_config()
            not_called = [
                'get_all_deployed_listeners', 'get_all_deployed_l7_policys',
                'get_all_deployed_pools', 'get_all_deployed_health_monitors',
                'purge_orphaned_listeners', 'purge_orphaned_l7_policys'
                'purge_orphaned_pools', 'purge_porphaned_health_monitors']
            builder.check_mocks(target, not_called=not_called)

        def global_agent_different_agent(self, builder, target):
            plugin_rpc_get_clusterwide_agent_retval = dict(host='not me')
            get_clusterwide_agent_expected = \
                tuple([target.conf.environment_prefix,
                       target.conf.environmentgroup_number])
            builder.mock_other_builders_method(
                target, 'get_clusterwide_agent', targets_attr='plugin_rpc',
                call_cnt=1, expected_args=get_clusterwide_agent_expected,
                return_value=plugin_rpc_get_clusterwide_agent_retval)
            assert target.clean_orphaned_objects_and_save_device_config()
            builder.check_mocks(target)

        no_global_agent_exists(self, standalone_builder, target)
        target = standalone_builder.new_fully_mocked_target()
        global_agent_exists(self, standalone_builder, target)
        target = standalone_builder.new_fully_mocked_target()
        global_agent_different_agent(self, standalone_builder, target)

    def test_fcwb_purge_orphaned_loadbalancers(
            self, service_with_loadbalancer, standalone_builder,
            mock_logger, fully_mocked_target):
        """FCWBT for purge_orphaned_listeners"""
        target = fully_mocked_target
        svc = service_with_loadbalancer

        def lbs_removed(logger, builder, target, svc):
            svc['loadbalancer']['provisioning_status'] = 'Unknown'
            lb = svc['loadbalancer']
            lb['hostnames'] = [target.agent_host]
            lb_id = lb['id']
            lbs = {lb_id: lb.copy()}
            lb_statuses = {lb_id: 'Unknown'}
            purge_args = dict(tenant_id=lb['tenant_id'], loadbalancer_id=lb_id,
                              hostnames=lb['hostnames'])
            get_all_args = dict(purge_orphaned_folders=True)
            builder.mock_other_builders_method(
                target, 'validate_loadbalancers_state',
                targets_attr='plugin_rpc', expected=tuple([lb_id]),
                return_value=lb_statuses)
            builder.mock_other_builders_method(
                target, 'purge_orphaned_loadbalancer',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=purge_args)
            builder.mock_other_builders_method(
                target, 'get_all_deployed_loadbalancers',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=get_all_args)
            target.purge_orphaned_loadbalancers(lbs)
            builder.check_mocks(target)

        lbs_removed(self.logger, standalone_builder, target, svc)

    def test_fcwb_purge_orphaned_listeners(
            self, service_with_listener, standalone_builder,
            mock_logger, fully_mocked_target):
        """FCWBT for purge_orphaned_listeners"""
        target = fully_mocked_target
        svc = service_with_listener

        def lstns_removed(logger, builder, target, svc):
            lst = svc['listeners'][0]
            lst['provisioning_status'] = 'Unknown'
            lst['hostnames'] = [target.agent_host]
            lst_id = lst['id']
            lsts = {lst_id: lst.copy()}
            lst_statuses = {lst_id: 'Unknown'}
            purge_args = dict(tenant_id=lst['tenant_id'], listeners_id=lst_id,
                              hostnames=lst['hostnames'])
            builder.mock_other_builders_method(
                target, 'validate_listeners_state', targets_attr='plugin_rpc',
                expected_args=tuple([lst_id]), return_value=lst_statuses)
            builder.mock_other_builders_method(
                target, 'purge_orphaned_listener',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=purge_args)
            target.purge_orphaned_listeners(lsts)
            builder.check_mocks(target)

        lstns_removed(self.logger, standalone_builder, target, svc)

    def test_fcwb_purge_orphaned_l7_policys(
            self, service_with_l7_policy, standalone_builder,
            mock_logger, fully_mocked_target):
        """FCWBT for purge_orphaned_l7_policys"""
        target = fully_mocked_target
        svc = service_with_l7_policy

        def pols_removed(logger, builder, target, svc):
            # fake data manipulation:
            pol = svc['l7_policies'][0]
            pol_id = pol['id']
            li = svc['listeners'][0]
            t_id = li['tenant_id']
            li_id = li['id']
            hostnames = [target.agent_host]
            deployed_pol = dict(id=pol_id, tenant_id=t_id,
                                hostnames=hostnames)
            deployed_li = dict(id=li_id, tenant_id=t_id, hostnames=hostnames,
                               l7_policy='')
            deployed_lis = {li_id: deployed_li}
            deployed_pols = {pol_id: deployed_pol}
            # mocks...
            builder.mock_other_builders_method(
                target, 'get_all_deployed_listeners',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=tuple([pol_id]), return_value=deployed_lis)
            builder.mock_other_builders_method(
                target, 'purge_orphaned_l7_policy',
                targets_attr='_LbaasAgentManager__lbdriver')
            # test...
            target.purge_orphaned_l7_policys(deployed_pols)
            # validation...
            builder.check_mocks(target)

        pols_removed(self.logger, standalone_builder, target, svc)

    def test_fcwb_purge_orphaned_pools(
            self, service_with_pool, standalone_builder,
            mock_logger, fully_mocked_target):
        """FCWBT for purge_orphaned_pools"""
        target = fully_mocked_target
        svc = service_with_pool

        def ps_removed(logger, builder, target, svc):
            p = svc['pools'][0]
            p['provisioning_status'] = 'Unknown'
            p_id = p['id']
            p['hostnames'] = [target.agent_host]
            ps = {p_id: p.copy()}
            p_statuses = {p_id: 'Unknown'}
            purge_args = dict(tenant_id=p['tenant_id'], pools_id=p_id,
                              hostnames=p['hostnames'])
            builder.mock_other_builders_method(
                target, 'validate_pools_state', targets_attr='plugin_rpc',
                expected_args=tuple([p_id]), return_value=p_statuses)
            builder.mock_other_builders_method(
                target, 'purge_orphaned_pool',
                targets_attr='_LbaasAgentManager__lbdriver',
                expected_args=purge_args)
            target.purge_orphaned_pools(ps)
            builder.check_mocks(target)

        ps_removed(self.logger, standalone_builder, target, svc)

    def test_fcwb_purge_orphaned_health_monitors(
            self, service_with_health_monitor, standalone_builder,
            fully_mocked_target, mock_logger):
        """FCWBT for purge_orphaned_health_monitors"""
        target = fully_mocked_target
        svc = service_with_health_monitor

        def hms_removed(logger, builder, target, svc):
            hm = svc['healthmonitors'][0]
            p = svc['pools'][0]
            p_id = p['id']
            hm_id = hm['id']
            deployed_monitors = dict(
                tenant_id=hm['tenant_id'], id=hm_id,
                hostnames=[target.agent_host])
            deployed_pool = dict(
                tenant_id=p['tenant_id'], id=p_id, monitor=hm_id,
                hostnames=[target.agent_host])
            hms = {hm_id: deployed_monitors}
            deployed_pool = {p_id: deployed_pool}
            builder.mock_other_builders_method(
                target, 'get_all_deployed_pools',
                targets_attr='_LbaasAgentManager__lbdriver',
                return_value=deployed_pool)
            builder.mock_other_builders_method(
                target, 'purge_orphaned_health_monitor',
                targets_attr='_LbaasAgentManager__lbdriver')
            target.purge_orphaned_health_monitors(hms)
            builder.check_mocks(target)

        hms_removed(self.logger, standalone_builder, target, svc)

    @pytest.mark.skip(reason='WIP')
    def test_pbb_clean_orphaned_objects_and_save_device_config(
            self, service_with_health_monitor, standalone_builder,
            fully_mocked_target):
        target = fully_mocked_target
        svc = service_with_health_monitor

        def down_to_plugin_rpc_functional(target, builder, svc):
            hosts = [target.agent_host]
            fake_bigip = mock.Mock()
            fake_bigip.status = 'active'
            fake_bigip.tm.sys.folders.folder.exist.return_value = True
            prefix = \
                target._LbaasAgentManager__lbdriver.service_adapter.prefix
            fake_bigip.tm.sys.folders.get_collection.return_value = [
                prefix + svc['loadbalancer']['tenant_id']]
            # need to continue down the route of mocking _call() and
            # system_adapter
            for list_obj in ['listeners', 'pools', 'healthmonitors']:
                svc[list_obj]['hostnames'] = hosts
            svc['loadbalancer']['hostnames'] = hosts
            _calls_side_effect = [
                {'host': target.agent_host},
                {}]
            # we'll just mock... not really validate much...
            builder.mock_other_builders_method(
                target, '_call', targets_attr='plugin_rpc',
                side_effect=_calls_side_effect)

        down_to_plugin_rpc_functional(target, standalone_builder, svc)

    def test_bb_l2_population(self, service_with_loadbalancer,
                              standalone_builder, fully_mocked_target):
        """Performs a L2 Population test against valid fdb_entry

        This is a feature black-box test that ends at the SDK.

        This test will perform the following:
            * Dope a "BIG-IP" mock with a tunnel
            * Dope the network_cache with a tunnel
            * Test the FdbBuilder via AgentManager with the orchestration of
                a fdb_entry
        """

        args = [fully_mocked_target, service_with_loadbalancer,
                standalone_builder]

        self.modify_service_with_vxlan(args[1])

        def fake_bigip(target, svc):
            partition = 'Project_{tenant_id}'.format(**svc['loadbalancer'])
            fake_bigip = mock.Mock()
            target._LbaasAgentManager__lbdriver._iControlDriver__bigips = \
                {'host': fake_bigip}
            fake_bigip.status = 'active'
            fake_bigip.hostname = 'host'
            tm_arp = mock.Mock()
            arp = mock.Mock()
            tm_tunnel = mock.Mock()
            tunnel = mock.Mock()
            tm_records = mock.Mock()
            records = [{'name': 'foozoo',
                        'endpoint': '201.0.155.3'},
                       {'name': 'doofoo',
                        'endpoint': '201.0.155.6'}]
            tunnel.records = records
            tm_tunnel.load.return_value = tunnel
            tm_tunnel.exists = True
            tm_arp.load.return_value = arp
            tm_arp.exists.reurn_value = True
            fake_bigip.status = 'active'
            fake_bigip.tm.net.fdb.tunnels.tunnel = tm_tunnel
            fake_bigip.tm.net.arps.arp = tm_arp
            tunnel.records_s.records = tm_records
            record = mock.Mock()
            record.name = records[0]['name']
            record.endpoint = records[0]['endpoint']
            tm_records.load.return_value = record
            tm_records.create.return_value = record
            fake_bigip.tm_records = tm_records
            fake_bigip.tm_fdb_tunnel = tm_tunnel
            # generate the fake network cache...
            network_id = svc['networks'].keys()[0]
            network = svc['networks'][network_id]
            segment_id = network['provider:segmentation_id']
            tunnel_type = network['provider:network_type']
            tunnel_obj = tunnel_mod.Tunnel(
                network_id, tunnel_type, segment_id, 'host', partition,
                '192.168.1.2', '201.0.155.1')
            tunnel_obj.exists = True
            # begin doping target...
            target.tunnel_handler._TunnelHandler__network_cache_handler.\
                network_cache = tunnel_obj
            # short-hand things...
            [fake_bigip.tunnel, fake_bigip.tm_arp, fake_bigip.tm_tunnel,
             fake_bigip.arp, fake_bigip.tm_tunnel] = \
                [tunnel_obj, tm_arp, tm_tunnel, arp, tunnel]
            fake_bigip.partition = partition
            return fake_bigip

        def test_add(target, svc, builder):
            bigip = fake_bigip(target, svc)
            target._LbaasAgentManager__tunnel_handler.\
                _TunnelHandler__pending_exists = []
            network_id = svc['loadbalancer']['network_id']
            fake_mac = '92:37:a2:b2:12:38'
            vtep_ip = '201.0.155.5'
            arp_address = '10.2.1.2'
            fdb_entry = {
                network_id: {
                    'network_type': 'vxlan',
                    'ports': {arp_address: [[fake_mac, vtep_ip]]},
                    'segment_id': 23}}
            context = mock.Mock()
            target._LbaasAgentManager__lbdriver.tunnel_handler = \
                target.tunnel_handler
            target.add_fdb_entries(context, fdb_entry)
            assert bigip.tm_fdb_tunnel.load.call_count
            assert bigip.tm_records.create.call_count
            assert target.tunnel_handler.l2pop_rpc.add_fdb_entries.call_count

        test_add(*args)
