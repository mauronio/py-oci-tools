import oci

def get_signer_from_config(config):
    # Generate the signer for the API calls using the info from the config file
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        # pass_phrase is optional and can be None
        pass_phrase=oci.config.get_config_value_or_default(
            config, "pass_phrase"),
        # private_key_content is optional and can be None
        private_key_content=config.get("key_content")
    )
    
    return signer

class OCIClient:

    def __init__(self, config_filename = "~/.oci/config", profile_name = "DEFAULT"):

        config = oci.config.from_file(config_filename, profile_name)
        signer = get_signer_from_config(config)

        self.identity_service = oci.identity.IdentityClient(config, signer=signer)
        self.vcn_service = oci.core.VirtualNetworkClient(config, signer=signer)

        self.tenancy_compartment = self.identity_service.get_compartment(compartment_id=config["tenancy"])

    def populate_artifacts(self, artifact_data, items, artifact_list_key, artifact_display_type):        
        artifact_data[artifact_list_key] = [] 
        for item in items:
            artifact_data[artifact_list_key].append(item.id)
            artifact_data['artifacts'][item.id] = {
                'display-type': artifact_display_type,
                'artifact': item
            }

    def get_vcn_artifacts(self, oci_client, network_compartment_ocid):

        result = {}

        vcn_list_response = self.vcn_service.list_vcns(network_compartment_ocid)
        vcn_list = vcn_list_response.data
        for vcn in vcn_list:
            result['vcn'] = vcn
            result['artifacts'] = {}

            self.populate_artifacts(result, self.vcn_service.list_nat_gateways(network_compartment_ocid, vcn_id = vcn.id).data, 'nat-gateways', 'NAT Gateway')
            self.populate_artifacts(result, self.vcn_service.list_internet_gateways(network_compartment_ocid, vcn_id = vcn.id).data, 'internet-gateways', 'Internet Gateway')
            self.populate_artifacts(result, oci_client.vcn_service.list_service_gateways(network_compartment_ocid, vcn_id = vcn.id).data, 'service-gateways', 'Service Gateway')
            self.populate_artifacts(result, oci_client.vcn_service.list_route_tables(network_compartment_ocid, vcn_id = vcn.id).data, 'route-tables', 'Route Table')
            self.populate_artifacts(result, oci_client.vcn_service.list_dhcp_options(network_compartment_ocid, vcn_id = vcn.id).data, 'dhcp-options', 'DHCP Options')
            self.populate_artifacts(result, oci_client.vcn_service.list_security_lists(network_compartment_ocid, vcn_id = vcn.id).data, 'security-lists', 'Security List')
            self.populate_artifacts(result, oci_client.vcn_service.list_subnets(network_compartment_ocid, vcn_id = vcn.id).data, 'subnets', 'Subnet')
            self.populate_artifacts(result, oci_client.vcn_service.list_local_peering_gateways(network_compartment_ocid, vcn_id = vcn.id).data, 'local-peering-gateways', 'Local Peering Gateway')
            self.populate_artifacts(result, oci_client.vcn_service.list_network_security_groups(network_compartment_ocid, vcn_id = vcn.id).data, 'network-security-groups', 'Network Security group')
            break

        self.populate_artifacts(result, oci_client.vcn_service.list_drgs(network_compartment_ocid).data, 'drgs', 'Dynamic Routing Gateway')

        return result