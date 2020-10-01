import oci_utils
import spreadsheet_utils
import os
import yaml
import report_builder
import sys

DEFAULT_WORK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace'))
CONFIG_FILE_NAME = 'config.yaml'

def get_writers(working_path, config):

    writers = []

    for writer_name in config['writers']:

        if writer_name == 'spreadsheet':
            writers.append(spreadsheet_utils.SpreadSheetWriter(working_path, config))

    return writers

def close_writers(writers):

    for writer in writers:
        writer.close()


def get_config(working_path):

    config = None

    with open(os.path.join(working_path, CONFIG_FILE_NAME), 'r') as f:
        config = yaml.safe_load(f)

    config['process-data'] = {}
    
    return config

def process(base_path = DEFAULT_WORK_PATH):

    oci_client = oci_utils.OCIClient()

    config = get_config(base_path)

    print('')
    print('Process started using work path ', base_path)
    writers = get_writers(base_path, config)

    for report_data in config['reports']:
        print('Processing', report_data['name'], '...')
        vcn_artifacts = oci_client.get_vcn_artifacts(oci_client, report_data['network-compartment-ocid'])

        report_builder.process_compartment_tree(report_data, oci_client, writers)
        report_builder.process_vcn(report_data, vcn_artifacts, writers)
        report_builder.process_network_artifacts(report_data, vcn_artifacts, writers)
        report_builder.process_routing_tables(report_data, vcn_artifacts, writers)
        report_builder.process_dhcp_options(report_data, vcn_artifacts, writers)
        report_builder.process_security_lists(report_data, vcn_artifacts, writers)
        report_builder.process_subnets(report_data, vcn_artifacts, writers)
        report_builder.process_local_peering_gateways(report_data, vcn_artifacts, writers)
        report_builder.process_network_security_groups(report_data, oci_client, vcn_artifacts, writers)

    close_writers(writers)

    print('Done')
    print('')


if __name__ == '__main__':

    if len(sys.argv) == 1:
        process()
    else:
        process(sys.argv[1])
