def build_compartment_tree(oci_client, compartment_ocid, compartment_tree, parent_compartment_name = None):

    compartment_response = oci_client.identity_service.get_compartment(compartment_id = compartment_ocid)
    compartment = compartment_response.data

    if not parent_compartment_name is None:
        compartment_tree.append(
            [
                compartment.name,
                compartment.description,
                parent_compartment_name
            ]
        )

    child_compartments_response = oci_client.identity_service.list_compartments(compartment_ocid)
    child_compartments = child_compartments_response.data

    for child_compartment in child_compartments:
        build_compartment_tree(oci_client, child_compartment.id, compartment_tree, parent_compartment_name=compartment.name)


def write_table(writers, report_name, title, column_list, row_list):

    for writer in writers:
        writer.write_table(
            report_name,
            title,
            column_list,
            row_list
        )


def process_compartment_tree(report_data, oci_client, writers):

    root_compartment_ocid = report_data['compartment-ocid']

    compartment_tree = []
    build_compartment_tree(oci_client, root_compartment_ocid, compartment_tree)

    title = 'Step 1: Compartments'
    column_list = [
        {   
            'name': 'Compartment name',
            'description': 'Compartment name'
        },
        {   
            'name': 'Description',
            'description': 'Compartment description'
        },
        {   
            'name': 'Parent Compartment',
            'description': 'Parent Compartment name'
        }
    ]
    row_list = compartment_tree

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )


def process_vcn(report_data, vcn_artifacts, writers):

    title = 'Step 2: VCN'
    column_list = [
        {   
            'name': 'VCN name',
            'description': 'VCN name'
        },
        {   
            'name': 'CIDR',
            'description': 'CIDR'
        },
        {   
            'name': 'DNS Label',
            'description': 'DNS Label'
        }
    ]

    row_list = []
    vcn = vcn_artifacts['vcn']
    row_list.append(
        [
            vcn.display_name,
            vcn.cidr_block,
            vcn.dns_label
        ]
    )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def get_artifact_list(vcn_artifacts, artifact_list_key):

    result = []

    for artifact_ocid in vcn_artifacts[artifact_list_key]:
        result.append(
            vcn_artifacts['artifacts'][artifact_ocid]['artifact']
        )

    return result


def process_network_artifacts(report_data, vcn_artifacts, writers):

    title = 'Step 3: Network Artifacts'
    column_list = [
        {   
            'name': 'Artifact',
            'description': 'Artifact'
        },
        {   
            'name': 'Artifact name',
            'description': 'Artifact name'
        }
    ]

    row_list = []

    for nat_gateway in get_artifact_list(vcn_artifacts, 'nat-gateways'):
        row_list.append(
            [
                'NAT Gateway',
                nat_gateway.display_name
            ]
        )

    for service_gateway in get_artifact_list(vcn_artifacts, 'service-gateways'):
        row_list.append(
            [
                'Service Gateway',
                service_gateway.display_name
            ]
        )

    for drg in get_artifact_list(vcn_artifacts, 'drgs'):
        row_list.append(
            [
                'Dynamic Routing Gateway',
                drg.display_name
            ]
        )


    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )


def process_routing_tables(report_data, vcn_artifacts, writers):

    title = 'Step 4: Route Tables'
    column_list = [
        {   
            'name': 'RT Name',
            'description': 'Routing table name'
        },
        {   
            'name': 'Destination / Prefix',
            'description': 'CIDR'
        },
        {   
            'name': 'Target Type',
            'description': 'Target Type'
        },
        {   
            'name': 'Target',
            'description': 'Target'
        },
        {   
            'name': 'Description',
            'description': 'Description'
        }
    ]

    row_list = []

    for route_table in get_artifact_list(vcn_artifacts, 'route-tables'):
        for route_rule in route_table.route_rules:

            target = vcn_artifacts['artifacts'].get(route_rule.network_entity_id)
            if not target is None:
                target_type = target['display-type']
                target_name = target['artifact'].display_name
            else:
                target_type = 'NOT FOUND'
                target_name = 'NOT FOUND'

            row_list.append(
                [
                    route_table.display_name,
                    route_rule.destination,
                    target_type,
                    target_name,
                    route_rule.description
                ]
            )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def process_dhcp_options(report_data, vcn_artifacts, writers):

    title = 'Step 5: DHCP Options'
    column_list = [
        {   
            'name': 'DHCP Opt Name',
            'description': 'DHCP Opt Name'
        },
        {   
            'name': 'Type',
            'description': 'Type'
        },
        {   
            'name': 'Search Domain',
            'description': 'Search Domain'
        }
    ]

    row_list = []

    for dhcp_option in get_artifact_list(vcn_artifacts, 'dhcp-options'):
        display_name = dhcp_option.display_name
        server_type = ''
        search_domain_names = '' 
        for option in dhcp_option.options:
            if option.type == 'SearchDomain':
                for search_domain_name in option.search_domain_names:
                    search_domain_names += search_domain_name + ' '
            if option.type == 'DomainNameServer':
                server_type = option.server_type

        row_list.append(
            [
                display_name,
                server_type,
                search_domain_names
            ]
        )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def get_protocol_description(protocol):

    if protocol == '1':
        return 'ICMP'

    if protocol == '6':
        return 'TCP'
        
    if protocol == '17':
        return 'UDP'
        
    if protocol == '58':
        return 'ICMPv6'

    if protocol == 'all':
        return 'All Protocols'
        
    return protocol + ' (NOT FOUND)'

def add_to_row_list(row_list, display_name, ingress_egress, security_rule):

    is_stateless = "Yes" if security_rule.is_stateless else "No"
    if ingress_egress == 'Ingress':
        source = security_rule.source
    else:
        source = security_rule.destination
    ip_protocol = get_protocol_description(security_rule.protocol)
    source_port_range = 'All'
    destination_port_range = 'All'
    if not security_rule.tcp_options is None:
        if not security_rule.tcp_options.destination_port_range is None:
            port_range = security_rule.tcp_options.destination_port_range
            if port_range.max == port_range.min:
                destination_port_range = str(port_range.max)
            else:
                destination_port_range = str(port_range.min) + '-' + str(port_range.max)
        if not security_rule.tcp_options.source_port_range is None:
            port_range = security_rule.tcp_options.source_port_range
            if port_range.max == port_range.min:
                source_port_range = str(port_range.max)
            else:
                source_port_range = str(port_range.min) + '-' + str(port_range.max)
    type_and_code = ''
    if not security_rule.icmp_options is None:
        if not security_rule.icmp_options.type is None:
            type_and_code = str(security_rule.icmp_options.type)
        if not security_rule.icmp_options.code is None:
            type_and_code += ', ' + str(security_rule.icmp_options.code)
    allows = 'All traffic for' if security_rule.protocol == 'all' else ip_protocol + ' traffic for'
    if ip_protocol == 'ICMP':
        if not type_and_code == '':
            allows += ' ' + type_and_code
            if '3' in type_and_code:
                allows += ' Destination Unreachable'
            if '4' in type_and_code:
                allows += " Fragmentation Needed and Don't Fragment was Set"
    else:
        if destination_port_range == 'All':
            allows += ' all ports'
        else:
            allows += ' ports ' + destination_port_range
    description = security_rule.description
    row_list.append(
        [
            display_name,
            ingress_egress,
            is_stateless,
            source,
            ip_protocol,
            source_port_range,
            destination_port_range,
            type_and_code,
            allows,
            description
        ]
    )

def process_security_lists(report_data, vcn_artifacts, writers):

    title = 'Step 6: Security Lists'
    column_list = [
        {   
            'name': 'Security List',
            'description': 'Security List'
        },
        {   
            'name': 'Ingress / Egress',
            'description': 'Ingress / Egress'
        },
        {   
            'name': 'Stateless?',
            'description': 'Stateless?'
        },
        {   
            'name': 'Source',
            'description': 'Source'
        },
        {   
            'name': 'IP Protocol',
            'description': 'IP Protocol'
        },
        {   
            'name': 'Source Port Range',
            'description': 'Source Port Range'
        },
        {   
            'name': 'Destination Port Range',
            'description': 'Destination Port Range'
        },
        {   
            'name': 'Type and Code',
            'description': 'Type and Code'
        },
        {   
            'name': 'Allows',
            'description': 'Allows'
        },
        {   
            'name': 'Description',
            'description': 'Description'
        },
    ]

    row_list = []

    for security_list in get_artifact_list(vcn_artifacts, 'security-lists'):
        display_name = security_list.display_name
        for security_rule in security_list.ingress_security_rules:
            ingress_egress = 'Ingress'
            add_to_row_list(row_list, display_name, ingress_egress, security_rule)
        for security_rule in security_list.egress_security_rules:
            ingress_egress = 'Egress'
            add_to_row_list(row_list, display_name, ingress_egress, security_rule)

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def process_subnets(report_data, vcn_artifacts, writers):

    title = 'Step 7: Subnets'
    column_list = [
        {   
            'name': 'Name',
            'description': 'Name'
        },
        {   
            'name': 'CIDR',
            'description': 'CIDR'
        },
        {   
            'name': 'DNS Label',
            'description': 'DNS Label'
        }
    ]

    row_list = []

    for subnet in get_artifact_list(vcn_artifacts, 'subnets'):
        display_name = subnet.display_name
        cidr = subnet.cidr_block
        dns_label = subnet.dns_label 

        row_list.append(
            [
                display_name,
                cidr,
                dns_label
            ]
        )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def process_local_peering_gateways(report_data, vcn_artifacts, writers):

    title = 'Step 8: Local Peering Gateway Configuration'
    column_list = [
        {   
            'name': 'Name',
            'description': 'Name'
        },
        {   
            'name': 'CIDR',
            'description': 'CIDR'
        }
    ]

    row_list = []

    for local_peering_gateway in get_artifact_list(vcn_artifacts, 'local-peering-gateways'):
        display_name = local_peering_gateway.display_name
        cidr = local_peering_gateway.peer_advertised_cidr

        row_list.append(
            [
                display_name,
                cidr
            ]
        )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

def process_network_security_groups(report_data, oci_client, vcn_artifacts, writers):

    title = 'Step 9: Network Security groups'
    column_list = [
        {   
            'name': 'Name',
            'description': 'Name'
        },
        {   
            'name': 'Direction',
            'description': 'Direction'
        },
        {   
            'name': 'Stateless',
            'description': 'Stateless'
        },
        {   
            'name': 'Source/Destination',
            'description': 'Source/Destination'
        },
        {   
            'name': 'Type',
            'description': 'Type'
        },
        {   
            'name': 'Protocol',
            'description': 'Protocol'
        },
        {   
            'name': 'Source Port Range',
            'description': 'Source Port Range'
        },
        {   
            'name': 'Destination Port Range',
            'description': 'Source Port Range'
        },
        {   
            'name': 'Allows',
            'description': 'Allows'
        },
        {   
            'name': 'Description',
            'description': 'Description'
        }

    ]

    row_list = []

    for network_security_group in get_artifact_list(vcn_artifacts, 'network-security-groups'):
        display_name = network_security_group.display_name
        security_rules = oci_client.vcn_service.list_network_security_group_security_rules(network_security_group.id).data
        for security_rule in security_rules:
            direction = security_rule.direction
            stateless = 'No' if security_rule.is_stateless is None else 'Yes' if security_rule.is_stateless else 'No'
            if not security_rule.source is None:
                source_destination =  security_rule.source
                source_destination_type = security_rule.source_type
            else:
                source_destination =  security_rule.destination
                source_destination_type = security_rule.destination_type
            ip_protocol = get_protocol_description(security_rule.protocol)
            source_port_range = 'All'
            destination_port_range = 'All'
            if not security_rule.tcp_options is None:
                if not security_rule.tcp_options.destination_port_range is None:
                    port_range = security_rule.tcp_options.destination_port_range
                    if port_range.max == port_range.min:
                        destination_port_range = str(port_range.max)
                    else:
                        destination_port_range = str(port_range.min) + '-' + str(port_range.max)
                if not security_rule.tcp_options.source_port_range is None:
                    port_range = security_rule.tcp_options.source_port_range
                    if port_range.max == port_range.min:
                        source_port_range = str(port_range.max)
                    else:
                        source_port_range = str(port_range.min) + '-' + str(port_range.max)
            type_and_code = ''
            if not security_rule.icmp_options is None:
                if not security_rule.icmp_options.type is None:
                    type_and_code = str(security_rule.icmp_options.type)
                if not security_rule.icmp_options.code is None:
                    type_and_code += ', ' + str(security_rule.icmp_options.code)
            allows = 'All traffic for' if security_rule.protocol == 'all' else ip_protocol + ' traffic for'
            if ip_protocol == 'ICMP':
                if not type_and_code == '':
                    allows += ' ' + type_and_code
                    if '3' in type_and_code:
                        allows += ' Destination Unreachable'
                    if '4' in type_and_code:
                        allows += " Fragmentation Needed and Don't Fragment was Set"
            else:
                if destination_port_range == 'All':
                    allows += ' all ports'
                else:
                    allows += ' ports ' + destination_port_range
            description = security_rule.description


            row_list.append(
                [
                    display_name,
                    direction,
                    stateless,
                    source_destination,
                    source_destination_type,
                    ip_protocol,
                    source_port_range,
                    destination_port_range,
                    allows,
                    description
                ]
            )

    write_table(
        writers,
        report_data['name'],
        title, 
        column_list, 
        row_list
    )

